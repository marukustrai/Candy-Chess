# Phase 1 legal moves

This is the source of truth for **Phase 1** rules. Phase 1 is classic chess with candy names. There are no twists yet.

Candy identity and art notes are in [`../pieces.md`](../pieces.md). The board layout and repo overview are also summarized in the [root README](../../README.md).

A move described below is still illegal if it leaves your own giant lollipop (king) in check.

## Board representation

The board is an **8×8** grid of 64 squares.

- **Files** are the columns, labeled `a` through `h` from left to right as Light sees the board.
- **Ranks** are the rows, numbered `1` through `8`. Rank 1 is Light’s back row. Rank 8 is Dark’s back row.
- A square is named by file then rank, with no space: `e4`, `a1`, `h8`.
- Light’s candies start on ranks 1 and 2. Dark’s candies start on ranks 7 and 8.
- Light moves first, then the two sides take turns.

### Starting position

```
8  LS  GB  CC  TB  LP  CC  GB  LS
7  JB  JB  JB  JB  JB  JB  JB  JB
6  .   .   .   .   .   .   .   .
5  .   .   .   .   .   .   .   .
4  .   .   .   .   .   .   .   .
3  .   .   .   .   .   .   .   .
2  JB  JB  JB  JB  JB  JB  JB  JB
1  LS  GB  CC  TB  LP  CC  GB  LS
   a   b   c   d   e   f   g   h
```

Rank 1 is nearest Light; rank 8 is nearest Dark. Abbreviations: `LP` giant lollipop (king), `TB` chocolate truffle box (queen), `LS` licorice stick (rook), `CC` candy cane (bishop), `GB` gummy bear (knight), `JB` jelly bean (pawn), `.` empty.

On the first rank, from `a` to `h`, Light has: licorice stick, gummy bear, candy cane, truffle box, lollipop, candy cane, gummy bear, licorice stick. Dark uses the same order on rank 8. The lollipop starts on the **e** file, the truffle box on the **d** file.

### Coordinates for code

To store the board in a program, use this numbering (it matches the names above):

- File index: `a = 0`, `b = 1`, `c = 2`, `d = 3`, `e = 4`, `f = 5`, `g = 6`, `h = 7`
- Rank index: `1 = 0`, `2 = 1`, `3 = 2`, `4 = 3`, `5 = 4`, `6 = 5`, `7 = 6`, `8 = 7`
- So `a1` is `(0, 0)`, `e4` is `(4, 3)`, and `h8` is `(7, 7)`
- A square is on the board only if both indexes are in `0` through `7`

Each occupied square holds a side (Light or Dark) and a piece type (one of the six candies). Empty squares hold nothing.

### What a position must remember

A legal-move generator needs more than the pieces on the squares. It must also know:

1. **Side to move** — Light or Dark.
2. **Castling rights** — four flags: Light king-side, Light queen-side, Dark king-side, Dark queen-side. A flag is lost if that lollipop has moved, or if that licorice stick has moved or been captured.
3. **En passant target** — the square a jelly bean just skipped with a two-square first move, or “none.” This lasts for only the opponent’s very next turn.
4. **Half-move clock** — how many consecutive moves have been made with no jelly-bean move and no capture (for the 50-move draw).
5. **Full-move number** — starts at 1, and goes up by 1 after each Dark move.

## How a turn works

On your turn you make **exactly one legal move** with one of your candies (castling is one move, even though two pieces shift). You may not skip a turn. After your move, it is the opponent’s turn.

A generated step (such as “this gummy bear can land on `c3`”) is a **legal move** only if all of the following are true:

- The piece you move is yours.
- The destination is on the board.
- The destination is empty or holds an opposing candy (you may never land on your own candy).
- The piece is allowed to move that way, as described below.
- After the move is made, **your own lollipop is not in check**.

That last rule is what stops a pinned piece from stepping off the line of attack. For example, if a licorice stick stands between your lollipop and an opposing truffle box on the same file, that stick may slide along that file but may not step off it.

Capturing: if you land on an opposing candy, you take it off the board and put it in that side’s candy jar. In Phase 1 the jar is only for display. It has no effect on the game.

No piece may move off the board.

## How sliding and hopping work

The truffle box, licorice stick, and candy cane are **sliding** pieces:

- They may move any number of squares in their allowed directions.
- Every square they pass *through* must be empty. They cannot hop over a candy.
- They may stop on an empty square, or on a square that holds an opposing candy (a capture). They then stop there. They may not continue past a capture.
- They may not land on their own candy.

The gummy bear is a **hopper**: other candies do not block it. The lollipop and jelly bean are neither long sliders nor hoppers; their steps are described with those pieces.

---

## Giant Lollipop (King)

**Ordinary move.** The lollipop moves **exactly one square** in any of the eight directions: forward, backward, left, right, or diagonal.

It may land on an empty square, or capture an opposing candy on an adjacent square. It may never move to a square attacked by the opponent, even to capture. (If an opposing candy is protected, the square it sits on is still attacked.)

### Castling

Castling is the lollipop’s special move. It is one move, made with your lollipop and one of your licorice sticks, and it is the only time two of your pieces move at once.

There are two kinds, with these exact destinations:

| Castle | Notation | Light | Dark |
|--------|----------|-------|------|
| King-side | `O-O` | Lollipop `e1` → `g1`, stick `h1` → `f1` | Lollipop `e8` → `g8`, stick `h8` → `f8` |
| Queen-side | `O-O-O` | Lollipop `e1` → `c1`, stick `a1` → `d1` | Lollipop `e8` → `c8`, stick `a8` → `d8` |

All of the following must be true, or you may not castle that way:

1. It is that lollipop’s first move of the game (it has never moved, and has not already castled).
2. It is that licorice stick’s first move of the game, and the stick is still on its original corner square.
3. Every square *between* the lollipop and that stick is empty.
4. The lollipop is not in check now.
5. The square the lollipop **crosses** is not attacked by the opponent (`f1` / `f8` for king-side; `d1` / `d8` for queen-side).
6. The square the lollipop **lands on** is not attacked (`g1` / `g8` or `c1` / `c8`).

The stick may pass through or land on an attacked square. In particular, queen-side castling is still allowed if `b1` or `b8` is attacked, as long as the lollipop’s squares are safe.

Castling is not a capture, and it does not move the lollipop into check.

---

## Chocolate Truffle Box (Queen)

The truffle box combines the licorice stick and the candy cane.

It may slide any number of clear squares **vertically, horizontally, or diagonally** (the eight directions). It cannot hop. It captures by landing on an opposing candy.

---

## Licorice Stick (Rook)

The licorice stick may slide any number of clear squares **vertically or horizontally** (along a file or along a rank). It cannot hop and cannot move diagonally. It captures by landing on an opposing candy.

This is the stick used in [castling](#castling). After the stick has moved, or if it is captured, that side may no longer castle with that stick.

---

## Candy Cane (Bishop)

The candy cane may slide any number of clear squares **diagonally**. It cannot hop, and it cannot move vertically or horizontally. It captures by landing on an opposing candy.

A candy cane always stays on the same square color it started on: the cane that begins on a light square never reaches a dark square, and the other way around.

---

## Gummy Bear (Knight)

The gummy bear moves in an **L**: two squares in one orthogonal direction, then one square at a right angle (or one square, then two at a right angle).

From a file index `f` and rank index `r` (see [coordinates for code](#coordinates-for-code)), the eight possible landing squares are:

`(f+1, r+2)`, `(f+1, r-2)`, `(f-1, r+2)`, `(f-1, r-2)`, `(f+2, r+1)`, `(f+2, r-1)`, `(f-2, r+1)`, `(f-2, r-1)`

Drop any landing square that is off the board. The bear **may hop over** any candies in the way. It cares only about the landing square: empty is a move; an opposing candy is a capture; your own candy is illegal.

---

## Jelly Bean (Pawn)

Jelly beans move **forward only**, toward the opposing back rank: Light toward rank 8, Dark toward rank 1. They never move backward, and they never move sideways except when capturing.

### Forward move (no capture)

- If the square directly in front is empty, the bean may move **one square forward**.
- It may never move forward onto a candy, even an opposing one. Jelly beans do not capture straight ahead.

### Two-square first move

If the bean is still on its starting rank (rank 2 for Light, rank 7 for Dark), and both the square directly in front and the square two in front are empty, it may move **two squares forward**. This is optional. The bean does not hop; both squares must be empty.

After this two-square move, the square the bean skipped becomes the **en passant target** for the opponent’s next turn only.

### Ordinary capture

The bean captures **one square diagonally forward**, left or right. There must be an opposing candy on that square. It may not move diagonally into an empty square, except for en passant.

### En passant

En passant (“in passing”) is a special jelly-bean capture.

It is allowed only in this situation:

1. An opposing jelly bean has just moved **two squares forward** from its starting rank, and that was the move that just ended.
2. Your jelly bean sits on the same rank, on a **file next to** that bean (for example, your bean on `e5`, theirs just arrived on `d5`).
3. It is now **your very next turn**. If you do anything else, the chance is gone.

Then you may capture that bean as if it had moved only one square: your bean moves into the skipped square (the en passant target), and the opposing bean is removed from the square it landed on.

Example: a Dark bean moves from `d7` to `d5`. A Light bean on `e5` may play `exd6`. The Light bean lands on `d6`, and the Dark bean on `d5` is captured.

### Promotion

If a jelly-bean move — a one-square step, a two-square step, an ordinary capture, or en passant — **lands on the far rank** (rank 8 for Light, rank 1 for Dark), the bean is **promoted at once**.

- Promotion is mandatory. The bean cannot stay a jelly bean.
- You choose one of: chocolate truffle box, licorice stick, candy cane, or gummy bear, of your side.
- The new piece replaces the bean on the landing square, as part of the same move.
- You may choose a truffle box even if you already have one (or more).

---

## Check, checkmate, and draws

**Check.** Your lollipop is in check if at least one opposing candy could capture it on this position (using ordinary capture moves, including en passant if it applied). You may never leave your own lollipop in check.

**Checkmate.** You win if the opponent’s lollipop is in check and that side has no legal move. The game ends at once.

**Stalemate.** If the side to move is *not* in check but has no legal move, the game is a draw.

**Other draws.** The game is also a draw if both players agree; if neither side has enough material left to checkmate; if the same position appears three times with the same side to move and the same castling and en passant rights; or if 50 consecutive moves by each side pass with no jelly-bean move and no capture.

Insufficient material includes, at least: lollipop vs lollipop; lollipop and a candy cane vs lollipop; lollipop and a gummy bear vs lollipop.

## Notation

Write moves in standard algebraic notation so game records stay familiar: `e4`, `Nf3`, `O-O`, `O-O-O`, `exd5`, `e8=Q`. The letters are the classic ones: `K` king, `Q` queen, `R` rook, `B` bishop, `N` knight. A jelly-bean move is written with no letter (`e4`).

Candy names are fine when teaching (“the Light gummy bear jumps to `c3`”).
