# -*- coding: utf-8 -*-
"""reeval_holdout_full2.py -- 修正 nmse_raw 定义，并补做迁移评估。"""
import json, math
import numpy as np
import torch

import capa_lib as C
from train import CAPANet

torch.set_num_threads(10)
T95 = {2: 4.303}
SNR = [-5.0, 0.0, 5.0, 10.0, 15.0, 20.0]
H256 = "F:/capa_data/test_M256_holdout2"
H512 = "F:/capa_data/test_M512_holdout"

ARMS = {"cls_raw": ["eq_cls_s0", "eq_cls_s1", "eq_cls_s2"],
        "phase_mag": ["eq_phmag_s0", "eq_phmag_s1", "eq_phmag_s2"],
        "reg": ["eq_reg_s0", "eq_reg_s1", "eq_reg_s2"],
        "recon": ["eq_recon_s0", "eq_recon_s1", "eq_recon_s2"],
        "capA1": ["eq_capA1_s0", "eq_capA1_s1", "eq_capA1_s2"],
        "capA3": ["eq_capA3_s0", "eq_capA3_s1", "eq_capA3_s2"]}
M128 = ["eq_m128_s0", "eq_m128_s1", "eq_m128_s2"]

def read(prefix, M, n):
    x = np.load(prefix + "_x.npy", mmap_mode="r")
    y = np.load(prefix + "_y.npy", mmap_mode="r")
    raw = np.asarray(x[:n])
    return ((raw[:, :M] + 1j*raw[:, M:]).astype(np.complex64),
            y[:n, 0].astype(np.float64), y[:n, 1].astype(np.float64))

def load_model(run):
    ck = torch.load("runs/%s/best.pt" % run, map_location="cpu", weights_only=False)
    hidden = [int(v) for v in ck["args"]["hidden"].split(",")]
    m = CAPANet(ck["in_dim"], hidden, head=ck["args"].get("head", "cls"))
    m.load_state_dict(ck["model"]); m.eval()
    return m, ck["mode"], ck.get("M", 256)

def eval_on(models, prefix, M_eval, n, snr):
    h, rt, tt = read(prefix, M_eval, n)
    rng = np.random.RandomState(11)
    y = C.add_noise(h, np.full(n, snr, np.float32), rng)
    out = []
    for (m, mode, M_in) in models:
        yin = C.resample_channel(y, M_eval, M_in) if M_eval != M_in else y
        with torch.no_grad():
            feat = C.preprocess(yin, mode)
            xt = torch.from_numpy(feat.reshape(n, -1))
            lr, lt = m(xt)
            rh, th = m.decode(lr, lt)
        rn = rh.numpy().astype(np.float64); tn = th.numpy().astype(np.float64)
        phi = C.channel_from_params(rn, tn, M_eval)
        fit = C.fit_gain_and_reconstruct(rn, tn, y, M_eval)
        out.append(dict(nmse=float(C.nmse(fit, h)), nmse_raw=float(C.nmse(phi, h)),
                        rmse_r=float(np.sqrt(np.mean((rn-rt)**2))),
                        rmse_th=float(np.sqrt(np.mean((tn-tt)**2)))))
    return out

def agg(rows):
    a = {k: np.array([r[k] for r in rows]) for k in rows[0]}
    o = {k: float(a[k].mean()) for k in a}
    for k in a:
        o[k + "_ci"] = float(T95[2]*a[k].std(ddof=1)/math.sqrt(3))
    return o

M6 = {k: [load_model(r) for r in v] for k, v in ARMS.items()}
MM = [load_model(r) for r in M128]

res = {"snr": SNR, "models": {}, "M256_holdout": H256, "M512_holdout": H512, "transfer": {}}
print("=" * 92)
print("独立 holdout 重评（M=256, N=2000）—— raw NMSE 已按「不拟合增益的重构」定义")
print("=" * 92)
for snr in SNR:
    entry = {}
    for k in ARMS:
        entry[k] = agg(eval_on(M6[k], H256, 256, 2000, snr))
    h, _, _ = read(H256, 256, 2000)
    rng = np.random.RandomState(11)
    y = C.add_noise(h, np.full(2000, snr, np.float32), rng)
    entry["LS"] = {"nmse": float(C.nmse(y, h)), "nmse_raw": float(C.nmse(y, h))}
    res["models"][str(snr)] = entry
    o = entry["cls_raw"]
    print("  %5.1f dB  fit %.4e  raw %.4f  rmse_r %.4f  |  phmag fit %.4e raw %.4f  |  reg fit %.4e"
          % (snr, o["nmse"], o["nmse_raw"], o["rmse_r"],
             entry["phase_mag"]["nmse"], entry["phase_mag"]["nmse_raw"], entry["reg"]["nmse"]))

print()
print("=" * 92)
print("迁移：M=128 训练的三种子，在 holdout 上评估 M=256 与 M=512")
print("=" * 92)
for M_eval, prefix in [(256, H256), (512, H512)]:
    for snr in [10.0, 20.0]:
        # 第十八轮：原为 1500，与主评估的 n=2000 不一致，需 unify_transfer_n.py 二次覆盖。
        # 统一为 2000 后本脚本单独即可再生归档 JSON（第十六轮可复现性缺口 #2）。
        nat = agg(eval_on(M6["cls_raw"], prefix, M_eval, 2000, snr))
        tr = agg(eval_on(MM, prefix, M_eval, 2000, snr))
        pen = 10*math.log10(tr["nmse"]/nat["nmse"])
        res["transfer"]["M%d_%ddB" % (M_eval, int(snr))] = {"native": nat, "M128": tr,
                                                            "penalty_dB": pen, "n_eval": 2000}
        print("  M_te=%d @%2.0f dB: 原生 %.4e  迁移 %.4e  代价 %.2f dB"
              % (M_eval, snr, nat["nmse"], tr["nmse"], pen))

res["transfer_note"] = "n_eval=2000 for both sides, matching the main evaluation"
json.dump(res, open("figs/holdout_eval_full.json", "w"), indent=2, default=float)
print()
print("saved figs/holdout_eval_full.json")
