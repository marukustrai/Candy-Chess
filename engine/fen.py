"""Forsyth-Edwards Notation (FEN) load and save.

FEN uses classic letters (KQRBNP / kqrbnp), not candy names, as required by
the Phase 1 rules. A FEN string has six fields:

1. Piece placement, ranks 8 to 1, files a to h. Digits are empty squares.
2. Side to move: w (Light) or b (Dark).
3. Castling rights: KQkq, or '-' if none remain.
4. En passant target square, or '-'.
5. Half-move clock (plies since the last jelly-bean move or capture).
6. Full-move number (starts at 1; increments after each Dark move).
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.board import Board
from engine.pieces import Color, Piece, PieceType
from engine.squares import Square

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

_LETTERS = {typ.letter: typ for typ in PieceType}


@dataclass(frozen=True)
class CastlingRights:
    """The four Phase 1 castling flags."""

    light_kingside: bool = True
    light_queenside: bool = True
    dark_kingside: bool = True
    dark_queenside: bool = True

    def fen(self) -> str:
        text = ""
        if self.light_kingside:
            text += "K"
        if self.light_queenside:
            text += "Q"
        if self.dark_kingside:
            text += "k"
        if self.dark_queenside:
            text += "q"
        return text or "-"

    @classmethod
    def from_fen(cls, text: str) -> CastlingRights:
        if text == "-":
            return cls(False, False, False, False)
        unknown = set(text) - set("KQkq")
        if unknown:
            raise ValueError(f"Invalid castling field: {text!r}")
        return cls(
            light_kingside="K" in text,
            light_queenside="Q" in text,
            dark_kingside="k" in text,
            dark_queenside="q" in text,
        )

    def without(self, **flags: bool) -> CastlingRights:
        """Return a copy with the named flags changed (pass False to clear a right)."""
        data = {
            "light_kingside": self.light_kingside,
            "light_queenside": self.light_queenside,
            "dark_kingside": self.dark_kingside,
            "dark_queenside": self.dark_queenside,
        }
        data.update(flags)
        return CastlingRights(**data)


@dataclass
class FenPosition:
    board: Board
    side_to_move: Color
    castling: CastlingRights
    ep_square: Square | None
    halfmove_clock: int
    fullmove_number: int


def parse_fen(fen: str) -> FenPosition:
    """Parse a FEN string. Raises ValueError if a field is malformed."""
    parts = fen.strip().split()
    if len(parts) != 6:
        raise ValueError(f"FEN must have 6 fields, got {len(parts)}: {fen!r}")
    placement, side, castle, ep, half, full = parts

    board = Board()
    ranks = placement.split("/")
    if len(ranks) != 8:
        raise ValueError(f"FEN placement must have 8 ranks: {placement!r}")
    for rank_index, rank_text in enumerate(reversed(ranks)):
        # ranks in FEN are written 8 → 1; reversed() walks 1 → 8 (index 0 → 7).
        file = 0
        for ch in rank_text:
            if ch.isdigit():
                file += int(ch)
                if file > 8:
                    raise ValueError(f"Too many squares in FEN rank: {rank_text!r}")
                continue
            typ = _LETTERS.get(ch.upper())
            if typ is None:
                raise ValueError(f"Unknown FEN piece letter: {ch!r}")
            if file > 7:
                raise ValueError(f"Too many squares in FEN rank: {rank_text!r}")
            color = Color.LIGHT if ch.isupper() else Color.DARK
            board.set(Square(file, rank_index), Piece(typ, color))
            file += 1
        if file != 8:
            raise ValueError(f"FEN rank does not cover 8 squares: {rank_text!r}")

    side_to_move = Color.parse(side)
    castling = CastlingRights.from_fen(castle)

    if ep == "-":
        ep_square = None
    else:
        ep_square = Square.parse(ep)

    try:
        halfmove_clock = int(half)
        fullmove_number = int(full)
    except ValueError as exc:
        raise ValueError(f"FEN clocks must be integers: {fen!r}") from exc
    if halfmove_clock < 0 or fullmove_number < 1:
        raise ValueError(f"FEN clocks out of range: {fen!r}")

    return FenPosition(
        board=board,
        side_to_move=side_to_move,
        castling=castling,
        ep_square=ep_square,
        halfmove_clock=halfmove_clock,
        fullmove_number=fullmove_number,
    )


def board_placement_fen(board: Board) -> str:
    """The first FEN field: piece placement only."""
    ranks: list[str] = []
    for rank in range(7, -1, -1):
        empty = 0
        chars: list[str] = []
        for file in range(8):
            piece = board.get(Square(file, rank))
            if piece is None:
                empty += 1
                continue
            if empty:
                chars.append(str(empty))
                empty = 0
            chars.append(piece.letter)
        if empty:
            chars.append(str(empty))
        ranks.append("".join(chars))
    return "/".join(ranks)


def dump_fen(
    board: Board,
    side_to_move: Color,
    castling: CastlingRights,
    ep_square: Square | None,
    halfmove_clock: int,
    fullmove_number: int,
) -> str:
    """Build a six-field FEN string."""
    ep = "-" if ep_square is None else str(ep_square)
    return " ".join(
        [
            board_placement_fen(board),
            side_to_move.fen_letter,
            castling.fen(),
            ep,
            str(halfmove_clock),
            str(fullmove_number),
        ]
    )
