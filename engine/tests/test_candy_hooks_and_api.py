"""Candy metadata does not change legality; Phase 2 hooks stay off."""

from engine import CANDY_NAMES, ChessAPI, Color, Game, Phase1Rules, Piece, PieceType
from engine.hooks import Ruleset
from engine.moves import Move


class RecordingHooks(Phase1Rules):
    """A test ruleset that records hook calls but does not change legality."""

    name = "recording"

    def __init__(self) -> None:
        self.moves: list[str] = []
        self.promotions: list[str] = []

    def on_move(self, before, move, after) -> None:  # type: ignore[no-untyped-def]
        self.moves.append(move.uci())

    def on_promotion(self, before, move, after) -> None:  # type: ignore[no-untyped-def]
        self.promotions.append(move.uci())


class ThemeHooks(Phase1Rules):
    """Pretend Phase 2 color themes — names change, moves must not."""

    name = "themes"

    def candy_for(self, piece: Piece) -> str:
        if piece.color is Color.LIGHT:
            return f"Fruity {piece.candy_name}"
        return f"Cocoa {piece.candy_name}"


def test_starting_pieces_carry_locked_candy_names():
    game = Game.starting()
    expected = {
        "e1": ("king", "Giant Lollipop"),
        "d1": ("queen", "Chocolate Truffle Box"),
        "a1": ("rook", "Licorice Stick"),
        "c1": ("bishop", "Candy Cane"),
        "b1": ("knight", "Gummy Bear"),
        "a2": ("pawn", "Jelly Bean"),
    }
    for square, (typ, candy) in expected.items():
        piece = game.board.get(square)
        assert piece is not None
        assert piece.type.value == typ
        assert piece.candy_name == candy
        assert CANDY_NAMES[piece.type] == candy


def test_board_json_includes_candy_and_color_metadata():
    data = Game.starting().board_json()
    by_square = {p["square"]: p for p in data["pieces"]}
    king = by_square["e1"]
    assert king["candy_name"] == "Giant Lollipop"
    assert king["color"] == "light"
    assert king["classic_color"] == "white"
    assert king["type"] == "king"
    dark_king = by_square["e8"]
    assert dark_king["color"] == "dark"
    assert dark_king["classic_color"] == "black"
    assert dark_king["candy_name"] == "Giant Lollipop"
    assert data["phase"] == 1
    assert data["side_to_move"] == "light"


def test_candy_names_do_not_change_legal_moves():
    plain = {m.uci() for m in Game.starting().legal_moves()}
    themed = {m.uci() for m in Game.starting(hooks=ThemeHooks()).legal_moves()}
    assert plain == themed
    assert len(plain) == 20
    # The themed hook only changes displayed names.
    themed_game = Game.starting(hooks=ThemeHooks())
    data = themed_game.to_dict(include_moves=False)
    king = next(p for p in data["pieces"] if p["square"] == "e1")
    assert king["candy_name"] == "Fruity Giant Lollipop"


def test_phase1_hooks_do_not_add_twists():
    game = Game.starting()
    hooks = game.hooks
    assert isinstance(hooks, Phase1Rules)
    assert hooks.extra_legal_moves(game) == []
    assert hooks.is_move_legal(game, game.legal_moves()[0]) is None
    # No sugar-rush points, no melting state, no one-time swap on the game.
    assert not hasattr(game, "sugar_points")
    assert not hasattr(game, "swap_used")
    assert not hasattr(game, "melt_counters")


def test_promotion_does_not_place_an_extra_pawn():
    fen = "4k3/6P1/8/8/8/8/8/4K3 w - - 0 1"
    before = Game.from_fen(fen)
    pawns_before = before.board.piece_counts()[PieceType.PAWN]
    after = before.apply("g7g8q")
    # The bean is replaced, not kept, and no extra bean is added (no Phase 2 bonus).
    assert after.board.get("g8").type is PieceType.QUEEN
    assert after.board.piece_counts()[PieceType.PAWN] == pawns_before - 1


def test_hooks_fire_on_real_applies_only():
    hooks = RecordingHooks()
    game = Game.from_fen("4k3/6P1/8/8/8/8/8/4K3 w - - 0 1", hooks=hooks)
    # Asking for SAN / legal moves should not record a real apply.
    game.legal_moves()
    assert hooks.moves == []
    game = game.apply("g7g8q")
    assert hooks.moves == ["g7g8q"]
    assert hooks.promotions == ["g7g8q"]


def test_json_facade_new_game_moves_and_illegal():
    api = ChessAPI()
    state = api.new_game()
    assert state["ok"] is True
    assert state["fen"].startswith("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
    game_id = state["game_id"]
    listed = api.legal_moves(game_id, "e2")
    uci = {m["uci"] for m in listed["moves"]}
    assert uci == {"e2e3", "e2e4"}
    after = api.apply(game_id, "e2e4")
    assert after["ok"] is True
    assert after["status"]["state"] == "in_progress"
    # A dark-side move is required next; e2e4 again is illegal.
    bad = api.apply(game_id, "e4e5")
    assert bad["ok"] is False
    assert "illegal" in bad["error"] or "rejected" in bad["error"]
    assert "message" in bad


def test_scholars_mate_through_the_api():
    api = ChessAPI()
    state = api.new_game()
    game_id = state["game_id"]
    for move in ["e4", "e5", "Qh5", "Nc6", "Bc4", "Nf6", "Qxf7"]:
        state = api.apply(game_id, move)
        assert state["ok"] is True, state
    assert state["status"]["state"] == "checkmate"
    assert state["status"]["winner"] == "light"
