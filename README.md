# Candy Chess 🍬♟️

An idiosyncratic version of chess where every piece is represented by a different type of candy. This is a **design & concept** project (rules + visuals), perfect for beginners.

## Concept

Instead of traditional chess pieces, we use candies. The game can start with standard chess rules and later add fun, sweet twists. The goal is to make chess more playful and visually delightful.

## Candy Piece Ideas

Here are suggested mappings (feel free to change them!):

| Chess Piece | Candy | Personality / Reason |
|-------------|-------|----------------------|
| **King** | Giant Lollipop | Tall, regal, the most important piece |
| **Queen** | Chocolate Truffle Box | Powerful, elegant, and a bit fancy |
| **Rook** | Licorice Rope / Stick | Long, straight, strong, and sturdy |
| **Bishop** | Candy Cane | Diagonal stripes, festive, slides on diagonals |
| **Knight** | Gummy Bear or Gummy Worm | Bouncy, jumpy, can "hop" over pieces |
| **Pawn** | Jelly Beans | Small, colorful, many of them, easy to promote into bigger candies |

### Extra Candy Ideas
- **Promotion**: When a pawn reaches the end, it turns into a bigger candy (e.g. a full chocolate bar or a bag of gummies).
- **Captured pieces**: Put them in a "candy jar" or eat them (thematically).
- Alternative pieces: Sour belts for rooks, peppermint patties for bishops, etc.

## Rules Plan

### Phase 1 – Classic Rules (Current Focus)
Use standard chess rules so anyone can play. Only the visuals change. Phase 1 is a playable board plus legal moves.

### Phase 2 – Idiosyncratic / Sweet Twists (Later)
Pick 1–2 of these once Phase 1 is playable:

1. **Sugar Rush**: Moving a piece gives the player a small "sugar" point. At 5 points you can do a special move.
2. **Melting**: Pieces that stay still for too long (e.g. 5 turns) start to "melt" and lose power (or become capturable more easily).
3. **Candy Swap**: Once per game, you can swap any two of your pieces’ positions (like a candy mix-up).
4. **Promotion Bonus**: When a pawn promotes, you also get to place a free extra pawn on your side.
5. **Color Themes**: White = fruity/sour candies, Black = chocolate/licorice candies.

Start with Phase 1. Add twists later if the project grows.

## Repo structure

- `docs/` — design docs and rules (Phase 1: legal moves)
- `engine/` — Python board representation and legal move generation
- `frontend/` — JavaScript/HTML/CSS interactive board with candy visuals

See `CONTRIBUTING.md` for a short, beginner-friendly workflow.

## Next Steps

Phase 1 work is tracked in the starter issues:

1. Write beginner-friendly **legal move rules** in `docs/` (standard chess, with candy piece names).
2. Implement a **Python board + legal move engine** in `engine/`.
3. Build a **JS interactive board** with candy visuals in `frontend/`.

After those are underway:

4. Review and pick your favorite candy mappings (edit the table above).
5. Add a `docs/pieces.md` file with more detailed descriptions or drawing ideas.
6. Collect reference images of the candies (or generate simple sketches).
7. Decide later whether to add any Phase 2 twists.

## How to Use This Repo

- Clone or download it
- Read `CONTRIBUTING.md` if you are new to the workflow
- Work in the folder that matches your task (`docs`, `engine`, or `frontend`)
- Open a pull request for your changes
- Open issues or discussions for new candy ideas or rule suggestions
- Keep it fun and sweet!

---

*Created as a starter concept for Candy Chess. Contributions and ideas welcome!*
