# -*- coding: utf-8 -*-
"""make_holdouts.py -- 生成真正独立的评估集（M=256 与 M=512）。

ZCode P0-1：原评估读 tr_M256 前 2000 行，而验证集（用于选 best.pt）是前 10000 行，
两者重叠。更糟的是 ev_M512 的种子也是 0，与训练集同源，所以 M=512 的迁移评估
同样落在训练池上。这里用全新种子生成两个真正独立、模型从未见过的评估集。
"""
import os, json
import numpy as np
import capa_lib as C

# 数据根目录：默认沿用本机数据盘；若不存在（例如在复现包里运行），
# 回退到本脚本上一级目录下的 data/。环境变量 CAPA_DATA 可覆盖。
DATA = os.environ.get("CAPA_DATA") or ("F:/capa_data" if os.path.isdir("F:/capa_data")
                                       else os.path.join(os.path.dirname(os.path.dirname(
                                           os.path.abspath(__file__))), "data"))
os.makedirs(DATA, exist_ok=True)
print("data root:", DATA)

for M, N, name in [(256, 6000, "test_M256_holdout2"), (512, 3000, "test_M512_holdout")]:
    out = os.path.join(DATA, name)
    if os.path.exists(out + "_x.npy"):
        j = json.load(open(out + "_meta.json", encoding="utf-8"))
        print("  %s already exists (N=%d, seed=%s)" % (name, j["N"], j.get("seed")))
        continue
    t = C.make_dataset(out, N, M, seed=999999)
    json.dump({"M": M, "N": N, "seed": 999999, "rayleigh_m": C.RAYLEIGH,
               "lambda": C.LAMBDA, "r_range": [C.R_MIN, C.R_MAX], "purpose": "independent holdout"},
              open(out + "_meta.json", "w"), indent=2)
    print("  %s generated: N=%d M=%d in %.1f s" % (name, N, M, t))

print()
print("=== independence check: first holdout sample vs train-set first samples ===")
for name, M in [("tr_M256", 256), ("test_M256_holdout2", 256), ("tr_M128", 128),
                ("ev_M512", 512), ("test_M512_holdout", 512)]:
    f = os.path.join(DATA, "%s_x.npy" % name)
    if not os.path.exists(f):
        print("  %-22s (missing, skipped)" % name)
        continue
    x = np.load(f, mmap_mode="r")
    print("  %-22s first-sample values [:3]: %s" % (name, np.round(np.asarray(x[0, :3]), 5)))
