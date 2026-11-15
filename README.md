# E2games

Games for Enigma2 receivers (developed for OpenViX). Version 0.1.002 contains one game: **Pinball**.

- Native Enigma2 plugin (no pygame/SDL needed): `plugin.py` (menu), `pinball.py` (screen), `pinball_engine.py` (pure-Python physics).
- Languages: English (source) and Finnish (`plugin/po/fi.po`), chosen automatically from the system language.
- HD (1280x720) and FHD (1920x1080) skins are supported.

## Install

    opkg install /tmp/enigma2-plugin-extensions-e2games_0.1.002_all.ipk
    # then restart the GUI

## Controls

LEFT / RED = left flipper, RIGHT / BLUE = right flipper, UP = both flippers,
OK / DOWN = hold and release to launch, EXIT = back to the menu.

## Build

    python3 tools/make_assets.py   # regenerate graphics (needs Pillow)
    python3 tools/test_engine.py   # physics self-test
    sh tools/build.sh              # compiles .mo and builds dist/*.ipk

## Releases

The installable `.ipk` is attached to each GitHub release; it is not stored in the repository.
Pushing a version tag (for example `v0.1.002`) builds the package and publishes the release automatically.

## License

E2games is free software, licensed under the GNU General Public License version 3.
See [LICENSE](LICENSE) for the full text.
