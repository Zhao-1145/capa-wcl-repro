# -*- coding: utf-8 -*-
"""exp_bd2.py -- 实验 B（SNR-agnostic 基线）与 D（高 SNR 外推），修正版。

关键修正：估计协方差必须来自训练集 tr_M256，不能来自评估集本身。
重建一律走论文自己的路径（fit_gain_and_reconstruct + nmse）。
"""
import os, json
import numpy as np
import torch
import capa_lib as C
from train import CAPANet

M = 256
H = "F:/capa_data/test_M256_holdout2"
TR = "F:/capa_data/tr_M256"
N = 2000


def load(run):
    ck = torch.load("runs/%s/best.pt" % run, map_location="cpu", weights_only=False)
    m = CAPANet(ck["in_dim"], ck["hidden"], head=ck["head"])
    m.load_state_dict(ck["model"]); m.eval()
    return m


def pred(ms, y, N):
    feat = C.preprocess(y, "raw")
    xt = torch.from_numpy(feat.reshape(N, -1))
    RH, TH = [], []
    with torch.no_grad():
        for m in ms:
            lr, lt = m(xt)
            r_, t_ = m.decode(lr, lt, tau=1.0)
            RH.append(r_.numpy()); TH.append(t_.numpy())
    return np.mean(RH, 0).astype(np.float64), np.mean(TH, 0).astype(np.float64)


def main():
    x = np.load(H + "_x.npy", mmap_mode="r")
    yy = np.load(H + "_y.npy", mmap_mode="r")
    raw = np.asarray(x[:N])
    h = (raw[:, :M] + 1j * raw[:, M:]).astype(np.complex64)
    rt = yy[:N, 0].astype(np.float64)
    ms = [load("eq_cls_s%d" % s) for s in [0, 1, 2]]
    out = {}

    # ---- 实验 B ----
    print("=== 实验 B: LMMSE oracle vs 估计协方差（估计值来自训练集）===", flush=True)
    tr = np.asarray(np.load(TR + "_x.npy", mmap_mode="r")[:20000])
    htr = (tr[:, :M] + 1j * tr[:, M:]).astype(np.complex64)
    Ch_est = (htr.conj().T @ htr) / len(htr)
    Ch_orc = (h.conj().T @ h) / len(h)
    d_est = np.linalg.norm(Ch_est - Ch_orc) / np.linalg.norm(Ch_orc)
    print("  估计协方差与 oracle 的相对差: %.4f" % d_est, flush=True)
    B = {}
    for snr in [-5.0, 0.0, 5.0, 10.0, 15.0, 20.0]:
        rng = np.random.RandomState(11)
        y = C.add_noise(h, np.full(N, snr, np.float32), rng)
        p = np.mean(np.abs(h) ** 2)
        sig2 = p / 10 ** (snr / 10.0)
        row = {}
        for tag, Ch in [("oracle", Ch_orc), ("est", Ch_est)]:
            W = Ch @ np.linalg.inv(Ch + sig2 * np.eye(M))
            hh = (W @ y.T).T.astype(np.complex64)
            row[tag] = float(C.nmse(hh, h))
        r_hat, th_hat = pred(ms, y, N)
        fit = C.fit_gain_and_reconstruct(r_hat, th_hat, y, M)
        row["proposed"] = float(C.nmse(fit, h))
        row["gain_dB"] = float(10 * np.log10(row["est"] / row["oracle"]))
        row["lead_dB"] = float(10 * np.log10(row["est"] / row["proposed"]))
        B[str(snr)] = row
        print("  %5.1f dB  oracle %.4g  est %.4g (差 %+.2f dB)  Proposed %.4g (领先 est %.2f dB)" %
              (snr, row["oracle"], row["est"], row["gain_dB"], row["proposed"], row["lead_dB"]), flush=True)
    out["B"] = B

    # ---- 实验 D ----
    print("", flush=True)
    print("=== 实验 D: 高 SNR 外推（训练区间 -5..20 dB）===", flush=True)
    D = {}
    for snr in [20.0, 25.0, 30.0, 35.0, 40.0]:
        rng = np.random.RandomState(11)
        y = C.add_noise(h, np.full(N, snr, np.float32), rng)
        r_hat, th_hat = pred(ms, y, N)
        fit = C.fit_gain_and_reconstruct(r_hat, th_hat, y, M)
        D[str(snr)] = {"rmse_r": float(np.sqrt(np.mean((r_hat - rt) ** 2))),
                       "nmse_fit": float(C.nmse(fit, h))}
        print("  %5.1f dB  距离 RMSE %.4f m   NMSE_fit %.4g" %
              (snr, D[str(snr)]["rmse_r"], D[str(snr)]["nmse_fit"]), flush=True)
    out["D"] = D
    json.dump(out, open("figs/exp_bd.json", "w"), indent=2, default=float)
    print("saved figs/exp_bd.json", flush=True)


if __name__ == "__main__":
    main()
