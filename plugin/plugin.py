# -*- coding: utf-8 -*-
# E2games - a small collection of games for Enigma2 receivers.
from enigma import getDesktop

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen

from . import _

VERSION = "0.3.001"


def getScale():
	return 1.5 if getDesktop(0).size().width() >= 1920 else 1.0


def openPinball(session, table=None):
	from .pinball import E2Pinball, lastTable

	def closed(result=None):
		# the pinball screen returns a table number when the player changes table
		if isinstance(result, int):
			openPinball(session, result)

	session.openWithCallback(closed, E2Pinball, lastTable() if table is None else table)


def gameList():
	# (title, function that opens the game) - add new games here
	from .bubble import E2Bubble
	from .solitaire import E2Solitaire
	from .sudoku import E2Sudoku
	return [
		(_("Pinball"), openPinball),
		(_("Solitaire"), lambda session: session.open(E2Solitaire)),
		(_("Bubble Shooter"), lambda session: session.open(E2Bubble)),
		(_("Sudoku"), lambda session: session.open(E2Sudoku)),
	]


class E2gamesMenu(Screen):
	def __init__(self, session):
		s = getScale()
		v = lambda x: int(round(x * s))
		dw, dh = getDesktop(0).size().width(), getDesktop(0).size().height()
		w, h = v(560), v(340)
		self.skin = """
		<screen name="E2gamesMenu" position="%d,%d" size="%d,%d" title="E2games" flags="wfNoBorder" backgroundColor="#101430">
			<widget name="title" position="%d,%d" size="%d,%d" font="Regular;%d" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#101430" transparent="1" />
			<widget name="subtitle" position="%d,%d" size="%d,%d" font="Regular;%d" halign="center" valign="center" foregroundColor="#96d7ff" backgroundColor="#101430" transparent="1" />
			<widget name="menu" position="%d,%d" size="%d,%d" font="Regular;%d" itemHeight="%d" backgroundColor="#101430" scrollbarMode="showOnDemand" />
			<widget name="hint" position="%d,%d" size="%d,%d" font="Regular;%d" halign="center" valign="center" foregroundColor="#8088b0" backgroundColor="#101430" transparent="1" />
		</screen>""" % (
			(dw - w) // 2, (dh - h) // 2, w, h,
			v(20), v(15), v(520), v(50), v(36),
			v(20), v(68), v(520), v(32), v(22),
			v(40), v(115), v(480), v(160), v(26), v(40),
			v(20), v(290), v(520), v(34), v(19))
		Screen.__init__(self, session)
		self.setTitle("E2games")
		self.games = gameList()
		self["title"] = Label("E2games")
		self["subtitle"] = Label(_("Select a game"))
		self["menu"] = MenuList([g[0] for g in self.games])
		self["hint"] = Label(_("OK: play    EXIT: close") + "    v" + VERSION)
		self["actions"] = ActionMap(["OkCancelActions"], {
			"ok": self.keyOk,
			"cancel": self.close,
		}, -1)

	def keyOk(self):
		index = self["menu"].getSelectedIndex()
		if 0 <= index < len(self.games):
			self.games[index][1](self.session)


def main(session, **kwargs):
	session.open(E2gamesMenu)


def Plugins(**kwargs):
	where = [PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU]
	return [PluginDescriptor(name="E2games", description=_("Games for your receiver"),
		where=where, icon="plugin.png", fnc=main)]
