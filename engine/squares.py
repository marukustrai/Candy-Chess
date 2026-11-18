"""Squares on the 8×8 Candy Chess board.

The official Phase 1 rules use this numbering (see docs/rules/legal-moves.md):

- File (column) index: a=0, b=1, c=2, d=3, e=4, f=5, g=6, h=7
- Rank (row) index:    1=0, 2=1, 3=2, 4=3, 5=4, 6=5, 7=6, 8=7
- A square is always written as (file, rank), so a1 is (0, 0) and h8 is (7, 7).

Rank 1 is Light's back row. Rank 8 is Dark's back row.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Union

FILES = "abcdefgh"
RANKS = "12345678"


def in_bounds(file: int, rank: int) -> bool:
    """Return True if both indexes are on the board (0 through 7)."""
    return 0 <= file <= 7 and 0 <= rank <= 7


@dataclass(frozen=True, order=True)
class Square:
    """One square, stored as a (file, rank) pair of indexes."""

    file: int
    rank: int

    def __post_init__(self) -> None:
        if not in_bounds(self.file, self.rank):
            raise ValueError(f"Square out of bounds: ({self.file}, {self.rank})")

    def __str__(self) -> str:
        """Algebraic name, such as 'e4'."""
        return f"{FILES[self.file]}{self.rank + 1}"

    def __repr__(self) -> str:
        return f"Square({self!s})"

    def offset(self, df: int, dr: int) -> Square | None:
        """Return the square df files and dr ranks away, or None if off the board."""
        file = self.file + df
        rank = self.rank + dr
        if in_bounds(file, rank):
            return Square(file, rank)
        return None

    def color_parity(self) -> int:
        """0 for dark-colored squares (including a1), 1 for light-colored squares.

        Used only for the optional same-color-bishop insufficient-material draw.
        """
        return (self.file + self.rank) % 2

    @classmethod
    def parse(cls, value: SquareLike) -> Square:
        """Build a Square from 'e4', a Square, or a (file, rank) tuple."""
        if isinstance(value, Square):
            return value
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) == 2:
            return cls(int(value[0]), int(value[1]))
        if isinstance(value, str):
            text = value.strip().lower()
            if len(text) != 2 or text[0] not in FILES or text[1] not in RANKS:
                raise ValueError(f"Invalid square: {value!r}")
            return cls(FILES.index(text[0]), int(text[1]) - 1)
        raise TypeError(f"Cannot parse square from {value!r}")


SquareLike = Union[Square, str, tuple[int, int]]

# Every square, rank by rank, a1 through h8. Handy for loops.
ALL_SQUARES: tuple[Square, ...] = tuple(Square(file, rank) for rank in range(8) for file in range(8))
