"""Castling: legal cases, path, check, and lost rights."""

import pytest

from engine import Game, IllegalMoveError


def _uci(game, square=None):
    moves = game.legal_moves_from(square) if square else game.legal_moves()
    return {m.uci() for m in moves}


def test_both_sides_can_castle_when_clear():
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    game = Game.from_fen(fen)
    assert "e1g1" in _uci(game, "e1")
    assert "e1c1" in _uci(game, "e1")
    kingside = game.apply("e1g1")
    assert kingside.board.get("g1").type.value == "king"
    assert kingside.board.get("f1").type.value == "rook"
    assert kingside.board.get("e1") is None
    assert kingside.board.get("h1") is None
    # Rights are gone after Light castles.
    assert kingside.castling.light_kingside is False
    assert kingside.castling.light_queenside is False
    # After Light's king-side castle the stick sits on f1 and attacks f8,
    # so Dark cannot castle king-side (the lollipop would cross a checked
    # square). Queen-side is still legal, and Dark's remaining rights are intact.
    assert "e8c8" in _uci(kingside, "e8")
    assert "e8g8" not in _uci(kingside, "e8")
    assert kingside.castling.dark_kingside is True
    assert kingside.castling.dark_queenside is True
    # Dark to move can castle king-side from the original position.
    dark_to_move = Game.from_fen("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
    assert "e8g8" in _uci(dark_to_move, "e8")
    assert "e8c8" in _uci(dark_to_move, "e8")

    queenside = game.apply("O-O-O")
    assert queenside.board.get("c1").type.value == "king"
    assert queenside.board.get("d1").type.value == "rook"
    assert queenside.board.get("a1") is None


def test_cannot_castle_through_check():
    # Dark rook on f8 attacks f1, so Light may not castle king-side.
    fen = "4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1"
    # add a rook on f8 — use a position with r on f8.
    fen = "5r1k/8/8/8/8/8/8/R3K2R w KQ - 0 1"
    game = Game.from_fen(fen)
    assert "e1g1" not in _uci(game, "e1")
    # Queen-side does not cross f1, so it may still be legal if d1 and c1 are safe.
    # f8 rook attacks f1 only, not d1/c1/e1. Queen-side should be allowed.
    assert "e1c1" in _uci(game, "e1")


def test_cannot_castle_into_check():
    # Dark rook on g8 attacks g1.
    fen = "6rk/8/8/8/8/8/8/R3K2R w KQ - 0 1"
    game = Game.from_fen(fen)
    assert "e1g1" not in _uci(game, "e1")


def test_cannot_castle_out_of_check():
    fen = "4r2k/8/8/8/8/8/8/R3K2R w KQ - 0 1"
    game = Game.from_fen(fen)
    assert game.status().in_check is True
    assert "e1g1" not in _uci(game)
    assert "e1c1" not in _uci(game)


def test_cannot_castle_when_path_is_occupied():
    fen = "r3k2r/8/8/8/8/8/8/RN2K2R w KQkq - 0 1"
    game = Game.from_fen(fen)
    assert "e1c1" not in _uci(game, "e1")
    assert "e1g1" in _uci(game, "e1")


def test_queen_side_allowed_if_b1_is_attacked():
    # A dark rook on b8 attacks b1. The lollipop crosses e1, d1, c1 — not b1.
    # Queen-side castling stays legal.
    fen = "1r2k3/8/8/8/8/8/8/R3K2R w KQ - 0 1"
    game = Game.from_fen(fen)
    assert "e1c1" in _uci(game, "e1")
    after = game.apply("e1c1")
    assert after.board.get("c1").type.value == "king"
    assert after.board.get("d1").type.value == "rook"


def test_cannot_castle_after_king_moved():
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    game = Game.from_fen(fen).apply("e1e2").apply("e8e7")
    # Even stepping back, rights are gone.
    game = game.apply("e2e1").apply("e7e8")
    assert "e1g1" not in _uci(game, "e1")
    assert "e1c1" not in _uci(game, "e1")
    assert game.castling.light_kingside is False
    assert game.castling.light_queenside is False


def test_cannot_castle_after_rook_moved():
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    game = Game.from_fen(fen).apply("h1h2").apply("a8a7")
    game = game.apply("h2h1").apply("a7a8")
    assert "e1g1" not in _uci(game, "e1")
    assert "e1c1" in _uci(game, "e1")  # the a1 stick has not moved


def test_capturing_a_rook_drops_that_right():
    fen = "r3k2r/8/8/8/8/8/7B/R3K3 w kq - 0 1"
    # Light bishop on h2 captures the dark rook on h8? h2 to a? Let's put a queen on a1 capturing a8? Simpler FEN:
    fen = "r3k2r/8/8/8/8/8/8/R3K2Q w kq - 0 1"
    game = Game.from_fen(fen)
    assert game.castling.dark_kingside is True
    after = game.apply("h1h8")
    assert after.board.get("h8").type.value == "queen"
    assert after.castling.dark_kingside is False
    assert after.castling.dark_queenside is True


def test_castle_rejected_when_rights_are_already_gone():
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w - - 0 1"
    game = Game.from_fen(fen)
    assert "e1g1" not in _uci(game)
    with pytest.raises(IllegalMoveError):
        game.apply("e1g1")
