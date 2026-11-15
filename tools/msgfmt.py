#!/usr/bin/env python3
# Minimal .po -> .mo compiler (single-line and continued msgid/msgstr entries).
import ast
import struct
import sys


def parse(path):
	entries, key, cur = {}, None, None
	msgid = msgstr = ""
	for raw in open(path, encoding="utf-8"):
		line = raw.strip()
		if line.startswith("msgid "):
			if cur == "str":
				entries[msgid] = msgstr
			msgid, cur = ast.literal_eval(line[6:]), "id"
		elif line.startswith("msgstr "):
			msgstr, cur = ast.literal_eval(line[7:]), "str"
		elif line.startswith('"'):
			if cur == "id":
				msgid += ast.literal_eval(line)
			elif cur == "str":
				msgstr += ast.literal_eval(line)
	if cur == "str":
		entries[msgid] = msgstr
	return entries


def write(entries, path):
	keys = sorted(k for k in entries if entries[k] or k == "")
	ids = [k.encode("utf-8") for k in keys]
	strs = [entries[k].encode("utf-8") for k in keys]
	n = len(keys)
	koff, voff = 28, 28 + 8 * n
	off = 28 + 16 * n
	ktab, vtab, blob = b"", b"", b""
	for i in ids:
		ktab += struct.pack("<II", len(i), off + len(blob))
		blob += i + b"\0"
	for s in strs:
		vtab += struct.pack("<II", len(s), off + len(blob))
		blob += s + b"\0"
	with open(path, "wb") as f:
		f.write(struct.pack("<IIIIIII", 0x950412DE, 0, n, koff, voff, 0, 0) + ktab + vtab + blob)


if __name__ == "__main__":
	write(parse(sys.argv[1]), sys.argv[2])
