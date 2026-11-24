#!/usr/bin/env python3
# Generates the 2048 graphics (needs Pillow).
# Usage: python3 tools/make_2048.py
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, "..", "plugin")
sys.path.insert(0, PLUGIN)
import g2048_engine as ge  # noqa: E402

SS = 4
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MAX_POWER = 17                   # tiles up to 131072
# tile colour, text colour
COLORS = {
	2: ((238, 228, 218), (110, 100, 90)), 4: ((236, 222, 196), (110, 100, 90)),
	8: ((242, 177, 121), (255, 255, 255)), 16: ((245, 149, 99), (255, 255, 255)),
	32: ((246, 124, 95), (255, 255, 255)), 64: ((246, 94, 59), (255, 255, 255)),
	128: ((237, 207, 114), (255, 255, 255)), 256: ((237, 204, 97), (255, 255, 255)),
	512: ((237, 200, 80), (255, 255, 255)), 1024: ((237, 197, 63), (255, 255, 255)),
	2048: ((237, 194, 46), (255, 255, 255)),
}
BIG = ((60, 58, 50), (255, 255, 255))


def save(img, k, s, outdir, name):
	w, h = int(round(img.size[0] / k * s)), int(round(img.size[1] / k * s))
	img.resize((w, h), Image.LANCZOS).save(os.path.join(outdir, name), optimize=True)


def board(k):
	n = ge.BOARD
	img = Image.new("RGBA", (int(n * k), int(n * k)), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	d.rounded_rectangle((0, 0, n * k - 1, n * k - 1), radius=12 * k, fill=(150, 136, 122, 255))
	for i in range(ge.CELLS):
		x, y = ge.cell_origin(i)
		d.rounded_rectangle((x * k, y * k, (x + ge.TILE) * k - 1, (y + ge.TILE) * k - 1), radius=7 * k, fill=(196, 182, 168, 255))
	return img


def tile(value, k):
	bg, fg = COLORS.get(value, BIG)
	img = Image.new("RGBA", (int(ge.TILE * k), int(ge.TILE * k)), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	d.rounded_rectangle((0, 0, ge.TILE * k - 1, ge.TILE * k - 1), radius=7 * k, fill=bg + (255,))
	text = str(value)
	size = {1: 60, 2: 58, 3: 50, 4: 40, 5: 32, 6: 27}[len(text)]
	d.text((ge.TILE / 2.0 * k, ge.TILE / 2.0 * k + 2 * k), text, font=ImageFont.truetype(FONT, int(size * k)), fill=fg + (255,), anchor="mm")
	return img


def main():
	for name, s in (("hd", 1.0), ("fhd", 1.5)):
		outdir = os.path.join(PLUGIN, "images", name, "2048")
		os.makedirs(outdir, exist_ok=True)
		k = SS * s
		save(board(k), k, s, outdir, "board.png")
		for p in range(1, MAX_POWER + 1):
			save(tile(2 ** p, k), k, s, outdir, "t%d.png" % 2 ** p)


if __name__ == "__main__":
	main()
