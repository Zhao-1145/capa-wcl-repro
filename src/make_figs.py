
"""Regenerate the paper figures from the stored evaluation JSONs.

Fixes a bug in evaluate.py: the range-RMSE panel plotted nmse_fit for the
LS and LMMSE curves.  Neither estimator produces geometric parameters, so
they must not appear in that panel at all.
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- 排版比例：源图按 2 倍设计，正文按 \columnwidth 排版，缩放 0.5 ----
plt.rcParams.update({
    "font.size": 15,
    "axes.labelsize": 16,
    "axes.titlesize": 17,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 11,
    "lines.linewidth": 2.2,
    "lines.markersize": 7,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "figure.autolayout": False,
})

os.makedirs("figs", exist_ok=True)


def save(fig, stem):
    """Write both a 300-dpi PNG (portable) and a vector PDF (IEEE preferred)."""
    fig.savefig("figs/%s.png" % stem, dpi=300)
    fig.savefig("figs/%s.pdf" % stem)
    print("wrote figs/%s.{png,pdf}" % stem)
d = json.load(open("figs/eval_results.json"))
snrs = d["snr"]
base = {float(k): v for k, v in d["baselines"].items()}
db = d["dict_baselines"]
snr_d = d["dict_snr"]
models = d["models"]

ORDER = ["Ours-1.28M", "Ours-0.48M", "Ours-2.29M", "Ours-phaseMag", "Ours-regression"]
STYLE = {"Ours-1.28M": ("r-^", "Proposed (1.28M)"),
         "Ours-0.48M": ("g-v", "Proposed (0.48M)"),
         "Ours-2.29M": ("m-d", "Proposed (2.29M)"),
         "Ours-phaseMag": ("c-p", "Phase-differenced input"),
         "Ours-regression": ("y-h", "Direct regression head")}

# ---------------- Figure 1: NMSE and range RMSE vs SNR ----------------
fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.7))

ax[0].semilogy(snrs, [base[s]["LS"]["nmse_fit"] for s in snrs], "k--o", ms=4, label="LS")
ax[0].semilogy(snrs, [base[s]["LMMSE"]["nmse_fit"] for s in snrs], "b-s", ms=4, label="LMMSE")
for lab in ORDER:
    st, name = STYLE[lab]
    ax[0].semilogy(snrs, [r["nmse_fit"] for r in models[lab]["rows"]], st, ms=4, label=name)
for k, (mk, nm) in zip(["OMP_50x100", "OMP_100x200", "OMP_refine"],
                       [("k*", "OMP 50x100"), ("ks", "OMP 100x200"), ("kp", "OMP + refine")]):
    ax[0].plot([snr_d], [db[k]["nmse_fit"]], mk[0], color="0.35", ms=10, label=nm)
ax[0].set_xlabel("SNR (dB)"); ax[0].set_ylabel("NMSE (gain-fitted)")
ax[0].set_title("Channel estimation accuracy"); ax[0].grid(alpha=.3, which="both")
ax[0].legend(fontsize=11, ncol=2, framealpha=0.95)

# range panel: only methods that actually estimate geometry
for lab in ORDER:
    st, name = STYLE[lab]
    ax[1].plot(snrs, [r["rmse_r"] for r in models[lab]["rows"]], st, ms=4, label=name)
for k, (mk, nm) in zip(["OMP_50x100", "OMP_100x200", "OMP_refine"],
                       [("k*", "OMP 50x100"), ("ks", "OMP 100x200"), ("kp", "OMP + refine")]):
    ax[1].plot([snr_d], [db[k]["rmse_r"]], mk[0], color="0.35", ms=10, label=nm)
ax[1].set_xlabel("SNR (dB)"); ax[1].set_ylabel("range RMSE (m)")
ax[1].set_title("Range estimation error")
ax[1].grid(alpha=.3); ax[1].legend(fontsize=11, ncol=2, framealpha=0.95)
ax[1].axhline(2.5, color="0.6", ls=":", lw=1)
ax[1].text(-4.7, 2.62, "dictionary baselines (grid-density independent)", fontsize=11, color="0.4")
plt.tight_layout(); save(plt.gcf(), "fig1-nmse-range"); plt.close()

# ---------------- Figure 2: capacity under fixed budget ----------------
cap = [("Ours-0.48M", 476416), ("Ours-1.28M", 1280128), ("Ours-2.29M", 2296704)]
steps = {"Ours-0.48M": 18685, "Ours-1.28M": 20931, "Ours-2.29M": 6603}
fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.7))
for idx, snr_i in [(3, "10 dB"), (5, "20 dB")]:
    xs = [p for _, p in cap]
    ys = [models[l]["rows"][idx]["nmse_fit"] for l, _ in cap]
    ax[0].semilogy(np.array(xs) / 1e6, ys, "o-", label="SNR " + snr_i)
ax[0].set_xlabel("parameters (millions)"); ax[0].set_ylabel("NMSE (gain-fitted)")
ax[0].set_title("Capacity under a fixed 90-min budget")
ax[0].grid(alpha=.3, which="both"); ax[0].legend(fontsize=11, framealpha=0.95)

ax[1].bar([l.replace("Ours-", "") for l, _ in cap],
          [steps[l] for l, _ in cap], color=["#4c72b0", "#dd8452", "#55a868"])
ax[1].set_ylabel("gradient steps completed")
ax[1].set_title("Steps actually completed in 90 min")
for i, (l, _) in enumerate(cap):
    ax[1].text(i, steps[l] + 400, str(steps[l]), ha="center", fontsize=8)
plt.tight_layout(); save(plt.gcf(), "fig2-capacity"); plt.close()

# ---------------- Figure 3: cross-discretisation transfer ----------------
fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.7))
for fn, ttl, axx in [("figs_transfer256/eval_results.json", r"test $M_{te}=256$", ax[0]),
                     ("figs_transfer512/eval_results.json", r"test $M_{te}=512$", ax[1])]:
    dd = json.load(open(fn))
    for lab, mk, nm in [("TrainM128", "b-o", r"trained at $M_{tr}=128$"),
                        ("TrainM256", "r-^", r"trained at $M_{tr}=256$")]:
        if lab in dd["models"]:
            axx.semilogy(dd["snr"], [r["nmse_fit"] for r in dd["models"][lab]["rows"]],
                         mk, ms=4, label=nm)
    b = {float(k): v for k, v in dd["baselines"].items()}
    axx.semilogy(dd["snr"], [b[s]["LMMSE"]["nmse_fit"] for s in dd["snr"]],
                 "k--s", ms=4, label="LMMSE")
    axx.set_xlabel("SNR (dB)"); axx.set_ylabel("NMSE (gain-fitted)")
    axx.set_title(ttl); axx.grid(alpha=.3, which="both"); axx.legend(fontsize=11, framealpha=0.95)
plt.tight_layout(); save(plt.gcf(), "fig3-transfer"); plt.close()
print("figures written (png)")

