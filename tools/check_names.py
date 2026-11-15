#!/usr/bin/env python3
# Fails if a plugin screen class uses an attribute or method name that the
# Enigma2 Screen base class already owns (taken from OpenViX Screens/Screen.py).
import re
import sys

RESERVED = set("""active_components additionalWidgets alreadyShown already_shown close close_on_next_exec
createGUIScreen deleteGUIScreen desktop execing globalScreen handledWidgets helpList hide instance items
keyboardMode mandatoryWidgets onClose onContentChanged onExecBegin onExecEnd onFirstExecBegin onHide
onLayoutFinish onShow onShown parent renderer scale screenImage screenPath screenTitle session setImage
setTitle shown skinAttributes skinName stacks standAlone stand_alone summaries values title path
execBegin execEnd doClose show getScreenPath getTitle setFocus setKeyboardModeNone setKeyboardModeAscii
restoreKeyboardMode saveKeyboardMode setDesktop setAnimationMode getRelatedScreen callLater
screenContentChanged applySkin addToStack createSummary addSummary removeSummary
keys get pop update clear copy setdefault popitem fromkeys""".split())
ALLOWED = {"session", "skin", "close", "setTitle", "execing", "onLayoutFinish", "onClose", "instance"}

bad = []
for path in sys.argv[1:]:
	src = open(path).read()
	names = set(re.findall(r"self\.([A-Za-z_]\w*)\s*=[^=]", src)) | set(re.findall(r"^\tdef ([A-Za-z_]\w*)\(self", src, re.M))
	bad += ["%s: %s" % (path, n) for n in sorted(names & RESERVED - ALLOWED)]
if bad:
	sys.exit("name clashes with Screen:\n" + "\n".join(bad))
print("names ok")
