#!/usr/bin/env python3
# Generates the sudoku graphics (needs Pillow).
# Usage: python3 tools/make_sudoku.py
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, "..", "plugin")
sys.path.insert(0, PLUGIN)
import sudoku_engine as se  # noqa: E402

SS = 4
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_USER = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
PAPER = (246, 244, 236)
SAME = (255, 236, 150)
STYLES = {                      # name: (digit colour, font)
	"given": ((20, 24, 40), FONT),
	"user": ((30, 90, 210), FONT_USER),
	"bad": ((215, 30, 40), FONT_USER),
	"hint": ((20, 140, 60), FONT_USER),
}


def save(img, k, s, outdir, name):
	w, h = int(round(img.size[0] / k * s)), int(round(img.size[1] / k * s))
	img.resize((w, h), Image.LANCZOS).save(os.path.join(outdir, name), optimize=True)


def board(k):
	n = se.BOARD
	img = Image.new("RGB", (int(n * k), int(n * k)), (20, 24, 40))
	d = ImageDraw.Draw(img)
	for i in range(81):
		x, y = se.cell_origin(i)
		shade = PAPER if (se.BOX[i] % 2 == 0) else (236, 236, 228)
		d.rectangle((x * k, y * k, (x + se.CELL) * k - 1, (y + se.CELL) * k - 1), fill=shade)
	return img


def digit(n, style, same, k):
	color, font = STYLES[style]
	img = Image.new("RGBA", (int(se.CELL * k), int(se.CELL * k)), SAME + (255,) if same else (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	f = ImageFont.truetype(font, int(40 * k))
	d.text((se.CELL / 2.0 * k, se.CELL / 2.0 * k + 1.5 * k), str(n), font=f, fill=color + (255,), anchor="mm")
	return img


def cursor(k):
	img = Image.new("RGBA", (int((se.CELL + 6) * k), int((se.CELL + 6) * k)), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	d.rounded_rectangle((0, 0, (se.CELL + 6) * k - 1, (se.CELL + 6) * k - 1), radius=6 * k, outline=(255, 170, 0, 255), width=int(5 * k))
	return img


def same_empty(k):
	return Image.new("RGBA", (int(se.CELL * k), int(se.CELL * k)), SAME + (255,))


def main():
	for name, s in (("hd", 1.0), ("fhd", 1.5)):
		outdir = os.path.join(PLUGIN, "images", name, "sudoku")
		os.makedirs(outdir, exist_ok=True)
		k = SS * s
		save(board(k), k, s, outdir, "board.png")
		save(cursor(k), k, s, outdir, "cursor.png")
		for style in STYLES:
			for n in range(1, 10):
				save(digit(n, style, False, k), k, s, outdir, "%s%d.png" % (style, n))
				save(digit(n, style, True, k), k, s, outdir, "%s%d_same.png" % (style, n))


if __name__ == "__main__":
	main()
