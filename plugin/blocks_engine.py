# -*- coding: utf-8 -*-
# E2games - falling blocks rules.
# Pure Python, no Enigma2 imports, so it can be tested on any machine.
#
# The well is COLS x ROWS cells; the top HIDDEN rows are above the visible
# area.  Rotation follows the common "SRS" system with wall kicks.

import random

COLS, ROWS, HIDDEN = 10, 22, 2
VISIBLE = ROWS - HIDDEN
LOCK_DELAY = 0.5
LOCK_RESETS = 15
SOFT_DROP_INTERVAL = 0.04
CLEAR_TIME = 0.3
LINE_SCORES = (0, 100, 300, 500, 800)
LINES_PER_LEVEL = 10

# piece shapes in their spawn orientation: (row, col) inside a 3x3 or 4x4 box
SHAPES = {
	"I": ((1, 0), (1, 1), (1, 2), (1, 3)),
	"O": ((0, 1), (0, 2), (1, 1), (1, 2)),
	"T": ((0, 1), (1, 0), (1, 1), (1, 2)),
	"S": ((0, 1), (0, 2), (1, 0), (1, 1)),
	"Z": ((0, 0), (0, 1), (1, 1), (1, 2)),
	"J": ((0, 0), (1, 0), (1, 1), (1, 2)),
	"L": ((0, 2), (1, 0), (1, 1), (1, 2)),
}
PIECES = "IOTSZJL"
BOX = {"I": 4, "O": 4}           # others use a 3x3 box

# wall kicks (dx, dy) with y growing upwards, as usually written down
_KICKS = {
	(0, 1): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
	(1, 0): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
	(1, 2): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
	(2, 1): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
	(2, 3): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
	(3, 2): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
	(3, 0): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
	(0, 3): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
}
_KICKS_I = {
	(0, 1): ((0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)),
	(1, 0): ((0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)),
	(1, 2): ((0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)),
	(2, 1): ((0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)),
	(2, 3): ((0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)),
	(3, 2): ((0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)),
	(3, 0): ((0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)),
	(0, 3): ((0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)),
}


def cells_of(piece, rotation):
	"""Cells (row, col) of a piece inside its box for a rotation 0..3."""
	size = BOX.get(piece, 3)
	cells = SHAPES[piece]
	if piece == "O":
		return cells
	for i in range(rotation % 4):
		cells = tuple((c, size - 1 - r) for r, c in cells)
	return cells


def gravity_interval(level):
	"""Seconds per row at a level (the usual guideline curve)."""
	return max(0.02, (0.8 - (level - 1) * 0.007) ** (level - 1))


class Blocks(object):
	PLAY, PAUSE, OVER = 0, 1, 2

	def __init__(self, rng=None, highscore=0):
		self.rng = rng or random.Random()
		self.highscore = highscore
		self.new_highscore = False
		self.board = [[None] * COLS for r in range(ROWS)]
		self.state = self.OVER
		self.score = 0
		self.lines = 0
		self.level = 1
		self.bag = []
		self.queue = []
		self.held = None
		self.hold_used = False
		self.piece = None
		self.rot = 0
		self.row = 0
		self.col = 0
		self.soft = False
		self.fall_time = 0.0
		self.lock_time = 0.0
		self.lock_resets = 0
		self.clearing = []
		self.clear_time = 0.0

	# ---- game control -------------------------------------------------------
	def new_game(self):
		self.board = [[None] * COLS for r in range(ROWS)]
		self.score = 0
		self.lines = 0
		self.level = 1
		self.new_highscore = False
		self.bag = []
		self.queue = [self._from_bag() for i in range(3)]
		self.held = None
		self.clearing = []
		self.soft = False
		self.state = self.PLAY
		self._spawn()

	def toggle_pause(self):
		if self.state == self.PLAY:
			self.state = self.PAUSE
		elif self.state == self.PAUSE:
			self.state = self.PLAY

	def _from_bag(self):
		if not self.bag:
			self.bag = list(PIECES)
			self.rng.shuffle(self.bag)
		return self.bag.pop()

	def _spawn(self, piece=None):
		if piece is None:
			piece = self.queue.pop(0)
			self.queue.append(self._from_bag())
		self.piece = piece
		self.rot = 0
		self.row = 1
		self.col = 3
		self.fall_time = 0.0
		self.lock_time = 0.0
		self.lock_resets = 0
		if not self._fits(self.row, self.col, self.rot):
			self.state = self.OVER
			self.piece = None

	def _add(self, points):
		self.score += points
		if self.score > self.highscore:
			self.highscore = self.score
			self.new_highscore = True

	# ---- collision ------------------------------------------------------------
	def _fits(self, row, col, rot, piece=None):
		for r, c in cells_of(piece or self.piece, rot):
			r += row
			c += col
			if c < 0 or c >= COLS or r >= ROWS or (r >= 0 and self.board[r][c] is not None):
				return False
		return True

	def piece_cells(self, row=None):
		if self.piece is None:
			return []
		row = self.row if row is None else row
		return [(r + row, c + self.col) for r, c in cells_of(self.piece, self.rot)]

	def ghost_row(self):
		row = self.row
		while self._fits(row + 1, self.col, self.rot):
			row += 1
		return row

	def _on_ground(self):
		return not self._fits(self.row + 1, self.col, self.rot)

	def _moved(self):
		# moving or turning on the ground gives a little more time, up to a limit
		if self._on_ground() and self.lock_resets < LOCK_RESETS:
			self.lock_resets += 1
			self.lock_time = 0.0

	# ---- player actions -------------------------------------------------------
	def _can_act(self):
		return self.state == self.PLAY and self.piece is not None and not self.clearing

	def move(self, dx):
		if self._can_act() and self._fits(self.row, self.col + dx, self.rot):
			self.col += dx
			self._moved()
			return True
		return False

	def rotate(self, direction):
		"""direction +1 = clockwise, -1 = counter-clockwise."""
		if not self._can_act() or self.piece == "O":
			return False
		new = (self.rot + direction) % 4
		kicks = (_KICKS_I if self.piece == "I" else _KICKS)[(self.rot, new)]
		for dx, dy in kicks:
			if self._fits(self.row - dy, self.col + dx, new):
				self.row -= dy
				self.col += dx
				self.rot = new
				self._moved()
				return True
		return False

	def set_soft_drop(self, on):
		self.soft = bool(on)

	def hard_drop(self):
		if not self._can_act():
			return False
		target = self.ghost_row()
		self._add(2 * (target - self.row))
		self.row = target
		self._lock()
		return True

	def hold(self):
		if not self._can_act() or self.hold_used:
			return False
		current = self.piece
		if self.held is None:
			self.held = current
			self._spawn()
		else:
			piece, self.held = self.held, current
			self._spawn(piece)
		self.hold_used = True
		return True

	# ---- simulation -----------------------------------------------------------
	def update(self, dt):
		if self.state != self.PLAY:
			return
		if self.clearing:
			self.clear_time -= dt
			if self.clear_time <= 0.0:
				self._collapse()
			return
		if self.piece is None:
			return
		interval = gravity_interval(self.level)
		if self.soft:
			interval = min(interval, SOFT_DROP_INTERVAL)
		if self._on_ground():
			self.fall_time = 0.0
			self.lock_time += dt
			if self.lock_time >= LOCK_DELAY:
				self._lock()
			return
		self.fall_time += dt
		while self.fall_time >= interval and not self._on_ground():
			self.fall_time -= interval
			self.row += 1
			if self.soft:
				self._add(1)
		if self._on_ground():
			self.fall_time = 0.0

	def _lock(self):
		for r, c in self.piece_cells():
			if r >= 0:
				self.board[r][c] = self.piece
		above = all(r < HIDDEN for r, c in self.piece_cells())
		self.piece = None
		full = [r for r in range(ROWS) if all(v is not None for v in self.board[r])]
		if full:
			self.clearing = full
			self.clear_time = CLEAR_TIME
			n = len(full)
			self._add(LINE_SCORES[min(n, 4)] * self.level)
			return
		if above:                # locked completely out of sight
			self.state = self.OVER
			return
		self._spawn()
		self.hold_used = False

	def _collapse(self):
		for r in sorted(self.clearing):
			del self.board[r]
			self.board.insert(0, [None] * COLS)
		self.lines += len(self.clearing)
		self.level = 1 + self.lines // LINES_PER_LEVEL
		self.clearing = []
		self._spawn()
		self.hold_used = False

	# ---- drawing helper -----------------------------------------------------
	def display(self):
		"""Visible rows as lists: piece letter, "ghost", "flash" or None."""
		rows = [list(self.board[r]) for r in range(HIDDEN, ROWS)]
		for r in self.clearing:
			if r >= HIDDEN:
				rows[r - HIDDEN] = ["flash"] * COLS
		if self.piece is not None and self.state != self.OVER:
			ghost = self.ghost_row()
			if ghost != self.row:
				for r, c in self.piece_cells(ghost):
					if r >= HIDDEN and rows[r - HIDDEN][c] is None:
						rows[r - HIDDEN][c] = "ghost"
			for r, c in self.piece_cells():
				if r >= HIDDEN:
					rows[r - HIDDEN][c] = self.piece
		return rows
