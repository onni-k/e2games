# -*- coding: utf-8 -*-
# E2games - translations follow the receiver's system language automatically.
import gettext

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

PluginLanguageDomain = "E2games"
PluginLanguagePath = "Extensions/E2games/locale"


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	translated = gettext.dgettext(PluginLanguageDomain, txt)
	if translated == txt:
		translated = gettext.gettext(txt)
	return translated


localeInit()
language.addCallback(localeInit)
