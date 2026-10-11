import os
# -*- coding: utf-8 -*-
"""check_figs.py -- automated self-check of the paper's figures.

Following the practice of the reference project OSD-Net: figures are not only
inspected by eye; a script rebuilds each Axes and checks for common defects
such as legend occlusion, data out of range, and truncated axes, printing a
VERDICT per item.

Checks
  1. data points fall inside the axis limits (out of range = fail)
  2. legend bounding box does not overlap data points
  3. bar-chart y-axes start at 0 (truncation exaggerates differences)
  4. no NaN / Inf values
  5. axis-label symbols match the manuscript (ASCII stand-ins such as
     Delta / >= are reported as warnings)
"""
import json, math, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FAIL, WARN, ROWS = [], [], []


def rep(ok, name, note, warn=False):
    ROWS.append((ok, name, note))
    if not ok:
        (WARN if warn else FAIL).append((name, note))


def check_axes(ax, name, require_zero_bar=False):
    fig = ax.figure
    fig.canvas.draw()
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()

    # 1. 数据越界
    npts, nbad = 0, 0
    for ln in ax.get_lines():
        xd, yd = ln.get_xdata(), ln.get_ydata()
        for x, y in zip(xd, yd):
            if y is None or (isinstance(y, float) and (math.isnan(y) or math.isinf(y))):
                nbad += 1; npts += 1; continue
            npts += 1
            if not (min(y0, y1) - 1e-12 <= y <= max(y0, y1) + 1e-12):
                nbad += 1
            if not (min(x0, x1) - 1e-12 <= x <= max(x0, x1) + 1e-12):
                nbad += 1
    rep(nbad == 0, name + " / data out of range", "%d points, %d out of range or invalid" % (npts, nbad))

    # 2. 图例遮挡
    leg = ax.get_legend()
    if leg is not None:
        lb = leg.get_window_extent()
        hits = 0
        for ln in ax.get_lines():
            pts = ax.transData.transform(np.column_stack([ln.get_xdata(), ln.get_ydata()]))
            for px, py in pts:
                if lb.x0 <= px <= lb.x1 and lb.y0 <= py <= lb.y1:
                    hits += 1
        rep(hits == 0, name + " / legend overlap", "%d data points inside the legend box" % hits)

    # 3. 柱状图纵轴起点
    if require_zero_bar and ax.patches:
        lo = min(ax.get_ylim())
        rep(abs(lo) < 1e-9, name + " / bar zero baseline",
            "y lower bound = %.4g (bar charts must start at 0, else differences are exaggerated)" % lo)
    elif ax.patches:
        rep(True, name + " / bar zero baseline", "no bar chart; skipped")

    # 4. 轴标签符号一致性
    bad_sym = []
    for lab in [ax.get_xlabel(), ax.get_ylabel(), ax.get_title()]:
        if lab and any(t in lab for t in ["Delta", " >= ", " <= ", "sigma", "alpha", "mu_"]):
            bad_sym.append(lab)
    rep(not bad_sym, name + " / symbol consistency",
        ("ASCII stand-ins found: %s" % bad_sym) if bad_sym else "axis labels consistent with the manuscript symbols", warn=True)


D = json.load(open("figs/eval_results.json", encoding="utf-8"))
snrs = D["snr"]
base = {float(k): v for k, v in D["baselines"].items()}
models = D["models"]
t256 = json.load(open("figs_transfer256/eval_results.json", encoding="utf-8"))
t512 = json.load(open("figs_transfer512/eval_results.json", encoding="utf-8"))

# ---- 重建 Fig.1 ----
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
ax[0].semilogy(snrs, [base[s]["LS"]["nmse_fit"] for s in snrs], "k--o", ms=4, label="LS")
ax[0].semilogy(snrs, [base[s]["LMMSE"]["nmse_fit"] for s in snrs], "b-s", ms=4, label="LMMSE")
for lab, st in [("Ours-1.28M", "r-^"), ("Ours-0.48M", "g-v"), ("Ours-2.29M", "m-d"),
                ("Ours-phaseMag", "c-p"), ("Ours-regression", "y-h")]:
    ax[0].semilogy(snrs, [r["nmse_fit"] for r in models[lab]["rows"]], st, ms=4, label=lab)
ax[0].set_xlabel("SNR (dB)"); ax[0].set_ylabel("NMSE"); ax[0].legend(fontsize=6.5)
for lab, st in [("Ours-1.28M", "r-^"), ("Ours-0.48M", "g-v"), ("Ours-2.29M", "m-d"),
                ("Ours-phaseMag", "c-p"), ("Ours-regression", "y-h")]:
    ax[1].plot(snrs, [r["rmse_r"] for r in models[lab]["rows"]], st, ms=4, label=lab)
ax[1].set_xlabel("SNR (dB)"); ax[1].set_ylabel("range RMSE (m)"); ax[1].legend(fontsize=6.5)
check_axes(ax[0], "Fig.1 left")
check_axes(ax[1], "Fig.1 right")
plt.close(fig)

# ---- 重建 Fig.2 ----
cap = [("Ours-0.48M", 476416), ("Ours-1.28M", 1280128), ("Ours-2.29M", 2296704)]
steps = {"Ours-0.48M": 18685, "Ours-1.28M": 20931, "Ours-2.29M": 6603}
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
for idx, nm in [(3, "10 dB"), (5, "20 dB")]:
    ax[0].semilogy(np.array([p for _, p in cap]) / 1e6,
                   [models[l]["rows"][idx]["nmse_fit"] for l, _ in cap], "o-", label=nm)
ax[0].set_xlabel("parameters (M)"); ax[0].set_ylabel("NMSE"); ax[0].legend(fontsize=8)
ax[1].bar([l for l, _ in cap], [steps[l] for l, _ in cap])
ax[1].set_ylabel("steps")
check_axes(ax[0], "Fig.2 left")
check_axes(ax[1], "Fig.2 right", require_zero_bar=True)
plt.close(fig)

# ---- 重建 Fig.3 ----
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
for dd, axx in [(t256, ax[0]), (t512, ax[1])]:
    for lab, mk in [("TrainM128", "b-o"), ("TrainM256", "r-^")]:
        if lab in dd["models"]:
            axx.semilogy(dd["snr"], [r["nmse_fit"] for r in dd["models"][lab]["rows"]],
                         mk, ms=4, label=lab)
    b = {float(k): v for k, v in dd["baselines"].items()}
    axx.semilogy(dd["snr"], [b[s]["LMMSE"]["nmse_fit"] for s in dd["snr"]],
                 "k--s", ms=4, label="LMMSE")
    axx.set_xlabel("SNR (dB)"); axx.set_ylabel("NMSE"); axx.legend(fontsize=7)
check_axes(ax[0], "Fig.3 left")
check_axes(ax[1], "Fig.3 right")
plt.close(fig)

print("=" * 78)
print("Figure self-check")
print("=" * 78)
for ok, name, note in ROWS:
    print("%s %-26s %s" % ("OK " if ok else "!! ", name, note))
print("-" * 78)
# ---------------- 数据源新鲜度（ZCode 第四轮 A 节指出的盲区）----------------
# 原 check_figs 只查轴标签与符号，不查图是否由当前数据重绘过，
# 于是 Fig.2 / Fig.S1 在数据切换到 holdout 后仍停留在旧年代。
_FIG_SRC = {
    "figs/fig1-nmse-range.png": ["figs/holdout_eval_full.json", "figs/baselines_holdout_n2000.json", "figs/crb.json", "figs/dl_channel_holdout.json", "figs/dl_geom_all_snr.json", "figs/dl_geom_perseed.json", "figs/dl_geom_perseed_20.json", "figs/dlcnn_geom_perseed.json", "figs/dlcnn_geom_20.json"],
    "figs/fig2-capacity.png": ["figs/holdout_eval_full.json"],
    "figs/fig3-transfer.png": ["figs/holdout_eval_full.json"],
    # ZCode 第七轮：Fig.5（标定曲线）此前不在覆盖范围内（第六轮 P1-6 指出的盲区）
    "figs/fig5-calibration.png": ["figs/exp_calib_v2.json"],
}
# 第十八轮升级：原实现比 mtime，数据文件被等价重写（数值不变）即误报「图过期」，
# 而真正的数据变更若未触碰 mtime（如从备份恢复）又会漏报。改为比内容哈希。
_MANIFEST = "figs/figsrc.sha256"


def _h(p):
    import hashlib
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def _load_manifest():
    m = {}
    if os.path.exists(_MANIFEST):
        for line in open(_MANIFEST, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                m[parts[1]] = parts[0]
    return m


def _record():
    """Call after redrawing figures: writes the current data-source hashes to the manifest."""
    lines = ["# check_figs.py figure-to-data-source provenance manifest (updated by --record after redrawing)"]
    for fig, srcs in _FIG_SRC.items():
        for src in srcs:
            if os.path.exists(src):
                lines.append("%s  %s" % (_h(src), src))
    open(_MANIFEST, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("  recorded %d data-source hashes to %s" % (len(lines) - 1, _MANIFEST))


if "--record" in sys.argv:
    _record()
    sys.exit(0)

_man = _load_manifest()
_stale = []
for _fig, _srcs in _FIG_SRC.items():
    if not os.path.exists(_fig):
        print("  !! missing %s" % _fig); _stale.append(_fig); continue
    _changed = []
    for src in _srcs:
        if not os.path.exists(src):
            continue
        _now = _h(src)
        _was = _man.get(src)
        if _was is None:
            _changed.append(src + "(no record)")
        elif _was != _now:
            _changed.append(src)
    if _changed:
        print("  !! %s data source changed: %s" % (_fig, _changed)); _stale.append(_fig)
    else:
        print("  OK %s (data-source hash unchanged)" % _fig)
if _stale:
    FAIL.append(("figure freshness", "figures not redrawn after a data change: %s" % _stale))
if _stale:
    print("  figures are stale; redraw, then run python check_figs.py --record")

print("pass %d / %d   warn %d   fail %d" % (sum(1 for o, _, _ in ROWS if o), len(ROWS),
                                            len(WARN), len(FAIL)))
if FAIL:
    print("VERDICT: FAIL")
    for n, d in FAIL:
        print("   -", n, ":", d)
    sys.exit(1)
print("VERDICT: PASS" + ("  (with warnings)" if WARN else ""))
