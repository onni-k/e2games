# -*- coding: utf-8 -*-
# E2games - Klondike solitaire rules.
# Pure Python, no Enigma2 imports, so it can be tested on any machine.
#
# A card is (rank, suit): rank 1 (ace) .. 13 (king), suit 0 spades, 1 hearts,
# 2 diamonds, 3 clubs.  Piles are named "S" (stock), "W" (waste),
# "F0".."F3" (foundations) and "T0".."T6" (tableau columns).

import random

RED_SUITS = (1, 2)
UNDO_LIMIT = 300


def is_red(card):
	return card[1] in RED_SUITS


class Klondike(object):
	def __init__(self, rng=None):
		self.rng = rng or random.Random()
		self.stock = []
		self.waste = []
		self.foundations = [[], [], [], []]
		self.tableau = [[] for i in range(7)]   # lists of [card, face_up]
		self.moves = 0
		self.history = []
		self.new_game()

	# ---- state ----------------------------------------------------------
	def new_game(self):
		if self.moves:
			self._remember()            # a new game can be undone as well
		deck = [(r, s) for s in range(4) for r in range(1, 14)]
		self.rng.shuffle(deck)
		self.tableau = []
		for i in range(7):
			column = [[deck.pop(), False] for j in range(i + 1)]
			column[-1][1] = True
			self.tableau.append(column)
		self.stock = deck
		self.waste = []
		self.foundations = [[], [], [], []]
		self.moves = 0

	def _snapshot(self):
		return (list(self.stock), list(self.waste), [list(f) for f in self.foundations],
			[[list(c) for c in col] for col in self.tableau], self.moves)

	def _remember(self):
		self.history.append(self._snapshot())
		if len(self.history) > UNDO_LIMIT:
			del self.history[0]

	def undo(self):
		if not self.history:
			return False
		self.stock, self.waste, self.foundations, self.tableau, self.moves = self.history.pop()
		return True

	def won(self):
		return sum(len(f) for f in self.foundations) == 52

	def first_face_up(self, column):
		col = self.tableau[column]
		for i, (card, up) in enumerate(col):
			if up:
				return i
		return len(col)

	# ---- moves ----------------------------------------------------------
	def draw(self):
		"""Turn a card from the stock, or recycle the waste when it is empty."""
		if not self.stock and not self.waste:
			return False
		self._remember()
		if self.stock:
			self.waste.append(self.stock.pop())
		else:
			self.stock = self.waste[::-1]
			self.waste = []
		self.moves += 1
		return True

	def cards_from(self, src, index=None):
		"""Cards that would be picked up from a pile (None if not possible)."""
		if src == "W":
			return [self.waste[-1]] if self.waste else None
		if src[0] == "F":
			pile = self.foundations[int(src[1])]
			return [pile[-1]] if pile else None
		if src[0] == "T":
			col = self.tableau[int(src[1])]
			if not col:
				return None
			if index is None:
				index = len(col) - 1
			if not (0 <= index < len(col)) or not col[index][1]:
				return None
			return [c for c, up in col[index:]]
		return None

	def can_place(self, cards, dst):
		first = cards[0]
		if dst[0] == "F":
			if len(cards) != 1:
				return False
			pile = self.foundations[int(dst[1])]
			if not pile:
				return first[0] == 1
			return pile[-1][1] == first[1] and pile[-1][0] + 1 == first[0]
		if dst[0] == "T":
			col = self.tableau[int(dst[1])]
			if not col:
				return first[0] == 13
			top, up = col[-1]
			return up and is_red(top) != is_red(first) and top[0] == first[0] + 1
		return False

	def move(self, src, index, dst, remember=True):
		cards = self.cards_from(src, index)
		if not cards or src == dst or not self.can_place(cards, dst):
			return False
		if remember:
			self._remember()
		if src == "W":
			self.waste.pop()
		elif src[0] == "F":
			self.foundations[int(src[1])].pop()
		else:
			col = self.tableau[int(src[1])]
			del col[len(col) - len(cards):]
			if col:
				col[-1][1] = True       # turn the exposed card
		if dst[0] == "F":
			self.foundations[int(dst[1])].append(cards[0])
		else:
			self.tableau[int(dst[1])].extend([c, True] for c in cards)
		self.moves += 1
		return True

	def to_foundation(self, src, remember=True):
		"""Move the top card of a waste/tableau pile to a fitting foundation."""
		if src[0] not in "WT":
			return False
		cards = self.cards_from(src)
		if not cards:
			return False
		for i in range(4):
			if self.can_place(cards[-1:], "F%d" % i) and self.move(src, None, "F%d" % i, remember):
				return True
		return False

	# ---- automatic finish -------------------------------------------------
	def can_autofinish(self):
		if self.won():
			return False
		return all(up for col in self.tableau for card, up in col)

	def autofinish_step(self):
		for src in ["T%d" % i for i in range(7)] + ["W"]:
			if self.to_foundation(src, remember=False):
				return True
		if self.stock or self.waste:
			if self.stock:
				self.waste.append(self.stock.pop())
			else:
				self.stock = self.waste[::-1]
				self.waste = []
			return True
		return False
