"""The playable Phase 1 game: legal moves, applying a move, and game status.

Game.apply() returns a new Game; the original is left unchanged. That makes
undo, hooks, and tests easier. Moves may be a Move, a UCI string (e2e4,
e7e8q), or SAN (Nf3, O-O, e8=Q). If a promoting jelly bean is given
without a piece (e7e8), the simple APIs default to a truffle box (queen).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from engine.board import Board
from engine.fen import (
    STARTING_FEN,
    CastlingRights,
    board_placement_fen,
    dump_fen,
    parse_fen,
)
from engine.hooks import Phase1Rules, Ruleset
from engine.moves import (
    CASTLE_SPECS,
    Move,
    ROOK_HOME,
    captured_square,
    describe_move,
    generate_pseudo_legal,
    in_check,
    is_castle_move,
    is_en_passant_move,
)
from engine.pieces import PROMOTION_TYPES, Color, Piece, PieceType
from engine.squares import Square, SquareLike


class IllegalMoveError(ValueError):
    """Raised when apply() is given a move that is not legal in this position."""


class GameOverError(ValueError):
    """Raised when apply() is called after the game has already ended."""


# Status.state values used by the API and the frontend.
IN_PROGRESS = "in_progress"
CHECK = "check"
CHECKMATE = "checkmate"
STALEMATE = "stalemate"
DRAW = "draw"


@dataclass(frozen=True)
class Status:
    """What the current position means for the players."""

    state: str
    reason: str | None
    winner: str | None  # 'light' or 'dark' only when someone has won
    in_check: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "state": self.state,
            "reason": self.reason,
            "winner": self.winner,
            "in_check": self.in_check,
        }

    @property
    def is_over(self) -> bool:
        return self.state in {CHECKMATE, STALEMATE, DRAW}


def _position_key(
    board: Board,
    side: Color,
    castling: CastlingRights,
    ep_for_repetition: Square | None,
) -> str:
    """Identity of a position for the threefold-repetition draw.

    The half-move and full-move clocks do not count. En passant is included
    only when a legal en passant capture actually exists in this position.
    """
    ep = str(ep_for_repetition) if ep_for_repetition is not None else "-"
    return f"{board_placement_fen(board)} {side.fen_letter} {castling.fen()} {ep}"


@dataclass(frozen=True)
class Game:
    """A full Phase 1 position, plus the history needed for draws.

    Use Game.starting() or Game() for the opening setup, or Game.from_fen()
    to load a position. apply() returns a new Game and does not mutate this one.
    """

    board: Board = field(default_factory=Board.starting)
    side_to_move: Color = Color.LIGHT
    castling: CastlingRights = field(default_factory=CastlingRights)
    ep_square: Square | None = None
    halfmove_clock: int = 0
    fullmove_number: int = 1
    # Captured candies, in the order they left the board. Display-only in Phase 1.
    candy_jar_light: tuple[Piece, ...] = ()
    candy_jar_dark: tuple[Piece, ...] = ()
    # Position keys after each ply, including the starting position.
    position_keys: tuple[str, ...] = ()
    agreed_draw: bool = False
    move_history: tuple[str, ...] = ()  # UCI strings, for records and the CLI
    hooks: Ruleset = field(default_factory=Phase1Rules)

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def starting(cls, hooks: Ruleset | None = None) -> Game:
        """The standard opening position. Light to move."""
        return cls.from_fen(STARTING_FEN, hooks=hooks)

    @classmethod
    def from_fen(cls, fen: str, hooks: Ruleset | None = None) -> Game:
        """Load a FEN. The candy jar starts empty; repetition is counted from here."""
        rules = hooks if hooks is not None else Phase1Rules()
        parsed = parse_fen(fen)
        game = cls(
            board=parsed.board,
            side_to_move=parsed.side_to_move,
            castling=parsed.castling,
            ep_square=parsed.ep_square,
            halfmove_clock=parsed.halfmove_clock,
            fullmove_number=parsed.fullmove_number,
            hooks=rules,
        )
        key = game._repetition_key()
        return replace(game, position_keys=(key,))

    def __post_init__(self) -> None:
        # Game() with no arguments is the starting position. Fill the
        # repetition key if a caller did not pass a history of their own.
        if not self.position_keys:
            object.__setattr__(self, "position_keys", (self._repetition_key(),))

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def fen(self) -> str:
        """Current position as a standard six-field FEN string."""
        return dump_fen(
            self.board,
            self.side_to_move,
            self.castling,
            self.ep_square,
            self.halfmove_clock,
            self.fullmove_number,
        )

    def is_in_check(self) -> bool:
        return in_check(self.board, self.side_to_move)

    def legal_moves(self) -> list[Move]:
        """Every legal move for the side to move, including promotions as four choices."""
        if self.agreed_draw:
            return []
        # Insufficient material and the 50-move rule end the game at once,
        # so no further moves are offered.
        if self._is_automatic_draw():
            return []
        moves: list[Move] = []
        for move in generate_pseudo_legal(
            self.board, self.side_to_move, self.castling, self.ep_square
        ):
            if self._leaves_king_safe(move) and self._hook_allows(move):
                moves.append(move)
        for extra in self.hooks.extra_legal_moves(self):
            # Phase 1 returns nothing. A later ruleset could add moves here.
            if extra not in moves:
                moves.append(extra)
        return moves

    def legal_moves_from(self, square: SquareLike) -> list[Move]:
        start = Square.parse(square)
        return [m for m in self.legal_moves() if m.start == start]

    def is_legal(self, move: Move | str) -> bool:
        try:
            parsed = self._parse_move(move, default_promotion=True)
        except ValueError:
            return False
        return any(self._same_move(parsed, legal) for legal in self.legal_moves())

    def status(self) -> Status:
        """in_progress / check / checkmate / stalemate / draw, plus reason and winner."""
        if self.agreed_draw:
            return Status(DRAW, "agreement", None, in_check=False)

        checked = self.is_in_check()
        # Legal-move generation would recurse through status if we are not careful,
        # so compute moves without going through the automatic-draw early exit
        # after we have already handled agreement. We still want mate to beat
        # a 50-move claim if a side has no move and is in check.
        raw_moves = self._legal_moves_ignoring_draw_clocks()

        if not raw_moves:
            if checked:
                winner = self.side_to_move.opponent.value
                return Status(CHECKMATE, "checkmate", winner, in_check=True)
            return Status(STALEMATE, "stalemate", None, in_check=False)

        if self._insufficient_material():
            return Status(DRAW, "insufficient_material", None, in_check=checked)
        if self.halfmove_clock >= 100:
            return Status(DRAW, "fifty_move", None, in_check=checked)
        if self._threefold():
            return Status(DRAW, "threefold", None, in_check=checked)
        if checked:
            return Status(CHECK, None, None, in_check=True)
        return Status(IN_PROGRESS, None, None, in_check=False)

    # ------------------------------------------------------------------
    # Applying moves (immutable)
    # ------------------------------------------------------------------

    def apply(self, move: Move | str) -> Game:
        """Return a new game with the move played. Raises IllegalMoveError if not legal."""
        status = self.status()
        if status.is_over:
            raise GameOverError(f"The game is already over ({status.state})")
        parsed = self._parse_move(move, default_promotion=True)
        legal = self._match_legal(parsed)
        if legal is None:
            raise IllegalMoveError(f"Illegal move: {parsed.uci()}")
        return self._apply_legal(legal, notify_hooks=True)

    def agree_draw(self) -> Game:
        """Both sides agree to a draw. Returns a new Game marked as drawn."""
        if self.status().is_over:
            raise GameOverError("The game is already over")
        return replace(self, agreed_draw=True)

    def perft(self, depth: int) -> int:
        """Count the leaf nodes of the legal-move tree. Used by tests."""
        if depth < 0:
            raise ValueError("depth must be >= 0")
        if depth == 0:
            return 1
        moves = self._legal_moves_ignoring_draw_clocks()
        if depth == 1:
            return len(moves)
        return sum(self._apply_legal(move).perft(depth - 1) for move in moves)

    # ------------------------------------------------------------------
    # Notation
    # ------------------------------------------------------------------

    def to_uci(self, move: Move) -> str:
        return move.uci()

    def to_san(self, move: Move) -> str:
        """Standard algebraic notation (e4, Nf3, O-O, exd5, e8=Q, Qxf7#)."""
        legal = self._match_legal(move)
        if legal is None:
            # Still try to render, but disambiguation uses legal moves only.
            legal = self._parse_move(move, default_promotion=False) if not isinstance(move, Move) else move
        return self._san(legal)

    def parse_move(self, text: str) -> Move:
        """Parse a UCI or SAN string in this position. Promotions default to queen."""
        return self._parse_move(text, default_promotion=True)

    # ------------------------------------------------------------------
    # JSON / frontend
    # ------------------------------------------------------------------

    def board_json(self, include_moves: bool = True) -> dict[str, object]:
        return self.to_dict(include_moves=include_moves)

    def to_dict(self, include_moves: bool = True) -> dict[str, object]:
        """JSON-friendly snapshot the frontend can render without extra lookups."""
        status = self.status()
        pieces = []
        for square, piece in self.board.pieces():
            data = piece.to_dict(candy_name=self.hooks.candy_for(piece))
            data["square"] = str(square)
            pieces.append(data)

        def jar(items: tuple[Piece, ...]) -> list[dict[str, str]]:
            return [p.to_dict(candy_name=self.hooks.candy_for(p)) for p in items]

        result: dict[str, object] = {
            "fen": self.fen(),
            "side_to_move": self.side_to_move.value,
            "classic_side_to_move": self.side_to_move.classic,
            "pieces": pieces,
            "castling": {
                "light_kingside": self.castling.light_kingside,
                "light_queenside": self.castling.light_queenside,
                "dark_kingside": self.castling.dark_kingside,
                "dark_queenside": self.castling.dark_queenside,
            },
            "en_passant": str(self.ep_square) if self.ep_square else None,
            "halfmove_clock": self.halfmove_clock,
            "fullmove_number": self.fullmove_number,
            "status": status.to_dict(),
            "candy_jar": {
                "light": jar(self.candy_jar_light),
                "dark": jar(self.candy_jar_dark),
            },
            "move_history": list(self.move_history),
            "phase": 1,
            "ruleset": getattr(self.hooks, "name", self.hooks.__class__.__name__),
        }
        if include_moves:
            result["legal_moves"] = [self._move_dict(m) for m in self.legal_moves()]
        return result

    def _move_dict(self, move: Move) -> dict[str, object]:
        data = describe_move(self.board, move, self.ep_square)
        data["san"] = self._san(move)
        # Check / mate flags after the move, so the UI can decorate it.
        after = self._apply_legal(move)
        after_status = after.status()
        flags = data["flags"]  # type: ignore[assignment]
        assert isinstance(flags, dict)
        flags["check"] = after_status.in_check and after_status.state != CHECKMATE
        flags["checkmate"] = after_status.state == CHECKMATE
        return data

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _hook_allows(self, move: Move) -> bool:
        verdict = self.hooks.is_move_legal(self, move)
        # None means "no opinion" — keep the Phase 1 answer.
        return True if verdict is None else bool(verdict)

    def _leaves_king_safe(self, move: Move) -> bool:
        nxt = self._play_on_board(move)
        return not in_check(nxt, self.side_to_move)

    def _legal_moves_ignoring_draw_clocks(self) -> list[Move]:
        moves: list[Move] = []
        for move in generate_pseudo_legal(
            self.board, self.side_to_move, self.castling, self.ep_square
        ):
            if self._leaves_king_safe(move) and self._hook_allows(move):
                moves.append(move)
        for extra in self.hooks.extra_legal_moves(self):
            if extra not in moves:
                moves.append(extra)
        return moves

    def _is_automatic_draw(self) -> bool:
        return self._insufficient_material() or self.halfmove_clock >= 100 or self._threefold()

    def _threefold(self) -> bool:
        if not self.position_keys:
            return False
        current = self.position_keys[-1]
        return self.position_keys.count(current) >= 3

    def _repetition_key(self) -> str:
        # En passant rights count only when a legal EP capture exists.
        ep = self.ep_square if self._has_legal_en_passant() else None
        return _position_key(self.board, self.side_to_move, self.castling, ep)

    def _has_legal_en_passant(self) -> bool:
        if self.ep_square is None:
            return False
        for move in generate_pseudo_legal(
            self.board, self.side_to_move, self.castling, self.ep_square
        ):
            if is_en_passant_move(self.board, move, self.ep_square) and self._leaves_king_safe(move):
                return True
        return False

    def _insufficient_material(self) -> bool:
        """True when neither side has enough material left to checkmate.

        Always drawn, as the rules require:
        - lollipop vs lollipop
        - lollipop + candy cane vs lollipop
        - lollipop + gummy bear vs lollipop

        Also treated as a draw (standard FIDE, documented in engine/README.md):
        - lollipop + candy cane vs lollipop + candy cane, both canes on the
          same square color, so they can never force mate.
        """
        light = [(sq, p) for sq, p in self.board.pieces() if p.color is Color.LIGHT]
        dark = [(sq, p) for sq, p in self.board.pieces() if p.color is Color.DARK]

        def minors(side: list[tuple[Square, Piece]]) -> list[tuple[Square, Piece]] | None:
            """Non-king pieces, or None if a heavy piece / bean is present (mate still possible)."""
            others: list[tuple[Square, Piece]] = []
            for sq, piece in side:
                if piece.type is PieceType.KING:
                    continue
                if piece.type in {PieceType.QUEEN, PieceType.ROOK, PieceType.PAWN}:
                    return None
                others.append((sq, piece))
            return others

        light_minors = minors(light)
        dark_minors = minors(dark)
        if light_minors is None or dark_minors is None:
            return False

        # Two lone lollipops, or one side has a single cane or bear.
        total = len(light_minors) + len(dark_minors)
        if total == 0:
            return True
        if total == 1:
            only = (light_minors or dark_minors)[0][1]
            return only.type in {PieceType.BISHOP, PieceType.KNIGHT}

        # K+B vs K+B, same-color bishops (FIDE; optional but included).
        if (
            len(light_minors) == 1
            and len(dark_minors) == 1
            and light_minors[0][1].type is PieceType.BISHOP
            and dark_minors[0][1].type is PieceType.BISHOP
        ):
            return light_minors[0][0].color_parity() == dark_minors[0][0].color_parity()
        return False

    def _play_on_board(self, move: Move) -> Board:
        """Apply the piece movement to a copy of the board (no clocks or rights)."""
        board = self.board.copy()
        piece = board.get(move.start)
        if piece is None:
            raise IllegalMoveError(f"No piece on {move.start}")

        cap = captured_square(board, move, self.ep_square)
        if cap is not None:
            board.set(cap, None)

        board.set(move.start, None)
        placed = piece if move.promotion is None else Piece(move.promotion, piece.color)
        board.set(move.end, placed)

        if is_castle_move(self.board, move):
            side = "kingside" if move.end.file == 6 else "queenside"
            _king_start, _king_end, rook_start, rook_end, _between, _path = CASTLE_SPECS[(piece.color, side)]
            rook = board.get(rook_start)
            board.set(rook_start, None)
            board.set(rook_end, rook)
        return board

    def _apply_legal(self, move: Move, *, notify_hooks: bool = False) -> Game:
        piece = self.board.get(move.start)
        assert piece is not None
        cap_sq = captured_square(self.board, move, self.ep_square)
        captured = self.board.get(cap_sq) if cap_sq is not None else None

        new_board = self._play_on_board(move)
        new_rights = self._updated_rights(move, cap_sq)
        new_ep = self._updated_ep(move, piece)

        if piece.type is PieceType.PAWN or captured is not None:
            half = 0
        else:
            half = self.halfmove_clock + 1

        full = self.fullmove_number
        if self.side_to_move is Color.DARK:
            full += 1

        light_jar = self.candy_jar_light
        dark_jar = self.candy_jar_dark
        if captured is not None:
            if self.side_to_move is Color.LIGHT:
                light_jar = light_jar + (captured,)
            else:
                dark_jar = dark_jar + (captured,)

        nxt = Game(
            board=new_board,
            side_to_move=self.side_to_move.opponent,
            castling=new_rights,
            ep_square=new_ep,
            halfmove_clock=half,
            fullmove_number=full,
            candy_jar_light=light_jar,
            candy_jar_dark=dark_jar,
            position_keys=self.position_keys,  # filled below
            agreed_draw=False,
            move_history=self.move_history + (move.uci(),),
            hooks=self.hooks,
        )
        nxt = replace(nxt, position_keys=self.position_keys + (nxt._repetition_key(),))
        if notify_hooks:
            self.hooks.on_move(self, move, nxt)
            if move.promotion is not None:
                self.hooks.on_promotion(self, move, nxt)
        return nxt

    def _updated_rights(self, move: Move, cap_sq: Square | None) -> CastlingRights:
        rights = self.castling
        piece = self.board.get(move.start)
        assert piece is not None
        flags: dict[str, bool] = {}
        if piece.type is PieceType.KING:
            if piece.color is Color.LIGHT:
                flags["light_kingside"] = False
                flags["light_queenside"] = False
            else:
                flags["dark_kingside"] = False
                flags["dark_queenside"] = False
        for sq in (move.start, cap_sq):
            if sq is None:
                continue
            flag = ROOK_HOME.get(sq)
            if flag is not None:
                flags[flag] = False
        return rights.without(**flags) if flags else rights

    def _updated_ep(self, move: Move, piece: Piece) -> Square | None:
        # A two-square jelly-bean first move sets the skipped square as the target.
        if piece.type is PieceType.PAWN and abs(move.end.rank - move.start.rank) == 2:
            skipped_rank = (move.start.rank + move.end.rank) // 2
            return Square(move.start.file, skipped_rank)
        return None

    def _same_move(self, a: Move, b: Move) -> bool:
        return a.start == b.start and a.end == b.end and a.promotion == b.promotion

    def _match_legal(self, move: Move) -> Move | None:
        for legal in self.legal_moves():
            if self._same_move(move, legal):
                return legal
        return None

    def _parse_move(self, move: Move | str, default_promotion: bool) -> Move:
        if isinstance(move, Move):
            if move.promotion is None and default_promotion:
                return self._default_promo(move)
            return move
        text = move.strip()
        if not text:
            raise ValueError("Empty move")
        # UCI first (e2e4, e7e8q, e1g1).
        if len(text) in (4, 5) and text[0] in "abcdefgh" and text[1] in "12345678":
            try:
                parsed = Move.from_uci(text)
            except ValueError:
                parsed = None
            else:
                return self._default_promo(parsed) if default_promotion else parsed
        return self._parse_san(text, default_promotion=default_promotion)

    def _default_promo(self, move: Move) -> Move:
        if move.promotion is not None:
            return move
        piece = self.board.get(move.start)
        if piece is not None and piece.type is PieceType.PAWN and move.end.rank == piece.color.promotion_rank:
            return Move(move.start, move.end, PieceType.QUEEN)
        return move

    def _san(self, move: Move) -> str:
        piece = self.board.get(move.start)
        if piece is None:
            return move.uci()

        if is_castle_move(self.board, move):
            core = "O-O" if move.end.file == 6 else "O-O-O"
        else:
            cap = captured_square(self.board, move, self.ep_square) is not None
            dest = str(move.end)
            if piece.type is PieceType.PAWN:
                core = f"{'abcdefgh'[move.start.file]}x{dest}" if cap else dest
            else:
                letter = piece.type.letter
                dis = self._disambiguate(move, piece)
                core = f"{letter}{dis}{'x' if cap else ''}{dest}"
            if move.promotion is not None:
                core += f"={move.promotion.letter}"

        after = self._apply_legal(move)
        after_status = after.status()
        if after_status.state == CHECKMATE:
            core += "#"
        elif after_status.in_check:
            core += "+"
        return core

    def _disambiguate(self, move: Move, piece: Piece) -> str:
        """Add file and/or rank when another identical piece can also go there."""
        others = [
            m
            for m in self._legal_moves_ignoring_draw_clocks()
            if m is not move
            and m.end == move.end
            and m.promotion == move.promotion
            and (p := self.board.get(m.start)) is not None
            and p.type is piece.type
            and p.color is piece.color
            and m.start != move.start
        ]
        if not others:
            return ""
        same_file = any(m.start.file == move.start.file for m in others)
        same_rank = any(m.start.rank == move.start.rank for m in others)
        file_letter = "abcdefgh"[move.start.file]
        rank_letter = str(move.start.rank + 1)
        if not same_file:
            return file_letter
        if not same_rank:
            return rank_letter
        return file_letter + rank_letter

    def _parse_san(self, text: str, default_promotion: bool) -> Move:
        raw = text.strip()
        raw = raw.replace("0-0-0", "O-O-O").replace("0-0", "O-O")
        raw = raw.replace("o-o-o", "O-O-O").replace("o-o", "O-O")
        while raw.endswith(("+", "#", "!", "?")):
            raw = raw[:-1]

        if raw in {"O-O", "O-O-O"}:
            wanted_file = 6 if raw == "O-O" else 2
            for move in self._legal_moves_ignoring_draw_clocks():
                if is_castle_move(self.board, move) and move.end.file == wanted_file:
                    return move
            raise ValueError(f"Illegal castling move: {text!r}")

        promo: PieceType | None = None
        if "=" in raw:
            raw, promo_letter = raw.split("=", 1)
            promo = PieceType.parse(promo_letter)
        elif raw and raw[-1] in "QRBNqrbn" and len(raw) >= 3 and raw[-2] in "12345678":
            # Also accept e8Q, without the equals sign.
            promo = PieceType.parse(raw[-1])
            raw = raw[:-1]

        raw = raw.replace("x", "").replace("X", "")
        if len(raw) < 2:
            raise ValueError(f"Invalid SAN: {text!r}")
        dest = Square.parse(raw[-2:])
        prefix = raw[:-2]

        start_file: int | None = None
        start_rank: int | None = None
        if prefix == "":
            typ = PieceType.PAWN
        elif len(prefix) == 1 and prefix in "abcdefgh":
            typ = PieceType.PAWN
            start_file = "abcdefgh".index(prefix)
        else:
            typ = PieceType.parse(prefix[0])
            rest = prefix[1:]
            if rest and rest[0] in "abcdefgh":
                start_file = "abcdefgh".index(rest[0])
                rest = rest[1:]
            if rest and rest[0] in "12345678":
                start_rank = int(rest[0]) - 1
                rest = rest[1:]
            if rest:
                raise ValueError(f"Invalid SAN: {text!r}")

        candidates: list[Move] = []
        for move in self._legal_moves_ignoring_draw_clocks():
            mover = self.board.get(move.start)
            if mover is None or mover.type is not typ:
                continue
            if move.end != dest:
                continue
            if start_file is not None and move.start.file != start_file:
                continue
            if start_rank is not None and move.start.rank != start_rank:
                continue
            if promo is not None:
                if move.promotion is not promo:
                    continue
            elif move.promotion is not None:
                if not (default_promotion and move.promotion is PieceType.QUEEN):
                    continue
            candidates.append(move)

        if len(candidates) == 1:
            return candidates[0]
        if not candidates:
            raise ValueError(f"No legal move matches {text!r}")
        raise ValueError(f"Ambiguous move {text!r}")

    def __str__(self) -> str:
        status = self.status()
        lines = [self.board.ascii(), f"{self.side_to_move.value.capitalize()} to move."]
        if status.in_check and status.state != CHECKMATE:
            lines.append("Check!")
        if status.is_over:
            lines.append(f"Game over: {status.state}" + (f" ({status.reason})" if status.reason else ""))
            if status.winner:
                lines.append(f"Winner: {status.winner}")
        return "\n".join(lines)
