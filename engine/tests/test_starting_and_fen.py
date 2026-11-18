"""Starting position counts and FEN round-trips."""

from engine import STARTING_FEN, Color, Game, PieceType


def test_game_and_starting_are_the_opening_position():
    a = Game()
    b = Game.starting()
    assert a.fen() == STARTING_FEN
    assert b.fen() == STARTING_FEN
    assert a.side_to_move is Color.LIGHT


def test_starting_position_has_20_legal_moves():
    game = Game.starting()
    moves = game.legal_moves()
    assert len(moves) == 20
    uci = sorted(m.uci() for m in moves)
    # Eight one-step beans, eight two-step beans, two gummy bears × 2.
    assert "e2e4" in uci
    assert "e2e3" in uci
    assert "g1f3" in uci
    assert "b1c3" in uci


def test_coordinates_match_the_rules_doc():
    game = Game.starting()
    e1 = game.board.get("e1")
    d1 = game.board.get("d1")
    a1 = game.board.get("a1")
    e8 = game.board.get("e8")
    assert e1 is not None and e1.type is PieceType.KING and e1.color is Color.LIGHT
    assert d1 is not None and d1.type is PieceType.QUEEN
    assert a1 is not None and a1.type is PieceType.ROOK
    assert e8 is not None and e8.type is PieceType.KING and e8.color is Color.DARK
    # a1 is (0, 0), h8 is (7, 7), e4 is (4, 3).
    from engine.squares import Square

    assert Square.parse("a1") == Square(0, 0)
    assert Square.parse("e4") == Square(4, 3)
    assert Square.parse("h8") == Square(7, 7)


def test_fen_round_trip_starting():
    game = Game.starting()
    assert Game.from_fen(game.fen()).fen() == game.fen()


def test_fen_round_trip_after_moves_and_ep():
    game = Game.starting().apply("e2e4").apply("d7d5").apply("e4e5").apply("f7f5")
    # After f7f5 the en passant target is f6.
    fen = game.fen()
    assert " f6 " in fen
    assert Game.from_fen(fen).fen() == fen
    reloaded = Game.from_fen(fen)
    assert reloaded.ep_square is not None
    assert str(reloaded.ep_square) == "f6"
    assert reloaded.side_to_move is Color.LIGHT


def test_fen_preserves_clocks_and_rights():
    fen = "r3k2r/8/8/8/8/8/8/R3K2R b Kq - 12 34"
    game = Game.from_fen(fen)
    assert game.fen() == fen
    assert game.castling.light_kingside is True
    assert game.castling.light_queenside is False
    assert game.castling.dark_kingside is False
    assert game.castling.dark_queenside is True
    assert game.halfmove_clock == 12
    assert game.fullmove_number == 34
    assert game.side_to_move is Color.DARK


def test_apply_does_not_mutate_the_original():
    game = Game.starting()
    after = game.apply("e2e4")
    assert game.fen() == STARTING_FEN
    assert after.fen() != STARTING_FEN
    assert after.board.get("e4") is not None
    assert game.board.get("e4") is None
