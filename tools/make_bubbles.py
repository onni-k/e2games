#!/usr/bin/env python3
# Generates the bubble shooter graphics (needs Pillow).
# Usage: python3 tools/make_bubbles.py
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, "..", "plugin")
sys.path.insert(0, PLUGIN)
import bubble_engine as be  # noqa: E402

SS = 4
BORDER = 8                   # frame around the field
ARROW_SIZE = 140
ARROW_STEP = 0.05            # radians between arrow frames
# red, yellow, green, blue, purple, cyan
COLORS = ((230, 40, 50), (250, 205, 30), (60, 200, 70), (40, 110, 240), (170, 60, 220), (30, 210, 220))


def save(img, k, s, outdir, name):
	w, h = int(round(img.size[0] / k * s)), int(round(img.size[1] / k * s))
	img.resize((w, h), Image.LANCZOS).save(os.path.join(outdir, name), optimize=True)


def circle(d, x, y, r, k, **kw):
	d.ellipse(((x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k), **kw)


def bubble(color, k):
	size = be.D
	img = Image.new("RGBA", (int(size * k), int(size * k)), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	c = size / 2.0
	r0, g0, b0 = color
	for i in range(30):
		t = i / 29.0
		r = (be.R - 1) * (1 - t * 0.8)
		mix = 0.25 + 0.75 * t
		col = (int(r0 * (0.55 + 0.45 * mix) + 255 * 0.35 * t * t), int(g0 * (0.55 + 0.45 * mix) + 255 * 0.35 * t * t), int(b0 * (0.55 + 0.45 * mix) + 255 * 0.35 * t * t))
		col = tuple(min(255, v) for v in col)
		circle(d, c - be.R * 0.22 * t, c - be.R * 0.25 * t, r, k, fill=col + (255,))
	circle(d, c - be.R * 0.35, c - be.R * 0.38, be.R * 0.22, k, fill=(255, 255, 255, 200))
	circle(d, c, c, be.R - 1, k, outline=(int(r0 * 0.4), int(g0 * 0.4), int(b0 * 0.4), 255), width=int(1.2 * k))
	return img


def pop(k):
	size = be.D
	img = Image.new("RGBA", (int(size * k), int(size * k)), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	c = size / 2.0
	for i in range(10):
		a = i * math.pi / 5
		x1, y1 = c + math.cos(a) * 8, c + math.sin(a) * 8
		x2, y2 = c + math.cos(a) * (be.R - 2), c + math.sin(a) * (be.R - 2)
		d.line((x1 * k, y1 * k, x2 * k, y2 * k), fill=(255, 255, 220, 255), width=int(3 * k))
	circle(d, c, c, 6, k, fill=(255, 255, 255, 255))
	return img


def field(k):
	w, h = be.W + 2 * BORDER, be.H + 2 * BORDER
	img = Image.new("RGBA", (int(w * k), int(h * k)), (0, 0, 0, 255))
	d = ImageDraw.Draw(img)
	d.rounded_rectangle((0, 0, w * k - 1, h * k - 1), radius=10 * k, fill=(70, 90, 140, 255))
	d.rectangle((BORDER * k, BORDER * k, (w - BORDER) * k, (h - BORDER) * k), fill=(12, 18, 44, 255))
	# soft vertical gradient
	for y in range(int(BORDER * k), int((h - BORDER) * k)):
		t = (y / k - BORDER) / be.H
		d.line((BORDER * k, y, (w - BORDER) * k, y), fill=(int(12 + 18 * t), int(18 + 10 * t), int(44 + 40 * t), 255))
	# danger line
	y = (BORDER + be.DEAD_Y) * k
	for x in range(0, int(be.W), 16):
		d.line(((BORDER + x) * k, y, (BORDER + x + 9) * k, y), fill=(230, 60, 60, 255), width=int(2 * k))
	# launcher base
	sx, sy = be.SHOOTER
	circle(d, BORDER + sx, BORDER + sy, be.R + 9, k, fill=(40, 52, 90, 255), outline=(120, 150, 210, 255), width=int(2 * k))
	nx, ny = be.NEXT_POS
	circle(d, BORDER + nx, BORDER + ny, be.R + 5, k, fill=(30, 38, 70, 255), outline=(90, 110, 170, 255), width=int(1.5 * k))
	return img


def arrow(angle, k):
	size = ARROW_SIZE
	img = Image.new("RGBA", (int(size * k), int(size * k)), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	c = size / 2.0
	dx, dy = math.sin(angle), -math.cos(angle)
	nx, ny = -dy, dx
	base, tip = be.R + 6, size / 2.0 - 3
	pts = [(c + dx * base + nx * 7, c + dy * base + ny * 7), (c + dx * (tip - 14) + nx * 7, c + dy * (tip - 14) + ny * 7),
		(c + dx * (tip - 14) + nx * 13, c + dy * (tip - 14) + ny * 13), (c + dx * tip, c + dy * tip),
		(c + dx * (tip - 14) - nx * 13, c + dy * (tip - 14) - ny * 13), (c + dx * (tip - 14) - nx * 7, c + dy * (tip - 14) - ny * 7),
		(c + dx * base - nx * 7, c + dy * base - ny * 7)]
	d.polygon([(x * k, y * k) for x, y in pts], fill=(255, 210, 60, 255), outline=(120, 80, 10, 255))
	return img


def dot(k):
	img = Image.new("RGBA", (int(10 * k), int(10 * k)), (0, 0, 0, 0))
	circle(ImageDraw.Draw(img), 5, 5, 3.5, k, fill=(255, 255, 255, 210))
	return img


def main():
	frames = int(round(2 * be.MAX_ANGLE / ARROW_STEP)) + 1
	for name, s in (("hd", 1.0), ("fhd", 1.5)):
		outdir = os.path.join(PLUGIN, "images", name, "bubble")
		os.makedirs(outdir, exist_ok=True)
		k = SS * s
		for i, color in enumerate(COLORS):
			save(bubble(color, k), k, s, outdir, "b%d.png" % i)
		save(pop(k), k, s, outdir, "pop.png")
		save(field(k).convert("RGB"), k, s, outdir, "field.png")
		save(dot(k), k, s, outdir, "dot.png")
		for i in range(frames):
			save(arrow(-be.MAX_ANGLE + i * ARROW_STEP, k), k, s, outdir, "arrow%02d.png" % i)
	print("arrow frames:", frames)


if __name__ == "__main__":
	main()
