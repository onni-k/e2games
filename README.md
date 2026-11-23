# E2games

Games for Enigma2 receivers (developed for OpenViX). Games: **Pinball** (three tables), **Solitaire** (Klondike), **Bubble Shooter**, **Sudoku** and **Blocks** (falling blocks).

- Native Enigma2 plugin (no pygame/SDL needed): `plugin.py` (menu), one screen module per game (`pinball.py`, `solitaire.py`, `bubble.py`, `sudoku.py`, `blocks.py`) and a pure-Python engine for each (`pinball_engine.py`, `solitaire_engine.py`, `bubble_engine.py`, `sudoku_engine.py`, `blocks_engine.py`).
- Languages: English (source) and Finnish (`plugin/po/fi.po`), chosen automatically from the system language.
- HD (1280x720) and FHD (1920x1080) skins are supported.

## Install

    opkg install /tmp/enigma2-plugin-extensions-e2games_<version>_all.ipk
    # then restart the GUI

## Controls

In every game the HELP key opens the receiver's own remote control help for that screen.

Pinball: LEFT / RED = left flipper, RIGHT / BLUE = right flipper, UP = both flippers,
OK / DOWN = hold and release to launch, YELLOW = change table (between games), EXIT = back to the menu.
Tables: Classic (stand-up targets), Target Bank (drop targets and a saucer), Star Lanes (rollover lanes,
posts and a saucer). Each table keeps its own high score.

Solitaire: arrows move the cursor (UP inside a column selects more cards), OK picks up
and places cards, OK twice on a card sends it to the foundation, OK on the stock turns a card.
RED = undo, GREEN = card to the foundation, YELLOW = new game, BLUE = turn a card from the stock,
EXIT = cancel selection / back to the menu.

Bubble Shooter: LEFT / RIGHT = aim (hold to turn), OK / UP = shoot, DOWN / BLUE = swap with the
next bubble, GREEN = aim speed (slow / normal / fast / very fast, remembered), YELLOW = new game,
EXIT = back to the menu.

Sudoku: arrows move, 1-9 enter a number, 0 clears, OK steps the number in the cell, RED = undo,
GREEN = hint, YELLOW = new game, BLUE = difficulty of the next game (easy / medium / hard),
EXIT = save and back to the menu. An unfinished game continues next time; best times are kept
per difficulty (games solved without hints).

Blocks: LEFT / RIGHT = move one cell (hold to repeat), UP = turn clockwise, RED = turn the other way,
DOWN = drop faster (hold), OK = drop at once, GREEN = hold the piece for later, BLUE = pause,
YELLOW = new game, EXIT = back to the menu.

## Build

    python3 tools/make_assets.py   # regenerate pinball graphics (needs Pillow)
    python3 tools/make_cards.py    # regenerate playing cards (needs Pillow)
    python3 tools/make_bubbles.py  # regenerate bubble shooter graphics (needs Pillow)
    python3 tools/make_sudoku.py   # regenerate sudoku graphics (needs Pillow)
    python3 tools/make_blocks.py   # regenerate falling blocks graphics (needs Pillow)
    python3 tools/test_engine.py   # pinball physics self-test
    python3 tools/test_solitaire.py  # solitaire rules self-test
    python3 tools/test_bubble.py   # bubble shooter rules self-test
    python3 tools/test_sudoku.py   # sudoku generator and rules self-test
    python3 tools/test_blocks.py   # falling blocks rules self-test
    sh tools/build.sh              # compiles .mo and builds dist/*.ipk

## Releases

The installable `.ipk` is attached to each GitHub release; it is not stored in the repository.
Pushing a version tag (for example `v0.1.002`) builds the package and publishes the release automatically.

## License

E2games is free software, licensed under the GNU General Public License version 3.
See [LICENSE](LICENSE) for the full text.
