#!/usr/bin/env python3
# Generates all E2games pinball graphics from the engine geometry (needs Pillow).
# Usage: python3 tools/make_assets.py
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, "..", "plugin")
sys.path.insert(0, PLUGIN)
import pinball_engine as pe  # noqa: E402

SS = 4                      # supersampling
FRAMES = 9                  # flipper animation frames
FLIP_BOX = (80, 78)         # flipper image size in table units
FLIP_ORG = (9, 39)          # pivot inside the left flipper image
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

WALL = (150, 215, 255)
WALL_DARK = (40, 70, 120)


def new(w, h, k, color=(0, 0, 0, 0)):
	return Image.new("RGBA", (int(round(w * k)), int(round(h * k))), color)


def done(img, k, s, name, outdir):
	w, h = int(round(img.size[0] / k * s)), int(round(img.size[1] / k * s))
	img.resize((w, h), Image.LANCZOS).save(os.path.join(outdir, name), optimize=True)


def line(d, pts, k, width, fill):
	p = [(x * k, y * k) for x, y in pts]
	d.line(p, fill=fill, width=int(width * k), joint="curve")
	r = width * k / 2.0
	for x, y in (p[0], p[-1]):
		d.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def circle(d, x, y, r, k, **kw):
	d.ellipse(((x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k), **kw)


def table(s, outdir):
	k = SS * s
	img = new(pe.W, pe.H, k, (0, 0, 0, 255))
	# playfield shape
	outline = pe.wall_polylines()[0]
	mask = Image.new("L", img.size, 0)
	ImageDraw.Draw(mask).polygon([(x * k, y * k) for x, y in outline], fill=255)
	grad = Image.new("RGBA", img.size)
	gd = ImageDraw.Draw(grad)
	for y in range(img.size[1]):
		t = y / float(img.size[1])
		gd.line((0, y, img.size[0], y), fill=(int(14 + 40 * t), int(18 + 6 * t), int(64 + 30 * t), 255))
	img.paste(grad, (0, 0), mask)
	d = ImageDraw.Draw(img)
	# decoration: star dots and guide arrows
	import random
	rnd = random.Random(7)
	for _ in range(90):
		x, y = rnd.uniform(20, 360), rnd.uniform(40, 680)
		if math.hypot(x - pe.ARC_CX, y - pe.ARC_CY) > pe.ARC_R - 12 and y < pe.ARC_CY:
			continue
		r = rnd.uniform(0.5, 1.3)
		c = rnd.randint(90, 190)
		circle(d, x, y, r, k, fill=(c, c, 255, 255))
	for i in range(5):
		y = 600 - i * 85
		d.polygon([(390 * k, (y - 12) * k), (382 * k, y * k), (398 * k, y * k)], fill=(70, 90, 150, 255))
	try:
		f = ImageFont.truetype(FONT, int(54 * k))
		d.text((190 * k, 455 * k), "E2", font=f, fill=(46, 44, 120, 255), anchor="mm")
		f2 = ImageFont.truetype(FONT, int(17 * k))
		d.text((190 * k, 498 * k), "PINBALL", font=f2, fill=(60, 56, 140, 255), anchor="mm")
	except Exception:
		pass
	# drain marker
	d.rectangle((120 * k, 690 * k, 260 * k, 700 * k), fill=(90, 10, 20, 255))
	# gate (one way)
	for y in range(96, 208, 12):
		d.line((370 * k, y * k, 370 * k, (y + 6) * k), fill=(110, 140, 200, 255), width=int(2 * k))
	# slingshots
	for tri in (pe.SLING_L, pe.SLING_R):
		d.polygon([(x * k, y * k) for x, y in tri], fill=(120, 50, 10, 255))
		line(d, [tri[2], tri[0]], k, 5, (255, 150, 40, 255))
	d.polygon([(x * k, y * k) for x, y in pe.LEFT_BUMP], fill=(40, 70, 120, 255))
	# walls
	for poly in pe.wall_polylines():
		line(d, poly, k, 6, WALL_DARK + (255,))
	for poly in pe.wall_polylines():
		line(d, poly, k, 3, WALL + (255,))
	# targets (unlit)
	for y1, y2 in pe.TARGETS:
		d.rounded_rectangle((11 * k, y1 * k, 17 * k, y2 * k), radius=2 * k, fill=(20, 90, 40, 255), outline=(60, 160, 80, 255), width=int(k))
	# bumpers (unlit)
	for x, y, r in pe.BUMPERS:
		circle(d, x, y, r, k, fill=(150, 20, 40, 255), outline=(255, 255, 255, 255), width=int(2 * k))
		circle(d, x, y, r * 0.62, k, fill=(210, 60, 70, 255))
		circle(d, x, y, r * 0.28, k, fill=(255, 230, 230, 255))
	# flipper pivots base
	for x, y in pe.FLIP_PIVOTS:
		circle(d, x, y, 9, k, fill=WALL_DARK + (255,))
	done(img.convert("RGB"), k, s, "table.png", outdir)


def capsule(d, k, ox, oy, a, sign, r1, r2, col):
	"""Tapered capsule from the pivot (radius r1) to the tip (radius r2)."""
	dx, dy = sign * math.cos(a), math.sin(a)
	tx, ty = ox + dx * pe.FLIP_LEN, oy + dy * pe.FLIP_LEN
	nx, ny = -dy, dx
	d.polygon([(x * k, y * k) for x, y in (
		(ox + nx * r1, oy + ny * r1), (tx + nx * r2, ty + ny * r2),
		(tx - nx * r2, ty - ny * r2), (ox - nx * r1, oy - ny * r1))], fill=col)
	circle(d, ox, oy, r1, k, fill=col)
	circle(d, tx, ty, r2, k, fill=col)


def flippers(s, outdir):
	k = SS * s
	for side, sign in (("L", 1), ("R", -1)):
		ox = FLIP_ORG[0] if sign > 0 else FLIP_BOX[0] - FLIP_ORG[0]
		for i in range(FRAMES):
			a = pe.FLIP_REST + (pe.FLIP_UP - pe.FLIP_REST) * i / (FRAMES - 1)
			img = new(FLIP_BOX[0], FLIP_BOX[1], k)
			d = ImageDraw.Draw(img)
			capsule(d, k, ox, FLIP_ORG[1], a, sign, 8.0, 5.0, (255, 235, 200, 255))
			capsule(d, k, ox, FLIP_ORG[1], a, sign, 6.4, 3.4, (240, 70, 30, 255))
			circle(d, ox, FLIP_ORG[1], 3, k, fill=(255, 255, 255, 255))
			done(img, k, s, "flip%s%d.png" % (side, i), outdir)


def ball(s, outdir):
	k = SS * s
	size = 2 * pe.R + 2
	img = new(size, size, k)
	d = ImageDraw.Draw(img)
	c = size / 2.0
	for i in range(24):
		t = i / 23.0
		r = pe.R * (1 - t * 0.85)
		g = int(120 + 135 * t)
		circle(d, c - pe.R * 0.25 * t, c - pe.R * 0.3 * t, r, k, fill=(g, g, min(255, g + 10), 255))
	done(img, k, s, "ball.png", outdir)


def lights(s, outdir):
	k = SS * s
	r = pe.BUMPERS[0][2]
	size = 2 * r + 12
	img = new(size, size, k)
	d = ImageDraw.Draw(img)
	c = size / 2.0
	circle(d, c, c, r + 4, k, fill=(255, 240, 120, 110))
	img = img.filter(ImageFilter.GaussianBlur(2 * k))
	d = ImageDraw.Draw(img)
	circle(d, c, c, r, k, fill=(255, 210, 60, 255), outline=(255, 255, 255, 255), width=int(2 * k))
	circle(d, c, c, r * 0.62, k, fill=(255, 245, 150, 255))
	circle(d, c, c, r * 0.28, k, fill=(255, 255, 255, 255))
	done(img, k, s, "bumper_lit.png", outdir)

	y1, y2 = pe.TARGETS[0]
	img = new(14, y2 - y1 + 8, k)
	d = ImageDraw.Draw(img)
	d.rounded_rectangle((2 * k, 2 * k, 12 * k, (y2 - y1 + 6) * k), radius=4 * k, fill=(80, 255, 120, 90))
	img = img.filter(ImageFilter.GaussianBlur(1.5 * k))
	d = ImageDraw.Draw(img)
	d.rounded_rectangle((4 * k, 4 * k, 10 * k, (y2 - y1 + 4) * k), radius=2 * k, fill=(90, 255, 130, 255), outline=(230, 255, 235, 255), width=int(k))
	done(img, k, s, "target_lit.png", outdir)

	for side, tri in (("L", pe.SLING_L), ("R", pe.SLING_R)):
		x0 = min(p[0] for p in tri) - 4
		y0 = min(p[1] for p in tri) - 4
		w = max(p[0] for p in tri) - x0 + 4
		h = max(p[1] for p in tri) - y0 + 4
		img = new(w, h, k)
		d = ImageDraw.Draw(img)
		line(d, [(tri[2][0] - x0, tri[2][1] - y0), (tri[0][0] - x0, tri[0][1] - y0)], k, 6, (255, 255, 190, 255))
		done(img, k, s, "sling%s_lit.png" % side, outdir)

	img = new(22, 30, k)
	d = ImageDraw.Draw(img)
	d.rounded_rectangle((1 * k, 0, 21 * k, 8 * k), radius=2 * k, fill=(230, 60, 50, 255))
	for i in range(4):
		y = (11 + i * 5) * k
		d.line((4 * k, y, 18 * k, y + 3 * k), fill=(200, 200, 210, 255), width=int(2 * k))
	done(img, k, s, "plunger.png", outdir)


def icon():
	k = SS
	img = new(100, 40, k)
	d = ImageDraw.Draw(img)
	d.rounded_rectangle((0, 0, 100 * k - 1, 40 * k - 1), radius=7 * k, fill=(22, 24, 80, 255), outline=WALL + (255,), width=int(1.5 * k))
	circle(d, 20, 20, 9, k, fill=(210, 60, 70, 255), outline=(255, 255, 255, 255), width=int(1.5 * k))
	circle(d, 17, 17, 3, k, fill=(255, 220, 220, 255))
	f = ImageFont.truetype(FONT, int(13 * k))
	d.text((65 * k, 20 * k), "E2games", font=f, fill=(255, 255, 255, 255), anchor="mm")
	img.resize((100, 40), Image.LANCZOS).save(os.path.join(PLUGIN, "plugin.png"))


def main():
	for name, s in (("hd", 1.0), ("fhd", 1.5)):
		outdir = os.path.join(PLUGIN, "images", name)
		os.makedirs(outdir, exist_ok=True)
		table(s, outdir)
		flippers(s, outdir)
		ball(s, outdir)
		lights(s, outdir)
	icon()


if __name__ == "__main__":
	main()
