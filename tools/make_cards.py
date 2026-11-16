#!/usr/bin/env python3
# Generates the playing card graphics for the solitaire game (needs Pillow).
# Usage: python3 tools/make_cards.py
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, "..", "plugin")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SS = 4
CW, CH = 100, 140            # card size on a 1280x720 screen
SUITS = "♠♥♦♣"   # spades, hearts, diamonds, clubs
SUIT_KEYS = "shdc"
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
BLACK, RED = (20, 20, 28, 255), (200, 20, 30, 255)


def font(size, k):
	return ImageFont.truetype(FONT, int(size * k))


def blank(k, fill, outline, width=1.5):
	img = Image.new("RGBA", (int(CW * k), int(CH * k)), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	d.rounded_rectangle((0, 0, CW * k - 1, CH * k - 1), radius=8 * k, fill=fill, outline=outline, width=int(width * k))
	return img, d


def save(img, s, outdir, name):
	img.resize((int(round(CW * s)), int(round(CH * s))), Image.LANCZOS).save(os.path.join(outdir, name), optimize=True)


def face(rank, suit, k):
	color = RED if suit in (1, 2) else BLACK
	img, d = blank(k, (252, 252, 246, 255), (90, 90, 90, 255))
	text = RANKS[rank - 1]
	# index in the top strip: must stay readable when cards overlap
	d.text((7 * k, 14 * k), text, font=font(23, k), fill=color, anchor="lm")
	x = 7 + (30 if len(text) == 2 else 17)
	d.text((x * k, 14 * k), SUITS[suit], font=font(22, k), fill=color, anchor="lm")
	d.text(((CW - 8) * k, 14 * k), SUITS[suit], font=font(22, k), fill=color, anchor="rm")
	if rank > 10:
		d.rounded_rectangle((18 * k, 38 * k, (CW - 18) * k, (CH - 16) * k), radius=5 * k, outline=color, width=int(1.5 * k),
			fill=(255, 238, 200, 255) if suit in (1, 2) else (222, 230, 245, 255))
		d.text((CW / 2 * k, 76 * k), text, font=font(46, k), fill=color, anchor="mm")
		d.text((CW / 2 * k, 108 * k), SUITS[suit], font=font(24, k), fill=color, anchor="mm")
	else:
		d.text((CW / 2 * k, 86 * k), SUITS[suit], font=font(64 if rank == 1 else 50, k), fill=color, anchor="mm")
	return img


def back(k):
	img, d = blank(k, (250, 250, 250, 255), (90, 90, 90, 255))
	d.rounded_rectangle((5 * k, 5 * k, (CW - 5) * k - 1, (CH - 5) * k - 1), radius=5 * k, fill=(28, 60, 150, 255))
	step = 10
	for y in range(10, CH - 5, step):
		for i, x in enumerate(range(10, CW - 5, step)):
			if (x // step + y // step) % 2 == 0:
				d.regular_polygon((x * k, y * k, 3.2 * k), 4, rotation=45, fill=(120, 160, 240, 255))
	d.rounded_rectangle((5 * k, 5 * k, (CW - 5) * k - 1, (CH - 5) * k - 1), radius=5 * k, outline=(200, 215, 255, 255), width=int(1.5 * k))
	return img


def slot(k, symbol=None):
	img, d = blank(k, (0, 0, 0, 45), (255, 255, 255, 110), 2)
	if symbol:
		d.text((CW / 2 * k, CH / 2 * k), symbol, font=font(44, k), fill=(255, 255, 255, 90), anchor="mm")
	return img


def main():
	for name, s in (("hd", 1.0), ("fhd", 1.5)):
		outdir = os.path.join(PLUGIN, "images", name, "cards")
		os.makedirs(outdir, exist_ok=True)
		k = SS * s
		for suit in range(4):
			for rank in range(1, 14):
				save(face(rank, suit, k), s, outdir, "c%02d%s.png" % (rank, SUIT_KEYS[suit]))
		save(back(k), s, outdir, "back.png")
		save(slot(k), s, outdir, "slot.png")
		save(slot(k, "A"), s, outdir, "slot_f.png")
		save(slot(k, "↻"), s, outdir, "slot_s.png")


if __name__ == "__main__":
	main()
