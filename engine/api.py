"""A JSON-friendly facade the frontend can call without using Game objects directly.

Each method takes and returns plain dicts / lists / strings, so a JavaScript
UI can talk to the engine over the optional HTTP server, or a Python caller
can use this class as a thin wrapper around Game.
"""

from __future__ import annotations

from engine.game import Game, GameOverError, IllegalMoveError
from engine.hooks import Phase1Rules, Ruleset
from engine.moves import Move
from engine.squares import Square


class ChessAPI:
    """Stateless helpers plus a tiny in-memory store of live games (for the server)."""

    def __init__(self, hooks: Ruleset | None = None) -> None:
        self.hooks = hooks if hooks is not None else Phase1Rules()
        self._games: dict[str, Game] = {}
        self._next_id = 1

    def new_game(self) -> dict[str, object]:
        """Start a Phase 1 game from the standard position and store it."""
        game = Game.starting(hooks=self.hooks)
        game_id = str(self._next_id)
        self._next_id += 1
        self._games[game_id] = game
        return self._pack(game_id, game)

    def from_fen(self, fen: str) -> dict[str, object]:
        game = Game.from_fen(fen, hooks=self.hooks)
        game_id = str(self._next_id)
        self._next_id += 1
        self._games[game_id] = game
        return self._pack(game_id, game)

    def get(self, game_id: str) -> dict[str, object]:
        return self._pack(game_id, self._require(game_id))

    def legal_moves(self, game_id: str, square: str | None = None) -> dict[str, object]:
        game = self._require(game_id)
        if square:
            moves = game.legal_moves_from(Square.parse(square))
        else:
            moves = game.legal_moves()
        return {
            "game_id": game_id,
            "square": square,
            "moves": [game._move_dict(m) for m in moves],
        }

    def apply(self, game_id: str, move: str) -> dict[str, object]:
        """Apply a UCI or SAN move. Illegal moves return a clear error dict."""
        game = self._require(game_id)
        try:
            nxt = game.apply(move)
        except (IllegalMoveError, GameOverError, ValueError) as exc:
            return {
                "ok": False,
                "error": "illegal_move" if isinstance(exc, IllegalMoveError) else "rejected",
                "message": str(exc),
                "game_id": game_id,
                "status": game.status().to_dict(),
            }
        self._games[game_id] = nxt
        packed = self._pack(game_id, nxt)
        packed["ok"] = True
        packed["applied"] = move
        return packed

    def snapshot(self, game: Game) -> dict[str, object]:
        """Serialize any Game (including one you built yourself) as JSON data."""
        return game.to_dict(include_moves=True)

    def apply_to_fen(self, fen: str, move: str) -> dict[str, object]:
        """Apply a move to a FEN and return the new state (no stored game).

        Repetition history starts at this FEN, so use a stored game if you
        need a full threefold record across many moves.
        """
        game = Game.from_fen(fen, hooks=self.hooks)
        try:
            nxt = game.apply(move)
        except (IllegalMoveError, GameOverError, ValueError) as exc:
            return {
                "ok": False,
                "error": "illegal_move" if isinstance(exc, IllegalMoveError) else "rejected",
                "message": str(exc),
                "fen": fen,
                "status": game.status().to_dict(),
            }
        data = nxt.to_dict(include_moves=True)
        data["ok"] = True
        data["applied"] = move
        return data

    def _require(self, game_id: str) -> Game:
        try:
            return self._games[game_id]
        except KeyError as exc:
            raise KeyError(f"Unknown game_id: {game_id}") from exc

    def _pack(self, game_id: str, game: Game) -> dict[str, object]:
        data = game.to_dict(include_moves=True)
        data["game_id"] = game_id
        data["ok"] = True
        return data


def move_to_json(game: Game, move: Move) -> dict[str, object]:
    """Public wrapper around a single move's JSON description."""
    return game._move_dict(move)
