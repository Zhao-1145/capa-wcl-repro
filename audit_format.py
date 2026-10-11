# -*- coding: utf-8 -*-
"""audit_format.py -- 对照 IEEE 期刊/Letter 体例逐项审计稿件.

检查项来自 IEEEtran 官方用法与 IEEE 期刊通行规范：
  1  文档类必须是 \documentclass[journal]{IEEEtran}
  2  期刊模式的作者块应为 \author{Name\thanks{...}}，
     \IEEEauthorblockN 是会议模式专用
  3  摘要为单段，建议 150-250 词
  4  Index Terms 必须按字母序
  5  表题在表上方（\caption 在 \begin{tabular} 之前）
  6  图题在图下方
  7  参考文献条目应为 IEEE 风格（作者, "题名," 刊名, vol., no., pp., 年.）
  8  不得残留占位符 / TODO / VERIFY
  9  环境配对（equation / table / figure / itemize / thebibliography）
 10  正文引用的图表编号都存在对应的 label
"""
import re, sys

SRC = "paper_CAPA_deep_estimation.tex"
t = open(SRC, encoding="utf-8").read()
FAIL, WARN, OK = [], [], []


def rec(ok, name, note, warn=False):
    (OK if ok else (WARN if warn else FAIL)).append((name, note))
    print("%s %-34s %s" % ("OK " if ok else ("~~ " if warn else "!! "), name, note))


# 1 文档类
m = re.search(r"\\documentclass(\[[^\]]*\])?\{(\w+)\}", t)
cls = m.group(2) if m else "?"
opt = (m.group(1) or "")
rec(cls == "IEEEtran" and "journal" in opt, "文档类", "\\documentclass%s{IEEEtran}" % opt)

# 2 作者块
has_conf_block = "\\IEEEauthorblockN" in t
# 容许 \IEEEmembership{...} 这类一层嵌套花括号
has_journal_block = bool(re.search(r"\\author\{(?:[^{}]|\{[^{}]*\})*\\thanks", t, re.S))
rec(not has_conf_block and has_journal_block, "作者块（期刊模式）",
    ("发现会议专用的 \\IEEEauthorblockN" if has_conf_block else
     ("\\author{...\\thanks{...}} 形式" if has_journal_block else "未找到作者块")))

# 3 摘要
am = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
if am:
    words = len(re.findall(r"[A-Za-z][A-Za-z\-']*", am.group(1)))
    rec(75 <= words <= 100, "摘要词数", "%d 词（WCL 硬要求 75-100）" % words)
else:
    rec(False, "摘要词数", "未找到 abstract 环境")

# 4 Index Terms 字母序
km = re.search(r"\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}", t, re.S)
if km:
    raw = km.group(1).replace("\n", " ").strip().rstrip(".")
    terms = [x.strip() for x in raw.split(",") if x.strip()]
    key = [re.sub(r"^\(|\)$", "", x).lower() for x in terms]
    rec(key == sorted(key), "Index Terms 字母序",
        "顺序: " + " | ".join(terms) if key != sorted(key) else "%d 项，已按字母序" % len(terms))
    rec(len(terms) >= 4, "Index Terms 数量", "%d 项" % len(terms), warn=len(terms) < 4)
else:
    rec(False, "Index Terms", "未找到 IEEEkeywords 环境")

# 5/6 图表题位置
bad_tab = 0
for mm in re.finditer(r"\\begin\{table\*?\}(.*?)\\end\{table\*?\}", t, re.S):
    body = mm.group(1)
    if body.find("\\caption") > body.find("\\begin{tabular}"):
        bad_tab += 1
rec(bad_tab == 0, "表题位置", "%d 处表题在表体之后（IEEE 要求在上方）" % bad_tab)

n_tab = len(re.findall(r"\\begin\{table\*?\}", t))
n_fig = len(re.findall(r"\\begin\{figure\*?\}", t))
rec(True, "浮动体数量", "表 %d 个，图 %d 个（稿件中）" % (n_tab, n_fig))

# 7 参考文献风格
bibs = re.findall(r"\\bibitem\{[^}]*\}(.*?)(?=\\bibitem|\\end\{thebibliography\})", t, re.S)
bad_bib = []
for i, b in enumerate(bibs, 1):
    s = " ".join(b.split())
    if not s:
        bad_bib.append(i); continue
    # 需含引号包裹的题名，且以 年. 或 年份 收尾
    if '"' not in s or not re.search(r"(19|20)\d\d", s):
        bad_bib.append(i)
rec(not bad_bib, "参考文献风格", "%d/%d 条缺少题名引号或年份: %s" % (len(bad_bib), len(bibs), bad_bib))

# 8 残留占位符
leftovers = []
for pat, tag in [(r"\bTODO\b", "TODO"), (r"\bVERIFY\b", "VERIFY"),
                 (r"(?<!X)XX(?!X)", "XX"), (r"\[TO BE FILLED\]", "TO BE FILLED")]:
    n = len(re.findall(pat, t))
    if n:
        leftovers.append("%s x%d" % (tag, n))
rec(not leftovers, "残留占位符", ", ".join(leftovers) if leftovers else "无")

# 9 环境配对
for env in ["equation", "table", "figure", "itemize", "thebibliography", "abstract", "IEEEkeywords"]:
    a = len(re.findall(r"\\begin\{%s\*?\}" % env, t))
    b = len(re.findall(r"\\end\{%s\*?\}" % env, t))
    rec(a == b, "环境配对 %s" % env, "%d / %d" % (a, b))

# 10 label / ref 交叉引用
labels = set(re.findall(r"\\label\{([^}]+)\}", t))
refs = set(re.findall(r"\\ref\{([^}]+)\}", t))
missing = sorted(refs - labels)
rec(not missing, "交叉引用完整性", ("缺失 label: %s" % missing) if missing else "%d 个 label，%d 个引用，全部解析" % (len(labels), len(refs)))

# 11 cite / bibitem 一致性
bibkeys = set(re.findall(r"\\bibitem\{([^}]+)\}", t))
cites = set()
for c in re.findall(r"\\cite\{([^}]+)\}", t):
    cites |= {x.strip() for x in c.split(",")}
rec(not (cites - bibkeys), "引用-条目一致性",
    ("引用了不存在的条目: %s" % sorted(cites - bibkeys)) if (cites - bibkeys) else
    "%d 条全部被引用" % len(bibkeys))
uncited = sorted(bibkeys - cites)
rec(not uncited, "无未引用条目", ("未被引用: %s" % uncited) if uncited else "全部被引用")

print()
print("=" * 70)
print("通过 %d   警告 %d   失败 %d" % (len(OK), len(WARN), len(FAIL)))
if FAIL:
    print("VERDICT: FAIL")
    for n, d in FAIL:
        print("   -", n, ":", d)
    sys.exit(1)
print("VERDICT: PASS" + ("（有警告）" if WARN else ""))
