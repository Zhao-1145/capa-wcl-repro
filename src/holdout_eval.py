# -*- coding: utf-8 -*-
"""holdout_eval.py -- 在独立测试集上重评估，量化检查点选择偏差（ZCode P9）。

原评估读的是 x[:1200]，完全落在 train.py 用于选 best.pt 的验证集内。
本脚本用一个**全新种子生成的、模型从未见过的**数据集重测同一模型。
"""
import json, math, time
import numpy as np
import torch

import capa_lib as C
import baselines as B
from train import CAPANet

torch.set_num_threads(8)
N_EVAL = 2000

def load(prefix, n):
    x = np.load(prefix + "_x.npy", mmap_mode="r")
    y = np.load(prefix + "_y.npy", mmap_mode="r")
    M = int(json.load(open(prefix + "_meta.json"))["M"])
    raw = np.asarray(x[:n])
    h = (raw[:, :M] + 1j * raw[:, M:]).astype(np.complex64)
    return h, y[:n, 0].astype(np.float64), y[:n, 1].astype(np.float64), M

ck = torch.load("runs/main_cls_raw/best.pt", map_location="cpu", weights_only=False)
hidden = [int(v) for v in ck["args"]["hidden"].split(",")]
model = CAPANet(ck["in_dim"], hidden, head="cls")
model.load_state_dict(ck["model"]); model.eval()
mode = ck["mode"]

def run(prefix, tag, n=N_EVAL):
    h, rt, tt, M = load(prefix, n)
    rng = np.random.RandomState(11)
    y = C.add_noise(h, np.full(n, 10.0, np.float32), rng)
    with torch.no_grad():
        feat = C.preprocess(y, mode)
        xt = torch.from_numpy(feat.reshape(n, -1))
        lr, lt = model(xt)
        rh, th = model.decode(lr, lt)
    rn = rh.numpy().astype(np.float64); tn = th.numpy().astype(np.float64)
    fit = C.fit_gain_and_reconstruct(rn, tn, y, M)
    out = dict(nmse=C.nmse(fit, h),
               rmse_r=float(np.sqrt(np.mean((rn - rt) ** 2))),
               rmse_th=float(np.sqrt(np.mean((tn - tt) ** 2))))
    print("  %-22s NMSE %.6g   rmse_r %.4f m   rmse_th %.5f rad" % (tag, out["nmse"], out["rmse_r"], out["rmse_th"]))
    return out

print("=" * 74)
print("P9：检查点选择偏差 —— 同一模型，两个数据集")
print("=" * 74)
a = run("F:/capa_data/tr_M256", "验证集内 (x[:2000])")
b = run("F:/capa_data/test_M256_holdout", "独立测试集 (seed 999999)")
print()
print("  相对差: NMSE %+.2f%%   rmse_r %+.2f%%"
      % ((b["nmse"] - a["nmse"]) / a["nmse"] * 100, (b["rmse_r"] - a["rmse_r"]) / a["rmse_r"] * 100))
print("  -> %s" % ("偏差 < 5%%，不构成实质影响"
                   if abs(b["nmse"] - a["nmse"]) / a["nmse"] < 0.05
                   else "**偏差 >= 5%%，需要在论文中如实报告**"))

json.dump({"in_val": a, "holdout": b}, open("figs/holdout_eval.json", "w"), indent=2, default=float)
print("\nsaved figs/holdout_eval.json")
