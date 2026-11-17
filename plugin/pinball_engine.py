# -*- coding: utf-8 -*-
# E2games - pinball physics engine.
# Pure Python, no Enigma2 imports, so it can be tested on any machine.
# All coordinates are in "table units" (table is W x H, y grows downwards).
#
# The outer cabinet (walls, launch lane, flippers, slingshots) is the same on
# every table; each entry in TABLES adds its own targets on the playfield.

import math
import random

W, H = 420.0, 700.0          # table size
R = 9.0                      # ball radius
GRAVITY = 760.0
MAX_SPEED = 1500.0
STEP = 1.0 / 240.0           # physics sub-step
MAX_STEPS = 14               # per update() call

PLAY_L, PLAY_R = 10.0, 370.0     # playfield walls
LANE_R = 410.0                   # outer wall of the launch lane
ARC_CX, ARC_CY, ARC_R = 210.0, 210.0, 200.0
PLUNGER_Y = 672.0
BALL_START = (390.0, PLUNGER_Y - R)

FLIP_LEN = 62.0
FLIP_RAD = 6.0
FLIP_REST = 0.50             # radians below horizontal
FLIP_UP = -0.50              # radians above horizontal
FLIP_SPEED_UP = 15.0
FLIP_SPEED_DOWN = 11.0
FLIP_PIVOTS = ((118.0, 610.0), (262.0, 610.0))   # left, right

SLING_L = ((55.0, 440.0), (55.0, 525.0), (100.0, 550.0))
SLING_R = ((325.0, 440.0), (325.0, 525.0), (280.0, 550.0))
GUIDE_L = ((10.0, 540.0), (118.0, 604.0))
GUIDE_R = ((370.0, 540.0), (262.0, 604.0))
GATE = ((370.0, 90.0), (370.0, 210.0))

SCORE_BUMPER = 100
SCORE_SLING = 10
SCORE_STANDUP = 500
SCORE_DROP = 300
SCORE_LANE = 200
SCORE_SAUCER = 1000
SCORE_BANK = 5000            # every target of a group done
MAX_MULT = 5
BALLS_PER_GAME = 3
BALL_SAVE_TIME = 8.0
SAUCER_HOLD = 1.0

K_WALL, K_SLING, K_STANDUP, K_DROP, K_GATE = 0, 1, 2, 3, 4

# ---- tables ---------------------------------------------------------------
# bumpers:  (x, y, radius)             active, kick the ball away
# posts:    (x, y, radius)             passive rubber posts
# standups: ((x1, y1), (x2, y2))       light up when hit
# drops:    ((x1, y1), (x2, y2))       fall down when hit, come back as a bank
# lanes:    (x1, y1, x2, y2)           rollover sensors (ball passes through)
# saucers:  (x, y, radius, vx, vy)     catch the ball and kick it out again
# walls:    polylines
TABLES = [
	{
		"name": "Classic",
		"colors": ((14, 18, 64), (54, 24, 94)),
		"bumpers": ((120.0, 215.0, 22.0), (260.0, 215.0, 22.0), (190.0, 300.0, 22.0)),
		"posts": (),
		"standups": (((14.0, 320.0), (14.0, 350.0)), ((14.0, 358.0), (14.0, 388.0)), ((14.0, 396.0), (14.0, 426.0))),
		"drops": (),
		"lanes": (),
		"saucers": (),
		"walls": (((10.0, 235.0), (42.0, 270.0), (10.0, 295.0)),),
	},
	{
		"name": "Target Bank",
		"colors": ((10, 46, 40), (16, 84, 60)),
		"bumpers": ((105.0, 175.0, 20.0), (275.0, 175.0, 20.0)),
		"posts": ((190.0, 165.0, 7.0),),
		"standups": (((366.0, 330.0), (366.0, 362.0)), ((366.0, 372.0), (366.0, 404.0))),
		"drops": (((122.0, 300.0), (148.0, 300.0)), ((154.0, 300.0), (180.0, 300.0)),
			((200.0, 300.0), (226.0, 300.0)), ((232.0, 300.0), (258.0, 300.0))),
		"lanes": (),
		"saucers": ((60.0, 380.0, 13.0, 260.0, -560.0),),
		"walls": (((10.0, 330.0), (34.0, 352.0)), ((10.0, 430.0), (34.0, 408.0))),
	},
	{
		"name": "Star Lanes",
		"colors": ((40, 12, 50), (90, 22, 50)),
		"bumpers": ((140.0, 180.0, 19.0), (240.0, 180.0, 19.0), (190.0, 245.0, 19.0), (100.0, 265.0, 17.0), (280.0, 265.0, 17.0)),
		"posts": ((110.0, 360.0, 6.0), (270.0, 360.0, 6.0), (190.0, 405.0, 6.0)),
		"standups": (),
		"drops": (),
		"lanes": ((132.0, 68.0, 168.0, 104.0), (172.0, 68.0, 208.0, 104.0), (212.0, 68.0, 248.0, 104.0)),
		"saucers": ((190.0, 335.0, 12.0, 0.0, -520.0),),
		"walls": (((128.0, 62.0), (128.0, 110.0)), ((170.0, 62.0), (170.0, 110.0)),
			((210.0, 62.0), (210.0, 110.0)), ((252.0, 62.0), (252.0, 110.0))),
	},
]


def arc_points(n=28):
	pts = []
	for i in range(n + 1):
		t = math.pi + math.pi * i / n
		pts.append((ARC_CX + ARC_R * math.cos(t), ARC_CY + ARC_R * math.sin(t)))
	return pts


def cabinet_polylines():
	"""Walls shared by every table."""
	return [
		[(PLAY_L, H), (PLAY_L, ARC_CY)] + arc_points()[1:] + [(LANE_R, H)],
		[(PLAY_R, H), (PLAY_R, ARC_CY)],
		[(PLAY_R, PLUNGER_Y), (LANE_R, PLUNGER_Y)],
		list(GUIDE_L),
		list(GUIDE_R),
		[SLING_L[0], SLING_L[1], SLING_L[2]],
		[SLING_R[0], SLING_R[1], SLING_R[2]],
	]


def wall_polylines(table=0):
	"""All static walls of a table (also used by the graphics generator)."""
	return cabinet_polylines() + [list(w) for w in TABLES[table]["walls"]]


def segment_box(seg, pad):
	"""Bounding box (x, y, w, h) around a segment, used for the light images."""
	(x1, y1), (x2, y2) = seg
	x, y = min(x1, x2) - pad, min(y1, y2) - pad
	return (x, y, abs(x2 - x1) + 2 * pad, abs(y2 - y1) + 2 * pad)


def lane_light(lane):
	"""Centre of the light below a rollover lane."""
	x1, y1, x2, y2 = lane
	return ((x1 + x2) / 2.0, y2 + 16.0)


def _seg(p1, p2, rest, kind, idx=0):
	dx, dy = p2[0] - p1[0], p2[1] - p1[1]
	return (p1[0], p1[1], dx, dy, 1.0 / (dx * dx + dy * dy), rest, kind, idx)


class Flipper(object):
	def __init__(self, pivot, sign):
		self.px, self.py = pivot
		self.sign = sign          # +1 = left flipper, -1 = right flipper
		self.angle = FLIP_REST
		self.adot = 0.0
		self.pressed = False

	def step(self, h):
		if self.pressed:
			a = self.angle - FLIP_SPEED_UP * h
			if a <= FLIP_UP:
				a = FLIP_UP
		else:
			a = self.angle + FLIP_SPEED_DOWN * h
			if a >= FLIP_REST:
				a = FLIP_REST
		self.adot = (a - self.angle) / h
		self.angle = a

	def frame(self, frames):
		"""Index of the graphics frame for the current angle (0 = rest)."""
		f = (FLIP_REST - self.angle) / (FLIP_REST - FLIP_UP) * (frames - 1)
		return int(f + 0.5)


class Pinball(object):
	READY, PLAY, OVER = 0, 1, 2

	def __init__(self, highscore=0, table=0):
		self.table = table
		t = TABLES[table]
		self.bumpers = t["bumpers"]
		self.posts = t["posts"]
		self.lanes = t["lanes"]
		self.saucers = t["saucers"]
		self.segs = []
		for poly in wall_polylines(table):
			for a, b in zip(poly[:-1], poly[1:]):
				self.segs.append(_seg(a, b, 0.45, K_WALL))
		self.segs.append(_seg(SLING_L[2], SLING_L[0], 0.3, K_SLING, 0))
		self.segs.append(_seg(SLING_R[2], SLING_R[0], 0.3, K_SLING, 1))
		for i, (a, b) in enumerate(t["standups"]):
			self.segs.append(_seg(a, b, 0.5, K_STANDUP, i))
		self.dropSegs = [_seg(a, b, 0.4, K_DROP, i) for i, (a, b) in enumerate(t["drops"])]
		self.gate = _seg(GATE[0], GATE[1], 0.45, K_GATE)
		self.flippers = (Flipper(FLIP_PIVOTS[0], 1), Flipper(FLIP_PIVOTS[1], -1))
		self.highscore = highscore
		self.new_highscore = False
		self.bumper_lit = [0.0] * len(self.bumpers)
		self.sling_lit = [0.0, 0.0]
		self.saucer_lit = [0.0] * len(self.saucers)
		self.acc = 0.0
		self.save_used = False
		self.state = self.OVER
		self.score = 0
		self.balls = 0
		self.mult = 1
		self.note = ""            # short event note: "saved", "bonus" or ""
		self.note_time = 0.0
		self._reset_targets()
		self._reset_ball()

	# ---- game control -------------------------------------------------
	def new_game(self):
		self.score = 0
		self.balls = BALLS_PER_GAME
		self.mult = 1
		self.new_highscore = False
		self.note = ""
		self.save_used = False
		self._reset_targets()
		self._reset_ball()
		self.state = self.READY

	def _reset_targets(self):
		t = TABLES[self.table]
		self.standup_lit = [False] * len(t["standups"])
		self.drop_down = [False] * len(t["drops"])
		self.lane_lit = [False] * len(self.lanes)
		self.lane_inside = [False] * len(self.lanes)

	def _reset_ball(self):
		self.bx, self.by = BALL_START
		self.vx = self.vy = 0.0
		self.charge = 0.0
		self.charging = False
		self.full_time = 0.0
		self.gate_closed = False
		self.play_time = 0.0
		self.still_time = 0.0
		self.held = -1            # index of the saucer holding the ball
		self.hold_time = 0.0
		self.saucer_cool = 0.0

	def set_flipper(self, index, pressed):
		self.flippers[index].pressed = pressed

	def plunger_press(self):
		if self.state == self.READY and not self.charging:
			self.charging = True
			self.charge = 0.0
			self.full_time = 0.0

	def plunger_release(self):
		if self.state == self.READY and self.charging:
			self.charging = False
			self.vx = 0.0
			self.vy = -(900.0 + 540.0 * self.charge)
			self.charge = 0.0
			self.state = self.PLAY
			self.play_time = 0.0

	def _add(self, points):
		self.score += points * self.mult
		if self.score > self.highscore:
			self.highscore = self.score
			self.new_highscore = True

	def _set_note(self, note):
		self.note = note
		self.note_time = 2.0

	def _bank_done(self):
		self._add(SCORE_BANK)
		if self.mult < MAX_MULT:
			self.mult += 1
		self._set_note("bonus")

	# ---- simulation ---------------------------------------------------
	def update(self, dt):
		for lit in (self.bumper_lit, self.sling_lit, self.saucer_lit):
			for i in range(len(lit)):
				if lit[i] > 0.0:
					lit[i] -= dt
		if self.note_time > 0.0:
			self.note_time -= dt
			if self.note_time <= 0.0:
				self.note = ""
		if self.state == self.READY and self.charging:
			self.charge = min(1.0, self.charge + dt / 1.0)
			if self.charge >= 1.0:
				self.full_time += dt
				if self.full_time > 0.5:
					self.plunger_release()
		self.acc += dt
		steps = 0
		while self.acc >= STEP and steps < MAX_STEPS:
			self.acc -= STEP
			steps += 1
			self._step(STEP)
		if self.acc > STEP * 2:
			self.acc = 0.0

	def _step(self, h):
		fl = self.flippers
		fl[0].step(h)
		fl[1].step(h)
		if self.state != self.PLAY:
			return
		self.play_time += h
		if self.saucer_cool > 0.0:
			self.saucer_cool -= h
		if self.held >= 0:
			self.hold_time -= h
			if self.hold_time <= 0.0:
				sx, sy, sr, ex, ey = self.saucers[self.held]
				self.vx = ex + random.uniform(-25.0, 25.0)
				self.vy = ey
				self.held = -1
				self.saucer_cool = 0.6
			return
		vx, vy = self.vx, self.vy + GRAVITY * h
		bx, by = self.bx + vx * h, self.by + vy * h
		R2 = R * R

		segs = self.segs
		if self.dropSegs:
			segs = segs + [s for s in self.dropSegs if not self.drop_down[s[7]]]
		if self.gate_closed:
			segs = segs + [self.gate]
		elif bx < 345.0:
			self.gate_closed = True
		for (x1, y1, dx, dy, inv, rest, kind, idx) in segs:
			t = ((bx - x1) * dx + (by - y1) * dy) * inv
			if t < 0.0:
				t = 0.0
			elif t > 1.0:
				t = 1.0
			ex = bx - (x1 + t * dx)
			ey = by - (y1 + t * dy)
			d2 = ex * ex + ey * ey
			if d2 >= R2 or d2 == 0.0:
				continue
			d = math.sqrt(d2)
			nx, ny = ex / d, ey / d
			bx += nx * (R - d)
			by += ny * (R - d)
			vn = vx * nx + vy * ny
			if vn >= 0.0:
				continue
			if vn > -40.0:
				rest = 0.0
			vx -= (1.0 + rest) * vn * nx
			vy -= (1.0 + rest) * vn * ny
			if kind == K_SLING and vn < -60.0 and 0.08 < t < 0.92:
				k = random.uniform(280.0, 440.0)
				j = random.uniform(-90.0, 90.0)     # breaks endless sling-to-sling loops
				vx += nx * k - ny * j
				vy += ny * k + nx * j
				self.sling_lit[idx] = 0.12
				self._add(SCORE_SLING)
			elif kind == K_STANDUP and vn < -60.0:
				self._hit_standup(idx)
			elif kind == K_DROP and vn < -60.0:
				self._hit_drop(idx)

		for i, (cx, cy, cr) in enumerate(self.bumpers):
			ex, ey = bx - cx, by - cy
			d2 = ex * ex + ey * ey
			rr = cr + R
			if d2 >= rr * rr or d2 == 0.0:
				continue
			d = math.sqrt(d2)
			nx, ny = ex / d, ey / d
			bx += nx * (rr - d)
			by += ny * (rr - d)
			vn = vx * nx + vy * ny
			if vn < 0.0:
				vx -= 1.5 * vn * nx
				vy -= 1.5 * vn * ny
			vn = vx * nx + vy * ny
			if vn < 400.0:
				vx += nx * (400.0 - vn)
				vy += ny * (400.0 - vn)
			vx += random.uniform(-15.0, 15.0)
			self.bumper_lit[i] = 0.15
			self._add(SCORE_BUMPER)

		for (cx, cy, cr) in self.posts:
			ex, ey = bx - cx, by - cy
			d2 = ex * ex + ey * ey
			rr = cr + R
			if d2 >= rr * rr or d2 == 0.0:
				continue
			d = math.sqrt(d2)
			nx, ny = ex / d, ey / d
			bx += nx * (rr - d)
			by += ny * (rr - d)
			vn = vx * nx + vy * ny
			if vn < 0.0:
				rest = 0.6 if vn < -40.0 else 0.0
				vx -= (1.0 + rest) * vn * nx
				vy -= (1.0 + rest) * vn * ny

		rr = R + FLIP_RAD
		for f in fl:
			dx = f.sign * math.cos(f.angle) * FLIP_LEN
			dy = math.sin(f.angle) * FLIP_LEN
			t = ((bx - f.px) * dx + (by - f.py) * dy) / (FLIP_LEN * FLIP_LEN)
			if t < 0.0:
				t = 0.0
			elif t > 1.0:
				t = 1.0
			rx, ry = t * dx, t * dy
			ex = bx - (f.px + rx)
			ey = by - (f.py + ry)
			d2 = ex * ex + ey * ey
			if d2 >= rr * rr or d2 == 0.0:
				continue
			d = math.sqrt(d2)
			nx, ny = ex / d, ey / d
			bx += nx * (rr - d)
			by += ny * (rr - d)
			sx = -f.adot * f.sign * ry      # surface velocity at the contact point
			sy = f.adot * f.sign * rx
			vn = (vx - sx) * nx + (vy - sy) * ny
			if vn < 0.0:
				rest = 0.35 if vn < -40.0 else 0.0
				vx -= (1.0 + rest) * vn * nx
				vy -= (1.0 + rest) * vn * ny

		vx *= 0.9995
		vy *= 0.9995
		sp2 = vx * vx + vy * vy
		if sp2 > MAX_SPEED * MAX_SPEED:
			k = MAX_SPEED / math.sqrt(sp2)
			vx *= k
			vy *= k

		# rollover lanes: count the moment the ball enters a lane
		for i, (x1, y1, x2, y2) in enumerate(self.lanes):
			inside = x1 <= bx <= x2 and y1 <= by <= y2
			if inside and not self.lane_inside[i]:
				self._hit_lane(i)
			self.lane_inside[i] = inside

		# saucers: catch a ball that rolls in
		if self.saucer_cool <= 0.0:
			for i, (cx, cy, cr, ex, ey) in enumerate(self.saucers):
				if (bx - cx) ** 2 + (by - cy) ** 2 < cr * cr:
					self.bx, self.by, self.vx, self.vy = cx, cy, 0.0, 0.0
					self.held = i
					self.hold_time = SAUCER_HOLD
					self.saucer_lit[i] = SAUCER_HOLD
					self._add(SCORE_SAUCER)
					return

		# ball fell back onto the plunger -> launch again
		if bx > PLAY_R and by > PLUNGER_Y - R - 3.0 and sp2 < 900.0 and not self.gate_closed:
			self._reset_ball()
			self.state = self.READY
			return

		# nudge a ball that got stuck somewhere
		if sp2 < 64.0 and not (fl[0].pressed or fl[1].pressed):
			self.still_time += h
			if self.still_time > 2.5:
				vx += random.uniform(-150.0, 150.0)
				vy -= 220.0
				self.still_time = 0.0
		else:
			self.still_time = 0.0

		self.bx, self.by, self.vx, self.vy = bx, by, vx, vy

		if by > H + R or bx < -R or bx > W + R or by < -R:
			self._drain()

	def _hit_standup(self, idx):
		self._add(SCORE_STANDUP)
		self.standup_lit[idx] = True
		if all(self.standup_lit):
			self.standup_lit = [False] * len(self.standup_lit)
			self._bank_done()

	def _hit_drop(self, idx):
		self._add(SCORE_DROP)
		self.drop_down[idx] = True
		if all(self.drop_down):
			self.drop_down = [False] * len(self.drop_down)
			self._bank_done()

	def _hit_lane(self, idx):
		self._add(SCORE_LANE)
		self.lane_lit[idx] = True
		if all(self.lane_lit):
			self.lane_lit = [False] * len(self.lane_lit)
			self._bank_done()

	def _drain(self):
		saved = self.play_time < BALL_SAVE_TIME and not self.save_used
		self._reset_ball()
		if saved:
			self.save_used = True
			self._set_note("saved")
			self.state = self.READY
			return
		self.balls -= 1
		self.save_used = False
		self.state = self.READY if self.balls > 0 else self.OVER
