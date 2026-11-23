# -*- coding: utf-8 -*-
# E2games - bubble shooter screen (Enigma2 front end for bubble_engine).
from time import time
try:
	from time import monotonic
except ImportError:
	monotonic = time

from enigma import eActionMap, ePoint, eTimer, getDesktop

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap

from . import _
from . import bubble_engine as be

FIELD_X, FIELD_Y = 464, 20    # field position on a 1280x720 screen
BORDER = 8                    # see tools/make_bubbles.py
ARROW_SIZE = 140
ARROW_STEP = 0.05
ARROW_FRAMES = int(round(2 * be.MAX_ANGLE / ARROW_STEP)) + 1
DOTS = 10
DOT_SPACING = 40.0
TICK_MS = 30
KEY_TIMEOUT = 0.6             # stop turning if no repeat arrives (lost "break")
TAP_TURN = 0.025              # a single short press turns this many times the speed
AIM_SPEEDS = (0.175, 0.325, 0.5, 0.65)   # radians per second, chosen with GREEN
AIM_DEFAULT = 1
SCORE_FILE = "/etc/enigma2/e2games_bubble.score"
SPEED_FILE = "/etc/enigma2/e2games_bubble.speed"

# Linux input key codes
KEYS_LEFT = (105,)            # LEFT
KEYS_RIGHT = (106,)           # RIGHT
KEYS_SHOOT = (352, 103, 28)   # OK, UP, ENTER
KEYS_SWAP = (108, 401)        # DOWN, BLUE


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


class E2Bubble(Screen):
	def __init__(self, session):
		fhd = getDesktop(0).size().width() >= 1920
		self.fieldScale = 1.5 if fhd else 1.0
		self.imgDir = resolveFilename(SCOPE_PLUGINS, "Extensions/E2games/images/%s/bubble/" % ("fhd" if fhd else "hd"))
		v = self.px
		img = self.imgDir
		parts = ['<screen name="E2Bubble" position="0,0" size="%d,%d" title="E2games" flags="wfNoBorder" backgroundColor="#000000">' % (v(1280), v(720))]
		parts.append('<ePixmap pixmap="%sfield.png" position="%d,%d" size="%d,%d" zPosition="1" />' % (
			img, v(FIELD_X - BORDER), v(FIELD_Y - BORDER), v(be.W + 2 * BORDER), v(be.H + 2 * BORDER)))

		def sprite(name, x, y, w, h, z):
			parts.append('<widget name="%s" position="%d,%d" size="%d,%d" zPosition="%d" alphatest="blend" />' % (
				name, v(FIELD_X + x), v(FIELD_Y + y), v(w), v(h), z))

		def label(name, x, y, w, h, size, color, align="left", extra=""):
			parts.append('<widget name="%s" position="%d,%d" size="%d,%d" font="Regular;%d" halign="%s" valign="center" foregroundColor="%s" backgroundColor="#000000" transparent="1" zPosition="9" %s/>' % (
				name, v(x), v(y), v(w), v(h), v(size), align, color, extra))

		sx, sy = be.SHOOTER
		sprite("arrow", sx - ARROW_SIZE / 2, sy - ARROW_SIZE / 2, ARROW_SIZE, ARROW_SIZE, 2)
		self.spriteNames = ["arrow"]
		for r in range(be.DEAD_ROW + 1):
			for c in range(be.COLS):
				sprite("c%d_%d" % (r, c), c * be.D, r * be.RS, be.D, be.D, 3)
				self.spriteNames.append("c%d_%d" % (r, c))
		for i in range(DOTS):
			sprite("dot%d" % i, 0, 0, 10, 10, 4)
			self.spriteNames.append("dot%d" % i)
		for i in range(be.MAX_EFFECTS):
			sprite("fx%d" % i, 0, 0, be.D, be.D, 5)
			self.spriteNames.append("fx%d" % i)
		nx, ny = be.NEXT_POS
		sprite("current", sx - be.R, sy - be.R, be.D, be.D, 6)
		sprite("next", nx - be.R, ny - be.R, be.D, be.D, 6)
		sprite("shot", sx - be.R, sy - be.R, be.D, be.D, 7)
		self.spriteNames += ["current", "next", "shot"]

		label("title", 40, 30, 380, 50, 38, "#ffffff")
		label("game", 40, 80, 380, 36, 26, "#96d7ff")
		label("scoreCaption", 40, 160, 380, 30, 22, "#8088b0")
		label("score", 40, 190, 380, 56, 46, "#ffd23c")
		label("highCaption", 40, 270, 380, 30, 22, "#8088b0")
		label("high", 40, 300, 380, 44, 34, "#ffffff")
		label("levelCaption", 40, 370, 170, 30, 22, "#8088b0")
		label("level", 40, 400, 170, 44, 34, "#ffffff")
		label("rowsCaption", 210, 370, 220, 30, 22, "#8088b0")
		label("rows", 210, 400, 200, 44, 34, "#ff8070")
		label("speedCaption", 40, 470, 380, 30, 22, "#8088b0")
		label("speed", 40, 500, 380, 40, 30, "#ffffff")
		label("nextCaption", FIELD_X + 4, FIELD_Y + be.NEXT_POS[1] - 62, 100, 26, 18, "#8088b0", "center")
		label("helpCaption", 860, 30, 390, 36, 26, "#96d7ff")
		parts.append('<widget name="help" position="%d,%d" size="%d,%d" font="Regular;%d" halign="left" valign="top" foregroundColor="#c8cce0" backgroundColor="#000000" transparent="1" zPosition="9" />' % (
			v(860), v(80), v(390), v(600), v(20)))
		label("message", FIELD_X + 10, FIELD_Y + 250, be.W - 20, 130, 28, "#ffffff", "center", 'borderWidth="2" borderColor="#000000" ')
		parts.append("</screen>")
		self.skin = "\n".join(parts)

		Screen.__init__(self, session)
		self.setTitle("E2games - " + _("Bubble Shooter"))

		for name in self.spriteNames:
			self[name] = Pixmap()
		self["title"] = Label("E2games")
		self["game"] = Label(_("Bubble Shooter"))
		self["scoreCaption"] = Label(_("Score"))
		self["score"] = Label("0")
		self["highCaption"] = Label(_("High score"))
		self["high"] = Label("0")
		self["levelCaption"] = Label(_("Level"))
		self["level"] = Label("1")
		self["rowsCaption"] = Label(_("New row in"))
		self["rows"] = Label("")
		self["nextCaption"] = Label(_("Next"))
		self["speedCaption"] = Label(_("Aim speed"))
		self["speed"] = Label("")
		self["helpCaption"] = Label(_("Controls"))
		self["help"] = Label("\n".join((
			_("LEFT / RIGHT: aim (hold to turn)"),
			_("OK / UP: shoot"),
			_("DOWN / BLUE: swap with the next bubble"),
			_("GREEN: change aim speed"),
			_("YELLOW: new game"),
			_("EXIT: back to menu"),
			"",
			_("Join three or more bubbles of the same colour to pop them. Bubbles left hanging fall down for extra points."),
			"",
			_("Each shot that pops nothing brings a new row closer. Do not let the bubbles cross the red line."))))
		self["message"] = Label("")

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {
			"cancel": self.keyExit,
			"yellow": self.keyNewGame,
			"green": self.keyAimSpeed,
		}, -1)

		self.game = be.BubbleShooter(highscore=readNumber(SCORE_FILE))
		self.savedHigh = self.game.highscore
		self.aimSpeed = readNumber(SPEED_FILE, AIM_DEFAULT)
		if not 0 <= self.aimSpeed < len(AIM_SPEEDS):
			self.aimSpeed = AIM_DEFAULT
		self.game.turn_speed = AIM_SPEEDS[self.aimSpeed]
		self.pixmaps = {}
		self.drawn = {}            # cache of what each widget currently shows
		self.keysHeld = {}         # "L" / "R" -> time of the last key event
		self.aimPoints = []
		self.keysBound = False
		self.lastTick = monotonic()
		self.gameTimer = eTimer()
		self.gameTimer.callback.append(self.tick)
		self.onLayoutFinish.append(self.gameStart)
		self.onClose.append(self.gameStop)

	def px(self, x):
		return int(round(x * self.fieldScale))

	# ---- start / stop -------------------------------------------------
	def gameStart(self):
		d = self.imgDir
		for i in range(be.COLORS):
			self.pixmaps[i] = LoadPixmap(d + "b%d.png" % i)
		self.pixmaps["pop"] = LoadPixmap(d + "pop.png")
		self.pixmaps["dot"] = LoadPixmap(d + "dot.png")
		for i in range(ARROW_FRAMES):
			self.pixmaps["arrow%d" % i] = LoadPixmap(d + "arrow%02d.png" % i)
		for name in self.spriteNames:
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

	def keyAimSpeed(self):
		self.aimSpeed = (self.aimSpeed + 1) % len(AIM_SPEEDS)
		self.game.turn_speed = AIM_SPEEDS[self.aimSpeed]
		writeNumber(SPEED_FILE, self.aimSpeed)

	def keyNewGame(self):
		self.storeHighscore()
		self.game.new_game()

	# ---- keys -----------------------------------------------------------
	def rawKey(self, key, flag):
		# flag: 0 = make, 1 = break, 2 = repeat, 3 = long
		try:
			if not self.execing:
				return 0
			if key in KEYS_LEFT or key in KEYS_RIGHT:
				group = "L" if key in KEYS_LEFT else "R"
				if flag == 1:
					self.keysHeld.pop(group, None)
				else:
					if flag == 0 and group not in self.keysHeld:
						tap = TAP_TURN * self.game.turn_speed
						self.game.rotate(-tap if group == "L" else tap)
					self.keysHeld[group] = monotonic()
				self.applyTurn()
				return 1
			if key in KEYS_SHOOT:
				if flag == 0:
					game = self.game
					if game.state == game.OVER:
						self.storeHighscore()
						game.new_game()
					else:
						game.shoot()
				return 1
			if key in KEYS_SWAP:
				if flag == 0:
					self.game.swap()
				return 1
			return 0
		except Exception as err:
			print("[E2games] key error: %s" % err)
			return 0

	def applyTurn(self):
		self.game.turn = ("R" in self.keysHeld) - ("L" in self.keysHeld)

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
		for group in list(self.keysHeld):
			if now - self.keysHeld[group] > KEY_TIMEOUT:
				del self.keysHeld[group]
				self.applyTurn()
		game = self.game
		before = game.state
		game.update(dt)
		if game.state == game.OVER and before != game.OVER:
			self.storeHighscore()
		self.draw()

	# ---- drawing --------------------------------------------------------
	def showSprite(self, name, key, x=0.0, y=0.0, w=be.D, h=be.D):
		"""Show pixmap `key` with its centre at field position x, y (None hides)."""
		if key is None:
			state = None
		else:
			state = (key, self.px(FIELD_X + x - w / 2.0), self.px(FIELD_Y + y - h / 2.0))
		old = self.drawn.get(name)
		if old == state:
			return
		self.drawn[name] = state
		widget = self[name]
		if state is None:
			widget.hide()
			return
		if old is None or old[1:] != state[1:]:
			widget.instance.move(ePoint(state[1], state[2]))
		if old is None or old[0] != key:
			widget.instance.setPixmap(self.pixmaps[key])
		if old is None:
			widget.show()

	def setText(self, name, text):
		if self.drawn.get(name) != text:
			self.drawn[name] = text
			self[name].setText(text)

	def draw(self):
		game = self.game
		playing = game.state == game.PLAY
		for r in range(be.DEAD_ROW + 1):
			for c in range(be.COLS):
				color = game.grid.get((r, c))
				if color is None:
					self.showSprite("c%d_%d" % (r, c), None)
				else:
					x, y = game.cell_xy(r, c)
					self.showSprite("c%d_%d" % (r, c), color, x, y)
		sx, sy = be.SHOOTER
		nx, ny = be.NEXT_POS
		frame = int(round((game.angle + be.MAX_ANGLE) / ARROW_STEP))
		frame = max(0, min(ARROW_FRAMES - 1, frame))
		self.showSprite("arrow", "arrow%d" % frame if playing else None, sx, sy, ARROW_SIZE, ARROW_SIZE)
		self.showSprite("current", game.current if playing else None, sx, sy)
		self.showSprite("next", game.next if playing else None, nx, ny)
		shot = game.shot
		self.showSprite("shot", shot[4] if shot else None, shot[0] if shot else 0, shot[1] if shot else 0)
		points = []
		if playing and shot is None:
			key = (game.angle, len(game.grid), game.parity, game.score, game.level)
			if self.drawn.get("aimKey") != key:
				self.drawn["aimKey"] = key
				self.aimPoints = game.aim_points(DOTS, DOT_SPACING)
			points = self.aimPoints
		for i in range(DOTS):
			if i < len(points):
				self.showSprite("dot%d" % i, "dot", points[i][0], points[i][1], 10, 10)
			else:
				self.showSprite("dot%d" % i, None)
		for i in range(be.MAX_EFFECTS):
			if i < len(game.effects):
				e = game.effects[i]
				self.showSprite("fx%d" % i, "pop" if e[5] == "pop" else e[4], e[0], e[1])
			else:
				self.showSprite("fx%d" % i, None)

		self.setText("score", str(game.score))
		self.setText("high", str(game.highscore))
		self.setText("level", str(game.level))
		self.setText("speed", (_("Slow"), _("Normal"), _("Fast"), _("Very fast"))[self.aimSpeed])
		self.setText("rows", str(game.shots_per_row - game.misses) if playing else "")
		if game.state == game.OVER:
			msg = _("GAME OVER")
			if game.new_highscore:
				msg += "\n" + _("New high score!")
			msg += "\n" + _("Press OK for a new game")
		elif game.state == game.CLEARED:
			msg = _("Level complete!") + "\n" + _("Level") + " %d" % (game.level + 1)
		else:
			msg = ""
		self.setText("message", msg)
