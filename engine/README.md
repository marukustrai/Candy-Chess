# Engine

Python 3.11+ code for the Phase 1 board and legal moves lives here.

Phase 1 follows [`docs/rules/legal-moves.md`](../docs/rules/legal-moves.md) exactly: classic chess rules, with locked candy names from [`docs/pieces.md`](../docs/pieces.md) as display metadata only. There is no computer opponent and no visual UI in this folder — just the rules engine, a tiny command-line demo, and an optional JSON HTTP facade the JavaScript frontend can call later.

## Setup

From the repository root:

```bash
python -m pip install -e ".[dev]"
```

If you only want to run tests, installing pytest and using the repo as `PYTHONPATH` is enough:

```bash
python -m pip install -r engine/requirements.txt
```

Python 3.11 or newer is required. The engine itself uses only the standard library.

## Run the tests

```bash
python -m pytest
```

Or, without installing the package:

```bash
PYTHONPATH=. python -m pytest engine/tests
```

## Try a game (CLI demo)

```bash
python -m engine.cli
```

Type moves in UCI (`e2e4`, `e7e8q`) or SAN (`Nf3`, `O-O`, `exd5`, `e8=Q`). Commands: `moves`, `moves e2`, `fen`, `candy` (toggle candy abbreviations), `undo`, `draw`, `resign`, `quit`.

## Optional JSON HTTP server

```bash
python -m engine.server --port 8765
```

The frontend can talk to these endpoints (JSON in, JSON out; CORS is open for local use):

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/games` | Start a new Phase 1 game |
| `POST` | `/games/fen` | Body `{"fen": "..."}` — start from a FEN |
| `GET`  | `/games/<id>` | Current board state |
| `GET`  | `/games/<id>/moves` | All legal moves (optional `?square=e2`) |
| `POST` | `/games/<id>/moves` | Body `{"move": "e2e4"}` — apply a UCI or SAN move |

Illegal moves return HTTP 400 with `ok: false`, an `error` code, and a `message`. A successful apply returns the new state plus `status` (`in_progress`, `check`, `checkmate`, `stalemate`, or `draw`, with a `reason` and a `winner` when someone has won).

You can also call the same logic in-process with `engine.ChessAPI` (see below).

## Python API

```python
from engine import Game

game = Game()                 # also Game.starting()
game = Game.from_fen(fen)

game.legal_moves()            # list[Move]
game.legal_moves_from("e2")
game.is_legal("e2e4")
game = game.apply("e2e4")     # returns a new Game; the old one is unchanged
game.status()                 # .state, .reason, .winner, .in_check
game.fen()
game.to_dict()                # or game.board_json() — pieces include candy names
game.agree_draw()             # both sides agree; returns a new Game
```

`apply()`, `is_legal()`, and `parse_move()` accept a `Move`, a UCI string (`e2e4`, `e7e8q`, `e1g1`), or SAN (`Nf3`, `O-O`, `e8=Q`). If a jelly bean reaches the far rank and no promotion piece is given, the simple APIs default to a chocolate truffle box (queen). `legal_moves()` still lists all four promotion choices.

### Coordinates

Matches the rules doc: file `a=0…h=7`, rank `1=0…8=7`, so `a1` is `(0, 0)` and `h8` is `(7, 7)`. Light (classic White) moves first, toward rank 8. Dark (classic Black) moves toward rank 1.

### Board state for the UI

`game.to_dict()` / `game.board_json()` is the contract a JS frontend should consume. Important fields:

- `fen` — standard FEN (classic `KQRBNP` letters, as the rules specify)
- `side_to_move` — `"light"` or `"dark"` (`classic_side_to_move` is `"white"` / `"black"`)
- `pieces` — each entry has `square`, `type`, `symbol`, `color`, `classic_color`, and `candy_name`
- `legal_moves` — `from`, `to`, `promotion`, `uci`, `san`, and `flags` (`capture`, `en_passant`, `castle`, `promotion`, `check`, `checkmate`)
- `status` — `state`, `reason`, `winner`, `in_check`
- `castling`, `en_passant`, `halfmove_clock`, `fullmove_number`
- `candy_jar` — captured pieces for Light and Dark, **display-only** in Phase 1 (no effect on legality)
- `phase` — always `1` in this engine

Locked candy names (same sweets on both sides; finish is Light vs Dark):

| Chess piece | Candy |
|-------------|-------|
| King | Giant Lollipop |
| Queen | Chocolate Truffle Box |
| Rook | Licorice Stick |
| Bishop | Candy Cane |
| Knight | Gummy Bear |
| Pawn | Jelly Bean |

### Moves are immutable

`Game.apply(move)` returns a **new** `Game`. That keeps undo, tests, and later hooks straightforward. It raises `IllegalMoveError` if the move is not legal, and `GameOverError` if the game is already over.

## Draws

These end the game automatically in this engine (the rules describe them as draws):

- **Stalemate** — side to move is not in check and has no legal move
- **Threefold repetition** — same piece placement, side to move, castling rights, and en passant rights (en passant counts only when a legal en passant capture exists)
- **Fifty-move rule** — 50 consecutive moves *by each side* with no jelly-bean move and no capture, i.e. a half-move clock of **100**
- **Insufficient material** — at least the cases required by the rules: lollipop vs lollipop; lollipop + candy cane vs lollipop; lollipop + gummy bear vs lollipop. This engine also treats **lollipop + candy cane vs lollipop + candy cane on the same square color** as a draw (standard FIDE; opposite-color canes are not a draw)
- **Agreement** — `game.agree_draw()`

Checkmate takes precedence over a draw clock if the side to move has no legal move and is in check.

Loading a FEN starts a fresh repetition history from that position (earlier repeats are not known). The candy jar also starts empty for a FEN.

## Phase 2 hooks (disabled)

`engine.hooks.Ruleset` / `Phase1Rules` is the extension point. The default game uses `Phase1Rules`, which returns the locked candy names and otherwise does nothing. Hooks such as `on_move`, `extra_legal_moves`, `is_move_legal`, and `on_promotion` are no-ops in Phase 1.

These twists are **not implemented and not enabled**:

1. Sugar Rush
2. Melting
3. Candy Swap
4. Promotion Bonus
5. Alternate color-theme candy names (a custom `candy_for` may change labels, never legality)

Do not turn them on in the default Phase 1 game. See the docstring in `engine/hooks.py` for where a later ruleset could plug in.

## Layout

```
engine/
  __init__.py     public API
  squares.py      a1–h8 and (file, rank) indexes
  pieces.py       colors, types, locked candy names
  board.py        8×8 grid, starting placement
  fen.py          FEN load/save and castling flags
  moves.py        Move, attack map, pseudo-legal generation
  hooks.py        Ruleset protocol and Phase1Rules
  game.py         legal moves, apply, status, SAN
  api.py          JSON facade (ChessAPI)
  cli.py          command-line demo
  server.py       optional stdlib HTTP server
  tests/          pytest suite
```
