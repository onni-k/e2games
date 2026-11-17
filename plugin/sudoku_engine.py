# -*- coding: utf-8 -*-
# E2games - sudoku generator, solver and game state.
# Pure Python, no Enigma2 imports, so it can be tested on any machine.
# A board is a list of 81 numbers, 0 = empty, read row by row.

import random

EASY, MEDIUM, HARD = 0, 1, 2
CLUES = (40, 32, 25)             # target number of given digits per difficulty
UNDO_LIMIT = 500

ROW = [i // 9 for i in range(81)]
COL = [i % 9 for i in range(81)]
BOX = [(i // 27) * 3 + (i % 9) // 3 for i in range(81)]
PEERS = []
for _i in range(81):
	PEERS.append(sorted(set(j for j in range(81) if j != _i and (ROW[j] == ROW[_i] or COL[j] == COL[_i] or BOX[j] == BOX[_i]))))
ALL = 0x3FE                      # bits 1..9

# board graphics layout (pixels on a 1280x720 screen, see tools/make_sudoku.py)
BORDER, CELL, LINE, THICK = 6, 60, 2, 5
BOARD = 2 * BORDER + 9 * CELL + 6 * LINE + 2 * THICK


def cell_origin(i):
	"""Top-left corner of cell i inside the board image."""
	r, c = ROW[i], COL[i]
	return (BORDER + c * (CELL + LINE) + (c // 3) * (THICK - LINE),
		BORDER + r * (CELL + LINE) + (r // 3) * (THICK - LINE))


def _bits(mask):
	return [d for d in range(1, 10) if mask & (1 << d)]


def count_solutions(board, limit=2, rng=None, out=None):
	"""Count solutions up to `limit`; the first one found goes to `out`."""
	cells = list(board)
	rows = [0] * 9
	cols = [0] * 9
	boxes = [0] * 9
	for i, v in enumerate(cells):
		if v:
			bit = 1 << v
			if rows[ROW[i]] & bit or cols[COL[i]] & bit or boxes[BOX[i]] & bit:
				return 0
			rows[ROW[i]] |= bit
			cols[COL[i]] |= bit
			boxes[BOX[i]] |= bit
	empty = [i for i in range(81) if not cells[i]]
	found = [0]

	def search():
		best, best_mask, best_n = -1, 0, 10
		for i in empty:
			if cells[i]:
				continue
			mask = ALL & ~(rows[ROW[i]] | cols[COL[i]] | boxes[BOX[i]])
			n = bin(mask).count("1")
			if n < best_n:
				best, best_mask, best_n = i, mask, n
				if n <= 1:
					break
		if best < 0:
			found[0] += 1
			if out is not None and found[0] == 1:
				out[:] = cells
			return found[0] >= limit
		if best_n == 0:
			return False
		digits = _bits(best_mask)
		if rng is not None:
			rng.shuffle(digits)
		r, c, b = ROW[best], COL[best], BOX[best]
		for d in digits:
			bit = 1 << d
			cells[best] = d
			rows[r] |= bit
			cols[c] |= bit
			boxes[b] |= bit
			if search():
				return True
			rows[r] &= ~bit
			cols[c] &= ~bit
			boxes[b] &= ~bit
		cells[best] = 0
		return False

	search()
	return found[0]


def generate(difficulty, rng=None):
	"""Return (puzzle, solution) with exactly one solution."""
	rng = rng or random.Random()
	solution = [0] * 81
	count_solutions([0] * 81, 1, rng, solution)
	puzzle = list(solution)
	target = CLUES[difficulty]
	order = list(range(81))
	rng.shuffle(order)
	filled = 81
	for i in order:
		if filled <= target:
			break
		keep = puzzle[i]
		puzzle[i] = 0
		if count_solutions(puzzle, 2) != 1:
			puzzle[i] = keep
		else:
			filled -= 1
	return puzzle, solution


class Sudoku(object):
	def __init__(self, rng=None):
		self.rng = rng or random.Random()
		self.difficulty = EASY
		self.puzzle = [0] * 81
		self.solution = [0] * 81
		self.values = [0] * 81
		self.hinted = [False] * 81
		self.history = []
		self.hints = 0
		self.seconds = 0

	def new_game(self, difficulty=None):
		if difficulty is not None:
			self.difficulty = difficulty
		self.puzzle, self.solution = generate(self.difficulty, self.rng)
		self.values = list(self.puzzle)
		self.hinted = [False] * 81
		self.history = []
		self.hints = 0
		self.seconds = 0

	def given(self, i):
		return self.puzzle[i] != 0

	def set_value(self, i, value):
		if self.given(i) or self.hinted[i] or self.values[i] == value or self.won():
			return False
		self.history.append((i, self.values[i]))
		if len(self.history) > UNDO_LIMIT:
			del self.history[0]
		self.values[i] = value
		return True

	def undo(self):
		while self.history:
			i, value = self.history.pop()
			if not self.hinted[i]:
				self.values[i] = value
				return i
		return None

	def hint(self, i):
		"""Fill cell i with the right digit (or pick a cell if i is not usable)."""
		if self.won():
			return None
		if self.given(i) or self.values[i] == self.solution[i]:
			wrong = [j for j in range(81) if self.values[j] != self.solution[j]]
			if not wrong:
				return None
			i = min(wrong, key=lambda j: (self.values[j] == 0, j))
		self.values[i] = self.solution[i]
		self.hinted[i] = True
		self.hints += 1
		return i

	def conflict(self, i):
		v = self.values[i]
		return v != 0 and any(self.values[j] == v for j in PEERS[i])

	def filled(self):
		return sum(1 for v in self.values if v)

	def won(self):
		return self.values == self.solution

	# ---- saving -----------------------------------------------------------
	def to_dict(self):
		return {"difficulty": self.difficulty, "puzzle": self.puzzle, "solution": self.solution,
			"values": self.values, "hinted": self.hinted, "hints": self.hints, "seconds": self.seconds}

	def from_dict(self, data):
		puzzle, solution, values = data["puzzle"], data["solution"], data["values"]
		hinted = data.get("hinted", [False] * 81)
		ok = all(len(x) == 81 for x in (puzzle, solution, values, hinted))
		ok = ok and all(0 <= v <= 9 for v in values) and all(1 <= v <= 9 for v in solution)
		ok = ok and all(p == 0 or (p == s and v == p) for p, s, v in zip(puzzle, solution, values))
		ok = ok and count_solutions(solution, 2) == 1
		if not ok:
			raise ValueError("bad saved game")
		self.difficulty = int(data["difficulty"]) if int(data["difficulty"]) in (EASY, MEDIUM, HARD) else EASY
		self.puzzle, self.solution, self.values = list(puzzle), list(solution), list(values)
		self.hinted = [bool(h) for h in hinted]
		self.hints = int(data.get("hints", 0))
		self.seconds = int(data.get("seconds", 0))
		self.history = []
