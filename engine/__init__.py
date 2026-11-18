"""Candy Chess Phase 1 engine: classic chess rules with candy metadata.

The rules live in docs/rules/legal-moves.md. Candy names live in docs/pieces.md.
This package generates and validates legal moves; it does not include a
visual UI or a computer opponent.

Typical use:

    from engine import Game

    game = Game.starting()          # or Game()
    print(game.legal_moves())       # 20 moves in the opening
    game = game.apply("e2e4")       # apply() returns a new Game
    print(game.fen())
    print(game.status().state)
"""

from engine.api import ChessAPI
from engine.fen import STARTING_FEN, CastlingRights
from engine.game import (
    CHECK,
    CHECKMATE,
    DRAW,
    IN_PROGRESS,
    STALEMATE,
    Game,
    GameOverError,
    IllegalMoveError,
    Status,
)
from engine.hooks import Phase1Rules, Ruleset
from engine.moves import Move
from engine.pieces import CANDY_NAMES, Color, Piece, PieceType
from engine.squares import Square

__all__ = [
    "CANDY_NAMES",
    "CHECK",
    "CHECKMATE",
    "DRAW",
    "IN_PROGRESS",
    "STARTING_FEN",
    "STALEMATE",
    "CastlingRights",
    "ChessAPI",
    "Color",
    "Game",
    "GameOverError",
    "IllegalMoveError",
    "Move",
    "Phase1Rules",
    "Piece",
    "PieceType",
    "Ruleset",
    "Square",
    "Status",
]

__version__ = "0.1.0"
