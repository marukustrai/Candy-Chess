"""En passant (including the pin case) and all promotion types."""

import pytest

from engine import Game, IllegalMoveError, PieceType


def test_en_passant_available_only_immediately():
    # Dark bean jumps d7-d5 next to a Light bean on e5.
    fen = "4k3/3p4/8/4P3/8/8/8/4K3 b - - 0 1"
    game = Game.from_fen(fen).apply("d7d5")
    assert game.ep_square is not None
    assert str(game.ep_square) == "d6"
    assert game.is_legal("e5d6")
    captured = game.apply("e5d6")
    assert captured.board.get("d6").type is PieceType.PAWN
    assert captured.board.get("d6").color.value == "light"
    assert captured.board.get("d5") is None  # the dark bean is gone
    assert captured.ep_square is None

    # If Light does anything else, the chance is gone.
    game2 = Game.from_fen(fen).apply("d7d5").apply("e1e2")
    assert game2.ep_square is None
    assert game2.is_legal("e5d6") is False


def test_en_passant_illegal_if_it_leaves_king_in_check():
    # Horizontal pin: Light king e1, Light pawn e5, Dark pawn d5 just arrived,
    # Dark rook a5... wait, they need to be on the same rank.
    # Light king on e5? Classic: White king e1, white pawn e5, black pawn d5,
    # black queen/rook on h5? Rank 5: K? No the king needs to be on rank 5.
    # Light king c5, Light pawn e5, Dark pawn d5, Dark rook a5 (or h5).
    # After d7d5, exd6 would remove both pawns from rank 5 and expose c5 to a5.
    fen = "4k3/3p4/8/K2P3r/8/8/8/8 b - - 0 1"
    # Dark to move, pawn d7, after d5: rank 5 is K . . p P . . r with Light pawn already on e5? 
    # FEN has K on a5, P on d5? That's wrong.
    # Let me use: 4k3/3p4/8/K3P2r/8/8/8/8 b - - 0 1
    # Rank 5: Light king a5, Light pawn e5, Dark rook h5. Dark plays d7d5.
    fen = "4k3/3p4/8/K3P2r/8/8/8/8 b - - 0 1"
    game = Game.from_fen(fen).apply("d7d5")
    assert game.is_legal("e5d6") is False
    with pytest.raises(IllegalMoveError):
        game.apply("e5d6")
    # The pawn can still push, if that's legal (e5e6 is empty).
    assert game.is_legal("e5e6")


def test_en_passant_uci_and_san():
    fen = "4k3/3p4/8/4P3/8/8/8/4K3 b - - 0 1"
    game = Game.from_fen(fen).apply("d5")
    assert game.to_san(game.parse_move("e5d6")) in {"exd6", "exd6+"}
    game = game.apply("exd6")
    assert game.board.get("d6") is not None
    assert game.board.get("d5") is None


def test_promotion_all_four_types():
    fen = "4k3/6P1/8/8/8/8/8/4K3 w - - 0 1"
    game = Game.from_fen(fen)
    dests = [m for m in game.legal_moves_from("g7") if m.end.rank == 7]
    promos = {m.promotion for m in dests}
    assert promos == {PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT}
    for typ, letter in (
        (PieceType.QUEEN, "q"),
        (PieceType.ROOK, "r"),
        (PieceType.BISHOP, "b"),
        (PieceType.KNIGHT, "n"),
    ):
        after = Game.from_fen(fen).apply(f"g7g8{letter}")
        placed = after.board.get("g8")
        assert placed is not None
        assert placed.type is typ
        assert placed.color.value == "light"
        assert after.board.get("g7") is None


def test_promotion_defaults_to_queen_in_simple_apis():
    fen = "4k3/6P1/8/8/8/8/8/4K3 w - - 0 1"
    game = Game.from_fen(fen).apply("g7g8")
    assert game.board.get("g8").type is PieceType.QUEEN
    game2 = Game.from_fen(fen).apply("g8=R")  # SAN with explicit rook? dest is g8, need g7 origin
    # SAN for a pawn promotion is g8=R
    game2 = Game.from_fen(fen).apply("g8=R")
    assert game2.board.get("g8").type is PieceType.ROOK


def test_capture_promotions():
    # Dark rook on f8, Dark king on g8, Light bean on g7.
    fen = "5rk1/6P1/8/8/8/8/8/4K3 w - - 0 1"
    game = Game.from_fen(fen)
    game = Game.from_fen(fen)
    uci = {m.uci() for m in game.legal_moves_from("g7")}
    assert "g7f8q" in uci
    assert "g7f8r" in uci
    assert "g7f8b" in uci
    assert "g7f8n" in uci
    # g8 is the dark lollipop, so a push there is not generated.
    assert "g7g8q" not in uci
    after = game.apply("g7f8n")
    assert after.board.get("f8").type is PieceType.KNIGHT
    assert after.board.get("f8").color.value == "light"
    # The captured rook went into Light's candy jar (display only).
    assert len(after.candy_jar_light) == 1
    assert after.candy_jar_light[0].type is PieceType.ROOK


def test_dark_promotes_on_rank_1():
    fen = "4K3/8/8/8/8/8/2p5/4k3 b - - 0 1"
    # Wait Light king should be... 4k3 on rank 1 with a dark pawn on c2. Dark king also... messy.
    fen = "4k3/8/8/8/8/8/2p5/4K3 b - - 0 1"
    game = Game.from_fen(fen).apply("c2c1q")
    assert game.board.get("c1").type is PieceType.QUEEN
    assert game.board.get("c1").color.value == "dark"
