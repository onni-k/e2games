# -*- coding: utf-8 -*-
# E2games - bubble shooter rules.
# Pure Python, no Enigma2 imports, so it can be tested on any machine.
#
# Bubbles sit on a hexagonal grid: COLS bubbles on a full row, COLS - 1 on a
# shifted row.  Coordinates are in "field units" (field is W x H, y downwards).

import math
import random

COLS = 8
R = 22.0                     # bubble radius
D = 2 * R
RS = R * math.sqrt(3.0)      # vertical distance between rows
W = COLS * D                 # 352
H = 680.0
DEAD_ROW = 14                # a bubble in this row (or below) ends the game
DEAD_Y = R + DEAD_ROW * RS - R
SHOOTER = (W / 2.0, 632.0)
NEXT_POS = (52.0, 650.0)
SPEED = 1100.0
MAX_ANGLE = 1.35             # radians from straight up
TURN_SPEED = 0.325           # default radians per second while a key is held
HIT_DIST = D * 0.86
COLORS = 6
MAX_EFFECTS = 40

SCORE_POP = 10
SCORE_DROP = 30
SCORE_LEVEL = 500


def level_setup(level):
	"""(rows, colours, shots before a new row) for a level."""
	return min(4 + level, 9), min(3 + level, COLORS), max(3, 8 - level)


class BubbleShooter(object):
	PLAY, CLEARED, OVER = 0, 1, 2

	def __init__(self, rng=None, highscore=0):
		self.rng = rng or random.Random()
		self.highscore = highscore
		self.new_highscore = False
		self.grid = {}
		self.parity = 0
		self.effects = []
		self.state = self.OVER
		self.score = 0
		self.level = 1
		self.angle = 0.0
		self.turn = 0
		self.turn_speed = TURN_SPEED
		self.shot = None
		self.current = 0
		self.next = 0
		self.misses = 0
		self.colors = 4
		self.shots_per_row = 6
		self.wait = 0.0
		self.note = ""
		self.note_time = 0.0

	# ---- grid helpers -----------------------------------------------------
	def shifted(self, row):
		return (row + self.parity) % 2 == 1

	def valid(self, row, col):
		return row >= 0 and 0 <= col < (COLS - 1 if self.shifted(row) else COLS)

	def cell_xy(self, row, col):
		return (R + col * D + (R if self.shifted(row) else 0.0), R + row * RS)

	def neighbours(self, row, col):
		if self.shifted(row):
			cells = ((row, col - 1), (row, col + 1), (row - 1, col), (row - 1, col + 1), (row + 1, col), (row + 1, col + 1))
		else:
			cells = ((row, col - 1), (row, col + 1), (row - 1, col - 1), (row - 1, col), (row + 1, col - 1), (row + 1, col))
		return [c for c in cells if self.valid(*c)]

	def present_colors(self):
		return sorted(set(self.grid.values()))

	def _random_color(self):
		colors = self.present_colors() or list(range(self.colors))
		return self.rng.choice(colors)

	# ---- game control -------------------------------------------------------
	def new_game(self):
		self.score = 0
		self.level = 1
		self.new_highscore = False
		self._start_level()

	def _start_level(self):
		rows, self.colors, self.shots_per_row = level_setup(self.level)
		self.grid = {}
		self.parity = 0
		for row in range(rows):
			for col in range(COLS):
				if self.valid(row, col):
					self.grid[(row, col)] = self.rng.randrange(self.colors)
		self.effects = []
		self.shot = None
		self.misses = 0
		self.angle = 0.0
		self.current = self._random_color()
		self.next = self._random_color()
		self.state = self.PLAY

	def _add(self, points):
		self.score += points
		if self.score > self.highscore:
			self.highscore = self.score
			self.new_highscore = True

	def _set_note(self, note, time=1.5):
		self.note = note
		self.note_time = time

	def shoot(self):
		if self.state != self.PLAY or self.shot is not None:
			return False
		x, y = SHOOTER
		self.shot = [x, y, SPEED * math.sin(self.angle), -SPEED * math.cos(self.angle), self.current]
		self.current = self.next
		self.next = self._random_color()
		return True

	def swap(self):
		if self.state == self.PLAY and self.current != self.next:
			self.current, self.next = self.next, self.current
			return True
		return False

	def rotate(self, amount):
		self.angle = max(-MAX_ANGLE, min(MAX_ANGLE, self.angle + amount))

	# ---- simulation -------------------------------------------------------
	def update(self, dt):
		if self.note_time > 0.0:
			self.note_time -= dt
			if self.note_time <= 0.0:
				self.note = ""
		if self.turn:
			self.rotate(self.turn * self.turn_speed * dt)
		self._update_effects(dt)
		if self.state == self.CLEARED:
			self.wait -= dt
			if self.wait <= 0.0:
				self.level += 1
				self._start_level()
			return
		if self.state != self.PLAY or self.shot is None:
			return
		steps = int(SPEED * dt / (R * 0.4)) + 1
		h = dt / steps
		for i in range(steps):
			if self._move_shot(h):
				break

	def _move_shot(self, h):
		s = self.shot
		s[0] += s[2] * h
		s[1] += s[3] * h
		if s[0] < R:
			s[0] = 2 * R - s[0]
			s[2] = abs(s[2])
		elif s[0] > W - R:
			s[0] = 2 * (W - R) - s[0]
			s[2] = -abs(s[2])
		if s[1] <= R or self._touching(s[0], s[1]):
			self._settle(s[0], max(s[1], R), s[4])
			return True
		return False

	def _touching(self, x, y):
		row = int(round((y - R) / RS))
		for r in (row - 1, row, row + 1):
			for c in range(COLS):
				if (r, c) in self.grid:
					cx, cy = self.cell_xy(r, c)
					if (cx - x) ** 2 + (cy - y) ** 2 < HIT_DIST * HIT_DIST:
						return True
		return False

	def _snap_cell(self, x, y):
		row = int(round((y - R) / RS))
		best, best_d = None, None
		for r in range(max(0, row - 1), row + 2):
			for c in range(COLS):
				if not self.valid(r, c) or (r, c) in self.grid:
					continue
				if r > 0 and not any(n in self.grid for n in self.neighbours(r, c)):
					continue
				cx, cy = self.cell_xy(r, c)
				d = (cx - x) ** 2 + (cy - y) ** 2
				if best_d is None or d < best_d:
					best, best_d = (r, c), d
		if best is None:          # should not happen; fall back to any free cell nearby
			for r in range(0, row + 3):
				for c in range(COLS):
					if self.valid(r, c) and (r, c) not in self.grid:
						cx, cy = self.cell_xy(r, c)
						d = (cx - x) ** 2 + (cy - y) ** 2
						if best_d is None or d < best_d:
							best, best_d = (r, c), d
		return best

	def _settle(self, x, y, color):
		self.shot = None
		cell = self._snap_cell(x, y)
		self.grid[cell] = color
		group = self._group(cell)
		if len(group) >= 3:
			for c in group:
				self._effect(c, "pop")
				del self.grid[c]
			self._add(SCORE_POP * len(group))
			floating = self._floating()
			for c in floating:
				self._effect(c, "fall")
				del self.grid[c]
			if floating:
				self._add(SCORE_DROP * len(floating))
		else:
			self.misses += 1
			if self.misses >= self.shots_per_row:
				self.misses = 0
				self._push_row()
		self._after_shot()

	def _after_shot(self):
		if not self.grid:
			self._add(SCORE_LEVEL * self.level)
			self.state = self.CLEARED
			self.wait = 2.0
			self._set_note("cleared", 2.0)
			return
		if any(r >= DEAD_ROW for r, c in self.grid):
			self.state = self.OVER
			return
		# keep the bubbles in hand to colours that are still on the board
		colors = self.present_colors()
		if self.current not in colors:
			self.current = self.rng.choice(colors)
		if self.next not in colors:
			self.next = self.rng.choice(colors)

	def _push_row(self):
		self.grid = dict(((r + 1, c), v) for (r, c), v in self.grid.items())
		self.parity ^= 1
		colors = self.present_colors() or list(range(self.colors))
		for c in range(COLS):
			if self.valid(0, c):
				self.grid[(0, c)] = self.rng.choice(colors)
		self._set_note("row", 1.0)

	def _group(self, cell):
		color = self.grid[cell]
		seen = set([cell])
		todo = [cell]
		while todo:
			for n in self.neighbours(*todo.pop()):
				if n not in seen and self.grid.get(n) == color:
					seen.add(n)
					todo.append(n)
		return seen

	def _floating(self):
		seen = set(c for c in self.grid if c[0] == 0)
		todo = list(seen)
		while todo:
			for n in self.neighbours(*todo.pop()):
				if n not in seen and n in self.grid:
					seen.add(n)
					todo.append(n)
		return [c for c in self.grid if c not in seen]

	# ---- effects ----------------------------------------------------------------
	def _effect(self, cell, kind):
		x, y = self.cell_xy(*cell)
		if len(self.effects) >= MAX_EFFECTS:
			del self.effects[0]
		vx = self.rng.uniform(-60.0, 60.0) if kind == "fall" else 0.0
		self.effects.append([x, y, vx, -80.0 if kind == "fall" else 0.0, self.grid[cell], kind, 0.25])

	def _update_effects(self, dt):
		alive = []
		for e in self.effects:
			if e[5] == "pop":
				e[6] -= dt
				if e[6] > 0.0:
					alive.append(e)
			else:
				e[3] += 1400.0 * dt
				e[0] += e[2] * dt
				e[1] += e[3] * dt
				if e[1] < H + R:
					alive.append(e)
		self.effects = alive

	# ---- aiming guide -------------------------------------------------------
	def aim_points(self, count, spacing):
		"""Points along the shot path (bouncing off the walls) until it hits."""
		x, y = SHOOTER
		dx, dy = math.sin(self.angle), -math.cos(self.angle)
		points = []
		travelled = 0.0
		step = R * 0.4
		next_point = spacing
		while len(points) < count and travelled < 2000.0:
			x += dx * step
			y += dy * step
			travelled += step
			if x < R:
				x = 2 * R - x
				dx = abs(dx)
			elif x > W - R:
				x = 2 * (W - R) - x
				dx = -abs(dx)
			if y <= R or self._touching(x, y):
				break
			if travelled >= next_point:
				points.append((x, y))
				next_point += spacing
		return points
