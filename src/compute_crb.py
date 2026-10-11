# -*- coding: utf-8 -*-
"""compute_crb.py -- 近场 (r, theta) 的克拉美-罗界，用正交投影做数值稳定处理.

为什么用投影而不是直接求逆（口径问题，不是数值问题）
--------------------------------------------------
解析上  dh/dr = h * (-j 2 pi/lambda - 1/d) * (r - s sin theta)/d
其中第一项 -j(2 pi/lambda) h 与增益的虚部方向 d mu/d alpha_I = j h 完全共线。
实测共线度 1-5e-7 (r=6 m) 至 1-2e-10 (r=16 m)；
4x4 FIM 条件数随几何从 2e9 (r=5 m) 变化到 1e13 (r=18 m)。

重要更正（ZCode 审查 P6，经独立复核确认）：
    先前此处写【任何求逆再相减的写法都会被灾难性相消污染】——此说法不成立。
    实测 float64 下直接求逆、Schur 补、投影三条路径结果一致（相对差 0.5%-0.8%）；
    条件数 1e9-1e13 对 float64 (eps~2.2e-16) 只损失 1e-5 至 1e-4 的相对精度。
    早先记录的 0.1 mm 是口径混淆——把增益已知的 0.222 mm 当成了增益未知的界，
    不是数值灾难。

第八轮补充（更精确的边界）：
    失败模式确实存在，但不属于"求逆"这一大类。在条件数最高的几何
    （r=16 m, th=1.3 rad, cond=9.6e12）处实测：
        投影 11.025 m   Schur 补 10.952 m   伪逆(rcond=1e-12) 0.00022 m
    即带截断阈值的伪逆会丢掉有效奇异值而给出差 4 个数量级的结果；
    而投影与 Schur 补（真正的算法）仍然一致。
    结论：危险的是"用截断阈值处理病态矩阵"，不是"求逆"本身。

因此投影法保留为实现选择而非正确性必需；它与 Schur 补在数学上恒等
（增益线性进入观测模型时，profiled CRB 等于投影 CRB）。

投影做法: 先把增益张成的子空间 H = span{h, j h} 投影掉，

口径
   A  增益已知    : 不投影，直接用 [dh/dr, dh/dtheta]
   C  幅度已知    : |alpha| 已知、载波相位 psi 未知 -> 3x3 FIM + Schur 消去 psi
   B  增益未知    : 投影掉增益子空间后再算

   注意 C 不能用投影法：复空间中 span{h} = span{j h}，投影只能一次消掉两维，
   那得到的仍是 B。C 必须用 3x3 FIM 的 Schur 补。

输出 figs/crb.json
"""
import json, math
import numpy as np
import capa_lib as C

M = 256
LAM = float(C.LAMBDA)
s = C.aperture_grid(M).astype(np.float64)


def derivs(r, th):
    r = float(r); th = float(th)
    d = np.sqrt(r * r + s * s - 2.0 * r * s * np.sin(th))
    h = np.exp(-1j * 2.0 * np.pi * d / LAM) / d
    coef = -1j * 2.0 * np.pi / LAM - 1.0 / d
    return h, h * coef * ((r - s * np.sin(th)) / d), h * coef * (-(r * s * np.cos(th)) / d)


def crb(r, th, snr_db):
    h, hr, ht = derivs(r, th)
    p = float(np.mean(np.abs(h) ** 2))
    sigma2 = p / (10.0 ** (snr_db / 10.0))
    k = 2.0 / sigma2

    # 口径 A
    JA = np.column_stack([hr, ht])
    CA = np.linalg.inv(k * np.real(JA.conj().T @ JA))
    a_r, a_t = math.sqrt(max(CA[0, 0], 0.0)), math.sqrt(max(CA[1, 1], 0.0))

    # 口径 B：投影掉增益子空间 span{h, j h}
    H = np.column_stack([h, 1j * h])
    Q, _ = np.linalg.qr(H)                       # 正交基
    P = np.eye(M, dtype=complex) - Q @ Q.conj().T
    JB = np.column_stack([P @ hr, P @ ht])
    FB = k * np.real(JB.conj().T @ JB)
    try:
        CB = np.linalg.inv(FB)
        b_r, b_t = math.sqrt(max(CB[0, 0], 0.0)), math.sqrt(max(CB[1, 1], 0.0))
    except np.linalg.LinAlgError:
        b_r = b_t = float("inf")

    # 口径 C：|alpha| 已知、载波相位 psi 未知 -> 3x3 FIM，Schur 消去 psi
    J3 = np.column_stack([hr, ht, 1j * h])
    F3 = k * np.real(J3.conj().T @ J3)
    Faa, Fab, Fbb = F3[:2, :2], F3[:2, 2:], F3[2:, 2:]
    try:
        FC = Faa - Fab @ np.linalg.inv(Fbb) @ Fab.T
        c_r, c_t = math.sqrt(max(np.linalg.inv(FC)[0, 0], 0.0)), math.sqrt(max(np.linalg.inv(FC)[1, 1], 0.0))
    except np.linalg.LinAlgError:
        c_r = c_t = float("inf")

    # 共线度诊断
    col = abs(np.vdot(1j * h, hr)) / (np.linalg.norm(h) * np.linalg.norm(hr))
    return a_r, a_t, b_r, b_t, c_r, c_t, float(col)


print("共线度诊断（=1 表示距离信息被增益完全吸收）与投影后残余能量")
for (r, th) in [(10.0, 0.0), (10.0, 1.2), (5.0, 0.0), (5.0, 1.4), (17.5, 0.0)]:
    h, hr, ht = derivs(r, th)
    H = np.column_stack([h, 1j * h]); Q, _ = np.linalg.qr(H)
    P = np.eye(M, dtype=complex) - Q @ Q.conj().T
    col = abs(np.vdot(1j * h, hr)) / (np.linalg.norm(h) * np.linalg.norm(hr))
    print("   r=%5.1f th=%4.2f | 共线度=%.10f | ||P hr||/||hr||=%.3e | ||P ht||/||ht||=%.4f"
          % (r, th, col, np.linalg.norm(P @ hr) / np.linalg.norm(hr),
             np.linalg.norm(P @ ht) / np.linalg.norm(ht)))

# 重要：theta -> +-pi/2 时 dd/dtheta = -r s cos(theta)/d -> 0，角度不可辨识，
# CRB 发散。对全角域取平均会被这个退化区主导，得到没有意义的数字。
# 因此把 CRB 报告限制在 |theta| <= 1.2 rad（避开端射退化区），并显式说明。
TH_LIM = 1.2
rng = np.random.RandomState(2026)
N = 400
R = rng.uniform(C.R_MIN, C.R_MAX, N)
TH = rng.uniform(-TH_LIM, TH_LIM, N)
snrs = [-5, 0, 5, 10, 15, 20]
out = {"M": M, "n": N, "snr": snrs, "theta_limit": TH_LIM,
       "calibers": {"A": "gain fully known",
                    "C": "|alpha| known, carrier phase unknown  <-- the setting of this paper",
                    "B": "gain fully unknown (applies to the dictionary baselines)"},
       # 聚合口径：RMS = sqrt(mean(square))，非算术平均。
       # 本数据上 RMS 得 2.23 m、均值得 1.92 m；论文引用 RMS。
       "aggregation": "rms",
       "rng_seed": 2026,
       "A_rmse_r": [], "A_rmse_th": [],
       "C_rmse_r": [], "C_rmse_th": [],
       "B_rmse_r": [], "B_rmse_th": [], "collinearity": []}
for snr in snrs:
    ar, at, br, bt, cr_, ct_, cl = [], [], [], [], [], [], []
    for r, th in zip(R, TH):
        x = crb(r, th, snr)
        ar.append(x[0]); at.append(x[1]); br.append(x[2]); bt.append(x[3])
        cr_.append(x[4]); ct_.append(x[5]); cl.append(x[6])
    out["A_rmse_r"].append(float(np.sqrt(np.nanmean(np.square(ar)))))
    out["A_rmse_th"].append(float(np.sqrt(np.nanmean(np.square(at)))))
    out["B_rmse_r"].append(float(np.sqrt(np.nanmean(np.square(br)))))
    out["B_rmse_th"].append(float(np.sqrt(np.nanmean(np.square(bt)))))
    out["C_rmse_r"].append(float(np.sqrt(np.nanmean(np.square(cr_)))))
    out["C_rmse_th"].append(float(np.sqrt(np.nanmean(np.square(ct_)))))
    out["collinearity"].append(float(np.nanmedian(cl)))

D = json.load(open("figs/eval_results.json", encoding="utf-8"))
o = D["models"]["Ours-1.28M"]["rows"]
print()
print(" SNR | 实测 r  | A下界(增益已知) | 倍数 | B下界(增益未知) | 倍数")
for i, snr in enumerate(snrs):
    rr = o[i]["rmse_r"]
    b = out["B_rmse_r"][i]
    print("%+4.0f | %7.4f | %13.3e | %5.0fx | %14.4g | %s"
          % (snr, rr, out["A_rmse_r"][i], rr / out["A_rmse_r"][i], b,
             ("%.2fx" % (rr / b)) if np.isfinite(b) else "不可辨识"))
print()
print("三口径对照（论文真实假设是 C，不是 B）")
print(" SNR | 实测 r  | A(增益已知) | C(幅度已知) | B(增益未知) | 实测/C | 实测/B")
for i, snr in enumerate(snrs):
    rr = o[i]["rmse_r"]; a = out["A_rmse_r"][i]; c = out["C_rmse_r"][i]; b = out["B_rmse_r"][i]
    print("%+4.0f | %7.4f | %11.3e | %11.3e | %11.4g | %5.2fx | %5.2fx"
          % (snr, rr, a, c, b, rr / c, rr / b))
print()
print("注：以下 CRB 限制在 |theta| <= %.1f rad（端射区角度不可辨识，CRB 发散）；" % TH_LIM)
print("    实测值则是全角域平均，因此角度一栏只能作量级参考，不可直接相除。")
print(" SNR | 实测 th  | A下界(增益已知) | 倍数 | B下界(增益未知) | 倍数")
for i, snr in enumerate(snrs):
    tr = o[i]["rmse_th"]
    print("%+4.0f | %8.6f | %13.6f | %5.1fx | %14.6f | %5.1fx"
          % (snr, tr, out["A_rmse_th"][i], tr / out["A_rmse_th"][i],
             out["B_rmse_th"][i], tr / out["B_rmse_th"][i]))
json.dump(out, open("figs/crb.json", "w"), indent=2)
print("\nsaved figs/crb.json")
