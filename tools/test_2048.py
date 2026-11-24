#!/usr/bin/env python3
# Self-test for the 2048 rules.
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugin"))
import g2048_engine as ge  # noqa: E402


def row(values, direction="left"):
	board = list(values) + [0] * 12
	new, points, moves, merged = ge.slide(board, direction)
	return new[:4], points


# merge rules on one row
assert row([2, 2, 2, 2]) == ([4, 4, 0, 0], 8)
assert row([2, 2, 4, 0]) == ([4, 4, 0, 0], 4)
assert row([4, 0, 0, 4]) == ([8, 0, 0, 0], 8)
assert row([2, 4, 2, 4]) == ([2, 4, 2, 4], 0)
assert row([0, 2, 2, 2]) == ([4, 2, 0, 0], 4)
assert row([8, 8, 16, 0]) == ([16, 16, 0, 0], 16)
assert row([2, 2, 2, 2], "right") == ([0, 0, 4, 4], 8)
assert row([2, 0, 2, 4], "right") == ([0, 0, 4, 4], 4)
# columns
board = [2, 0, 0, 0, 2, 0, 0, 0, 4, 0, 0, 0, 4, 0, 0, 0]
new, points, moves, merged = ge.slide(board, "up")
assert [new[i] for i in (0, 4, 8, 12)] == [4, 8, 0, 0] and points == 12 and merged == {0, 4}
new, points, moves, merged = ge.slide(board, "down")
assert [new[i] for i in (0, 4, 8, 12)] == [0, 0, 4, 8] and merged == {8, 12}
# move list: every tile has one move, values are conserved
for seed in range(200):
	rnd = random.Random(seed)
	board = [rnd.choice((0, 0, 2, 4, 8, 16)) for i in range(16)]
	for d in ge.LINES:
		new, points, moves, merged = ge.slide(board, d)
		assert sum(new) == sum(board)
		assert sorted(m[0] for m in moves) == [i for i in range(16) if board[i]]
		for src, dst, v in moves:
			assert board[src] == v and new[dst] in (v, 2 * v)

# game: random play keeps the board valid; undo restores exactly one step
best_tile = 0
for seed in range(60):
	rnd = random.Random(seed)
	g = ge.Game2048(random.Random(seed))
	g.new_game()
	assert sum(1 for v in g.board if v) == 2
	while not g.over():
		if g.waiting_at_goal():
			assert g.continue_after_goal()
		before = (list(g.board), g.score)
		order = ["down", "left", "right", "up"] if seed % 2 else list(ge.LINES)
		rnd.shuffle(order) if seed % 3 == 0 else None
		result = None
		for d in order:
			result = g.move(d)
			if result:
				break
		assert result, "can_move() said yes but no direction worked"
		assert sum(1 for v in g.board if v) <= 16
		if rnd.random() < 0.05:
			assert g.undo() and (g.board, g.score) == before and not g.undo()
	best_tile = max(best_tile, max(g.board))
	assert g.move("left") is None and g.best >= g.score
print("best tile in random games:", best_tile)

# reaching the goal pauses until the player continues
g = ge.Game2048(random.Random(1))
g.board = [1024, 1024] + [0] * 14
g.score = 0
assert g.move("left") and g.reached and g.waiting_at_goal() and g.move("right") is None
assert g.continue_after_goal() and g.move("right") is not None
# saving
data = json.loads(json.dumps(g.to_dict()))
g2 = ge.Game2048()
g2.from_dict(data)
assert g2.board == g.board and g2.score == g.score and g2.keep_going
try:
	g2.from_dict(dict(data, board=[3] * 16))
	assert False
except ValueError:
	pass
print("2048 ok")
