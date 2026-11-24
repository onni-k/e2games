# -*- coding: utf-8 -*-
# E2games - 2048 screen (Enigma2 front end for g2048_engine).
import json
import os
from time import time
try:
	from time import monotonic
except ImportError:
	monotonic = time

from enigma import ePoint, eTimer, getDesktop

from Components.ActionMap import HelpableActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Screens.HelpMenu import HelpableScreen
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap

from . import _
from . import g2048_engine as ge

BOARD_X = (1280 - ge.BOARD) // 2
BOARD_Y = (720 - ge.BOARD) // 2
ANIM_TIME = 0.1               # seconds for the tiles to slide
ANIM_TICK_MS = 20
MAX_POWER = 17                # see tools/make_2048.py
SAVE_FILE = "/etc/enigma2/e2games_2048.json"
BEST_FILE = "/etc/enigma2/e2games_2048.best"


def readNumber(path, default=0):
	try:
		with open(path) as f:
			return int(f.read().strip())
	except Exception:
		return default


def writeNumber(path, value):
	try:
		with open(path, "w") as f:
			f.write("%d\n" % value)
	except Exception:
		pass


class E2Game2048(Screen, HelpableScreen):
	def __init__(self, session):
		fhd = getDesktop(0).size().width() >= 1920
		self.boardScale = 1.5 if fhd else 1.0
		self.imgDir = resolveFilename(SCOPE_PLUGINS, "Extensions/E2games/images/%s/2048/" % ("fhd" if fhd else "hd"))
		v = self.px
		img = self.imgDir
		parts = ['<screen name="E2Game2048" position="0,0" size="%d,%d" title="E2games" flags="wfNoBorder" backgroundColor="#14120f">' % (v(1280), v(720))]
		parts.append('<ePixmap pixmap="%sboard.png" position="%d,%d" size="%d,%d" zPosition="1" alphatest="blend" />' % (
			img, v(BOARD_X), v(BOARD_Y), v(ge.BOARD), v(ge.BOARD)))
		for i in range(ge.CELLS):
			x, y = ge.cell_origin(i)
			parts.append('<widget name="t%d" position="%d,%d" size="%d,%d" zPosition="2" alphatest="blend" />' % (
				i, v(BOARD_X + x), v(BOARD_Y + y), v(ge.TILE), v(ge.TILE)))
			parts.append('<widget name="m%d" position="%d,%d" size="%d,%d" zPosition="3" alphatest="blend" />' % (
				i, v(BOARD_X + x), v(BOARD_Y + y), v(ge.TILE), v(ge.TILE)))

		def label(name, x, y, w, h, size, color, align="left", valign="center", extra=""):
			parts.append('<widget name="%s" position="%d,%d" size="%d,%d" font="Regular;%d" halign="%s" valign="%s" foregroundColor="%s" backgroundColor="#14120f" transparent="1" zPosition="5" %s/>' % (
				name, v(x), v(y), v(w), v(h), v(size), align, valign, color, extra))

		label("title", 40, 30, 300, 50, 38, "#ffffff")
		label("game", 40, 80, 300, 36, 26, "#f2b179")
		label("scoreCaption", 40, 160, 300, 30, 22, "#a09080")
		label("score", 40, 190, 300, 56, 46, "#ffd23c")
		label("bestCaption", 40, 270, 300, 30, 22, "#a09080")
		label("best", 40, 300, 300, 44, 34, "#ffffff")
		label("movesCaption", 40, 370, 300, 30, 22, "#a09080")
		label("moves", 40, 400, 300, 44, 34, "#ffffff")
		label("helpCaption", 950, 30, 300, 36, 26, "#f2b179")
		label("help", 950, 80, 300, 600, 19, "#d8d0c8", valign="top")
		# message on a dark see-through panel over the board (alpha 0x40 = mostly opaque)
		parts.append('<widget name="message" position="%d,%d" size="%d,%d" font="Regular;%d" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#40000000" transparent="0" zPosition="6" />' % (
			v(BOARD_X + 20), v(BOARD_Y + 190), v(ge.BOARD - 40), v(170), v(32)))
		parts.append("</screen>")
		self.skin = "\n".join(parts)

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.setTitle("E2games - 2048")

		for i in range(ge.CELLS):
			self["t%d" % i] = Pixmap()
			self["m%d" % i] = Pixmap()
		self["title"] = Label("E2games")
		self["game"] = Label("2048")
		self["scoreCaption"] = Label(_("Score"))
		self["score"] = Label("0")
		self["bestCaption"] = Label(_("Best score"))
		self["best"] = Label("0")
		self["movesCaption"] = Label(_("Moves"))
		self["moves"] = Label("0")
		self["helpCaption"] = Label(_("Controls"))
		self["help"] = Label("\n".join((
			_("Arrows: slide the tiles"),
			_("RED: undo the last move"),
			_("YELLOW: new game"),
			_("EXIT: save and back to menu"),
			_("HELP: remote control help"),
			"",
			_("Tiles with the same number join into one when they touch. Make a tile with 2048!"),
			"",
			_("An unfinished game is saved and continues next time."))))
		self["message"] = Label("")

		self["actions"] = HelpableActionMap(self, "OkCancelActions", {
			"ok": (self.keyOk, _("Continue / new game")),
			"cancel": (self.keyExit, _("Save and back to menu")),
		}, -1)
		self["directionActions"] = HelpableActionMap(self, "DirectionActions", {
			"left": (self.keyLeft, _("Slide left")),
			"right": (self.keyRight, _("Slide right")),
			"up": (self.keyUp, _("Slide up")),
			"down": (self.keyDown, _("Slide down")),
		}, -1)
		self["colorActions"] = HelpableActionMap(self, "ColorActions", {
			"red": (self.keyUndo, _("Undo the last move")),
			"yellow": (self.keyNewGame, _("New game")),
		}, -1)

		self.tiles = ge.Game2048(best=readNumber(BEST_FILE))
		self.savedBest = self.tiles.best
		self.pixmaps = {}
		self.drawn = {}
		self.slides = []           # running animation: (sprite name, x0, y0, x1, y1)
		self.animStart = 0.0
		self.animTimer = eTimer()
		self.animTimer.callback.append(self.animTick)
		self.onLayoutFinish.append(self.gameStart)
		self.onClose.append(self.gameStop)

	def px(self, x):
		return int(round(x * self.boardScale))

	# ---- start / stop -------------------------------------------------
	def gameStart(self):
		for p in range(1, MAX_POWER + 1):
			self.pixmaps[2 ** p] = LoadPixmap(self.imgDir + "t%d.png" % 2 ** p)
		for i in range(ge.CELLS):
			self["t%d" % i].hide()
			self["m%d" % i].hide()
		self["message"].hide()
		self.drawn["message"] = ""
		if not self.loadGame():
			self.tiles.new_game()
		self.draw()

	def gameStop(self):
		self.animTimer.stop()
		self.saveGame()
		self.storeBest()

	def loadGame(self):
		try:
			with open(SAVE_FILE) as f:
				self.tiles.from_dict(json.load(f))
			return not self.tiles.over() and any(self.tiles.board)
		except Exception:
			return False

	def saveGame(self):
		try:
			if self.tiles.over():
				if os.path.exists(SAVE_FILE):
					os.remove(SAVE_FILE)
			else:
				with open(SAVE_FILE, "w") as f:
					json.dump(self.tiles.to_dict(), f)
		except Exception as err:
			print("[E2games] 2048 save error: %s" % err)

	def storeBest(self):
		if self.tiles.best > self.savedBest:
			self.savedBest = self.tiles.best
			writeNumber(BEST_FILE, self.savedBest)

	# ---- keys -----------------------------------------------------------
	def keyLeft(self):
		self.slide("left")

	def keyRight(self):
		self.slide("right")

	def keyUp(self):
		self.slide("up")

	def keyDown(self):
		self.slide("down")

	def keyOk(self):
		if self.tiles.over():
			self.keyNewGame()
		elif self.tiles.continue_after_goal():
			self.draw()

	def keyUndo(self):
		self.finishAnimation()
		if self.tiles.undo():
			self.draw()

	def keyNewGame(self):
		self.finishAnimation()
		self.storeBest()
		self.tiles.new_game()
		self.draw()

	def keyExit(self):
		self.close()

	def slide(self, direction):
		self.finishAnimation()
		result = self.tiles.move(direction)
		if result is None:
			return
		moves, merged = result
		if self.tiles.over():
			self.storeBest()
		# show the tiles sliding from their old places to the new ones
		for i in range(ge.CELLS):
			self.showTile("t%d" % i, None)
		self.slides = []
		for j, (src, dst, value) in enumerate(moves):
			x0, y0 = ge.cell_origin(src)
			x1, y1 = ge.cell_origin(dst)
			name = "m%d" % j
			self.showTile(name, value, x0, y0)
			self.slides.append((name, x0, y0, x1, y1))
		self.animStart = monotonic()
		self.animTimer.start(ANIM_TICK_MS, False)

	# ---- animation ------------------------------------------------------
	def animTick(self):
		try:
			t = (monotonic() - self.animStart) / ANIM_TIME
			if t >= 1.0:
				self.finishAnimation()
				return
			for name, x0, y0, x1, y1 in self.slides:
				self.showTile(name, self.drawn[name][0], x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
		except Exception:
			import traceback
			traceback.print_exc()
			self.finishAnimation()

	def finishAnimation(self):
		self.animTimer.stop()
		if self.slides:
			self.slides = []
			for j in range(ge.CELLS):
				self.showTile("m%d" % j, None)
		self.draw()

	# ---- drawing --------------------------------------------------------
	def showTile(self, name, value, x=None, y=None):
		pos = None if x is None else (self.px(BOARD_X + x), self.px(BOARD_Y + y))
		state = (value, pos)
		old = self.drawn.get(name)
		if old == state:
			return
		self.drawn[name] = state
		widget = self[name]
		if value is None:
			widget.hide()
			return
		if pos is not None and (old is None or old[1] != pos):
			widget.instance.move(ePoint(pos[0], pos[1]))
		if old is None or old[0] != value:
			widget.instance.setPixmap(self.pixmaps[min(value, 2 ** MAX_POWER)])
		if old is None or old[0] is None:
			widget.show()

	def setText(self, name, text):
		if self.drawn.get(name) != text:
			self.drawn[name] = text
			self[name].setText(text)

	def draw(self):
		tiles = self.tiles
		if not self.slides:
			for i in range(ge.CELLS):
				self.showTile("t%d" % i, tiles.board[i] or None)
		self.setText("score", str(tiles.score))
		self.setText("best", str(tiles.best))
		self.setText("moves", str(tiles.moves))
		if tiles.waiting_at_goal():
			msg = _("You made 2048!") + "\n" + _("Press OK to keep playing")
		elif tiles.over():
			msg = _("No more moves") + "\n" + _("Press OK for a new game")
		else:
			msg = ""
		if self.drawn.get("message") != msg:
			self.drawn["message"] = msg
			self["message"].setText(msg)
			if msg:
				self["message"].show()
			else:
				self["message"].hide()
