"""Perft counts on the starting position, plus a little SAN/UCI coverage."""

from engine import Game


def test_perft_starting_depth_1():
    assert Game.starting().perft(1) == 20


def test_perft_starting_depth_2():
    assert Game.starting().perft(2) == 400


def test_perft_starting_depth_3():
    assert Game.starting().perft(3) == 8902


def test_uci_and_san_round_trip_on_common_moves():
    game = Game.starting()
    move = game.parse_move("e2e4")
    assert move.uci() == "e2e4"
    assert game.to_san(move) == "e4"
    game = game.apply(move)
    move = game.parse_move("Nf6")
    assert move.uci() == "g8f6"
    assert game.to_san(move) == "Nf6"


def test_castling_san():
    game = Game.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    assert game.to_san(game.parse_move("e1g1")) == "O-O"
    assert game.to_san(game.parse_move("O-O-O")) == "O-O-O"
    # Accept zeros as a friendly alias.
    assert game.parse_move("0-0").uci() == "e1g1"


def test_disambiguation_san():
    # Two light knights can go to d2? Put knights on b1 and f1, dest d2 is not both.
    # Knights on a3 and a5, both can go to b5? Use two rooks on a1 and h1 going to a3? 
    # FEN: two rooks on a4 and a1, both can capture? Simpler: 8/8/8/8/8/8/8/R3K2R w - - 0 1
    # Both rooks can go to a2? a1 rook can, h1 cannot go to a2 in one slide... h1 can go along rank 1 only or file h.
    # Two rooks on a1 and a3, dest a2. SAN should be... actually both on the a file, so rank disambiguation: R1a2 / R3a2.
    fen = "4k3/8/8/8/8/R7/8/R3K3 w - - 0 1"
    game = Game.from_fen(fen)
    move = game.parse_move("a1a2")
    assert game.to_san(move) == "R1a2"
    move = game.parse_move("R3a2")
    assert move.uci() == "a3a2"
