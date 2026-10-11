# -*- coding: utf-8 -*-
"""grid_aliasing_test.py -- 判定"字典法无法估计距离"究竟是网格混叠还是本质限制.

背景：匹配滤波统计量在距离维以 lambda 为周期。若字典的 r 间距 > lambda/2，
      就会混叠（aliasing），此时失败是网格太粗导致的，不是方法本质。
      本文原基线 100 个 r 点 => 间距 0.13 m > lambda/2 = 0.05 m。

本脚本用逐级加密的 r 网格重跑 OMP，看距离 RMSE 是否随网格加密而收敛到 CRB 附近。
若收敛 => 论文结论 3 必须修正为"网格需细于 lambda/2"，否则维持原判。

同时报告：每个网格的原子数、字典体积、相关运算耗时。
"""
import json, time, math
import numpy as np
import capa_lib as C

M = 256
N = 300
x = np.load("F:/capa_data/tr_M256_x.npy", mmap_mode="r")
raw = np.asarray(x[:N])
h_true = (raw[:, :M] + 1j * raw[:, M:]).astype(np.complex64)
lab = np.load("F:/capa_data/tr_M256_y.npy", mmap_mode="r")
r_true = lab[:N, 0].astype(np.float64)
th_true = lab[:N, 1].astype(np.float64)

rng = np.random.RandomState(7)
y = C.add_noise(h_true, np.full(N, 10.0, np.float32), rng)

lam = C.LAMBDA
print("原基线 r 间距 = %.4f m (100 点)  |  lambda/2 = %.4f m" % (13.0 / 99, lam / 2))
print()
print("%-28s %10s %10s %9s %9s %9s" % ("r 网格", "原子数", "r 间距(m)", "rmse_r", "rmse_th", "耗时(s)"))
print("-" * 82)

rows = []
import baselines as B
for n_r, n_th in [(50, 100), (100, 200), (200, 200), (260, 200), (400, 200), (520, 200), (800, 200)]:
    spacing = (C.R_MAX - C.R_MIN) / (n_r - 1)
    t0 = time.time()
    D, rr, tt = B.build_dictionary(M, n_r, n_th)
    tdict = time.time() - t0
    G = D.shape[0]
    # 分块相关，控制内存
    best = np.empty(N, dtype=np.int64)
    chunk = max(1, int(2e7 // max(G, 1)))
    for i in range(0, N, chunk):
        sl = slice(i, min(i + chunk, N))
        corr = np.abs(y[sl] @ np.conj(D).T)
        best[sl] = np.argmax(corr, axis=1)
    rh, th_ = rr[best], tt[best]
    rmse_r = float(np.sqrt(np.mean((rh - r_true) ** 2)))
    rmse_th = float(np.sqrt(np.mean((th_ - th_true) ** 2)))
    dt = time.time() - t0 - tdict
    rows.append(dict(n_r=n_r, n_th=n_th, G=int(G), spacing=spacing,
                     rmse_r=rmse_r, rmse_th=rmse_th, t_corr=dt, t_dict=tdict))
    print("%-28s %10d %10.4f %9.4f %9.5f %9.2f"
          % ("%d x %d" % (n_r, n_th), G, spacing, rmse_r, rmse_th, dt))

json.dump(rows, open("figs/grid_aliasing.json", "w"), indent=2)
print()
print("判据：若 rmse_r 随 r 间距降到 lambda/2 以下而骤降并趋近 CRB(2.23e-4 m)，")
print("      则原结论 3 需修正为「网格必须细于 lambda/2」；")
print("      若始终停在 ~2.5 m 量级，则原结论成立（本质限制）。")
