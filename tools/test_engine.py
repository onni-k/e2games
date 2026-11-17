#!/usr/bin/env python3
# Self-test for the pinball physics: a simple bot plays every table and the
# ball must stay inside the cabinet, never get stuck, and hit each target type.
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugin"))
import pinball_engine as pe  # noqa: E402


def play(table, seed, skill, limit=900.0):
	random.seed(seed)
	g = pe.Pinball(table=table)
	g.new_game()
	t, dt = 0.0, 0.033
	hold, cool = [0.0, 0.0], [0.0, 0.0]
	stats = {"standups": 0, "drops": 0, "lanes": 0, "saucer": 0, "bonus": 0}
	last = (list(g.standup_lit), list(g.drop_down), list(g.lane_lit))
	still = 0.0
	while g.state != g.OVER and t < limit:
		if g.state == g.READY:
			g.plunger_press()
			g.update(random.uniform(0.1, 1.0))
			g.plunger_release()
		for i, f in enumerate(g.flippers):
			hold[i] -= dt
			cool[i] -= dt
			tipx = f.px + f.sign * 40
			if g.state == g.PLAY and hold[i] <= 0 and cool[i] <= 0 and abs(g.bx - tipx) < 28 and 585 < g.by < 625 and g.vy > -50:
				if random.random() < skill:
					hold[i] = 0.25
				cool[i] = 0.5
			g.set_flipper(i, hold[i] > 0)
		held_before = g.held
		note_before = g.note
		g.update(dt)
		t += dt
		if g.held >= 0 and held_before < 0:
			stats["saucer"] += 1
		if g.note == "bonus" and note_before != "bonus":
			stats["bonus"] += 1
		stats["standups"] += sum(1 for a, b in zip(last[0], g.standup_lit) if b and not a)
		stats["drops"] += sum(1 for a, b in zip(last[1], g.drop_down) if b and not a)
		stats["lanes"] += sum(1 for a, b in zip(last[2], g.lane_lit) if b and not a)
		last = (list(g.standup_lit), list(g.drop_down), list(g.lane_lit))
		if g.state == g.PLAY:
			assert g.bx == g.bx and g.by == g.by
			if g.by < 690:
				assert pe.PLAY_L - 1 <= g.bx - pe.R + 1 and g.bx + pe.R - 1 <= pe.LANE_R + 1, (table, g.bx, g.by)
				if g.by < pe.ARC_CY:
					assert math.hypot(g.bx - pe.ARC_CX, g.by - pe.ARC_CY) <= pe.ARC_R - pe.R + 2, (table, g.bx, g.by)
			# a ball must not sit in one place for long (saucers hold only 1 s)
			if math.hypot(g.vx, g.vy) < 5 and g.held < 0 and not any(f.pressed for f in g.flippers):
				still += dt
				assert still < 6.0, ("stuck", table, round(g.bx), round(g.by))
			else:
				still = 0.0
	return g.score, round(t), g.mult, stats


for table, spec in enumerate(pe.TABLES):
	total = {"standups": 0, "drops": 0, "lanes": 0, "saucer": 0, "bonus": 0}
	results = []
	for seed in range(8):
		score, secs, mult, stats = play(table, seed, 0.9)
		results.append((score, secs))
		for k in total:
			total[k] += stats[k]
	print("table %d %-12s" % (table, spec["name"]), "games(score,s):", results)
	print("   events:", total)
	if spec["standups"]:
		assert total["standups"] > 0
	if spec["drops"]:
		assert total["drops"] > 0
	if spec["lanes"]:
		assert total["lanes"] > 0
	if spec["saucers"]:
		assert total["saucer"] > 0
print("pinball ok")
