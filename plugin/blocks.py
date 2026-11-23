# -*- coding: utf-8 -*-
# E2games - falling blocks screen (Enigma2 front end for blocks_engine).
from time import time
try:
	from time import monotonic
except ImportError:
	monotonic = time

from enigma import eActionMap, ePoint, eTimer, getDesktop

from Components.ActionMap import HelpableActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Screens.HelpMenu import HelpableScreen
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap

from . import _
from . import blocks_engine as be

CELL = 32
BORDER = 8                    # see tools/make_blocks.py
WELL_X, WELL_Y = 480, 40      # well position on a 1280x720 screen
HOLD_X, HOLD_Y = 300, 70
NEXT_X, NEXT_Y = 830, 70
BOX_W, HOLD_H, NEXT_H = 150, 110, 330
NEXT_SLOT = 110
TICK_MS = 30
KEY_TIMEOUT = 0.6             # treat a key as released if no repeat arrives
MOVE_DELAY = 0.3              # LEFT / RIGHT: a held key starts repeating after this
MOVE_REPEAT = 0.1             # and then moves at most one cell per this many seconds
SCORE_FILE = "/etc/enigma2/e2games_blocks.score"

# Linux input key codes
KEY_LEFT, KEY_RIGHT, KEY_DOWN, KEY_UP = 105, 106, 108, 103
KEYS_DROP = (352, 28)         # OK, ENTER
KEY_RED, KEY_GREEN = 398, 399


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


def previewCells(piece):
	"""Cells of a piece in spawn orientation, centred in a box (x, y offsets)."""
	cells = be.cells_of(piece, 0)
	rows = [r for r, c in cells]
	cols = [c for r, c in cells]
	w = (max(cols) - min(cols) + 1) * CELL
	h = (max(rows) - min(rows) + 1) * CELL
	ox = (BOX_W - w) / 2.0 - min(cols) * CELL
	oy = (NEXT_SLOT - h) / 2.0 - min(rows) * CELL
	return [(ox + c * CELL, oy + r * CELL) for r, c in cells]


class E2Blocks(Screen, HelpableScreen):
	def __init__(self, session):
		fhd = getDesktop(0).size().width() >= 1920
		self.wellScale = 1.5 if fhd else 1.0
		self.imgDir = resolveFilename(SCOPE_PLUGINS, "Extensions/E2games/images/%s/blocks/" % ("fhd" if fhd else "hd"))
		v = self.px
		img = self.imgDir
		parts = ['<screen name="E2Blocks" position="0,0" size="%d,%d" title="E2games" flags="wfNoBorder" backgroundColor="#000000">' % (v(1280), v(720))]
		for png, x, y, w, h in (("well.png", WELL_X, WELL_Y, be.COLS * CELL, be.VISIBLE * CELL),
				("hold.png", HOLD_X, HOLD_Y, BOX_W, HOLD_H), ("next.png", NEXT_X, NEXT_Y, BOX_W, NEXT_H)):
			parts.append('<ePixmap pixmap="%s%s" position="%d,%d" size="%d,%d" zPosition="1" />' % (
				img, png, v(x - BORDER), v(y - BORDER), v(w + 2 * BORDER), v(h + 2 * BORDER)))

		def cell(name, x, y):
			parts.append('<widget name="%s" position="%d,%d" size="%d,%d" zPosition="2" alphatest="blend" />' % (
				name, v(x), v(y), v(CELL), v(CELL)))

		def label(name, x, y, w, h, size, color, align="left", valign="center", extra=""):
			parts.append('<widget name="%s" position="%d,%d" size="%d,%d" font="Regular;%d" halign="%s" valign="%s" foregroundColor="%s" backgroundColor="#000000" transparent="1" zPosition="5" %s/>' % (
				name, v(x), v(y), v(w), v(h), v(size), align, valign, color, extra))

		self.cellNames = []
		for r in range(be.VISIBLE):
			for c in range(be.COLS):
				cell("w%d_%d" % (r, c), WELL_X + c * CELL, WELL_Y + r * CELL)
				self.cellNames.append("w%d_%d" % (r, c))
		for i in range(4):
			cell("h%d" % i, HOLD_X, HOLD_Y)
			self.cellNames.append("h%d" % i)
		for j in range(3):
			for i in range(4):
				cell("q%d_%d" % (j, i), NEXT_X, NEXT_Y)
				self.cellNames.append("q%d_%d" % (j, i))

		label("title", 40, 30, 250, 50, 38, "#ffffff")
		label("game", 40, 80, 250, 36, 26, "#96d7ff")
		label("scoreCaption", 40, 160, 250, 30, 22, "#8088b0")
		label("score", 40, 190, 250, 56, 44, "#ffd23c")
		label("highCaption", 40, 270, 250, 30, 22, "#8088b0")
		label("high", 40, 300, 250, 44, 34, "#ffffff")
		label("levelCaption", 40, 370, 120, 30, 22, "#8088b0")
		label("level", 40, 400, 120, 44, 34, "#ffffff")
		label("linesCaption", 160, 370, 130, 30, 22, "#8088b0")
		label("lines", 160, 400, 130, 44, 34, "#ffffff")
		label("holdCaption", HOLD_X, HOLD_Y - 40, BOX_W, 28, 21, "#8088b0", "center")
		label("nextCaption", NEXT_X, NEXT_Y - 40, BOX_W, 28, 21, "#8088b0", "center")
		label("helpCaption", 1010, 30, 250, 36, 26, "#96d7ff")
		label("help", 1010, 80, 250, 620, 18, "#c8cce0", valign="top")
		label("message", WELL_X + 10, WELL_Y + 240, be.COLS * CELL - 20, 160, 28, "#ffffff", "center", "center", 'borderWidth="2" borderColor="#000000" ')
		parts.append("</screen>")
		self.skin = "\n".join(parts)

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.setTitle("E2games - " + _("Blocks"))

		for name in self.cellNames:
			self[name] = Pixmap()
		self["title"] = Label("E2games")
		self["game"] = Label(_("Blocks"))
		self["scoreCaption"] = Label(_("Score"))
		self["score"] = Label("0")
		self["highCaption"] = Label(_("High score"))
		self["high"] = Label("0")
		self["levelCaption"] = Label(_("Level"))
		self["level"] = Label("1")
		self["linesCaption"] = Label(_("Lines"))
		self["lines"] = Label("0")
		self["holdCaption"] = Label(_("Hold"))
		self["nextCaption"] = Label(_("Next"))
		self["helpCaption"] = Label(_("Controls"))
		self["help"] = Label("\n".join((
			_("LEFT / RIGHT: move"),
			_("UP: turn clockwise"),
			_("RED: turn the other way"),
			_("DOWN: drop faster (hold)"),
			_("OK: drop at once"),
			_("GREEN: hold the piece for later"),
			_("BLUE: pause"),
			_("YELLOW: new game"),
			_("EXIT: back to menu"),
			_("HELP: remote control help"),
			"",
			_("Fill whole rows to clear them. The more rows at once, the more points. Every ten rows the blocks fall faster."))))
		self["message"] = Label("")

		self["actions"] = HelpableActionMap(self, "OkCancelActions", {
			"ok": (self.keyHelpOnly, _("Drop at once")),
			"cancel": (self.keyExit, _("Back to menu")),
		}, -1)
		self["directionActions"] = HelpableActionMap(self, "DirectionActions", {
			"left": (self.keyHelpOnly, _("Move left")),
			"right": (self.keyHelpOnly, _("Move right")),
			"up": (self.keyHelpOnly, _("Turn clockwise")),
			"down": (self.keyHelpOnly, _("Drop faster (hold)")),
		}, -1)
		self["colorActions"] = HelpableActionMap(self, "ColorActions", {
			"red": (self.keyHelpOnly, _("Turn the other way")),
			"green": (self.keyHelpOnly, _("Hold the piece for later")),
			"yellow": (self.keyNewGame, _("New game")),
			"blue": (self.keyPause, _("Pause")),
		}, -1)

		self.game = be.Blocks(highscore=readNumber(SCORE_FILE))
		self.savedHigh = self.game.highscore
		self.pixmaps = {}
		self.drawn = {}
		self.keysHeld = {}         # key code -> [time of last event, time pressed, time of last move]
		self.keysBound = False
		self.lastTick = monotonic()
		self.gameTimer = eTimer()
		self.gameTimer.callback.append(self.tick)
		self.onLayoutFinish.append(self.gameStart)
		self.onClose.append(self.gameStop)

	def keyHelpOnly(self):
		# keys read directly from the remote (see rawKey) are listed in the
		# HELP screen through this placeholder; the game itself handles them
		pass

	def px(self, x):
		return int(round(x * self.wellScale))

	# ---- start / stop -------------------------------------------------
	def gameStart(self):
		for piece in be.PIECES:
			self.pixmaps[piece] = LoadPixmap(self.imgDir + "cell_%s.png" % piece)
		self.pixmaps["ghost"] = LoadPixmap(self.imgDir + "ghost.png")
		self.pixmaps["flash"] = LoadPixmap(self.imgDir + "flash.png")
		for name in self.cellNames:
			self[name].hide()
		self.game.new_game()
		self.draw()
		eActionMap.getInstance().bindAction("", -0x7FFFFFFF, self.rawKey)
		self.keysBound = True
		self.lastTick = monotonic()
		self.gameTimer.start(TICK_MS, False)

	def gameStop(self):
		self.gameTimer.stop()
		if self.keysBound:
			eActionMap.getInstance().unbindAction("", self.rawKey)
			self.keysBound = False
		self.storeHighscore()

	def storeHighscore(self):
		if self.game.highscore > self.savedHigh:
			self.savedHigh = self.game.highscore
			writeNumber(SCORE_FILE, self.savedHigh)

	def keyExit(self):
		self.close()

	def keyNewGame(self):
		self.storeHighscore()
		self.game.new_game()

	def keyPause(self):
		self.game.toggle_pause()

	# ---- keys -----------------------------------------------------------
	def rawKey(self, key, flag):
		# flag: 0 = make, 1 = break, 2 = repeat, 3 = long
		try:
			if not self.execing:
				return 0
			game = self.game
			now = monotonic()
			if key in (KEY_LEFT, KEY_RIGHT, KEY_DOWN):
				# A press moves exactly one cell. Only the remote's own repeat
				# messages (key held down) move further, one cell at a time.
				if flag == 1:
					self.keysHeld.pop(key, None)
				elif key in self.keysHeld:
					held = self.keysHeld[key]
					held[0] = now
					if key != KEY_DOWN and now - held[1] >= MOVE_DELAY and now - held[2] >= MOVE_REPEAT:
						held[2] = now
						game.move(-1 if key == KEY_LEFT else 1)
				elif flag == 0:
					self.keysHeld[key] = [now, now, now]
					if key != KEY_DOWN:
						game.move(-1 if key == KEY_LEFT else 1)
				game.set_soft_drop(KEY_DOWN in self.keysHeld)
				return 1
			if key in (KEY_UP, KEY_RED, KEY_GREEN) or key in KEYS_DROP:
				if flag == 0:
					if key == KEY_UP:
						game.rotate(1)
					elif key == KEY_RED:
						game.rotate(-1)
					elif key == KEY_GREEN:
						game.hold()
					elif game.state == game.OVER:
						self.keyNewGame()
					else:
						game.hard_drop()
				return 1
			return 0
		except Exception as err:
			print("[E2games] key error: %s" % err)
			return 0

	# ---- main loop ------------------------------------------------------
	def tick(self):
		try:
			self.runFrame()
		except Exception:
			# never let a game error take the whole GUI down: stop and leave
			import traceback
			traceback.print_exc()
			self.gameStop()
			self.close()

	def runFrame(self):
		now = monotonic()
		dt = min(now - self.lastTick, 0.1)
		self.lastTick = now
		if not self.execing:
			return
		game = self.game
		for key in list(self.keysHeld):
			if now - self.keysHeld[key][0] > KEY_TIMEOUT:
				del self.keysHeld[key]
		game.set_soft_drop(KEY_DOWN in self.keysHeld)
		before = game.state
		game.update(dt)
		if game.state == game.OVER and before != game.OVER:
			self.storeHighscore()
		self.draw()

	# ---- drawing --------------------------------------------------------
	def showCell(self, name, key, x=None, y=None):
		state = (key, x, y)
		old = self.drawn.get(name)
		if old == state:
			return
		self.drawn[name] = state
		widget = self[name]
		if key is None:
			widget.hide()
			return
		if x is not None and (old is None or old[1:] != (x, y)):
			widget.instance.move(ePoint(self.px(x), self.px(y)))
		if old is None or old[0] != key:
			widget.instance.setPixmap(self.pixmaps[key])
		if old is None or old[0] is None:
			widget.show()

	def setText(self, name, text):
		if self.drawn.get(name) != text:
			self.drawn[name] = text
			self[name].setText(text)

	def draw(self):
		game = self.game
		paused = game.state == game.PAUSE
		rows = game.display()
		for r in range(be.VISIBLE):
			for c in range(be.COLS):
				self.showCell("w%d_%d" % (r, c), None if paused else rows[r][c])
		cells = previewCells(game.held) if game.held and not paused else []
		for i in range(4):
			if i < len(cells):
				self.showCell("h%d" % i, game.held, HOLD_X + cells[i][0], HOLD_Y + cells[i][1])
			else:
				self.showCell("h%d" % i, None)
		for j in range(3):
			piece = game.queue[j] if j < len(game.queue) and game.state != game.OVER and not paused else None
			cells = previewCells(piece) if piece else []
			for i in range(4):
				if i < len(cells):
					self.showCell("q%d_%d" % (j, i), piece, NEXT_X + cells[i][0], NEXT_Y + j * NEXT_SLOT + cells[i][1])
				else:
					self.showCell("q%d_%d" % (j, i), None)
		self.setText("score", str(game.score))
		self.setText("high", str(game.highscore))
		self.setText("level", str(game.level))
		self.setText("lines", str(game.lines))
		if game.state == game.OVER:
			msg = _("GAME OVER")
			if game.new_highscore:
				msg += "\n" + _("New high score!")
			msg += "\n" + _("Press OK for a new game")
		elif paused:
			msg = _("Paused") + "\n" + _("Press BLUE to continue")
		else:
			msg = ""
		self.setText("message", msg)
