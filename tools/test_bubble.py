#!/usr/bin/env python3
# Self-test for the bubble shooter rules: bots play many games and the board
# must always stay consistent (valid cells, nothing floating, no lost bubbles).
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugin"))
import bubble_engine as be  # noqa: E402


def check(g):
	for (r, c), color in g.grid.items():
		assert g.valid(r, c), (r, c)
		assert 0 <= color < be.COLORS
	assert not g._floating(), "floating bubbles left on the board"
	if g.state == g.PLAY and g.grid:
		colors = g.present_colors()
		assert g.current in colors and g.next in colors


def landing(g, angle):
	"""Cell where a shot at this angle would stop (same path as aim_points)."""
	x, y = be.SHOOTER
	dx, dy = math.sin(angle), -math.cos(angle)
	step = be.R * 0.4
	for i in range(5000):
		x += dx * step
		y += dy * step
		if x < be.R:
			x = 2 * be.R - x
			dx = abs(dx)
		elif x > be.W - be.R:
			x = 2 * (be.W - be.R) - x
			dx = -abs(dx)
		if y <= be.R or g._touching(x, y):
			return g._snap_cell(x, max(y, be.R))
	return None


def aim_for(g, rnd, smart):
	"""Pick an angle: the best landing spot for a skilled player, or random."""
	if not smart:
		return rnd.uniform(-be.MAX_ANGLE, be.MAX_ANGLE)
	best, best_score = 0.0, -1
	for i in range(-27, 28):
		angle = i * 0.05
		cell = landing(g, angle)
		if cell is None:
			continue
		g.grid[cell] = g.current
		size = len(g._group(cell))
		del g.grid[cell]
		score = size * 10 - cell[0] + rnd.random()
		if score > best_score:
			best, best_score = angle, score
	return best


def play(seed, smart, limit=250):
	rnd = random.Random(seed)
	g = be.BubbleShooter(random.Random(seed))
	g.new_game()
	shots = 0
	while g.state != g.OVER and shots < limit:
		if g.state == g.PLAY and g.shot is None:
			if rnd.random() < 0.1:
				g.swap()
			g.angle = aim_for(g, rnd, smart)
			pts = g.aim_points(10, 40.0)
			for x, y in pts:
				assert be.R - 0.01 <= x <= be.W - be.R + 0.01
			assert g.shoot()
			shots += 1
		before, level = len(g.grid), g.level
		g.update(0.03)
		if g.shot is not None:
			assert be.R - 0.01 <= g.shot[0] <= be.W - be.R + 0.01
		if g.shot is None:
			check(g)
		if g.level == level:
			assert len(g.grid) <= before + be.COLS + 1
	return g.score, g.level, shots


for smart in (False, True):
	res = [play(seed, smart) for seed in range(6 if smart else 40)]
	print("smart" if smart else "random", "avg score %d, max level %d, avg shots %d" % (
		sum(r[0] for r in res) / len(res), max(r[1] for r in res), sum(r[2] for r in res) / len(res)))

# rotation limits and swapping
g = be.BubbleShooter(random.Random(1))
g.new_game()
g.turn = 1
for i in range(100):
	g.update(0.05)
assert abs(g.angle - be.MAX_ANGLE) < 1e-9
g.turn = 0
a, b = g.current, g.next
if a != b:
	assert g.swap() and (g.current, g.next) == (b, a)
print("bubble ok")
