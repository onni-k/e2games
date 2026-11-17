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


def bumper(d, x, y, r, k, lit=False):
	if lit:
		circle(d, x, y, r, k, fill=(255, 210, 60, 255), outline=(255, 255, 255, 255), width=int(2 * k))
		circle(d, x, y, r * 0.62, k, fill=(255, 245, 150, 255))
		circle(d, x, y, r * 0.28, k, fill=(255, 255, 255, 255))
	else:
		circle(d, x, y, r, k, fill=(150, 20, 40, 255), outline=(255, 255, 255, 255), width=int(2 * k))
		circle(d, x, y, r * 0.62, k, fill=(210, 60, 70, 255))
		circle(d, x, y, r * 0.28, k, fill=(255, 230, 230, 255))


def target(d, seg, k, fill, outline, pad=3.0):
	x, y, w, h = pe.segment_box(seg, pad)
	d.rounded_rectangle((x * k, y * k, (x + w) * k, (y + h) * k), radius=2 * k, fill=fill, outline=outline, width=int(k))


def table(n, s, outdir):
	spec = pe.TABLES[n]
	k = SS * s
	img = new(pe.W, pe.H, k, (0, 0, 0, 255))
	# playfield shape
	outline = pe.wall_polylines(n)[0]
	mask = Image.new("L", img.size, 0)
	ImageDraw.Draw(mask).polygon([(x * k, y * k) for x, y in outline], fill=255)
	grad = Image.new("RGBA", img.size)
	gd = ImageDraw.Draw(grad)
	(r1, g1, b1), (r2, g2, b2) = spec["colors"]
	for y in range(img.size[1]):
		t = y / float(img.size[1])
		gd.line((0, y, img.size[0], y), fill=(int(r1 + (r2 - r1) * t), int(g1 + (g2 - g1) * t), int(b1 + (b2 - b1) * t), 255))
	img.paste(grad, (0, 0), mask)
	d = ImageDraw.Draw(img)
	# decoration: star dots and guide arrows
	import random
	rnd = random.Random(7 + n)
	for _ in range(90):
		x, y = rnd.uniform(20, 360), rnd.uniform(40, 680)
		if math.hypot(x - pe.ARC_CX, y - pe.ARC_CY) > pe.ARC_R - 12 and y < pe.ARC_CY:
			continue
		r = rnd.uniform(0.5, 1.3)
		c = rnd.randint(110, 200)
		circle(d, x, y, r, k, fill=(c, c, 255, 255))
	for i in range(5):
		y = 600 - i * 85
		d.polygon([(390 * k, (y - 12) * k), (382 * k, y * k), (398 * k, y * k)], fill=(90, 110, 170, 255))
	text = tuple(min(255, c + 34) for c in spec["colors"][1]) + (255,)
	d.text((190 * k, 455 * k), "E2", font=ImageFont.truetype(FONT, int(54 * k)), fill=text, anchor="mm")
	d.text((190 * k, 498 * k), spec["name"].upper(), font=ImageFont.truetype(FONT, int(16 * k)), fill=text, anchor="mm")
	# drain marker
	d.rectangle((120 * k, 690 * k, 260 * k, 700 * k), fill=(90, 10, 20, 255))
	# gate (one way)
	for y in range(96, 208, 12):
		d.line((370 * k, y * k, 370 * k, (y + 6) * k), fill=(110, 140, 200, 255), width=int(2 * k))
	# slingshots
	for tri in (pe.SLING_L, pe.SLING_R):
		d.polygon([(x * k, y * k) for x, y in tri], fill=(120, 50, 10, 255))
		line(d, [tri[2], tri[0]], k, 5, (255, 150, 40, 255))
	# closed wall shapes are filled
	for poly in spec["walls"]:
		if len(poly) > 2:
			d.polygon([(x * k, y * k) for x, y in poly], fill=WALL_DARK + (255,))
	# rollover lanes: arrows and unlit lights
	for lane in spec["lanes"]:
		x1, y1, x2, y2 = lane
		cx = (x1 + x2) / 2.0
		d.polygon([((cx - 7) * k, (y1 + 10) * k), ((cx + 7) * k, (y1 + 10) * k), (cx * k, (y1 + 22) * k)], fill=(150, 120, 200, 255))
		lx, ly = pe.lane_light(lane)
		circle(d, lx, ly, 7, k, fill=(60, 40, 80, 255), outline=(170, 150, 210, 255), width=int(k))
	# saucers (dark holes)
	for x, y, r, ex, ey in spec["saucers"]:
		circle(d, x, y, r + 4, k, fill=(200, 170, 60, 255))
		circle(d, x, y, r, k, fill=(10, 8, 14, 255))
	# drop target slots (the targets themselves are separate images)
	for seg in spec["drops"]:
		target(d, seg, k, (8, 20, 18, 255), (60, 90, 80, 255), 4.0)
	# walls
	for poly in pe.wall_polylines(n):
		line(d, poly, k, 6, WALL_DARK + (255,))
	for poly in pe.wall_polylines(n):
		line(d, poly, k, 3, WALL + (255,))
	# stand-up targets (unlit)
	for seg in spec["standups"]:
		target(d, seg, k, (20, 90, 40, 255), (60, 160, 80, 255))
	# posts
	for x, y, r in spec["posts"]:
		circle(d, x, y, r, k, fill=(230, 230, 240, 255), outline=(90, 100, 140, 255), width=int(1.5 * k))
	for x, y, r in spec["bumpers"]:
		bumper(d, x, y, r, k)
	# flipper pivots base
	for x, y in pe.FLIP_PIVOTS:
		circle(d, x, y, 9, k, fill=WALL_DARK + (255,))
	done(img.convert("RGB"), k, s, "table%d.png" % (n + 1), outdir)


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
	radii = sorted(set([int(r) for t in pe.TABLES for x, y, r in t["bumpers"]]))
	for r in radii:
		size = 2 * r + 12
		img = new(size, size, k)
		d = ImageDraw.Draw(img)
		c = size / 2.0
		circle(d, c, c, r + 4, k, fill=(255, 240, 120, 110))
		img = img.filter(ImageFilter.GaussianBlur(2 * k))
		bumper(ImageDraw.Draw(img), c, c, r, k, lit=True)
		done(img, k, s, "bumper_lit_%d.png" % r, outdir)

	for n, spec in enumerate(pe.TABLES):
		for i, seg in enumerate(spec["standups"]):
			x, y, w, h = pe.segment_box(seg, 7)
			img = new(w, h, k)
			d = ImageDraw.Draw(img)
			local = ((seg[0][0] - x, seg[0][1] - y), (seg[1][0] - x, seg[1][1] - y))
			target(d, local, k, (80, 255, 120, 90), None, 5)
			img = img.filter(ImageFilter.GaussianBlur(1.5 * k))
			target(ImageDraw.Draw(img), local, k, (90, 255, 130, 255), (230, 255, 235, 255))
			done(img, k, s, "t%d_standup%d.png" % (n + 1, i), outdir)
		for i, seg in enumerate(spec["drops"]):
			x, y, w, h = pe.segment_box(seg, 6)
			img = new(w, h, k)
			local = ((seg[0][0] - x, seg[0][1] - y), (seg[1][0] - x, seg[1][1] - y))
			target(ImageDraw.Draw(img), local, k, (255, 140, 40, 255), (255, 230, 190, 255), 5)
			done(img, k, s, "t%d_drop%d.png" % (n + 1, i), outdir)

	img = new(20, 20, k)
	d = ImageDraw.Draw(img)
	circle(d, 10, 10, 9, k, fill=(255, 220, 120, 110))
	img = img.filter(ImageFilter.GaussianBlur(1.5 * k))
	circle(ImageDraw.Draw(img), 10, 10, 7, k, fill=(255, 235, 110, 255), outline=(255, 255, 230, 255), width=int(k))
	done(img, k, s, "lane_lit.png", outdir)

	for r in sorted(set(int(x[2]) for t in pe.TABLES for x in t["saucers"])):
		size = 2 * r + 16
		img = new(size, size, k)
		d = ImageDraw.Draw(img)
		c = size / 2.0
		circle(d, c, c, r + 7, k, fill=(255, 230, 90, 120))
		img = img.filter(ImageFilter.GaussianBlur(2 * k))
		d = ImageDraw.Draw(img)
		circle(d, c, c, r + 4, k, fill=(255, 235, 120, 255))
		circle(d, c, c, r, k, fill=(10, 8, 14, 255))
		done(img, k, s, "saucer_lit_%d.png" % r, outdir)

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
		for old in ("table.png", "bumper_lit.png", "target_lit.png"):
			if os.path.exists(os.path.join(outdir, old)):
				os.remove(os.path.join(outdir, old))
		for n in range(len(pe.TABLES)):
			table(n, s, outdir)
		flippers(s, outdir)
		ball(s, outdir)
		lights(s, outdir)
	icon()


if __name__ == "__main__":
	main()
