# -*- coding: utf-8 -*-
# E2games - Klondike solitaire screen (Enigma2 front end for solitaire_engine).
from enigma import ePoint, eSize, eTimer, getDesktop

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap

from . import _
from .solitaire_engine import Klondike

# Layout on a 1280x720 screen (scaled by 1.5 for FHD skins)
CW, CH = 100, 140             # card size
COL_X, COL_STEP = 40, 124     # tableau columns
TOP_Y, TAB_Y = 28, 190        # top row / tableau row
BOTTOM = 710
OFF_DOWN, OFF_UP = 12, 34     # vertical step of face-down / face-up cards
SLOTS = 19                    # card widgets per tableau column (6 down + 13 up)
BAR = 4                       # thickness of the cursor frame
SUIT_KEYS = "shdc"
TOP_PILES = ("S", "W", "F0", "F1", "F2", "F3")
TOP_COLS = (0, 1, 3, 4, 5, 6)   # column above which each top pile sits


class E2Solitaire(Screen):
	def __init__(self, session):
		fhd = getDesktop(0).size().width() >= 1920
		self.cardScale = 1.5 if fhd else 1.0
		self.cardDir = resolveFilename(SCOPE_PLUGINS, "Extensions/E2games/images/%s/cards/" % ("fhd" if fhd else "hd"))
		v = self.px
		img = self.cardDir
		parts = ['<screen name="E2Solitaire" position="0,0" size="%d,%d" title="E2games" flags="wfNoBorder" backgroundColor="#0b5a2a">' % (v(1280), v(720))]

		def static(png, x, y):
			parts.append('<ePixmap pixmap="%s%s" position="%d,%d" size="%d,%d" zPosition="1" alphatest="blend" />' % (img, png, v(x), v(y), v(CW), v(CH)))

		def card(name, x, y, z):
			parts.append('<widget name="%s" position="%d,%d" size="%d,%d" zPosition="%d" alphatest="blend" />' % (name, v(x), v(y), v(CW), v(CH), z))

		def label(name, x, y, w, h, size, color, align="left", valign="center"):
			parts.append('<widget name="%s" position="%d,%d" size="%d,%d" font="Regular;%d" halign="%s" valign="%s" foregroundColor="%s" backgroundColor="#0b5a2a" transparent="1" zPosition="3" />' % (
				name, v(x), v(y), v(w), v(h), v(size), align, valign, color))

		self.cardNames = []
		for i, pile in enumerate(TOP_PILES):
			x = COL_X + TOP_COLS[i] * COL_STEP
			static("slot_s.png" if pile == "S" else "slot_f.png" if pile[0] == "F" else "slot.png", x, TOP_Y)
			card("top%d" % i, x, TOP_Y, 2)
			self.cardNames.append("top%d" % i)
		for c in range(7):
			static("slot.png", COL_X + c * COL_STEP, TAB_Y)
			for i in range(SLOTS):
				card("t%d_%d" % (c, i), COL_X + c * COL_STEP, TAB_Y, 2 + i)
				self.cardNames.append("t%d_%d" % (c, i))
		# cursor frame (yellow) and frame around the picked cards (green): four bars each
		self.barNames = []
		for prefix, color, z in (("pick", "#40ff70", 40), ("cur", "#ffd23c", 41)):
			for i in range(4):
				parts.append('<widget name="%s%d" position="0,0" size="%d,%d" backgroundColor="%s" zPosition="%d" />' % (prefix, i, v(BAR), v(BAR), color, z))
				self.barNames.append("%s%d" % (prefix, i))

		label("title", 930, 24, 320, 46, 36, "#ffffff")
		label("game", 930, 70, 320, 34, 26, "#c8f0d0")
		label("movesCaption", 930, 130, 150, 28, 21, "#a0d0b0")
		label("moves", 930, 158, 150, 42, 34, "#ffffff")
		label("timeCaption", 1090, 130, 160, 28, 21, "#a0d0b0")
		label("time", 1090, 158, 160, 42, 34, "#ffffff")
		label("message", 930, 215, 320, 80, 25, "#ffd23c")
		label("help", 930, 310, 330, 400, 19, "#e0f0e4", valign="top")
		parts.append("</screen>")
		self.skin = "\n".join(parts)

		Screen.__init__(self, session)
		self.setTitle("E2games - " + _("Solitaire"))

		for name in self.cardNames:
			self[name] = Pixmap()
		for name in self.barNames:
			self[name] = Label("")
		self["title"] = Label("E2games")
		self["game"] = Label(_("Solitaire"))
		self["movesCaption"] = Label(_("Moves"))
		self["moves"] = Label("0")
		self["timeCaption"] = Label(_("Time"))
		self["time"] = Label("0:00")
		self["message"] = Label("")
		self["help"] = Label("\n".join((
			_("Arrows: move the cursor"),
			_("OK: pick up cards / place them"),
			_("OK twice on a card: send it to the foundation"),
			_("OK on the stock: turn a new card"),
			"",
			_("RED: undo"),
			_("GREEN: card to the foundation"),
			_("YELLOW: new game"),
			_("BLUE: turn a card from the stock"),
			_("EXIT: cancel selection / back to menu"))))

		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions"], {
			"ok": self.keyOk,
			"cancel": self.keyCancel,
			"left": self.keyLeft,
			"right": self.keyRight,
			"up": self.keyUp,
			"down": self.keyDown,
			"red": self.keyUndo,
			"green": self.keyFoundation,
			"yellow": self.keyNewGame,
			"blue": self.keyDraw,
		}, -1)

		self.deal = Klondike()
		self.cardPixmaps = {}
		self.drawnState = {}       # cache of what each widget currently shows
		self.cursorTop = False     # True: cursor in the top row, False: in the tableau
		self.cursorCol = 0         # index into TOP_PILES or tableau column
		self.cursorIndex = 0       # card index inside the tableau column
		self.picked = None         # (pile, index) of the picked cards
		self.noteText = ""
		self.seconds = 0
		self.finishing = False
		self.clockTimer = eTimer()
		self.clockTimer.callback.append(self.clockTick)
		self.finishTimer = eTimer()
		self.finishTimer.callback.append(self.finishTick)
		self.onLayoutFinish.append(self.gameStart)
		self.onClose.append(self.gameStop)

	def px(self, x):
		return int(round(x * self.cardScale))

	# ---- start / stop -------------------------------------------------
	def gameStart(self):
		d = self.cardDir
		for suit in range(4):
			for rank in range(1, 14):
				self.cardPixmaps[(rank, suit)] = LoadPixmap(d + "c%02d%s.png" % (rank, SUIT_KEYS[suit]))
		self.cardPixmaps["back"] = LoadPixmap(d + "back.png")
		self.resetCursor()
		self.redraw()
		self.clockTimer.start(1000, False)

	def gameStop(self):
		self.clockTimer.stop()
		self.finishTimer.stop()

	def clockTick(self):
		if self.execing and not self.deal.won():
			self.seconds += 1
			self.showStatus()

	# ---- cursor ---------------------------------------------------------
	def resetCursor(self):
		self.cursorTop = False
		self.cursorCol = 0
		self.picked = None
		self.clampCursor()

	def cursorPile(self):
		return TOP_PILES[self.cursorCol] if self.cursorTop else "T%d" % self.cursorCol

	def clampCursor(self, toLast=False):
		"""Keep the tableau cursor on a face-up card of its column."""
		if self.cursorTop:
			return
		col = self.deal.tableau[self.cursorCol]
		first = self.deal.first_face_up(self.cursorCol)
		last = max(0, len(col) - 1)
		if toLast or self.picked or self.cursorIndex > last:
			self.cursorIndex = last
		elif self.cursorIndex < first:
			self.cursorIndex = min(first, last)

	def keyLeft(self):
		self.moveCursor(-1)

	def keyRight(self):
		self.moveCursor(1)

	def moveCursor(self, step):
		if self.finishing:
			return
		count = len(TOP_PILES) if self.cursorTop else 7
		self.cursorCol = (self.cursorCol + step) % count
		self.clampCursor(toLast=True)
		self.note("")
		self.redraw()

	def keyUp(self):
		if self.finishing or self.cursorTop:
			return
		if not self.picked and self.cursorIndex > self.deal.first_face_up(self.cursorCol):
			self.cursorIndex -= 1
		else:
			# to the top row pile nearest to this column
			col = self.cursorCol
			self.cursorTop = True
			self.cursorCol = min(range(len(TOP_COLS)), key=lambda i: (abs(TOP_COLS[i] - col), i))
		self.note("")
		self.redraw()

	def keyDown(self):
		if self.finishing:
			return
		if self.cursorTop:
			self.cursorTop = False
			self.cursorCol = TOP_COLS[self.cursorCol]
			self.clampCursor(toLast=True)
		elif not self.picked and self.cursorIndex < len(self.deal.tableau[self.cursorCol]) - 1:
			self.cursorIndex += 1
		self.note("")
		self.redraw()

	# ---- actions --------------------------------------------------------
	def keyOk(self):
		if self.finishing or self.deal.won():
			return
		deal = self.deal
		pile = self.cursorPile()
		self.note("")
		if self.picked is None:
			if pile == "S":
				deal.draw()
			else:
				index = None if self.cursorTop else self.cursorIndex
				if deal.cards_from(pile, index):
					self.picked = (pile, index)
		else:
			src, index = self.picked
			self.picked = None
			if src == pile:
				# second OK on the same pile: send a single card to its foundation
				if len(deal.cards_from(src, index) or ()) == 1:
					deal.to_foundation(src)
			elif pile == "S":
				deal.draw()
			elif not deal.move(src, index, pile):
				self.note(_("Invalid move"))
		self.afterMove()

	def keyCancel(self):
		if self.picked is not None:
			self.picked = None
			self.redraw()
		else:
			self.close()

	def keyUndo(self):
		if self.finishing:
			return
		self.picked = None
		self.note("")
		self.deal.undo()
		self.afterMove()

	def keyFoundation(self):
		if self.finishing:
			return
		self.picked = None
		pile = self.cursorPile()
		if not self.deal.to_foundation(pile):
			self.note(_("Invalid move"))
		else:
			self.note("")
		self.afterMove()

	def keyDraw(self):
		if self.finishing:
			return
		self.picked = None
		self.note("")
		self.deal.draw()
		self.afterMove()

	def keyNewGame(self):
		self.finishTimer.stop()
		self.finishing = False
		self.deal.new_game()
		self.seconds = 0
		self.note("")
		self.resetCursor()
		self.redraw()

	def afterMove(self):
		self.clampCursor()
		if self.deal.can_autofinish():
			self.finishing = True
			self.picked = None
			self.finishTimer.start(90, False)
		self.redraw()

	def finishTick(self):
		try:
			if not self.execing:
				return
			if not self.deal.autofinish_step() or self.deal.won():
				self.finishTimer.stop()
				self.finishing = False
				self.clampCursor()
			self.redraw()
		except Exception:
			import traceback
			traceback.print_exc()
			self.finishTimer.stop()
			self.finishing = False

	def note(self, text):
		self.noteText = text

	# ---- drawing --------------------------------------------------------
	def columnLayout(self, column):
		"""y position of every card in a tableau column (squeezed to fit)."""
		col = self.deal.tableau[column]
		steps = [OFF_UP if up else OFF_DOWN for card, up in col[:-1]]
		total = sum(steps)
		room = BOTTOM - TAB_Y - CH
		k = float(room) / total if total > room else 1.0
		ys, y = [], float(TAB_Y)
		for i in range(len(col)):
			ys.append(y)
			if i < len(steps):
				y += steps[i] * k
		return ys

	def showCard(self, name, key, x=None, y=None):
		"""key: card tuple, "back" or None (hidden)."""
		state = (key, x, y)
		if self.drawnState.get(name) == state:
			return
		old = self.drawnState.get(name, (None, None, None))
		self.drawnState[name] = state
		widget = self[name]
		if key is None:
			widget.hide()
			return
		if x is not None and (old[1], old[2]) != (x, y):
			widget.instance.move(ePoint(x, y))
		if old[0] != key:
			widget.instance.setPixmap(self.cardPixmaps[key])
		if old[0] is None:
			widget.show()

	def showFrame(self, prefix, rect):
		"""Draw a frame from four bars; rect = (x, y, w, h) in screen pixels or None."""
		if self.drawnState.get(prefix, False) == rect:
			return
		self.drawnState[prefix] = rect
		bars = [self["%s%d" % (prefix, i)] for i in range(4)]
		if rect is None:
			for bar in bars:
				bar.hide()
			return
		x, y, w, h = rect
		b = self.px(BAR)
		geometry = ((x - b, y - b, w + 2 * b, b), (x - b, y + h, w + 2 * b, b), (x - b, y, b, h), (x + w, y, b, h))
		for bar, (bx, by, bw, bh) in zip(bars, geometry):
			bar.instance.move(ePoint(bx, by))
			bar.instance.resize(eSize(bw, bh))
			bar.show()

	def pileRect(self, pile, index, layouts):
		v = self.px
		if pile[0] == "T":
			c = int(pile[1])
			ys = layouts[c]
			x = v(COL_X + c * COL_STEP)
			if not ys:
				return (x, v(TAB_Y), v(CW), v(CH))
			if index is None or index >= len(ys):
				index = len(ys) - 1
			top = v(ys[index])
			return (x, top, v(CW), v(ys[-1]) + v(CH) - top)
		i = TOP_PILES.index(pile)
		return (v(COL_X + TOP_COLS[i] * COL_STEP), v(TOP_Y), v(CW), v(CH))

	def redraw(self):
		deal = self.deal
		v = self.px
		tops = [("back" if deal.stock else None), (deal.waste[-1] if deal.waste else None)]
		tops += [(f[-1] if f else None) for f in deal.foundations]
		for i, key in enumerate(tops):
			self.showCard("top%d" % i, key)
		layouts = []
		for c in range(7):
			col = deal.tableau[c]
			ys = self.columnLayout(c)
			layouts.append(ys)
			x = v(COL_X + c * COL_STEP)
			for i in range(SLOTS):
				if i < len(col):
					card, up = col[i]
					self.showCard("t%d_%d" % (c, i), card if up else "back", x, v(ys[i]))
				else:
					self.showCard("t%d_%d" % (c, i), None)
		if self.finishing or deal.won():
			self.showFrame("cur", None)
			self.showFrame("pick", None)
		else:
			self.showFrame("cur", self.pileRect(self.cursorPile(), None if self.cursorTop else self.cursorIndex, layouts))
			self.showFrame("pick", self.pileRect(self.picked[0], self.picked[1], layouts) if self.picked else None)
		self.showStatus()

	def showStatus(self):
		deal = self.deal
		if deal.won():
			message = _("You won!") + "\n" + _("Press YELLOW for a new game")
		elif self.finishing:
			message = _("Finishing...")
		else:
			message = self.noteText
		for name, text in (("moves", str(deal.moves)), ("time", "%d:%02d" % (self.seconds // 60, self.seconds % 60)), ("message", message)):
			if self.drawnState.get(name) != text:
				self.drawnState[name] = text
				self[name].setText(text)
