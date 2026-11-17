#!/bin/sh
# Builds the .mo files and the installable .ipk (needs python3, tar, ar).
set -e
cd "$(dirname "$0")/.."
VERSION=$(sed -n 's/^VERSION = "\(.*\)"/\1/p' plugin/plugin.py)
DEST=usr/lib/enigma2/python/Plugins/Extensions/E2games
python3 -c 'import ast, glob, sys; [ast.parse(open(f).read(), f) for f in glob.glob("plugin/*.py")]'
python3 tools/check_names.py plugin/plugin.py plugin/pinball.py plugin/solitaire.py plugin/bubble.py plugin/sudoku.py
python3 tools/msgfmt.py plugin/po/fi.po plugin/locale/fi/LC_MESSAGES/E2games.mo
rm -rf build && mkdir -p build/data/$DEST build/control dist
cp -r plugin/*.py plugin/plugin.png plugin/images plugin/locale build/data/$DEST/
cat > build/control/control <<CTL
Package: enigma2-plugin-extensions-e2games
Version: $VERSION
Section: extra
Priority: optional
Architecture: all
Maintainer: E2games
Depends: enigma2
Description: E2games - games for Enigma2 receivers (pinball, solitaire, bubble shooter, sudoku)
CTL
printf '#!/bin/sh\nrm -rf /%s\nexit 0\n' "$DEST" > build/control/postrm
chmod 755 build/control/postrm
echo 2.0 > build/debian-binary
(cd build/control && tar --owner=0 --group=0 -czf ../control.tar.gz ./control ./postrm)
(cd build/data && tar --owner=0 --group=0 -czf ../data.tar.gz ./usr)
OUT=dist/enigma2-plugin-extensions-e2games_${VERSION}_all.ipk
rm -f $OUT
(cd build && ar r ../$OUT debian-binary control.tar.gz data.tar.gz 2>/dev/null)
rm -rf build
echo "built $OUT"
