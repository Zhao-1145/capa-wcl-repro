# -*- coding: utf-8 -*-
"""rerun_baselines_n2000.py -- 把字典基线按 n=2000 重跑，与提议方法对齐样本量。"""
import json, time, sys
import numpy as np
import capa_lib as C
import baselines as B

SNR = [-5.0, 0.0, 5.0, 10.0, 15.0, 20.0]
N = 2000
H = "F:/capa_data/test_M256_holdout2"
M = 256
OUT = "figs/baselines_holdout_n2000.json"

x = np.load(H + "_x.npy", mmap_mode="r")
yy = np.load(H + "_y.npy", mmap_mode="r")
raw = np.asarray(x[:N])
h = (raw[:, :M] + 1j*raw[:, M:]).astype(np.complex64)
rt = yy[:N, 0].astype(np.float64)
tt_true = yy[:N, 1].astype(np.float64)
print("N=%d  M=%d  mem=%.1f MB" % (N, M, h.nbytes/1e6), flush=True)

D1, rr1, tt1 = B.build_dictionary(M, 50, 100)
D2, rr2, tt2 = B.build_dictionary(M, 100, 200)
print("字典已建", flush=True)

# 注意：Ch 由测试样本自身估计，属 genie/oracle，正文必须写明
Ch = (h.conj().T @ h) / len(h)

out = {"snr": SNR, "baselines": {}, "dict": {}, "n_eval": N, "source": H,
       "note": "n raised 1200 -> 2000 to match the proposed method; LMMSE covariance is the sample covariance of the evaluation set (genie-aided)."}

def run_omp(y, D, rr, tt, refine=False):
    if refine:
        r_, t_ = B.polar_omp_refine(y, D, rr, tt, M, rounds=3)
    else:
        r_, t_ = B.polar_omp(y, D, rr, tt)
    fit = C.fit_gain_and_reconstruct(r_, t_, y, M)
    phi = C.channel_from_params(r_, t_, M)
    return {"nmse_fit": float(C.nmse(fit, h)), "nmse_raw": float(C.nmse(phi, h)),
            "rmse_r": float(np.sqrt(np.mean((r_ - rt) ** 2))),
            "rmse_th": float(np.sqrt(np.mean((t_ - tt_true) ** 2)))}

for s in SNR:
    t_all = time.time()
    rng = np.random.RandomState(11)
    y = C.add_noise(h, np.full(N, s, np.float32), rng)
    row = {}
    row["LS"] = {"nmse_fit": float(C.nmse(y, h)), "nmse_raw": float(C.nmse(y, h))}
    hl = B.lmmse(y, np.full(N, s), Ch, M)
    row["LMMSE"] = {"nmse_fit": float(C.nmse(hl, h)), "nmse_raw": float(C.nmse(hl, h))}
    out["baselines"][str(s)] = row
    o1 = run_omp(y, D1, rr1, tt1)
    t0 = time.time(); o3 = run_omp(y, D1, rr1, tt1, refine=True); o3["time_s"] = time.time() - t0
    o2 = run_omp(y, D2, rr2, tt2)
    out["dict"][str(s)] = {"OMP_50x100": o1, "OMP_refine": o3, "OMP_100x200": o2}
    print("%5.1f dB  LS %.4g  LMMSE %.4g  OMP50 %.4g  refine %.4g (%.0fs)  OMP100 %.4g"
          % (s, row["LS"]["nmse_fit"], row["LMMSE"]["nmse_fit"], o1["nmse_fit"],
             o3["nmse_fit"], o3["time_s"], o2["nmse_fit"]), flush=True)
    print("         refine rmse_r %.4f  rmse_th %.5f   [本轮 %.0fs]"
          % (o3["rmse_r"], o3["rmse_th"], time.time() - t_all), flush=True)

json.dump(out, open(OUT, "w"), indent=2, default=float)
print("saved", OUT, flush=True)