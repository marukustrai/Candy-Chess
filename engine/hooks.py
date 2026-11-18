"""Ruleset hooks so Phase 2 twists can be added later without rewriting the core.

Phase 1 uses standard FIDE / classic chess rules only. The default ruleset,
Phase1Rules, returns locked candy names and otherwise does nothing.

These hooks exist as empty extension points. They are documented here so a
later ruleset can plug in, but **no Phase 2 twist is implemented or enabled**
in the default game:

1. Sugar Rush — points per move, a special move at 5 points.
   A later ruleset could tally points in on_move and add a move in
   extra_legal_moves once the total reaches 5.
2. Melting — pieces that stand still for N turns lose power.
   A later ruleset could track stillness in on_move and filter or weaken
   moves in is_move_legal.
3. Candy Swap — once per game, swap two of your own pieces.
   A later ruleset could expose that as an extra legal move.
4. Promotion Bonus — promoting a jelly bean also places a free extra bean.
   A later ruleset could do that in on_promotion.
5. Color themes — Light fruity/sour, Dark chocolate/licorice skins.
   A later ruleset could return themed names from candy_for. Phase 1 uses
   the same locked candy names for both sides (finish is metadata only).

Do not enable any of the above in default play.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from engine.pieces import CANDY_NAMES, Piece

if TYPE_CHECKING:
    from engine.game import Game
    from engine.moves import Move


@runtime_checkable
class Ruleset(Protocol):
    """The hook interface a Game talks to. Phase1Rules is the default."""

    def candy_for(self, piece: Piece) -> str:
        """Return the display name for this piece."""
        ...

    def extra_legal_moves(self, game: Game) -> list[Move]:
        """Extra moves to add after standard legal-move generation.

        Phase 1 must return an empty list.
        """
        ...

    def is_move_legal(self, game: Game, move: Move) -> bool | None:
        """Optional extra filter. Return None to leave the Phase 1 answer alone.

        True/False would allow a later ruleset to add or veto a move.
        Phase 1 always returns None.
        """
        ...

    def on_move(self, before: Game, move: Move, after: Game) -> None:
        """Called after a legal move is applied. Phase 1 is a no-op."""
        ...

    def on_promotion(self, before: Game, move: Move, after: Game) -> None:
        """Called after a promotion is applied. Phase 1 is a no-op."""
        ...


class Phase1Rules:
    """Classic chess only. Candy names are locked; every other hook is a no-op."""

    name = "phase1"

    def candy_for(self, piece: Piece) -> str:
        return CANDY_NAMES[piece.type]

    def extra_legal_moves(self, game: Game) -> list[Move]:
        return []

    def is_move_legal(self, game: Game, move: Move) -> bool | None:
        return None

    def on_move(self, before: Game, move: Move, after: Game) -> None:
        return None

    def on_promotion(self, before: Game, move: Move, after: Game) -> None:
        return None
