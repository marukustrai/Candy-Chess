"""Fifty-move, threefold repetition, insufficient material, and agreement."""

from engine import Game


def test_fifty_move_rule_at_100_halfmoves():
    # 50 moves by each side = half-move clock 100. A quiet king move from a
    # position already at 99 should trip the draw.
    fen = "4k3/8/8/8/8/8/8/4K2R w - - 99 60"
    game = Game.from_fen(fen)
    assert game.status().state == "in_progress"
    after = game.apply("h1h2")
    status = after.status()
    assert status.state == "draw"
    assert status.reason == "fifty_move"
    assert after.halfmove_clock == 100
    assert after.legal_moves() == []


def test_pawn_move_resets_the_fifty_move_clock():
    fen = "8/8/8/8/8/P7/8/K6k w - - 99 60"
    game = Game.from_fen(fen).apply("a3a4")
    assert game.halfmove_clock == 0
    assert game.status().state != "draw" or game.status().reason != "fifty_move"


def test_threefold_repetition():
    # Knights jump out and back, twice, repeating the start position.
    # 1. Nf3 Nf6 2. Ng1 Ng8 3. Nf3 Nf6 4. Ng1 Ng8 — start appears three times
    # (start, after 2...Ng8, after 4...Ng8).
    game = Game.starting()
    start_key = game.position_keys[-1]
    sequence = ["Nf3", "Nf6", "Ng1", "Ng8", "Nf3", "Nf6", "Ng1", "Ng8"]
    for san in sequence:
        game = game.apply(san)
    assert game.position_keys.count(start_key) >= 3
    status = game.status()
    assert status.state == "draw"
    assert status.reason == "threefold"


def test_insufficient_material_king_vs_king():
    game = Game.from_fen("8/8/8/8/8/8/8/K6k w - - 0 1")
    status = game.status()
    assert status.state == "draw"
    assert status.reason == "insufficient_material"


def test_insufficient_material_king_and_bishop():
    game = Game.from_fen("8/8/8/8/8/8/8/K5Bk w - - 0 1")
    assert game.status().reason == "insufficient_material"
    assert game.status().state == "draw"


def test_insufficient_material_king_and_knight():
    game = Game.from_fen("8/8/8/8/8/8/8/K5Nk w - - 0 1")
    assert game.status().reason == "insufficient_material"


def test_insufficient_material_same_color_bishops():
    # Both canes sit on light-colored squares (c1 and a3? a1 is dark,
    # c1 is dark, b1 is light, d1 is light? a1=(0,0) parity 0 dark;
    # c1=(2,0) parity 0 dark; b2=(1,1) parity 0 dark.
    # Light squares have parity 1: b1=(1,0), c2=(2,1), a2=(0,1).
    # FEN: 8/8/8/8/8/2B5/8/K1B4k — wait we need one bishop each.
    # Light bishop on c1 (dark square), Dark bishop on a3 (a3=(0,2) parity 0, dark).
    fen = "8/8/8/8/8/b7/8/K1B4k w - - 0 1"
    game = Game.from_fen(fen)
    assert game.status().reason == "insufficient_material"

    # Opposite-color bishops are NOT a draw under this rule (mate is possible).
    # Light bishop on c1 (dark), Dark bishop on b3 (b3=(1,2) parity 1, light).
    fen2 = "8/8/8/8/8/1b6/8/K1B4k w - - 0 1"
    game2 = Game.from_fen(fen2)
    assert game2.status().state != "draw" or game2.status().reason != "insufficient_material"


def test_queen_is_enough_material():
    game = Game.from_fen("8/8/8/8/8/8/8/K5Qk w - - 0 1")
    assert game.status().state != "draw" or game.status().reason != "insufficient_material"


def test_draw_by_agreement():
    game = Game.starting().apply("e4").agree_draw()
    status = game.status()
    assert status.state == "draw"
    assert status.reason == "agreement"
    assert game.legal_moves() == []
