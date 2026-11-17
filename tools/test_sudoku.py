#!/usr/bin/env python3
# Self-test for the sudoku generator and game rules.
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugin"))
import sudoku_engine as se  # noqa: E402


def valid_solution(b):
	for group in range(9):
		for key in (se.ROW, se.COL, se.BOX):
			assert sorted(b[i] for i in range(81) if key[i] == group) == list(range(1, 10))


for difficulty in (se.EASY, se.MEDIUM, se.HARD):
	clues, times = [], []
	for seed in range(15):
		t0 = time.time()
		puzzle, solution = se.generate(difficulty, random.Random(seed))
		times.append(time.time() - t0)
		valid_solution(solution)
		assert all(p in (0, s) for p, s in zip(puzzle, solution))
		out = [0] * 81
		assert se.count_solutions(puzzle, 2, out=out) == 1 and out == solution
		clues.append(sum(1 for v in puzzle if v))
	print("difficulty %d: clues %d-%d, generation max %.2f s, avg %.2f s" % (
		difficulty, min(clues), max(clues), max(times), sum(times) / len(times)))

g = se.Sudoku(random.Random(3))
g.new_game(se.MEDIUM)
empty = [i for i in range(81) if not g.given(i)]
assert not g.set_value([i for i in range(81) if g.given(i)][0], 5)
i = empty[0]
wrong = (g.solution[i] % 9) + 1
assert g.set_value(i, wrong) and g.values[i] == wrong
peer = [j for j in se.PEERS[i] if g.values[j] == 0][0]
assert g.set_value(peer, wrong) and g.conflict(i) and g.conflict(peer)
assert g.undo() == peer and g.undo() == i and g.values[i] == 0 and g.undo() is None
h = g.hint(i)
assert h == i and g.values[i] == g.solution[i] and not g.set_value(i, 0)
data = json.loads(json.dumps(g.to_dict()))
g2 = se.Sudoku()
g2.from_dict(data)
assert g2.values == g.values and g2.hinted == g.hinted
bad = dict(data, values=[9] * 81)
try:
	g2.from_dict(bad)
	assert False
except ValueError:
	pass
for j in range(81):
	if not g.given(j) and not g.hinted[j]:
		g.set_value(j, g.solution[j])
assert g.won() and not g.set_value(empty[-1], 0) and g.hint(0) is None
print("sudoku ok")
