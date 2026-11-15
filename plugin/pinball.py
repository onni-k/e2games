# -*- coding: utf-8 -*-
# E2games - pinball screen (Enigma2 front end for pinball_engine).
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
from . import pinball_engine as pe

FRAMES = 9                    # flipper animation frames (see tools/make_assets.py)
FLIP_BOX = (80, 78)
FLIP_ORG = (9, 39)
TABLE_X, TABLE_Y = 430, 10    # table position on a 1280x720 screen
TICK_MS = 30
KEY_TIMEOUT = 1.0             # release a key if no repeat arrives (lost "break")
SCORE_FILE = "/etc/enigma2/e2games_pinball.score"

# Linux input key codes
KEYS_LEFT = (105, 398)        # LEFT, RED
KEYS_RIGHT = (106, 401)       # RIGHT, BLUE
KEYS_BOTH = (103,)            # UP
KEYS_LAUNCH = (352, 108, 28)  # OK, DOWN, ENTER


def loadHighscore():
	try:
		with open(SCORE_FILE) as f:
			return int(f.read().strip())
	except Exception:
		return 0


def saveHighscore(value):
	try:
		with open(SCORE_FILE, "w") as f:
			f.write("%d\n" % value)
	except Exception:
		pass


class E2Pinball(Screen):
	def __init__(self, session):
		fhd = getDesktop(0).size().width() >= 1920
		self.tableScale = s = 1.5 if fhd else 1.0
		self.imgdir = resolveFilename(SCOPE_PLUGINS, "Extensions/E2games/images/%s/" % ("fhd" if fhd else "hd"))
		v = self.px
		img = self.imgdir
		parts = ['<screen name="E2Pinball" position="0,0" size="%d,%d" title="E2games" flags="wfNoBorder" backgroundColor="#000000">' % (v(1280), v(720))]
		parts.append('<ePixmap pixmap="%stable.png" position="%d,%d" size="%d,%d" zPosition="1" />' % (img, v(TABLE_X), v(TABLE_Y), v(pe.W), v(pe.H)))

		def pix(name, png, x, y, w, h, z):
			src = ' pixmap="%s%s"' % (img, png) if png else ""
			parts.append('<widget name="%s"%s position="%d,%d" size="%d,%d" zPosition="%d" alphatest="blend" />' % (
				name, src, v(TABLE_X + x), v(TABLE_Y + y), v(w), v(h), z))

		def label(name, x, y, w, h, size, color, align="left", extra=""):
			parts.append('<widget name="%s" position="%d,%d" size="%d,%d" font="Regular;%d" halign="%s" valign="center" foregroundColor="%s" backgroundColor="#000000" transparent="1" zPosition="8" %s/>' % (
				name, v(x), v(y), v(w), v(h), v(size), align, color, extra))

		for i, (bx, by, br) in enumerate(pe.BUMPERS):
			pix("bumper%d" % i, "bumper_lit.png", bx - br - 6, by - br - 6, 2 * br + 12, 2 * br + 12, 2)
		for i, (y1, y2) in enumerate(pe.TARGETS):
			pix("target%d" % i, "target_lit.png", pe.TARGET_X - 7, y1 - 4, 14, y2 - y1 + 8, 2)
		for i, (side, tri) in enumerate((("L", pe.SLING_L), ("R", pe.SLING_R))):
			x0 = min(p[0] for p in tri) - 4
			y0 = min(p[1] for p in tri) - 4
			pix("sling%d" % i, "sling%s_lit.png" % side, x0, y0, max(p[0] for p in tri) - x0 + 4, max(p[1] for p in tri) - y0 + 4, 2)
		pix("plunger", "plunger.png", 379, pe.PLUNGER_Y, 22, 30, 2)
		pix("flipL", None, pe.FLIP_PIVOTS[0][0] - FLIP_ORG[0], pe.FLIP_PIVOTS[0][1] - FLIP_ORG[1], FLIP_BOX[0], FLIP_BOX[1], 3)
		pix("flipR", None, pe.FLIP_PIVOTS[1][0] - (FLIP_BOX[0] - FLIP_ORG[0]), pe.FLIP_PIVOTS[1][1] - FLIP_ORG[1], FLIP_BOX[0], FLIP_BOX[1], 3)
		pix("ball", "ball.png", pe.BALL_START[0] - pe.R - 1, pe.BALL_START[1] - pe.R - 1, 2 * pe.R + 2, 2 * pe.R + 2, 5)

		label("title", 40, 30, 360, 50, 38, "#ffffff")
		label("game", 40, 80, 360, 36, 26, "#96d7ff")
		label("scoreCaption", 40, 170, 360, 30, 22, "#8088b0")
		label("score", 40, 200, 360, 56, 46, "#ffd23c")
		label("highCaption", 40, 290, 360, 30, 22, "#8088b0")
		label("high", 40, 320, 360, 44, 34, "#ffffff")
		label("ballsCaption", 40, 400, 170, 30, 22, "#8088b0")
		label("balls", 40, 430, 170, 44, 34, "#ffffff")
		label("multCaption", 220, 400, 180, 30, 22, "#8088b0")
		label("mult", 220, 430, 180, 44, 34, "#5aff82")
		label("helpCaption", 890, 30, 350, 36, 26, "#96d7ff")
		parts.append('<widget name="help" position="%d,%d" size="%d,%d" font="Regular;%d" halign="left" valign="top" foregroundColor="#c8cce0" backgroundColor="#000000" transparent="1" zPosition="8" />' % (
			v(890), v(80), v(350), v(420), v(20)))
		label("message", TABLE_X + 20, TABLE_Y + 335, 340, 100, 26, "#ffffff", "center", 'borderWidth="2" borderColor="#000000" ')
		parts.append("</screen>")
		self.skin = "\n".join(parts)

		Screen.__init__(self, session)
		self.setTitle("E2games - " + _("Pinball"))

		for name in ("bumper0", "bumper1", "bumper2", "target0", "target1", "target2", "sling0", "sling1", "plunger", "flipL", "flipR", "ball"):
			self[name] = Pixmap()
		self["title"] = Label("E2games")
		self["game"] = Label(_("Pinball"))
		self["scoreCaption"] = Label(_("Score"))
		self["score"] = Label("0")
		self["highCaption"] = Label(_("High score"))
		self["high"] = Label("0")
		self["ballsCaption"] = Label(_("Balls"))
		self["balls"] = Label("")
		self["multCaption"] = Label(_("Multiplier"))
		self["mult"] = Label("")
		self["helpCaption"] = Label(_("Controls"))
		self["help"] = Label("\n\n".join((
			_("LEFT / RED: left flipper"),
			_("RIGHT / BLUE: right flipper"),
			_("UP: both flippers"),
			_("OK / DOWN: hold and release to launch the ball"),
			_("EXIT: back to menu"),
			_("Light all three green targets for a bonus and a higher multiplier."))))
		self["message"] = Label("")

		self["actions"] = ActionMap(["OkCancelActions"], {
			"cancel": self.keyExit,
		}, -1)

		self.game = pe.Pinball(loadHighscore())
		self.savedHigh = self.game.highscore
		self.keysHeld = {}             # key group -> time of the last key event
		self.drawn = {}            # cache of what is currently drawn
		self.flipFrames = None
		self.keysBound = False
		self.lastTick = monotonic()
		self.gameTimer = eTimer()
		self.gameTimer.callback.append(self.tick)
		self.onLayoutFinish.append(self.gameStart)
		self.onClose.append(self.gameStop)

	def px(self, x):
		return int(round(x * self.tableScale))

	# ---- start / stop -------------------------------------------------
	def gameStart(self):
		self.flipFrames = (
			[LoadPixmap(self.imgdir + "flipL%d.png" % i) for i in range(FRAMES)],
			[LoadPixmap(self.imgdir + "flipR%d.png" % i) for i in range(FRAMES)])
		for name in ("bumper0", "bumper1", "bumper2", "target0", "target1", "target2", "sling0", "sling1"):
			self[name].hide()
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
			saveHighscore(self.savedHigh)

	def keyExit(self):
		self.close()

	# ---- keys -----------------------------------------------------------
	def rawKey(self, key, flag):
		# flag: 0 = make, 1 = break, 2 = repeat, 3 = long
		try:
			if not self.execing:
				return 0
			if key in KEYS_LEFT:
				group = "L"
			elif key in KEYS_RIGHT:
				group = "R"
			elif key in KEYS_BOTH:
				group = "B"
			elif key in KEYS_LAUNCH:
				group = "P"
			else:
				return 0
			if flag == 1:
				self.keyUp(group)
			else:
				if flag == 0 or group in self.keysHeld:
					if group not in self.keysHeld:
						self.keyDown(group)
					self.keysHeld[group] = monotonic()
			return 1
		except Exception as err:
			print("[E2games] key error: %s" % err)
			return 0

	def keyDown(self, group):
		game = self.game
		if group == "P":
			if game.state == game.OVER:
				game.new_game()
			else:
				game.plunger_press()
		self.keysHeld[group] = monotonic()
		self.applyFlippers()

	def keyUp(self, group):
		if group in self.keysHeld:
			del self.keysHeld[group]
			if group == "P":
				self.game.plunger_release()
			self.applyFlippers()

	def applyFlippers(self):
		both = "B" in self.keysHeld
		self.game.set_flipper(0, both or "L" in self.keysHeld)
		self.game.set_flipper(1, both or "R" in self.keysHeld)

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
				self.keyUp(group)
		game = self.game
		before = game.state
		game.update(dt)
		if game.state == game.OVER and before != game.OVER:
			self.storeHighscore()
		self.draw()

	def changed(self, key, value):
		"""True if the value differs from what is on screen."""
		if self.drawn.get(key) == value:
			return False
		self.drawn[key] = value
		return True

	def draw(self):
		game = self.game
		v = self.px
		pos = (v(TABLE_X + game.bx - pe.R - 1), v(TABLE_Y + game.by - pe.R - 1))
		if self.changed("ball", pos):
			self["ball"].instance.move(ePoint(pos[0], pos[1]))
		visible = game.state != game.OVER
		if self.changed("ballVisible", visible):
			if visible:
				self["ball"].show()
			else:
				self["ball"].hide()
		y = v(TABLE_Y + pe.PLUNGER_Y + 14 * game.charge)
		if self.changed("plunger", y):
			self["plunger"].instance.move(ePoint(v(TABLE_X + 379), y))
		for i, name in ((0, "flipL"), (1, "flipR")):
			frame = game.flippers[i].frame(FRAMES)
			if self.changed(name, frame):
				self[name].instance.setPixmap(self.flipFrames[i][frame])
		for i in (0, 1, 2):
			self.setLight("bumper%d" % i, game.bumper_lit[i] > 0.0)
			self.setLight("target%d" % i, game.target_lit[i])
		for i in (0, 1):
			self.setLight("sling%d" % i, game.sling_lit[i] > 0.0)
		if self.changed("score", game.score):
			self["score"].setText(str(game.score))
		if self.changed("high", game.highscore):
			self["high"].setText(str(game.highscore))
		if self.changed("balls", game.balls):
			self["balls"].setText(str(game.balls))
		if self.changed("mult", game.mult):
			self["mult"].setText("x%d" % game.mult)
		if game.state == game.OVER:
			if game.new_highscore:
				msg = _("GAME OVER") + "\n" + _("New high score!") + "\n" + _("Press OK for a new game")
			elif game.balls == 0 and game.score == 0 and not self.drawn.get("played"):
				msg = _("Press OK for a new game")
			else:
				msg = _("GAME OVER") + "\n" + _("Press OK for a new game")
		else:
			self.drawn["played"] = True
			if game.note == "saved":
				msg = _("Ball saved!")
			elif game.note == "bonus":
				msg = _("Bonus!") + " x%d" % game.mult
			elif game.state == game.READY and not game.charging:
				msg = _("Hold OK and release to launch")
			else:
				msg = ""
		if self.changed("message", msg):
			self["message"].setText(msg)

	def setLight(self, name, on):
		if self.changed(name, on):
			if on:
				self[name].show()
			else:
				self[name].hide()
