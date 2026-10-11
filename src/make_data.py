"""Generate the noiseless CAPA channel dataset."""
import os, sys, json, time, argparse
import numpy as np
import capa_lib as C

ap = argparse.ArgumentParser()
ap.add_argument("--M", type=int, default=256)
ap.add_argument("--N", type=int, default=2_000_000)
ap.add_argument("--out", default="F:/capa_data/capa_M256")
ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()

os.makedirs(os.path.dirname(args.out), exist_ok=True)
print("generating M=%d N=%d -> %s" % (args.M, args.N, args.out), flush=True)
t = C.make_dataset(args.out, args.N, args.M, seed=args.seed)
size = os.path.getsize(args.out + "_x.npy") + os.path.getsize(args.out + "_y.npy")
json.dump({"M": args.M, "N": args.N, "seed": args.seed,
           "rayleigh_m": C.RAYLEIGH, "lambda": C.LAMBDA,
           "r_range": [C.R_MIN, C.R_MAX]},
          open(args.out + "_meta.json", "w"), indent=2)
print("done in %.1f s (%.0f samples/s), %.2f GB" %
      (t, args.N / t, size / 1e9), flush=True)
