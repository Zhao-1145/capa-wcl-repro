# -*- coding: utf-8 -*-
"""exp_p0p2.py -- 偏差/方差、多用户、端射、噪声（推理-only）。"""
import os, json, time
import numpy as np, torch
import capa_lib as C
from train import CAPANet
M = 256
H = "F:/capa_data/test_M256_holdout2"
N = 2000

def load(runs):
    ms = []
    for r in runs:
        ck = torch.load("runs/%s/best.pt" % r, map_location="cpu", weights_only=False)
        m = CAPANet(ck["in_dim"], ck["hidden"], head=ck["head"])
        m.load_state_dict(ck["model"]); m.eval(); ms.append(m)
    return ms

def pred(ms, y):
    feat = C.preprocess(y, "raw")
    xt = torch.from_numpy(feat.reshape(len(y), -1))
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
    tht = yy[:N, 1].astype(np.float64)
    ms = load(["eq_cls_s0", "eq_cls_s1", "eq_cls_s2"])
    out = {}
    CRB = json.load(open("figs/crb.json", encoding="utf-8"))
    print("=== 1) bias/variance ===", flush=True)
    B = {}
    for snr in [-5.0, 0.0, 5.0, 10.0, 15.0, 20.0]:
        rng = np.random.RandomState(11)
        y = C.add_noise(h, np.full(N, snr, np.float32), rng)
        r_hat, _ = pred(ms, y)
        bias = float(np.mean(r_hat - rt))
        var = float(np.var(r_hat - rt, ddof=1))
        rmse = float(np.sqrt(np.mean((r_hat - rt) ** 2)))
        i = CRB["snr"].index(snr) if snr in CRB["snr"] else -1
        # C_rmse_r is already an RMS RMSE (see compute_crb.py); do NOT take a sqrt again.
        crbC = float(CRB["C_rmse_r"][i]) if i >= 0 else 0.0
        B[str(snr)] = {"bias": bias, "sd": float(np.sqrt(var)), "rmse": rmse, "crb_C": crbC}
        print("  %5.1f dB bias %+8.5f sd %.4f rmse %.4f crbC %.4f" % (snr, bias, np.sqrt(var), rmse, crbC), flush=True)
    out["bias_variance"] = B
    print("", flush=True)
    print("=== 2) multiuser ===", flush=True)
    MU = {}
    for K in [1, 2, 4, 8, 16]:
        rng = np.random.RandomState(11)
        yk = C.add_noise(h, np.full(N, 10.0, np.float32), rng)
        t0 = time.time()
        for k in range(K):
            rk, _ = pred(ms, yk)
        dt = time.time() - t0
        MU[str(K)] = {"total_s": dt, "per_user_ms": 1000 * dt / K, "rmse_r": float(np.sqrt(np.mean((rk - rt) ** 2)))}
        print("  K=%2d total %.2f s (%.1f ms/user) rmse %.4f" % (K, dt, 1000 * dt / K, MU[str(K)]["rmse_r"]), flush=True)
    out["multiuser"] = MU
    print("", flush=True)
    print("=== 3) endfire ===", flush=True)
    EF = {}
    for lo, hi, tag in [(0.0, 0.2, "broadside"), (0.2, 0.6, "low"), (0.6, 1.2, "mid"), (1.2, 1.5, "endfire")]:
        sel = (np.abs(tht) >= lo) & (np.abs(tht) < hi)
        if sel.sum() < 20:
            EF[tag] = {"n": int(sel.sum())}; continue
        rng = np.random.RandomState(11)
        y = C.add_noise(h[sel], np.full(int(sel.sum()), 10.0, np.float32), rng)
        r_hat, t_hat = pred(ms, y)
        EF[tag] = {"n": int(sel.sum()), "rmse_r": float(np.sqrt(np.mean((r_hat - rt[sel]) ** 2))), "rmse_th": float(np.sqrt(np.mean((t_hat - tht[sel]) ** 2)))}
        print("  %-10s n=%4d rmse_r %.4f rmse_th %.5f" % (tag, sel.sum(), EF[tag]["rmse_r"], EF[tag]["rmse_th"]), flush=True)
    out["endfire"] = EF
    print("", flush=True)
    print("=== 4) noise ===", flush=True)
    NZ = {}
    rng0 = np.random.RandomState(11)
    y0 = C.add_noise(h, np.full(N, 10.0, np.float32), rng0)
    for sp in [0.0, 0.05, 0.10, 0.20]:
        rng = np.random.RandomState(23)
        ph = rng.normal(0, sp, size=(N, M))
        y = (y0 * np.exp(1j * ph)).astype(np.complex64)
        r_hat, _ = pred(ms, y)
        NZ["phase_%.2f" % sp] = float(np.sqrt(np.mean((r_hat - rt) ** 2)))
        print("  phase sigma=%.2f rmse %.4f" % (sp, NZ["phase_%.2f" % sp]), flush=True)
    for rho in [0.0, 0.5, 0.9]:
        d = np.abs(np.arange(M)[:, None] - np.arange(M)[None, :])
        R = rho ** d
        Lc = np.linalg.cholesky(R + 1e-9 * np.eye(M))
        rng = np.random.RandomState(31)
        p = np.mean(np.abs(h) ** 2)
        sig = np.sqrt(p / 10.0)
        wn = (rng.randn(M, N) + 1j * rng.randn(M, N)) * sig / np.sqrt(2.0)
        cn = (Lc @ wn).T.astype(np.complex64)
        y = (h + cn).astype(np.complex64)
        r_hat, _ = pred(ms, y)
        NZ["corr_%.1f" % rho] = float(np.sqrt(np.mean((r_hat - rt) ** 2)))
        print("  corr rho=%.1f rmse %.4f" % (rho, NZ["corr_%.1f" % rho]), flush=True)
    out["noise"] = NZ
    json.dump(out, open("figs/exp_p0p2.json", "w"), indent=2, default=float)
    print("saved", flush=True)

if __name__ == "__main__":
    main()
