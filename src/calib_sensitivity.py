# -*- coding: utf-8 -*-
"""calib_sensitivity.py -- 幅度标定误差对距离估计的影响（审稿人明确要求的实验）。

模型：接收端的链路预算标定存在增益误差 (1+eps)，即观测被未知地乘以 (1+eps)。
提议方法依赖已标定的接收幅度，因此这直接冲击它的距离估计。

对 eps in {0, 0.01, 0.02, 0.05, 0.10} 与两个符号，测量：
  - 提议方法的距离 RMSE
  - 一行式读出口 1/mean|y| 的距离 RMSE
  - 相对无误差时的偏差
只做推理，不训练。
"""
import os, json
import numpy as np
import torch
import capa_lib as C
from train import CAPANet

M = 256
H = "F:/capa_data/test_M256_holdout2"
N = 2000
SNRS = [10.0, 20.0]
EPS = [0.0, 0.01, 0.02, 0.05, 0.10]

def load(run, ck="best.pt"):
    ck_ = torch.load("runs/%s/%s" % (run, ck), map_location="cpu", weights_only=False)
    m = CAPANet(ck_["in_dim"], ck_["hidden"], head=ck_["head"])
    m.load_state_dict(ck_["model"]); m.eval()
    return m

def main():
    x = np.load(H + "_x.npy", mmap_mode="r")
    yy = np.load(H + "_y.npy", mmap_mode="r")
    raw = np.asarray(x[:N])
    h = (raw[:, :M] + 1j * raw[:, M:]).astype(np.complex64)
    rt = yy[:N, 0].astype(np.float64)

    models = [load(r) for r in ["eq_cls_s0", "eq_cls_s1", "eq_cls_s2"]]
    print("载入 %d 个提议方法模型" % len(models), flush=True)

    out = {"note": "applied a positive real gain error (1+eps) to the observation", "per": {}}
    for snr in SNRS:
        rng = np.random.RandomState(11)
        y0 = C.add_noise(h, np.full(N, snr, np.float32), rng)
        for eps in EPS:
            for sign in [+1, -1]:
                e = sign * eps
                y = (y0 * (1.0 + e)).astype(np.complex64)
                feat = C.preprocess(y, "raw")
                xt = torch.from_numpy(feat.reshape(N, -1))
                rs, ts = [], []
                with torch.no_grad():
                    for m in models:
                        lr, lt = m(xt)
                        r_, t_ = m.decode(lr, lt, tau=1.0)
                        rs.append(r_.numpy().astype(np.float64))
                        ts.append(t_.numpy().astype(np.float64))
                r_mean = np.mean(rs, axis=0)
                rmse = float(np.sqrt(np.mean((r_mean - rt) ** 2)))
                # 一行式读出口
                ol = 1.0 / np.mean(np.abs(y), axis=1)
                olr = float(np.sqrt(np.mean((ol - rt) ** 2)))
                key = "%+.2f" % e
                out["per"].setdefault(str(snr), {})[key] = {
                    "proposed_rmse_r": rmse, "one_line_rmse_r": olr,
                    "bias_r": float(np.mean(r_mean - rt)),
                }
                print("  %5.1f dB  eps=%+5.1f%%   提议 %.4f m   一行式 %.4f m   偏差 %+.3f m" %
                      (snr, 100 * e, rmse, olr, float(np.mean(r_mean - rt))), flush=True)
        print(flush=True)

    json.dump(out, open("figs/calib_sensitivity.json", "w"), indent=2, default=float)
    print("saved figs/calib_sensitivity.json", flush=True)

if __name__ == "__main__":
    main()
