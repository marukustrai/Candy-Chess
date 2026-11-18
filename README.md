# Candy Chess 🍬♟️

Candy Chess is ordinary chess with candy pieces. **Phase 1** (the current work) uses **classic chess rules only**. Only the look of the pieces changes. There are no special candy twists yet.

The locked candy mappings are in [`docs/pieces.md`](docs/pieces.md). The board and the exact legal move for every piece are in [`docs/rules/legal-moves.md`](docs/rules/legal-moves.md).

## Concept

The board, the moves, and the goal are chess. The pieces just happen to be sweets. That keeps the game easy to learn and straightforward to implement. Optional twists can wait until Phase 1 is playable.

## Candy mappings (locked)

Both sides use the same sweets. Light and Dark are different finishes of those candies, not different types. Details and drawing notes are in [`docs/pieces.md`](docs/pieces.md).

| Chess piece | Candy |
|-------------|-------|
| King | Giant Lollipop |
| Queen | Chocolate Truffle Box |
| Rook | Licorice Stick |
| Bishop | Candy Cane |
| Knight | Gummy Bear |
| Pawn | Jelly Bean |

Licorice rope and gummy worm were considered and are not used in Phase 1.

## Phase 1 rules

Phase 1 is classic chess, with candy names and candy art.

- How the board is labeled, what a position must remember, and how turns, check, checkmate, and draws work: [`docs/rules/legal-moves.md`](docs/rules/legal-moves.md)
- The exact legal move for the lollipop, truffle box, licorice stick, candy cane, gummy bear, and jelly bean, including **castling**, **en passant**, and **promotion**: the same file, with a short pointer from each piece in [`docs/pieces.md`](docs/pieces.md)

Optional later ideas (sugar rush, melting, candy swap, promotion bonus, alternate color themes) are **not** part of Phase 1 and should not be implemented yet.

## Repo structure

- `docs/` — design docs and rules (Phase 1: pieces and legal moves)
- `engine/` — Python board representation and legal move generation
- `frontend/` — JavaScript/HTML/CSS interactive board with candy visuals

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for a short, beginner-friendly workflow.

## Next steps

- [x] Lock the candy mappings in `docs/pieces.md`.
- [x] Document the board and the exact Phase 1 legal moves in `docs/rules/legal-moves.md`.
- [ ] Implement a Python board and legal-move engine in `engine/`.
- [ ] Build a JS interactive board with candy visuals in `frontend/`.
- [ ] Collect reference images or simple sketches for each candy (Light and Dark).
- [ ] After Phase 1 is playable, decide whether to add any Phase 2 twists.

## How to use this repo

- Clone or download it.
- Read `CONTRIBUTING.md` if you are new to the workflow.
- Treat `docs/pieces.md` as the source of truth for candy identity and appearance.
- Treat `docs/rules/legal-moves.md` as the source of truth for Phase 1 rules.
- Work in the folder that matches your task (`docs`, `engine`, or `frontend`).
- Keep it fun and sweet.

---

*Phase 1 design docs: classic chess rules, candy pieces, no twists yet.*
