"""A tiny command-line demo so you can try the engine without a UI.

Start it from the repo root:

    python -m engine.cli

Type moves in UCI (e2e4, e7e8q) or SAN (Nf3, O-O, e8=Q). Commands:

    help, moves, moves e2, fen, candy, resign, draw, undo, quit
"""

from __future__ import annotations

import sys

from engine.game import Game, GameOverError, IllegalMoveError


INTRO = """Candy Chess — Phase 1 (classic rules, candy names)

Enter moves as UCI (e2e4) or SAN (Nf3, O-O, exd5, e8=Q).
Commands: help, moves [square], fen, candy, undo, draw, resign, quit
"""


def _print_board(game: Game, candy: bool) -> None:
    print()
    print(game.board.ascii(candy=candy))
    print(f"{game.side_to_move.value.capitalize()} to move.  {game.fen()}")
    status = game.status()
    if status.in_check and status.state != "checkmate":
        print("Check!")
    if status.is_over:
        line = f"Game over: {status.state}"
        if status.reason:
            line += f" ({status.reason})"
        if status.winner:
            line += f" — winner: {status.winner}"
        print(line)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    game = Game.from_fen(args[0]) if args and not args[0].startswith("-") else Game.starting()
    history = [game]
    candy = False

    print(INTRO)
    _print_board(game, candy)

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not raw:
            continue
        cmd = raw.lower()
        if cmd in {"quit", "exit", "q"}:
            return 0
        if cmd in {"help", "?"}:
            print(INTRO)
            continue
        if cmd == "fen":
            print(game.fen())
            continue
        if cmd == "candy":
            candy = not candy
            _print_board(game, candy)
            continue
        if cmd == "undo":
            if len(history) == 1:
                print("Nothing to undo.")
                continue
            history.pop()
            game = history[-1]
            _print_board(game, candy)
            continue
        if cmd == "draw":
            try:
                game = game.agree_draw()
            except GameOverError as exc:
                print(exc)
                continue
            history.append(game)
            _print_board(game, candy)
            continue
        if cmd == "resign":
            print(f"{game.side_to_move.value.capitalize()} resigns. Winner: {game.side_to_move.opponent.value}.")
            return 0
        if cmd == "moves" or cmd.startswith("moves "):
            square = raw.split(None, 1)[1] if " " in raw else None
            listing = game.legal_moves_from(square) if square else game.legal_moves()
            if not listing:
                print("No legal moves" + (f" from {square}" if square else "") + ".")
                continue
            shown = [f"{game.to_san(m)} ({m.uci()})" for m in listing]
            print(", ".join(shown))
            continue

        if game.status().is_over:
            print("The game is over. Type undo, quit, or start again.")
            continue
        try:
            game = game.apply(raw)
        except (IllegalMoveError, GameOverError, ValueError) as exc:
            print(f"Illegal move: {exc}")
            continue
        history.append(game)
        _print_board(game, candy)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
