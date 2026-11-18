# Candy Chess Pieces

This file locks the **Phase 1 candy mappings**. Both sides use the same sweets. Light and Dark are told apart by finish and color, not by different candy types.

The exact legal moves, including castling, en passant, and promotion, are in [`rules/legal-moves.md`](rules/legal-moves.md). If a drawing note here ever disagrees with that file about how a piece moves, the rules file wins.

## Locked mappings

| Chess piece | Candy (locked) | How many per side | Why this candy |
|-------------|----------------|-------------------|----------------|
| King | Giant Lollipop | 1 | Tall and regal; the piece you must protect |
| Queen | Chocolate Truffle Box | 1 | The richest, most flexible piece on the board |
| Rook | Licorice Stick | 2 | Upright, sturdy, and built for straight lines |
| Bishop | Candy Cane | 2 | Diagonal stripes match diagonal slides |
| Knight | Gummy Bear | 2 | Bouncy and able to hop over other pieces |
| Pawn | Jelly Bean | 8 | Small, plentiful, and able to promote into a bigger candy |

These choices are locked for Phase 1. Licorice rope and gummy worm were considered and are not used.

### Sides: Light and Dark

| Side | Classic name | Candy finish | Moves toward |
|------|----------------|--------------|--------------|
| Light | White | Sugar-dusted, pastel, white chocolate, or lighter wrappers | Rank 8 |
| Dark | Black | Cocoa-dusted, jewel-tone, dark chocolate, or deeper wrappers | Rank 1 |

Light moves first.

### Starting squares

| Piece | Light | Dark |
|-------|-------|------|
| Giant Lollipop | `e1` | `e8` |
| Chocolate Truffle Box | `d1` | `d8` |
| Licorice Stick | `a1`, `h1` | `a8`, `h8` |
| Candy Cane | `c1`, `f1` | `c8`, `f8` |
| Gummy Bear | `b1`, `g1` | `b8`, `g8` |
| Jelly Bean | `a2`–`h2` | `a7`–`h7` |

---

## Giant Lollipop (King)

- **Moves:** One square in any direction, plus castling. See [legal moves: lollipop](rules/legal-moves.md#giant-lollipop-king).
- **Visual:** A tall lollipop on a stick, wrapper flared like a small crown. It should read as the most important piece, but not as large as the truffle box.
- **Light:** Pastel swirl or pale fruit lollipop, light stick.
- **Dark:** Cola, blackberry, or chocolate lollipop, darker stick.

## Chocolate Truffle Box (Queen)

- **Moves:** Any number of clear squares vertically, horizontally, or diagonally. See [legal moves: truffle box](rules/legal-moves.md#chocolate-truffle-box-queen).
- **Visual:** A small, ornate box of truffles, slightly wider than the other pieces so it feels powerful, without hiding neighboring squares.
- **Light:** White or milk-chocolate box, gold or cream ribbon.
- **Dark:** Dark-chocolate box, deep red or burgundy ribbon.

## Licorice Stick (Rook)

- **Moves:** Any number of clear squares vertically or horizontally. This is the stick used in castling. See [legal moves: licorice stick](rules/legal-moves.md#licorice-stick-rook).
- **Visual:** A standing stick that reads as a tower. Avoid a floppy rope shape, which is easy to mix up with the candy cane.
- **Light:** Red or strawberry licorice.
- **Dark:** Black licorice.

## Candy Cane (Bishop)

- **Moves:** Any number of clear squares diagonally. Each cane stays on the square color it started on. See [legal moves: candy cane](rules/legal-moves.md#candy-cane-bishop).
- **Visual:** A cane with clear diagonal striping, standing or slightly hooked at the top. The stripes should stay readable at piece size.
- **Light:** Classic red-and-white.
- **Dark:** Chocolate-mint, cocoa-and-white, or red-and-black.

## Gummy Bear (Knight)

- **Moves:** An L-shape; it may hop over other pieces. See [legal moves: gummy bear](rules/legal-moves.md#gummy-bear-knight).
- **Visual:** A gummy bear in a short leaping pose, clearly larger than a jelly bean.
- **Light:** Yellow, lemon, or pale fruit gummy.
- **Dark:** Berry, cola, or another deep-colored gummy.

## Jelly Bean (Pawn)

- **Moves:** Forward steps, diagonal captures, en passant, and promotion. See [legal moves: jelly bean](rules/legal-moves.md#jelly-bean-pawn).
- **Visual:** The smallest piece: a simple bean, tinted for its army rather than a mixed rainbow that hides its side. When it promotes, it is replaced by the chosen bigger candy in that army’s finish.
- **Light:** Pastel beans.
- **Dark:** Jewel-tone or darker beans.

## Drawing and UI notes

- Keep a consistent scale: jelly beans smallest, gummy bears a step up, lollipop tallest, truffle box widest.
- Silhouettes should stay recognizable at small size: hook for the cane, stick or tower for the rook, crown-wrapper for the king, box for the queen, ears for the bear, oval for the bean.
- Do not use a second candy type for the same role in Phase 1.
- A captured candy goes into a **candy jar** (any off-board tray). In Phase 1 the jar is for display only.
- Optional later palettes or rule twists are out of scope until Phase 1 is built.
