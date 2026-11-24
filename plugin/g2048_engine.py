# -*- coding: utf-8 -*-
# E2games - 2048 rules.
# Pure Python, no Enigma2 imports, so it can be tested on any machine.
# The board is a list of SIZE * SIZE numbers read row by row, 0 = empty.

import random

SIZE = 4
CELLS = SIZE * SIZE
GOAL = 2048
FOUR_CHANCE = 0.1

# board graphics layout (pixels on a 1280x720 screen, see tools/make_2048.py)
TILE, GAP = 120, 14
BOARD = SIZE * TILE + (SIZE + 1) * GAP


def cell_origin(i):
	"""Top-left corner of cell i inside the board image."""
	return (GAP + (i % SIZE) * (TILE + GAP), GAP + (i // SIZE) * (TILE + GAP))

# for each direction: the lines of cell indices, first index = the wall the tiles move to
LINES = {
	"left": [[r * SIZE + c for c in range(SIZE)] for r in range(SIZE)],
	"right": [[r * SIZE + c for c in reversed(range(SIZE))] for r in range(SIZE)],
	"up": [[r * SIZE + c for r in range(SIZE)] for c in range(SIZE)],
	"down": [[r * SIZE + c for r in reversed(range(SIZE))] for c in range(SIZE)],
}


def slide(board, direction):
	"""Return (new board, points, moves, merged) without adding a tile.
	moves: list of (from index, to index, value before the move);
	merged: set of indices where two tiles became one."""
	new = list(board)
	points = 0
	moves = []
	merged = set()
	for line in LINES[direction]:
		out = [0] * SIZE
		target = 0               # next free position in this line
		can_merge = False        # out[target - 1] may still take a tile
		for i in line:
			v = board[i]
			if not v:
				continue
			if can_merge and out[target - 1] == v:
				out[target - 1] = v * 2
				dest = line[target - 1]
				points += v * 2
				merged.add(dest)
				can_merge = False   # a tile merges only once per move
			else:
				out[target] = v
				dest = line[target]
				target += 1
				can_merge = True
			moves.append((i, dest, v))
		for k in range(SIZE):
			new[line[k]] = out[k]
	return new, points, moves, merged


class Game2048(object):
	def __init__(self, rng=None, best=0):
		self.rng = rng or random.Random()
		self.best = best
		self.board = [0] * CELLS
		self.score = 0
		self.moves = 0
		self.reached = False      # the goal tile has been made
		self.keep_going = False   # the player chose to continue after the goal
		self.undo_state = None
		self.last_spawn = None

	def new_game(self):
		self.board = [0] * CELLS
		self.score = 0
		self.moves = 0
		self.reached = False
		self.keep_going = False
		self.undo_state = None
		self.spawn()
		self.spawn()

	def spawn(self):
		empty = [i for i in range(CELLS) if not self.board[i]]
		if not empty:
			self.last_spawn = None
			return None
		i = self.rng.choice(empty)
		self.board[i] = 4 if self.rng.random() < FOUR_CHANCE else 2
		self.last_spawn = i
		return i

	def can_move(self):
		if 0 in self.board:
			return True
		for r in range(SIZE):
			for c in range(SIZE):
				v = self.board[r * SIZE + c]
				if c + 1 < SIZE and self.board[r * SIZE + c + 1] == v:
					return True
				if r + 1 < SIZE and self.board[(r + 1) * SIZE + c] == v:
					return True
		return False

	def over(self):
		return not self.can_move()

	def waiting_at_goal(self):
		"""True when the goal was just reached and the player has not continued."""
		return self.reached and not self.keep_going

	def move(self, direction):
		"""Make a move. Returns (moves, merged) or None if nothing moved."""
		if self.waiting_at_goal() or self.over():
			return None
		new, points, moves, merged = slide(self.board, direction)
		if new == self.board:
			return None
		self.undo_state = (list(self.board), self.score, self.moves, self.reached)
		self.board = new
		self.score += points
		self.moves += 1
		if self.score > self.best:
			self.best = self.score
		if not self.reached and max(new) >= GOAL:
			self.reached = True
		self.spawn()
		return moves, merged

	def continue_after_goal(self):
		if self.waiting_at_goal():
			self.keep_going = True
			return True
		return False

	def undo(self):
		"""Take back the last move (one step only)."""
		if self.undo_state is None:
			return False
		self.board, self.score, self.moves, self.reached = self.undo_state
		self.board = list(self.board)
		self.undo_state = None
		self.last_spawn = None
		return True

	# ---- saving -----------------------------------------------------------
	def to_dict(self):
		return {"board": self.board, "score": self.score, "moves": self.moves,
			"reached": self.reached, "keep_going": self.keep_going}

	def from_dict(self, data):
		board = [int(v) for v in data["board"]]
		if len(board) != CELLS or any(v and (v < 2 or v & (v - 1)) for v in board):
			raise ValueError("bad saved game")
		self.board = board
		self.score = int(data.get("score", 0))
		self.moves = int(data.get("moves", 0))
		self.reached = bool(data.get("reached", False))
		self.keep_going = bool(data.get("keep_going", False))
		self.undo_state = None
		self.last_spawn = None
		if self.score > self.best:
			self.best = self.score
