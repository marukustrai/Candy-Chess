"""Scholar's mate, pins, illegal moves, and stalemate."""

import pytest

from engine import Game, IllegalMoveError, PieceType


def test_scholars_mate():
    # 1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7#
    game = Game.starting()
    for move in ["e4", "e5", "Qh5", "Nc6", "Bc4", "Nf6", "Qxf7"]:
        game = game.apply(move)
    status = game.status()
    assert status.state == "checkmate"
    assert status.reason == "checkmate"
    assert status.winner == "light"
    assert status.in_check is True
    assert game.legal_moves() == []
    with pytest.raises(Exception):
        game.apply("e8e7")


def test_pin_cannot_expose_the_king():
    # Light lollipop on e1, Light gummy bear on e2, Dark truffle box on e8.
    # The bear is pinned and may not step off the e-file.
    fen = "4q3/8/8/8/8/8/4N3/4K3 w - - 0 1"
    game = Game.from_fen(fen)
    uci = {m.uci() for m in game.legal_moves_from("e2")}
    # Legal along the pin file? Nothing is open on e-file for a knight.
    # All knight landings leave the e-file, so there should be no moves from e2.
    assert uci == set()
    assert game.is_legal("e2c3") is False
    assert game.is_legal("e2d4") is False
    with pytest.raises(IllegalMoveError):
        game.apply("e2c3")


def test_pinned_rook_may_slide_along_the_pin():
    # Light king e1, Light rook e2, Dark queen e8. The rook may move on the e-file.
    fen = "4q3/8/8/8/8/8/4R3/4K3 w - - 0 1"
    game = Game.from_fen(fen)
    uci = {m.uci() for m in game.legal_moves_from("e2")}
    assert "e2e3" in uci
    assert "e2e8" in uci  # capture the queen, still on the pin line
    assert "e2d2" not in uci
    assert "e2a2" not in uci


def test_illegal_move_rejected_from_start():
    game = Game.starting()
    assert game.is_legal("e2e5") is False
    assert game.is_legal("e1e2") is False
    with pytest.raises(IllegalMoveError):
        game.apply("e2e5")
    # The original position is unchanged (apply does not mutate, and the
    # failed call never returned a new game).
    assert game.board.get("e2").type is PieceType.PAWN


def test_moving_the_wrong_side_is_illegal():
    game = Game.starting()
    with pytest.raises(IllegalMoveError):
        game.apply("e7e5")


def test_stalemate():
    # Classic: Dark king on a8, Light king on c6, Light queen on b6? Wait.
    # A well-known stalemate: king a8, pawn a7, opposing king a6 is pawn stalemate.
    # Use: Light king c1, Light queen a3? Better known FEN:
    # 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1  — queen on f7, kings on h8 and g6.
    # Black to move is stalemated (h8 has no escape; not in check).
    fen = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
    game = Game.from_fen(fen)
    status = game.status()
    assert status.state == "stalemate"
    assert status.reason == "stalemate"
    assert status.winner is None
    assert status.in_check is False
    assert game.legal_moves() == []


def test_check_is_not_mate_when_escapes_exist():
    fen = "4k3/8/8/8/8/8/4R3/4K3 b - - 0 1"
    game = Game.from_fen(fen)
    status = game.status()
    assert status.state == "check"
    assert status.in_check is True
    assert status.winner is None
    assert len(game.legal_moves()) > 0
