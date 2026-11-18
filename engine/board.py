"""An 8×8 board of candy pieces.

The board is stored as board[file][rank], matching the official coordinates:
a1 is (0, 0) and h8 is (7, 7). Empty squares hold None.
"""

from __future__ import annotations

from engine.pieces import Color, Piece, PieceType
from engine.squares import ALL_SQUARES, Square, SquareLike


# Back-rank order from file a to file h, same for Light (rank 1) and Dark (rank 8).
BACK_RANK_TYPES: tuple[PieceType, ...] = (
    PieceType.ROOK,
    PieceType.KNIGHT,
    PieceType.BISHOP,
    PieceType.QUEEN,
    PieceType.KING,
    PieceType.BISHOP,
    PieceType.KNIGHT,
    PieceType.ROOK,
)


class Board:
    """A simple 8×8 grid. Use Game for rules, clocks, and legal moves."""

    def __init__(self, grid: list[list[Piece | None]] | None = None) -> None:
        # grid[file][rank] — eight files, each with eight ranks.
        if grid is None:
            self._grid = [[None] * 8 for _ in range(8)]
        else:
            if len(grid) != 8 or any(len(col) != 8 for col in grid):
                raise ValueError("Board must be 8×8")
            self._grid = grid

    def copy(self) -> Board:
        """Return a new board with the same pieces (piece objects are immutable)."""
        return Board([col[:] for col in self._grid])

    def get(self, square: SquareLike) -> Piece | None:
        sq = Square.parse(square)
        return self._grid[sq.file][sq.rank]

    def set(self, square: SquareLike, piece: Piece | None) -> None:
        sq = Square.parse(square)
        self._grid[sq.file][sq.rank] = piece

    def __getitem__(self, square: SquareLike) -> Piece | None:
        return self.get(square)

    def __setitem__(self, square: SquareLike, piece: Piece | None) -> None:
        self.set(square, piece)

    def pieces(self) -> list[tuple[Square, Piece]]:
        """All occupied squares, as (square, piece) pairs."""
        occupied: list[tuple[Square, Piece]] = []
        for square in ALL_SQUARES:
            piece = self.get(square)
            if piece is not None:
                occupied.append((square, piece))
        return occupied

    def find_king(self, color: Color) -> Square:
        """Return the square of this side's giant lollipop (king)."""
        for square, piece in self.pieces():
            if piece.type is PieceType.KING and piece.color is color:
                return square
        raise ValueError(f"No {color.value} king (lollipop) on the board")

    def piece_counts(self, color: Color | None = None) -> dict[PieceType, int]:
        """How many of each type are on the board, optionally for one side."""
        counts = {typ: 0 for typ in PieceType}
        for _, piece in self.pieces():
            if color is None or piece.color is color:
                counts[piece.type] += 1
        return counts

    @classmethod
    def starting(cls) -> Board:
        """The standard opening layout from docs/rules/legal-moves.md."""
        board = cls()
        for file, typ in enumerate(BACK_RANK_TYPES):
            board.set(Square(file, 0), Piece(typ, Color.LIGHT))
            board.set(Square(file, 7), Piece(typ, Color.DARK))
        for file in range(8):
            board.set(Square(file, 1), Piece(PieceType.PAWN, Color.LIGHT))
            board.set(Square(file, 6), Piece(PieceType.PAWN, Color.DARK))
        return board

    def ascii(self, candy: bool = False) -> str:
        """A printable board. Rank 8 is at the top, as Light sees it from below.

        By default, classic letters are used (uppercase Light, lowercase Dark).
        Pass candy=True to use the two-letter candy abbreviations instead
        (a leading L/D marks the side, e.g. LJB, DLP).
        """
        lines: list[str] = []
        for rank in range(7, -1, -1):
            cells: list[str] = []
            for file in range(8):
                piece = self._grid[file][rank]
                if piece is None:
                    cells.append("  . " if candy else ".")
                elif candy:
                    side = "L" if piece.color is Color.LIGHT else "D"
                    cells.append(f"{side}{piece.type.abbreviation}")
                else:
                    cells.append(piece.letter)
            if candy:
                lines.append(f"{rank + 1}  " + " ".join(cells))
            else:
                lines.append(f"{rank + 1}  " + " ".join(f"{c:2}" for c in cells))
        if candy:
            lines.append("    " + "  ".join(f" {f} " for f in "abcdefgh"))
        else:
            lines.append("   " + " ".join(f"{f:2}" for f in "abcdefgh"))
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.ascii()
