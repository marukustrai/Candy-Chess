"""Piece types, sides, and locked Phase 1 candy names.

Candy names are metadata only. They never change how a piece moves.
Sides are called Light and Dark in the rules; classic chess calls them
White and Black. Light moves first, toward rank 8. Dark moves toward rank 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Color(Enum):
    """The two sides. Light is classic White; Dark is classic Black."""

    LIGHT = "light"
    DARK = "dark"

    @property
    def classic(self) -> str:
        """Classic chess name: 'white' or 'black'."""
        return "white" if self is Color.LIGHT else "black"

    @property
    def fen_letter(self) -> str:
        """FEN side letter: 'w' or 'b'."""
        return "w" if self is Color.LIGHT else "b"

    @property
    def opponent(self) -> Color:
        return Color.DARK if self is Color.LIGHT else Color.LIGHT

    @property
    def pawn_direction(self) -> int:
        """How a jelly bean's rank index changes when it steps forward."""
        return 1 if self is Color.LIGHT else -1

    @property
    def pawn_start_rank(self) -> int:
        """Rank index of the jelly beans' starting row (1 for Light, 6 for Dark)."""
        return 1 if self is Color.LIGHT else 6

    @property
    def promotion_rank(self) -> int:
        """Rank index a jelly bean must reach to promote (7 for Light, 0 for Dark)."""
        return 7 if self is Color.LIGHT else 0

    @property
    def back_rank(self) -> int:
        """Rank index of this side's back row (0 for Light, 7 for Dark)."""
        return 0 if self is Color.LIGHT else 7

    @classmethod
    def parse(cls, value: str | Color) -> Color:
        if isinstance(value, Color):
            return value
        text = value.strip().lower()
        if text in {"light", "white", "w"}:
            return cls.LIGHT
        if text in {"dark", "black", "b"}:
            return cls.DARK
        raise ValueError(f"Invalid color: {value!r}")


class PieceType(Enum):
    """The six classic piece types. FEN/SAN letters stay KQRBNP as the rules require."""

    KING = "king"
    QUEEN = "queen"
    ROOK = "rook"
    BISHOP = "bishop"
    KNIGHT = "knight"
    PAWN = "pawn"

    @property
    def letter(self) -> str:
        """Classic letter used in FEN and SAN (P is used only in FEN)."""
        return {
            PieceType.KING: "K",
            PieceType.QUEEN: "Q",
            PieceType.ROOK: "R",
            PieceType.BISHOP: "B",
            PieceType.KNIGHT: "N",
            PieceType.PAWN: "P",
        }[self]

    @property
    def candy_name(self) -> str:
        """Locked Phase 1 candy name. The same for both sides."""
        return CANDY_NAMES[self]

    @property
    def abbreviation(self) -> str:
        """Two-letter candy abbreviation used in some board diagrams."""
        return CANDY_ABBREVIATIONS[self]

    @classmethod
    def parse(cls, value: str | PieceType) -> PieceType:
        if isinstance(value, PieceType):
            return value
        text = value.strip().lower()
        letters = {t.letter.lower(): t for t in cls}
        if text in letters:
            return letters[text]
        names = {t.value: t for t in cls}
        if text in names:
            return names[text]
        # Candy names and a few short aliases, for friendlier input.
        candies = {name.lower(): typ for typ, name in CANDY_NAMES.items()}
        if text in candies:
            return candies[text]
        aliases = {
            "lollipop": cls.KING,
            "giant lollipop": cls.KING,
            "truffle": cls.QUEEN,
            "truffle box": cls.QUEEN,
            "chocolate truffle box": cls.QUEEN,
            "licorice": cls.ROOK,
            "licorice stick": cls.ROOK,
            "cane": cls.BISHOP,
            "candy cane": cls.BISHOP,
            "gummy": cls.KNIGHT,
            "gummy bear": cls.KNIGHT,
            "bean": cls.PAWN,
            "jelly bean": cls.PAWN,
        }
        if text in aliases:
            return aliases[text]
        raise ValueError(f"Invalid piece type: {value!r}")


# Locked in docs/pieces.md. Do not use "Licorice Rope" or "Gummy Worm".
CANDY_NAMES: dict[PieceType, str] = {
    PieceType.KING: "Giant Lollipop",
    PieceType.QUEEN: "Chocolate Truffle Box",
    PieceType.ROOK: "Licorice Stick",
    PieceType.BISHOP: "Candy Cane",
    PieceType.KNIGHT: "Gummy Bear",
    PieceType.PAWN: "Jelly Bean",
}

CANDY_ABBREVIATIONS: dict[PieceType, str] = {
    PieceType.KING: "LP",
    PieceType.QUEEN: "TB",
    PieceType.ROOK: "LS",
    PieceType.BISHOP: "CC",
    PieceType.KNIGHT: "GB",
    PieceType.PAWN: "JB",
}

# Promotion may be one of these four (never a lollipop, never a jelly bean).
PROMOTION_TYPES: tuple[PieceType, ...] = (
    PieceType.QUEEN,
    PieceType.ROOK,
    PieceType.BISHOP,
    PieceType.KNIGHT,
)


@dataclass(frozen=True)
class Piece:
    """A candy on a square: classic type + side + candy name metadata."""

    type: PieceType
    color: Color

    @property
    def candy_name(self) -> str:
        return self.type.candy_name

    @property
    def letter(self) -> str:
        """FEN letter: uppercase for Light, lowercase for Dark."""
        letter = self.type.letter
        return letter if self.color is Color.LIGHT else letter.lower()

    def to_dict(self, candy_name: str | None = None) -> dict[str, str]:
        """JSON-friendly piece metadata for the frontend."""
        return {
            "type": self.type.value,
            "symbol": self.type.letter,
            "color": self.color.value,
            "classic_color": self.color.classic,
            "candy_name": candy_name if candy_name is not None else self.candy_name,
        }
