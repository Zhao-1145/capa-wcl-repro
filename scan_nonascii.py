# -*- coding: utf-8 -*-
"""scan_nonascii.py -- 找出稿件中所有非 ASCII 字符及其位置。"""
import collections, re, sys

SRC = "paper_CAPA_deep_estimation.tex"
txt = open(SRC, encoding="utf-8").read()
lines = txt.split("\n")

hits = collections.defaultdict(list)
for i, ln in enumerate(lines, 1):
    for m in re.finditer(r"[^\x00-\x7F]", ln):
        ch = m.group(0)
        hits[ch].append((i, m.start(), ln[max(0, m.start()-45):m.start()+45]))

print("非 ASCII 字符汇总（共 %d 种）" % len(hits))
for ch, occ in sorted(hits.items(), key=lambda kv: -len(kv[1])):
    print("\nU+%04X  '%s'   出现 %d 次" % (ord(ch), ch, len(occ)))
    for (i, col, ctx) in occ[:4]:
        print("   line %-4d col %-4d  ...%s..." % (i, col, ctx.replace("\n", " ")))
if not hits:
    print("  稿件为纯 ASCII。")
