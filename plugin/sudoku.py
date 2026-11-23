# -*- coding: utf-8 -*-
# E2games - sudoku screen (Enigma2 front end for sudoku_engine).
import json
import os

from enigma import ePoint, eTimer, getDesktop

from Components.ActionMap import HelpableActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Screens.HelpMenu import HelpableScreen
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap

from . import _
from . import sudoku_engine as se

BOARD_X = (1280 - se.BOARD) // 2
BOARD_Y = (720 - se.BOARD) // 2
SAVE_FILE = "/etc/enigma2/e2games_sudoku.json"
BEST_FILE = "/etc/enigma2/e2games_sudoku.best"
STYLES = ("given", "user", "bad", "hint")


def difficultyNames():
	return [_("Easy"), _("Medium"), _("Hard")]


def formatTime(seconds):
	if seconds >= 3600:
		return "%d:%02d:%02d" % (seconds // 3600, seconds // 60 % 60, seconds % 60)
	return "%d:%02d" % (seconds // 60, seconds % 60)


def loadBest():
	try:
		with open(BEST_FILE) as f:
			best = [int(x) for x in f.read().split()]
		if len(best) == 3:
			return best
	except Exception:
		pass
	return [0, 0, 0]


def saveBest(best):
	try:
		with open(BEST_FILE, "w") as f:
			f.write("%d %d %d\n" % tuple(best))
	except Exception:
		pass


class E2Sudoku(Screen, HelpableScreen):
	def __init__(self, session):
		fhd = getDesktop(0).size().width() >= 1920
		self.boardScale = 1.5 if fhd else 1.0
		self.imgDir = resolveFilename(SCOPE_PLUGINS, "Extensions/E2games/images/%s/sudoku/" % ("fhd" if fhd else "hd"))
		v = self.px
		img = self.imgDir
		parts = ['<screen name="E2Sudoku" position="0,0" size="%d,%d" title="E2games" flags="wfNoBorder" backgroundColor="#101828">' % (v(1280), v(720))]
		parts.append('<ePixmap pixmap="%sboard.png" position="%d,%d" size="%d,%d" zPosition="1" />' % (
			img, v(BOARD_X), v(BOARD_Y), v(se.BOARD), v(se.BOARD)))
		for i in range(81):
			x, y = se.cell_origin(i)
			parts.append('<widget name="n%d" position="%d,%d" size="%d,%d" zPosition="2" alphatest="blend" />' % (
				i, v(BOARD_X + x), v(BOARD_Y + y), v(se.CELL), v(se.CELL)))
		parts.append('<widget name="cursor" pixmap="%scursor.png" position="0,0" size="%d,%d" zPosition="3" alphatest="blend" />' % (
			img, v(se.CELL + 6), v(se.CELL + 6)))

		def label(name, x, y, w, h, size, color, align="left", valign="center"):
			parts.append('<widget name="%s" position="%d,%d" size="%d,%d" font="Regular;%d" halign="%s" valign="%s" foregroundColor="%s" backgroundColor="#101828" transparent="1" zPosition="4" />' % (
				name, v(x), v(y), v(w), v(h), v(size), align, valign, color))

		label("title", 40, 30, 290, 50, 38, "#ffffff")
		label("game", 40, 80, 290, 36, 26, "#96d7ff")
		label("levelCaption", 40, 150, 290, 28, 21, "#8088b0")
		label("level", 40, 178, 290, 40, 32, "#ffffff")
		label("timeCaption", 40, 240, 140, 28, 21, "#8088b0")
		label("time", 40, 268, 140, 40, 32, "#ffffff")
		label("hintsCaption", 190, 240, 140, 28, 21, "#8088b0")
		label("hints", 190, 268, 140, 40, 32, "#ffffff")
		label("bestCaption", 40, 330, 290, 28, 21, "#8088b0")
		label("best", 40, 358, 290, 40, 32, "#ffd23c")
		label("next", 40, 420, 290, 60, 21, "#c8cce0", valign="top")
		label("message", 40, 500, 290, 180, 26, "#ffd23c", valign="top")
		label("helpCaption", 950, 30, 300, 36, 26, "#96d7ff")
		label("help", 950, 80, 300, 600, 19, "#c8cce0", valign="top")
		parts.append("</screen>")
		self.skin = "\n".join(parts)

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.setTitle("E2games - " + _("Sudoku"))

		for i in range(81):
			self["n%d" % i] = Pixmap()
		self["cursor"] = Pixmap()
		self["title"] = Label("E2games")
		self["game"] = Label(_("Sudoku"))
		self["levelCaption"] = Label(_("Difficulty"))
		self["level"] = Label("")
		self["timeCaption"] = Label(_("Time"))
		self["time"] = Label("")
		self["hintsCaption"] = Label(_("Hints"))
		self["hints"] = Label("")
		self["bestCaption"] = Label(_("Best time"))
		self["best"] = Label("")
		self["next"] = Label("")
		self["message"] = Label("")
		self["helpCaption"] = Label(_("Controls"))
		self["help"] = Label("\n".join((
			_("Arrows: move"),
			_("1-9: enter a number"),
			_("0: clear the cell"),
			_("OK: next number in the cell"),
			"",
			_("RED: undo"),
			_("GREEN: hint"),
			_("YELLOW: new game"),
			_("BLUE: difficulty of the next game"),
			_("EXIT: save and back to menu"),
			_("HELP: remote control help"),
			"",
			_("Fill every row, column and 3x3 box with the numbers 1-9. Numbers that clash are shown in red."),
			"",
			_("An unfinished game is saved and continues next time."))))

		self["actions"] = HelpableActionMap(self, "OkCancelActions", {
			"ok": (self.keyOk, _("Next number in the cell")),
			"cancel": (self.keyExit, _("Save and back to menu")),
		}, -1)
		self["directionActions"] = HelpableActionMap(self, "DirectionActions", {
			"left": (self.keyLeft, _("Move left")),
			"right": (self.keyRight, _("Move right")),
			"up": (self.keyUp, _("Move up")),
			"down": (self.keyDown, _("Move down")),
		}, -1)
		self["colorActions"] = HelpableActionMap(self, "ColorActions", {
			"red": (self.keyUndo, _("Undo")),
			"green": (self.keyHint, _("Hint")),
			"yellow": (self.keyNewGame, _("New game")),
			"blue": (self.keyDifficulty, _("Difficulty of the next game")),
		}, -1)
		numbers = {"0": (lambda: self.keyNumber(0), _("Clear the cell"))}
		for n in range(1, 10):
			numbers[str(n)] = (lambda n=n: self.keyNumber(n), _("Enter a number"))
		self["numbers"] = HelpableActionMap(self, "NumberActions", numbers, -1)

		self.puzzle = se.Sudoku()
		self.pixmaps = {}
		self.drawn = {}
		self.cursorCell = 40
		self.best = loadBest()
		self.nextDifficulty = se.EASY
		self.solvedShown = False
		self.clockTimer = eTimer()
		self.clockTimer.callback.append(self.clockTick)
		self.onLayoutFinish.append(self.gameStart)
		self.onClose.append(self.gameStop)

	def px(self, x):
		return int(round(x * self.boardScale))

	# ---- start / stop -------------------------------------------------
	def gameStart(self):
		for style in STYLES:
			for n in range(1, 10):
				self.pixmaps[(style, n, False)] = LoadPixmap(self.imgDir + "%s%d.png" % (style, n))
				self.pixmaps[(style, n, True)] = LoadPixmap(self.imgDir + "%s%d_same.png" % (style, n))
		for i in range(81):
			self["n%d" % i].hide()
		if not self.loadGame():
			self.puzzle.new_game(se.EASY)
		self.nextDifficulty = self.puzzle.difficulty
		self.cursorCell = self.firstEmpty()
		self.solvedShown = self.puzzle.won()
		self.draw()
		self.clockTimer.start(1000, False)

	def gameStop(self):
		self.clockTimer.stop()
		self.saveGame()

	def loadGame(self):
		try:
			with open(SAVE_FILE) as f:
				self.puzzle.from_dict(json.load(f))
			return not self.puzzle.won()
		except Exception:
			return False

	def saveGame(self):
		try:
			if self.puzzle.won():
				if os.path.exists(SAVE_FILE):
					os.remove(SAVE_FILE)
			else:
				with open(SAVE_FILE, "w") as f:
					json.dump(self.puzzle.to_dict(), f)
		except Exception as err:
			print("[E2games] sudoku save error: %s" % err)

	def firstEmpty(self):
		for i in range(81):
			if self.puzzle.values[i] == 0:
				return i
		return 40

	def clockTick(self):
		if self.execing and not self.puzzle.won():
			self.puzzle.seconds += 1
			self.draw()

	# ---- keys -----------------------------------------------------------
	def moveCursor(self, dr, dc):
		r, c = divmod(self.cursorCell, 9)
		self.cursorCell = ((r + dr) % 9) * 9 + (c + dc) % 9
		self.draw()

	def keyLeft(self):
		self.moveCursor(0, -1)

	def keyRight(self):
		self.moveCursor(0, 1)

	def keyUp(self):
		self.moveCursor(-1, 0)

	def keyDown(self):
		self.moveCursor(1, 0)

	def keyNumber(self, number):
		self.puzzle.set_value(self.cursorCell, int(number))
		self.afterChange()

	def keyOk(self):
		value = self.puzzle.values[self.cursorCell]
		self.puzzle.set_value(self.cursorCell, (value + 1) % 10)
		self.afterChange()

	def keyUndo(self):
		cell = self.puzzle.undo()
		if cell is not None:
			self.cursorCell = cell
		self.afterChange()

	def keyHint(self):
		cell = self.puzzle.hint(self.cursorCell)
		if cell is not None:
			self.cursorCell = cell
		self.afterChange()

	def keyNewGame(self):
		self.puzzle.new_game(self.nextDifficulty)
		self.cursorCell = self.firstEmpty()
		self.solvedShown = False
		self.draw()

	def keyDifficulty(self):
		self.nextDifficulty = (self.nextDifficulty + 1) % 3
		self.draw()

	def keyExit(self):
		self.close()

	def afterChange(self):
		puzzle = self.puzzle
		if puzzle.won() and not self.solvedShown:
			self.solvedShown = True
			d = puzzle.difficulty
			seconds = max(1, puzzle.seconds)    # 0 means "no best time yet"
			if puzzle.hints == 0 and (self.best[d] == 0 or seconds < self.best[d]):
				self.best[d] = seconds
				saveBest(self.best)
				self.drawn["newBest"] = True
			else:
				self.drawn["newBest"] = False
			self.saveGame()
		self.draw()

	# ---- drawing --------------------------------------------------------
	def setText(self, name, text):
		if self.drawn.get(name) != text:
			self.drawn[name] = text
			self[name].setText(text)

	def draw(self):
		puzzle = self.puzzle
		values = puzzle.values
		same = values[self.cursorCell]
		for i in range(81):
			v = values[i]
			if v == 0:
				key = None
			else:
				if puzzle.given(i):
					style = "given"
				elif puzzle.conflict(i):
					style = "bad"
				elif puzzle.hinted[i]:
					style = "hint"
				else:
					style = "user"
				key = (style, v, v == same)
			name = "n%d" % i
			if self.drawn.get(name, False) != key:
				self.drawn[name] = key
				if key is None:
					self[name].hide()
				else:
					self[name].instance.setPixmap(self.pixmaps[key])
					self[name].show()
		won = puzzle.won()
		x, y = se.cell_origin(self.cursorCell)
		cursor = None if won else (self.px(BOARD_X + x - 3), self.px(BOARD_Y + y - 3))
		if self.drawn.get("cursor", False) != cursor:
			self.drawn["cursor"] = cursor
			if cursor is None:
				self["cursor"].hide()
			else:
				self["cursor"].instance.move(ePoint(cursor[0], cursor[1]))
				self["cursor"].show()

		names = difficultyNames()
		d = puzzle.difficulty
		self.setText("level", names[d])
		self.setText("time", formatTime(puzzle.seconds))
		self.setText("hints", str(puzzle.hints))
		self.setText("best", formatTime(self.best[d]) if self.best[d] else "-")
		self.setText("next", _("Next game: %s") % names[self.nextDifficulty] if self.nextDifficulty != d or won else "")
		if won:
			msg = _("Solved!") + "\n" + formatTime(puzzle.seconds)
			if self.drawn.get("newBest"):
				msg += "\n" + _("New best time!")
			msg += "\n" + _("Press YELLOW for a new game")
		else:
			msg = ""
		self.setText("message", msg)
