#!/usr/bin/env python3
# Self-test for the solitaire rules: random legal play, undo and auto-finish.
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugin"))
from solitaire_engine import Klondike, is_red  # noqa: E402


def all_cards(g):
	cards = list(g.stock) + list(g.waste)
	for f in g.foundations:
		cards += f
	for col in g.tableau:
		cards += [c for c, up in col]
	return cards


def check(g):
	cards = all_cards(g)
	assert len(cards) == 52 and len(set(cards)) == 52
	for f in g.foundations:
		assert [c[0] for c in f] == list(range(1, len(f) + 1)) and len(set(c[1] for c in f)) <= 1
	for col in g.tableau:
		ups = [up for c, up in col]
		assert ups == sorted(ups), "face-down card above a face-up one"
		if col:
			assert col[-1][1]
		run = [c for c, up in col if up]
		for a, b in zip(run[:-1], run[1:]):
			assert a[0] == b[0] + 1 and is_red(a) != is_red(b)


wins = finished = 0
for seed in range(300):
	rnd = random.Random(seed)
	g = Klondike(random.Random(seed))
	check(g)
	for step in range(600):
		if g.can_autofinish():
			n = 0
			while g.autofinish_step():
				n += 1
				assert n < 2000
			assert g.won()
			finished += 1
			break
		piles = ["W"] + ["T%d" % i for i in range(7)] + ["F%d" % i for i in range(4)]
		options = []
		for src in piles:
			idxs = [None]
			if src[0] == "T":
				c = int(src[1])
				idxs = list(range(g.first_face_up(c), len(g.tableau[c])))
			for idx in idxs:
				cards = g.cards_from(src, idx)
				if not cards:
					continue
				for dst in piles[1:]:
					if dst != src and g.can_place(cards, dst) and not (src[0] == "F" and dst[0] == "F"):
						options.append((src, idx, dst))
		good = [o for o in options if o[2][0] == "F" and o[0][0] != "F"]
		before = g._snapshot()
		acted = True
		if good:
			assert g.move(*good[0])
		elif options and rnd.random() < 0.6:
			assert g.move(*rnd.choice(options))
		else:
			acted = g.draw()
		check(g)
		if acted and rnd.random() < 0.05:
			assert g.undo() and g._snapshot() == before
		assert not g.move("T0", None, "T0")
	wins += g.won()
print("solitaire ok: %d of 300 random games reached auto-finish, %d won" % (finished, wins))
