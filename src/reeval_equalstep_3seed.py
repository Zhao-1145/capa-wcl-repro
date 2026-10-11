# -*- coding: utf-8 -*-
"""reeval_equalstep_3seed.py -- 改为三种子均值，使 Fig.1 与 Table II 同源。"""
import json, math
import numpy as np
import torch

import capa_lib as C
from train import CAPANet

torch.set_num_threads(10)
T95 = {2: 4.303}
SNR = [-5.0, 0.0, 5.0, 10.0, 15.0, 20.0]
N = 2000
ARMS = {"cls_raw": ["eq_cls_s0", "eq_cls_s1", "eq_cls_s2"],
        "phase_mag": ["eq_phmag_s0", "eq_phmag_s1", "eq_phmag_s2"],
        "reg": ["eq_reg_s0", "eq_reg_s1", "eq_reg_s2"]}

x = np.load("F:/capa_data/tr_M256_x.npy", mmap_mode="r")
yy_ = np.load("F:/capa_data/tr_M256_y.npy", mmap_mode="r")
M = int(json.load(open("F:/capa_data/tr_M256_meta.json"))["M"])
raw = np.asarray(x[:N])
h = (raw[:, :M] + 1j * raw[:, M:]).astype(np.complex64)
rt = yy_[:N, 0].astype(np.float64); tt = yy_[:N, 1].astype(np.float64)

models = {}
for key, runs in ARMS.items():
    models[key] = []
    for r in runs:
        ck = torch.load("runs/%s/best.pt" % r, map_location="cpu", weights_only=False)
        hidden = [int(v) for v in ck["args"]["hidden"].split(",")]
        m = CAPANet(ck["in_dim"], hidden, head=ck["args"].get("head", "cls"))
        m.load_state_dict(ck["model"]); m.eval()
        models[key].append((m, ck["mode"]))

out = {"snr": SNR, "models": {}, "baselines": {}, "seeds": 3, "n_eval": N}
print("=" * 80)
print("三种子均值的全 SNR 曲线（N=%d）" % N)
print("=" * 80)
for s in SNR:
    rng = np.random.RandomState(11)
    y = C.add_noise(h, np.full(N, s, np.float32), rng)
    entry = {}
    for key, ms in models.items():
        acc = {"nmse": [], "rmse_r": [], "rmse_th": []}
        for m, mode in ms:
            with torch.no_grad():
                feat = C.preprocess(y, mode)
                xt = torch.from_numpy(feat.reshape(N, -1))
                lr, lt = m(xt)
                rh, th = m.decode(lr, lt)
            rn = rh.numpy().astype(np.float64); tn = th.numpy().astype(np.float64)
            fit = C.fit_gain_and_reconstruct(rn, tn, y, M)
            acc["nmse"].append(float(C.nmse(fit, h)))
            acc["rmse_r"].append(float(np.sqrt(np.mean((rn-rt)**2))))
            acc["rmse_th"].append(float(np.sqrt(np.mean((tn-tt)**2))))
        e = {}
        for k, v in acc.items():
            a = np.array(v)
            ci = float(T95[2]*a.std(ddof=1)/math.sqrt(3))
            e[k] = float(a.mean()); e[k+"_ci"] = ci
        entry[key] = e
    out["baselines"][str(s)] = {"LS": float(C.nmse(y, h))}
    out["models"][str(s)] = entry
    o = entry["cls_raw"]
    d = 10*math.log10(out["baselines"][str(s)]["LS"]/o["nmse"])
    print("  %5.1f dB  NMSE %.4e+-%.1e  rmse_r %.4f  rmse_th %.5f  vs LS %.1f dB"
          % (s, o["nmse"], o["nmse_ci"], o["rmse_r"], o["rmse_th"], d))

json.dump(out, open("figs/eval_equalstep.json", "w"), indent=2, default=float)
print()
print("saved figs/eval_equalstep.json（三种子均值）")
