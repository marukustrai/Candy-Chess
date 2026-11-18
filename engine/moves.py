"""Moves, attack maps, and pseudo-legal move generation.

A *pseudo-legal* move follows the piece's movement rules (including
castling path-empty, en passant, and promotion) but does not yet check
that the mover's own lollipop (king) would be safe. Game.legal_moves()
filters those out.

Castling, en passant, and promotion follow docs/rules/legal-moves.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator

from engine.board import Board
from engine.fen import CastlingRights
from engine.pieces import PROMOTION_TYPES, Color, Piece, PieceType
from engine.squares import Square, SquareLike

if TYPE_CHECKING:
    pass

# One-square steps in all eight directions (the lollipop, and sliding steps).
KING_DELTAS: tuple[tuple[int, int], ...] = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

# The gummy bear's eight L-shaped landings: (file delta, rank delta).
KNIGHT_DELTAS: tuple[tuple[int, int], ...] = (
    (1, 2), (1, -2), (-1, 2), (-1, -2),
    (2, 1), (2, -1), (-2, 1), (-2, -1),
)

ROOK_DIRECTIONS: tuple[tuple[int, int], ...] = ((0, 1), (0, -1), (1, 0), (-1, 0))
BISHOP_DIRECTIONS: tuple[tuple[int, int], ...] = ((1, 1), (1, -1), (-1, 1), (-1, -1))
QUEEN_DIRECTIONS: tuple[tuple[int, int], ...] = ROOK_DIRECTIONS + BISHOP_DIRECTIONS

# King-side and queen-side castle destinations, keyed by the side that is moving.
# Values: (king_start, king_end, rook_start, rook_end, squares_between, king_path)
# king_path is every square the lollipop stands on or crosses, including start and end.
# Those must all be unattacked. The stick may pass through an attacked square
# (so b1/b8 being attacked does not block queen-side castling).
CastleSpec = tuple[Square, Square, Square, Square, tuple[Square, ...], tuple[Square, ...]]


def _castle_specs() -> dict[tuple[Color, str], CastleSpec]:
    light_ks: CastleSpec = (
        Square.parse("e1"), Square.parse("g1"),
        Square.parse("h1"), Square.parse("f1"),
        (Square.parse("f1"), Square.parse("g1")),
        (Square.parse("e1"), Square.parse("f1"), Square.parse("g1")),
    )
    light_qs: CastleSpec = (
        Square.parse("e1"), Square.parse("c1"),
        Square.parse("a1"), Square.parse("d1"),
        (Square.parse("b1"), Square.parse("c1"), Square.parse("d1")),
        (Square.parse("e1"), Square.parse("d1"), Square.parse("c1")),
    )
    dark_ks: CastleSpec = (
        Square.parse("e8"), Square.parse("g8"),
        Square.parse("h8"), Square.parse("f8"),
        (Square.parse("f8"), Square.parse("g8")),
        (Square.parse("e8"), Square.parse("f8"), Square.parse("g8")),
    )
    dark_qs: CastleSpec = (
        Square.parse("e8"), Square.parse("c8"),
        Square.parse("a8"), Square.parse("d8"),
        (Square.parse("b8"), Square.parse("c8"), Square.parse("d8")),
        (Square.parse("e8"), Square.parse("d8"), Square.parse("c8")),
    )
    return {
        (Color.LIGHT, "kingside"): light_ks,
        (Color.LIGHT, "queenside"): light_qs,
        (Color.DARK, "kingside"): dark_ks,
        (Color.DARK, "queenside"): dark_qs,
    }


CASTLE_SPECS = _castle_specs()

# Original licorice-stick squares, used to drop the matching castling right.
ROOK_HOME = {
    Square.parse("a1"): "light_queenside",
    Square.parse("h1"): "light_kingside",
    Square.parse("a8"): "dark_queenside",
    Square.parse("h8"): "dark_kingside",
}


@dataclass(frozen=True)
class Move:
    """A single move: from one square to another, with an optional promotion.

    Castling is represented as the lollipop's two-square step (e1g1, e1c1,
    e8g8, or e8c8). En passant is represented as the jelly bean moving into
    the skipped square. Flags such as capture or castle are derived from the
    position the move is played in, not stored on the move itself.
    """

    start: Square
    end: Square
    promotion: PieceType | None = None

    def __post_init__(self) -> None:
        if self.promotion is not None and self.promotion not in PROMOTION_TYPES:
            raise ValueError(f"Cannot promote to {self.promotion}")

    def uci(self) -> str:
        """Universal Chess Interface form: e2e4, e7e8q, e1g1."""
        text = f"{self.start}{self.end}"
        if self.promotion is not None:
            text += self.promotion.letter.lower()
        return text

    def __str__(self) -> str:
        return self.uci()

    @classmethod
    def from_uci(cls, text: str) -> Move:
        raw = text.strip()
        if len(raw) not in (4, 5):
            raise ValueError(f"Invalid UCI move: {text!r}")
        start = Square.parse(raw[:2])
        end = Square.parse(raw[2:4])
        promo = PieceType.parse(raw[4]) if len(raw) == 5 else None
        return cls(start, end, promo)


def _occupied_by(board: Board, square: Square, color: Color) -> bool:
    piece = board.get(square)
    return piece is not None and piece.color is color


def _is_enemy(board: Board, square: Square, color: Color) -> bool:
    piece = board.get(square)
    return piece is not None and piece.color is not color


def iter_slide(board: Board, start: Square, color: Color, directions: tuple[tuple[int, int], ...]) -> Iterator[Square]:
    """Yield every square a slider can stop on in the given directions."""
    for df, dr in directions:
        current = start.offset(df, dr)
        while current is not None:
            occupant = board.get(current)
            if occupant is None:
                yield current
            else:
                if occupant.color is not color:
                    yield current  # capture, then stop
                break
            current = current.offset(df, dr)


def pawn_attack_squares(start: Square, color: Color) -> list[Square]:
    """Squares a jelly bean on `start` attacks (diagonals ahead), even if empty."""
    ahead = color.pawn_direction
    squares: list[Square] = []
    for df in (-1, 1):
        dest = start.offset(df, ahead)
        if dest is not None:
            squares.append(dest)
    return squares


def is_square_attacked(board: Board, square: Square, by: Color) -> bool:
    """True if `by` could capture a piece sitting on `square` (pins ignored).

    Used for check and for the lollipop's path during castling. En passant
    cannot capture a lollipop, so it is not part of this attack map.
    """
    # Gummy bears (knights).
    for df, dr in KNIGHT_DELTAS:
        src = square.offset(df, dr)
        if src is None:
            continue
        piece = board.get(src)
        if piece is not None and piece.color is by and piece.type is PieceType.KNIGHT:
            return True

    # Giant lollipop (king), one step away.
    for df, dr in KING_DELTAS:
        src = square.offset(df, dr)
        if src is None:
            continue
        piece = board.get(src)
        if piece is not None and piece.color is by and piece.type is PieceType.KING:
            return True

    # Jelly beans (pawns) attack one step diagonally forward, so a bean that
    # attacks `square` stands one rank *behind* it from that bean's view.
    behind = -by.pawn_direction
    for df in (-1, 1):
        src = square.offset(df, behind)
        if src is None:
            continue
        piece = board.get(src)
        if piece is not None and piece.color is by and piece.type is PieceType.PAWN:
            return True

    # Sliding candies: licorice stick, candy cane, truffle box.
    for directions, types in (
        (ROOK_DIRECTIONS, (PieceType.ROOK, PieceType.QUEEN)),
        (BISHOP_DIRECTIONS, (PieceType.BISHOP, PieceType.QUEEN)),
    ):
        for df, dr in directions:
            current = square.offset(df, dr)
            while current is not None:
                piece = board.get(current)
                if piece is not None:
                    if piece.color is by and piece.type in types:
                        return True
                    break
                current = current.offset(df, dr)
    return False


def in_check(board: Board, color: Color) -> bool:
    """True if this side's lollipop is attacked."""
    return is_square_attacked(board, board.find_king(color), by=color.opponent)


def generate_pawn_moves(board: Board, start: Square, color: Color, ep_square: Square | None) -> Iterator[Move]:
    """Forward steps, two-square first move, diagonal captures, and en passant."""
    ahead = color.pawn_direction
    one = start.offset(0, ahead)
    if one is not None and board.get(one) is None:
        yield from _pawn_arrivals(start, one, color)
        # Two-square first move: both squares must be empty, and the bean
        # must still be on its starting rank.
        if start.rank == color.pawn_start_rank:
            two = start.offset(0, 2 * ahead)
            if two is not None and board.get(two) is None:
                yield from _pawn_arrivals(start, two, color)

    for dest in pawn_attack_squares(start, color):
        target = board.get(dest)
        if target is not None and target.color is not color:
            yield from _pawn_arrivals(start, dest, color)
        elif ep_square is not None and dest == ep_square:
            # Capture the opposing bean as if it had stepped only one square.
            yield Move(start, dest)


def _pawn_arrivals(start: Square, dest: Square, color: Color) -> Iterator[Move]:
    if dest.rank == color.promotion_rank:
        for typ in PROMOTION_TYPES:
            yield Move(start, dest, typ)
    else:
        yield Move(start, dest)


def generate_castling(
    board: Board,
    color: Color,
    rights: CastlingRights,
) -> Iterator[Move]:
    """Yield castle moves that satisfy rights, empty path, and unattacked king path.

    Queen-side is still allowed if b1/b8 is attacked, as long as the
    lollipop's own squares are safe.
    """
    sides = []
    if color is Color.LIGHT:
        if rights.light_kingside:
            sides.append("kingside")
        if rights.light_queenside:
            sides.append("queenside")
    else:
        if rights.dark_kingside:
            sides.append("kingside")
        if rights.dark_queenside:
            sides.append("queenside")

    opponent = color.opponent
    for side in sides:
        king_start, king_end, rook_start, _rook_end, between, king_path = CASTLE_SPECS[(color, side)]
        king = board.get(king_start)
        rook = board.get(rook_start)
        if king is None or king.type is not PieceType.KING or king.color is not color:
            continue
        if rook is None or rook.type is not PieceType.ROOK or rook.color is not color:
            continue
        if any(board.get(sq) is not None for sq in between):
            continue
        if any(is_square_attacked(board, sq, by=opponent) for sq in king_path):
            continue
        yield Move(king_start, king_end)


def generate_pseudo_legal(
    board: Board,
    color: Color,
    rights: CastlingRights,
    ep_square: Square | None,
) -> list[Move]:
    """All moves that follow piece movement, before king-safety is checked."""
    moves: list[Move] = []
    for start, piece in board.pieces():
        if piece.color is not color:
            continue
        typ = piece.type
        if typ is PieceType.PAWN:
            moves.extend(generate_pawn_moves(board, start, color, ep_square))
        elif typ is PieceType.KNIGHT:
            for df, dr in KNIGHT_DELTAS:
                dest = start.offset(df, dr)
                if dest is not None and not _occupied_by(board, dest, color):
                    moves.append(Move(start, dest))
        elif typ is PieceType.BISHOP:
            moves.extend(Move(start, dest) for dest in iter_slide(board, start, color, BISHOP_DIRECTIONS))
        elif typ is PieceType.ROOK:
            moves.extend(Move(start, dest) for dest in iter_slide(board, start, color, ROOK_DIRECTIONS))
        elif typ is PieceType.QUEEN:
            moves.extend(Move(start, dest) for dest in iter_slide(board, start, color, QUEEN_DIRECTIONS))
        elif typ is PieceType.KING:
            for df, dr in KING_DELTAS:
                dest = start.offset(df, dr)
                if dest is not None and not _occupied_by(board, dest, color):
                    moves.append(Move(start, dest))
    moves.extend(generate_castling(board, color, rights))
    return moves


def is_castle_move(board: Board, move: Move) -> bool:
    """True if this is a lollipop stepping two files (the Phase 1 castle move)."""
    piece = board.get(move.start)
    if piece is None or piece.type is not PieceType.KING:
        return False
    return abs(move.end.file - move.start.file) == 2 and move.start.rank == move.end.rank


def is_en_passant_move(board: Board, move: Move, ep_square: Square | None) -> bool:
    piece = board.get(move.start)
    if piece is None or piece.type is not PieceType.PAWN:
        return False
    return ep_square is not None and move.end == ep_square and board.get(move.end) is None


def captured_square(board: Board, move: Move, ep_square: Square | None) -> Square | None:
    """The square whose candy is taken, if this move is a capture (including EP)."""
    if is_en_passant_move(board, move, ep_square):
        # The captured bean sits on the start rank, on the destination file.
        return Square(move.end.file, move.start.rank)
    target = board.get(move.end)
    if target is not None:
        return move.end
    return None


def describe_move(board: Board, move: Move, ep_square: Square | None) -> dict[str, object]:
    """Flags a frontend can use without re-deriving them."""
    piece = board.get(move.start)
    castle = is_castle_move(board, move)
    ep = is_en_passant_move(board, move, ep_square)
    cap_sq = captured_square(board, move, ep_square)
    side = None
    if castle:
        side = "kingside" if move.end.file == 6 else "queenside"
    return {
        "from": str(move.start),
        "to": str(move.end),
        "promotion": move.promotion.letter if move.promotion else None,
        "piece": piece.type.value if piece else None,
        "flags": {
            "capture": cap_sq is not None,
            "en_passant": ep,
            "castle": side,
            "promotion": move.promotion is not None,
        },
        "uci": move.uci(),
    }
