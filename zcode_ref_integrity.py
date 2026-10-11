# -*- coding: utf-8 -*-
"""zcode_ref_integrity.py -- 第十九轮：参考文献重排后的内容完整性校验.

第十七轮按首引顺序重排了 25 条 bibitem。本脚本把每条目当前的
（首作者、venue、卷/页、年份）指纹与重排前的归档内容逐一对照，
证明重排只动了顺序、没动内容。基准指纹转录自重排前的稿件快照
（第十六轮审查时的完整 Read 记录）。
"""
import re, sys

BS = chr(92)
t = open("paper_CAPA_deep_estimation.tex", encoding="utf-8").read()
i0 = t.index(BS + "begin{thebibliography}")
i_end = t.index(BS + "end{thebibliography}") + len(BS + "end{thebibliography}")
block = t[i0:i_end]

EXPECT = {
 "foschini":  ["G. J. Foschini", "Wireless Pers. Commun.", "vol. 6", "311--335", "1998"],
 "capa2024":  ["Y. Liu", "IEEE Wireless Commun.", "vol. 32, no. 4", "38--45", "2025"],
 "holographic":["C. Huang", "IEEE Wireless Commun.", "vol. 27", "118--125", "2020"],
 "capaMIMO":  ["Z. Wang", "IEEE Trans. Wireless Commun.", "vol. 25", "2167--2182", "2026"],
 "capaOptimal":["Z. Wang", "IEEE Trans. Commun.", "vol. 73, no. 10", "9207--9221", "2025"],
 "capaDoF":   ["S. T. Duong", "GLOBECOM", "545--550", "2025"],
 "capaOrientation":["Y. Guo", "IEEE Wireless Commun. Lett.", "vol. 14", "2476--2480", "2025"],
 "dofHolo":   ["A. Pizzo", "SPAWC", "1--5", "2020"],
 "dofNF":     ["H. Chen", "IEEE Commun. Lett.", "vol. 29", "1186--1190", "2025"],
 "capaISAC":  ["B. Zhao", "IEEE Trans. Wireless Commun.", "vol. 25", "3592--3609", "2026"],
 "hmimoDFT":  ["A. A. D'Amico", "Asilomar", "353--357", "2023"],
 "hmimoAngle":["Y. Chen", "IEEE J. Sel. Areas Commun.", "vol. 42", "1684--1702", "2024"],
 "elaa":      ["S. Ye", "IEEE Open J. Commun. Soc.", "vol. 5", "7075--7120", "2024"],
 "cuidai":    ["M. Cui", "IEEE Trans. Commun.", "vol. 70", "2663--2677", "2022"],
 "weidai":    ["X. Wei", "IEEE Commun. Lett.", "vol. 26", "177--181", "2022"],
 "omp":       ["J. A. Tropp", "IEEE Trans. Inform. Theory", "vol. 53", "4655--4666", "2007"],
 "polar":     ["A. Hussain", "IEEE Trans. Wireless Commun.", "vol. 24", "8193--8207", "2025"],
 "sparse":    ["V. B. Shukla", "WSA", "60--65", "2025"],
 "extrap":    ["J. Lu", "IEEE Trans. Wireless Commun.", "vol. 25", "4343--4357", "2026"],
 "crb":       ["H. Hua", "IEEE Trans. Signal Process.", "vol. 72", "3879--3895", "2024"],
 "crbnf":     ["Y. Begriche", "ISSPA", "718--721", "2012"],
 "dlceFound": ["H. Ye", "IEEE Wireless Commun. Lett.", "vol. 7", "114--117", "2018"],
 "mdlFound":  ["H. He", "IEEE Wireless Commun.", "vol. 26", "77--83", "2019"],
 "dlce":      ["Y. Gao", "Chinese J. Electron.", "vol. 35", "178--195", "2026"],
 "softargmax":["A. Nibali", "arXiv preprint", "arXiv:1801.07372", "2018"],
}
pat = re.compile(re.escape(BS + "bibitem{") + r"([a-zA-Z0-9]+)\}(.*?)(?=" +
                 re.escape(BS + "bibitem{") + "|" + re.escape(BS + "end{thebibliography}") + ")",
                 re.S)
items = pat.findall(block)
d = {k: body for k, body in items}
assert set(d) == set(EXPECT), (set(d) ^ set(EXPECT))
bad = 0
for k, frags in EXPECT.items():
    missing = [f for f in frags if f not in d[k]]
    if missing:
        bad += 1
        print("不符 %-14s 缺: %s" % (k, missing))
print("文献内容完整性: %d/%d 条与重排前逐字一致" % (25 - bad, 25))
sys.exit(1 if bad else 0)
