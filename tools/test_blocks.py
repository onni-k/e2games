#!/usr/bin/env python3
# Self-test for the falling blocks rules: rotations, kicks, line clears and
# bots playing many games without the board ever becoming inconsistent.
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugin"))
import blocks_engine as be  # noqa: E402

# every rotation keeps 4 distinct cells inside the box; four turns = start
for p in be.PIECES:
	size = be.BOX.get(p, 3)
	for rot in range(4):
		cells = be.cells_of(p, rot)
		assert len(set(cells)) == 4 and all(0 <= r < size and 0 <= c < size for r, c in cells)
	assert sorted(be.cells_of(p, 4)) == sorted(be.cells_of(p, 0))

# bag: each run of 7 contains every piece once
g = be.Blocks(random.Random(1))
seq = [g._from_bag() for i in range(70)]
for i in range(0, 70, 7):
	assert sorted(seq[i:i + 7]) == sorted(be.PIECES)

# a tetris (4 lines) with an I piece
g = be.Blocks(random.Random(2))
g.new_game()
for r in range(be.ROWS - 4, be.ROWS):
	for c in range(be.COLS):
		if c != 9:
			g.board[r][c] = "J"
g.piece, g.rot, g.row, g.col = "I", 1, 1, 7       # vertical I in column 9
assert [c for r, c in g.piece_cells()] == [9, 9, 9, 9]
assert g.hard_drop() and len(g.clearing) == 4
g.update(be.CLEAR_TIME + 0.01)
assert g.lines == 4 and g.score >= 800 and all(v is None for row in g.board for v in row)

# wall kick: a T turned against the left wall still turns
g = be.Blocks(random.Random(3))
g.new_game()
g.piece, g.rot, g.row, g.col = "T", 1, 10, -1
assert g._fits(g.row, g.col, g.rot)
assert g.rotate(1) and g._fits(g.row, g.col, g.rot) and g.col >= 0

# hold: swaps once per piece
g = be.Blocks(random.Random(4))
g.new_game()
first = g.piece
assert g.hold() and g.held == first and not g.hold()
g.hard_drop()
second = g.piece
assert g.hold() and g.piece == first and g.held == second

# pause stops everything
g.toggle_pause()
row = g.row
g.update(5.0)
assert g.row == row and not g.move(1)
g.toggle_pause()


def check(g):
	assert len(g.board) == be.ROWS and all(len(r) == be.COLS for r in g.board)
	assert not any(all(v is not None for v in row) for row in g.board) or g.clearing
	if g.piece is not None and g.state == g.PLAY:
		assert g._fits(g.row, g.col, g.rot)
	rows = g.display()
	assert len(rows) == be.VISIBLE


def play(seed, smart):
	rnd = random.Random(seed)
	g = be.Blocks(random.Random(seed))
	g.new_game()
	t = 0.0
	pieces = 0
	while g.state != g.OVER and pieces < 400:
		if g.piece is not None and not g.clearing:
			if smart:
				# choose the placement with the fewest holes and lowest height
				best = None
				for rot in range(4):
					for col in range(-2, be.COLS):
						if not g._fits(g.row, col, rot):
							continue
						row = g.row
						while g._fits(row + 1, col, rot):
							row += 1
						cells = [(r + row, c + col) for r, c in be.cells_of(g.piece, rot)]
						board = [list(x) for x in g.board]
						for r, c in cells:
							board[r][c] = "x"
						full = sum(1 for x in board if all(v is not None for v in x))
						heights, holes = [], 0
						for c in range(be.COLS):
							col_cells = [r for r in range(be.ROWS) if board[r][c] is not None]
							top = min(col_cells) if col_cells else be.ROWS
							heights.append(be.ROWS - top)
							holes += sum(1 for r in range(top, be.ROWS) if board[r][c] is None)
						score = -4 * holes - max(heights) - sum(abs(a - b) for a, b in zip(heights, heights[1:])) * 0.5 + 8 * full
						if best is None or score > best[0]:
							best = (score, rot, col)
				if best:
					for i in range(best[1]):
						g.rotate(1)
					while g.col < best[2] and g.move(1):
						pass
					while g.col > best[2] and g.move(-1):
						pass
				g.hard_drop()
			else:
				action = rnd.random()
				if action < 0.3:
					g.move(rnd.choice((-1, 1)))
				elif action < 0.45:
					g.rotate(rnd.choice((-1, 1)))
				elif action < 0.5:
					g.hold()
				elif action < 0.55:
					g.hard_drop()
				g.set_soft_drop(rnd.random() < 0.3)
			pieces += 1
		g.update(0.03)
		t += 0.03
		check(g)
	return g.score, g.lines, g.level, pieces


for smart in (False, True):
	res = [play(seed, smart) for seed in range(6)]
	print("smart" if smart else "random", [(s, l) for s, l, lv, p in res])
	if smart:
		assert min(r[1] for r in res) >= 30, "a careful player should clear many lines"
print("blocks ok")
