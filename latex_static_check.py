# -*- coding: utf-8 -*-
"""latex_static_check.py -- 在无编译器环境下做严格静态校验.

模拟编译器会报出的错误：
  1  花括号平衡
  2  \begin/\end 按栈配对（顺序错误也会被抓到）
  3  数学模式 $ 配对（跳过 \$ 与 verbatim）
  4  所有 \ref/\eqref 都有对应 \label
  5  所有 \cite 键都有 \bibitem
  6  所有 \includegraphics 文件真实存在
  7  表格列数与 tabular 声明一致
  8  未转义的特殊字符 & % # _ （数学/表格环境外）
  9  IEEEtran 常用命令拼写
 10  注释掉的 \begin 不会污染配对计数
"""
import os, re, sys, glob

SRC = "paper_CAPA_deep_estimation.tex"
raw = open(SRC, encoding="utf-8").read()
FAIL, OK = [], []


def rec(ok, name, note):
    (OK if ok else FAIL).append((name, note))
    print("%s %-32s %s" % ("OK " if ok else "!! ", name, note))


# ---- 去掉注释行（保留转义 \%）与 verbatim ----
nocom = []
for ln in raw.split("\n"):
    s = re.sub(r"(?<!\\)%.*$", "", ln)
    nocom.append(s)
body = "\n".join(nocom)
body = re.sub(r"\\begin\{verbatim\}.*?\\end\{verbatim\}", "", body, flags=re.S)

# 1 花括号
depth = 0; bad = -1
for i, ch in enumerate(body):
    if ch == "{" and (i == 0 or body[i-1] != "\\"):
        depth += 1
    elif ch == "}" and (i == 0 or body[i-1] != "\\"):
        depth -= 1
        if depth < 0 and bad < 0:
            bad = i
rec(depth == 0 and bad < 0, "花括号平衡",
    "最终深度 %d%s" % (depth, "" if bad < 0 else "，首个多余 } 位于偏移 %d" % bad))

# 2 环境栈
stack, errs = [], []
for m in re.finditer(r"\\(begin|end)\{([^}]+)\}", body):
    kind, env = m.group(1), m.group(2)
    if kind == "begin":
        stack.append((env, m.start()))
    else:
        if not stack:
            errs.append("多余的 \\end{%s}" % env)
        elif stack[-1][0] != env:
            errs.append("\\end{%s} 与栈顶 \\begin{%s} 不匹配" % (env, stack[-1][0]))
            stack.pop()
        else:
            stack.pop()
if stack:
    errs.append("未闭合: " + ", ".join(e for e, _ in stack))
rec(not errs, "环境栈配对", "; ".join(errs) if errs else "全部配对")

# 3 数学模式 $ 配对
dollars = len(re.findall(r"(?<!\\)\$", re.sub(r"\$\$", "", body)))
rec(dollars % 2 == 0, "数学模式 $ 配对", "%d 个 $（应为偶数）" % dollars)

# 4 ref / label
labels = set(re.findall(r"\\label\{([^}]+)\}", body))
refs = set()
for c in re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", body):
    refs.add(c.strip())
miss = sorted(refs - labels)
rec(not miss, "交叉引用", "缺失 label: %s" % miss if miss else "%d 个引用全部解析" % len(refs))

# 5 cite / bibitem
bibs = set(re.findall(r"\\bibitem\{([^}]+)\}", body))
cites = set()
for c in re.findall(r"\\cite\{([^}]+)\}", body):
    cites |= {x.strip() for x in c.split(",")}
miss = sorted(cites - bibs)
rec(not miss, "引用-条目", "引用不存在的条目: %s" % miss if miss else "%d 条全部存在" % len(bibs))

# 6 图片文件
figs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", body)
missing = []
EXTS = ["", ".pdf", ".png", ".jpg", ".jpeg", ".eps", ".mps"]
for f in figs:
    found = False
    for cand in (f, os.path.join("figs", f), os.path.join("..", "figs", f)):
        for e in EXTS:
            if os.path.exists(cand + e):
                found = True
                break
        if found:
            break
    if not found:
        missing.append(f)
rec(not missing, "图片文件存在", "缺失: %s" % missing if missing else "%d 个图片全部找到" % len(figs))

# 7 表格列数
badtab = []
for m in re.finditer(r"\\begin\{tabular\}\{((?:[^{}]|\{[^{}]*\})*)\}(.*?)\\end\{tabular\}", body, re.S):
    spec, content = m.group(1), m.group(2)
    # 第十轮：列声明可能含 @{...}（去首尾列距），须先剥离再数列，否则会被误判为 0 列。
    _spec = re.sub(r"@\{(?:[^{}]|\{[^{}]*\})*\}", "", spec)
    ncol = len(re.findall(r"[lcrp]", re.sub(r"\|", "", _spec)))
    for row in re.findall(r"^(.*?)\\\\\s*$", content, re.M):
        row = re.sub(r"\\(?:hline|toprule|midrule|bottomrule|cmidrule\([^)]*\)\{[^}]*\})", "", row).strip()
        if not row or row.startswith("\\multicolumn") and row.count("&") == 0:
            continue
        n = row.count("&") + 1
        if n != ncol and "\\multicolumn" not in row:
            badtab.append("列数 %d != 声明 %d : %s" % (n, ncol, row[:60]))
rec(not badtab, "表格列数一致", "; ".join(badtab[:3]) if badtab else "全部一致")

# 8 未转义特殊字符（表格/数学外）
stripped = re.sub(r"\$[^$]*\$", "", body)
stripped = re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", "", stripped, flags=re.S)
# 文件名里的下划线是合法的，先去掉 includegraphics 的参数再检查
stripped = re.sub(r"\\includegraphics(?:\[[^\]]*\])?\{[^}]*\}", "", stripped)
stripped = re.sub(r"\\begin\{equation\}.*?\\end\{equation\}", "", stripped, flags=re.S)
badchar = []
for ln in stripped.split("\n"):
    s = re.sub(r"\\(?:[a-zA-Z]+|.)", "", ln)
    for ch in "&#_":
        if ch in s:
            badchar.append("%s in: %s" % (ch, ln.strip()[:70]))
rec(not badchar, "特殊字符转义", "; ".join(badchar[:3]) if badchar else "无未转义的 & # _")

# 9 已知 IEEEtran 命令
known = {"IEEEauthorblockN","IEEEauthorblockA","IEEEkeywords","IEEEPARstart","IEEEeqnarray",
         "maketitle","thanks","author","title","documentclass","usepackage","graphicspath",
         "IEEEmembership","pagestyle","IEEEpeerreviewmaketitle",
         "hyphenation","caption","label","ref","eqref","cite","bibitem","begin","end",
         "includegraphics","centering","hline","textbf","emph","textit","item","multicolumn",
         "resizebox",
         "columnwidth","textwidth","triangleq","jmath","mathbf","mathrm","mathcal","bm",
         "Re","Im","approx","times","leq","geq","cdot","left","right","frac","sqrt","sum",
         "int","exp","log","max","min","s","t","d","partial","phi","theta","lambda","alpha",
         "sigma","mu","Delta","Omega","pi","qquad","quad",";",",","!"," ","\\","%","$","{","}",
         "setlength","itemsep","parsep","textfloatsep","floatsep","intextsep",
         "abovecaptionskip","belowcaptionskip","abovedisplayskip","belowdisplayskip",
         "parskip","parindent","bibsep",
         "footnotesize","small","noindent","vspace","hspace",
         "langle","rangle","|","cdot","text","mathrm","mathbb","color","vspace","small","footnotesize",
         # standard LaTeX / amsmath commands that are legitimately undefined in this file
         "sin","cos","tan","log","exp","hat","widehat","bar","tilde","vec","dot","ddot",
         "propto","sim","simeq","ll","gg","in","notin","subset","cup","cap","forall","exists",
         "section","subsection","subsubsection","paragraph","noindent","indent","newline","linebreak",
         "tau","upsilon","varepsilon","varphi","varrho","vartheta","ell","hbar","imath",
         "operatorname","limits","nolimits","textstyle","displaystyle","nonumber","notag",
         "cite","Cref","cref","SI","si","unit","SIrange","num","ang","qty",
         "toprule","midrule","bottomrule","cmidrule","multicolumn","hline","cline",
         "includegraphics","graphicspath","DeclareMathOperator","newcommand","renewcommand",
         "def","ifx","else","fi","RequirePackage","PassOptionsToPackage","AtBeginDocument",
         "pm","mp","times","cdot","le","ge","leq","geq",
         "psi","phi","theta","alpha","beta","gamma","lambda","mu","sigma","tau","omega",
         "jmath","bm","mathcal","mathrm","triangleq","langle","rangle","approx","propto","in","sim",
         "setlength","addtolength","tabcolsep","arraystretch","baselineskip","columnsep",
         "textfloatsep","floatsep","intextsep","abovecaptionskip","belowcaptionskip",
         "abovedisplayskip","belowdisplayskip","abovedisplayshortskip","belowdisplayshortskip",
         "textwidth","linewidth","hspace","vspace","smallskip","medskip","bigskip",
         "renewcommand","providecommand","ensuremath","mbox","hbox","vbox","parbox",
         "IEEEeqnarray","IEEEyessubnumber","IEEEyesnumber","IEEEsplit","dagger","ddagger","FloatBarrier","enlargethispage","scriptsize","setcounter"}
cmds = set(re.findall(r"\\([a-zA-Z]+)", body))
unknown = sorted(c for c in cmds if c not in known and not c.startswith("IEEE"))
rec(not unknown, "控制序列识别", "未在已知清单中（需人工确认）: %s" % unknown[:12] if unknown else "全部识别")

print()
# ---------------- 参考文献结构（第五轮补） ----------------
_cites = set()
for _m in re.finditer(r"\\cite\{([^}]*)\}", raw):
    for _k in _m.group(1).split(","):
        _cites.add(_k.strip())
_bibs = set(re.findall(r"\\bibitem\{([^}]*)\}", raw))
_orphan = sorted(_bibs - _cites)
_dangling = sorted(_cites - _bibs)
rec(not _orphan, "参考文献-无孤儿条目",
    ("未被引用的条目: %s" % _orphan) if _orphan else "%d 条全部被引用" % len(_bibs))
rec(not _dangling, "参考文献-无悬空引用",
    ("引用了不存在的条目: %s" % _dangling) if _dangling else "全部 \\cite 键均可解析")
rec(15 <= len(_bibs) <= 35, "参考文献数量",
    "%d 条（IEEE WCL 常见 15-35 条）" % len(_bibs))

print("=" * 70)
print("通过 %d   失败 %d" % (len(OK), len(FAIL)))



if FAIL:
    print("VERDICT: FAIL")
    for n, d in FAIL:
        print("   -", n, ":", d)
    sys.exit(1)
print("VERDICT: PASS")
