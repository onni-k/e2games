#!/usr/bin/env python3
# Generates the falling blocks graphics (needs Pillow).
# Usage: python3 tools/make_blocks.py
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, "..", "plugin")
sys.path.insert(0, PLUGIN)
import blocks_engine as be  # noqa: E402

SS = 4
CELL = 32
BORDER = 8
BOX_W, HOLD_H, NEXT_H = 150, 110, 330
COLORS = {"I": (40, 200, 230), "O": (245, 205, 40), "T": (170, 70, 210), "S": (70, 200, 80),
	"Z": (225, 55, 60), "J": (50, 100, 230), "L": (240, 140, 40)}


def save(img, k, s, outdir, name):
	w, h = int(round(img.size[0] / k * s)), int(round(img.size[1] / k * s))
	img.resize((w, h), Image.LANCZOS).save(os.path.join(outdir, name), optimize=True)


def shade(color, f):
	return tuple(max(0, min(255, int(v * f))) for v in color)


def cell(color, k):
	img = Image.new("RGBA", (int(CELL * k), int(CELL * k)), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	n = CELL * k
	b = 4 * k
	d.rectangle((k, k, n - k - 1, n - k - 1), fill=shade(color, 1.0) + (255,))
	d.polygon([(k, k), (n - k, k), (n - k - b, k + b), (k + b, k + b)], fill=shade(color, 1.35) + (255,))
	d.polygon([(k, k), (k + b, k + b), (k + b, n - k - b), (k, n - k)], fill=shade(color, 1.18) + (255,))
	d.polygon([(n - k, n - k), (k, n - k), (k + b, n - k - b), (n - k - b, n - k - b)], fill=shade(color, 0.6) + (255,))
	d.polygon([(n - k, n - k), (n - k - b, n - k - b), (n - k - b, k + b), (n - k, k)], fill=shade(color, 0.75) + (255,))
	return img


def ghost(k):
	img = Image.new("RGBA", (int(CELL * k), int(CELL * k)), (0, 0, 0, 0))
	ImageDraw.Draw(img).rectangle((3 * k, 3 * k, (CELL - 3) * k - 1, (CELL - 3) * k - 1), outline=(200, 210, 240, 150), width=int(2 * k))
	return img


def flash(k):
	img = Image.new("RGBA", (int(CELL * k), int(CELL * k)), (0, 0, 0, 0))
	ImageDraw.Draw(img).rectangle((k, k, (CELL - 1) * k - 1, (CELL - 1) * k - 1), fill=(255, 255, 240, 255))
	return img


def frame(w, h, k, grid=False):
	img = Image.new("RGB", (int((w + 2 * BORDER) * k), int((h + 2 * BORDER) * k)), (0, 0, 0))
	d = ImageDraw.Draw(img)
	d.rounded_rectangle((0, 0, img.size[0] - 1, img.size[1] - 1), radius=8 * k, fill=(70, 90, 140))
	d.rectangle((BORDER * k, BORDER * k, (w + BORDER) * k - 1, (h + BORDER) * k - 1), fill=(10, 14, 30))
	if grid:
		for c in range(1, be.COLS):
			x = (BORDER + c * CELL) * k
			d.line((x, BORDER * k, x, (h + BORDER) * k), fill=(24, 30, 52), width=int(k))
		for r in range(1, be.VISIBLE):
			y = (BORDER + r * CELL) * k
			d.line((BORDER * k, y, (w + BORDER) * k, y), fill=(24, 30, 52), width=int(k))
	return img


def main():
	for name, s in (("hd", 1.0), ("fhd", 1.5)):
		outdir = os.path.join(PLUGIN, "images", name, "blocks")
		os.makedirs(outdir, exist_ok=True)
		k = SS * s
		for piece, color in COLORS.items():
			save(cell(color, k), k, s, outdir, "cell_%s.png" % piece)
		save(ghost(k), k, s, outdir, "ghost.png")
		save(flash(k), k, s, outdir, "flash.png")
		save(frame(be.COLS * CELL, be.VISIBLE * CELL, k, True), k, s, outdir, "well.png")
		save(frame(BOX_W, HOLD_H, k), k, s, outdir, "hold.png")
		save(frame(BOX_W, NEXT_H, k), k, s, outdir, "next.png")


if __name__ == "__main__":
	main()
