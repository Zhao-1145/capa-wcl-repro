"""
Baseline channel estimators for CAPA near-field channels.

B1  LS                : raw observation (no structure exploited)
B2  LMMSE             : linear MMSE using the prior channel covariance
B3  Polar-grid OMP    : dictionary matching on a uniform (r,theta) grid
B4  Polar OMP + refine: B3 followed by coarse-to-fine local refinement
B5  Perfect CSI       : oracle (NMSE = 0 reference)

All baselines return estimated (r, theta) per sample, from which the channel
is reconstructed analytically; NMSE is then computed on the reconstructed
channel so that every method is scored identically.
"""
import os, json, time, argparse
import numpy as np
import capa_lib as C


# ----------------------------------------------------------------------
def build_dictionary(M, n_r, n_th, r_lo=C.R_MIN, r_hi=C.R_MAX,
                     th_lo=C.TH_MIN, th_hi=C.TH_MAX):
    rs = np.linspace(r_lo, r_hi, n_r, dtype=np.float32)
    ths = np.linspace(th_lo, th_hi, n_th, dtype=np.float32)
    RR, TT = np.meshgrid(rs, ths, indexing="ij")
    rr = RR.ravel(); tt = TT.ravel()
    D = C.channel_from_params(rr, tt, M)             # (G, M) complex64
    D = D / np.linalg.norm(D, axis=1, keepdims=True)
    return D, rr, tt


def polar_omp(y, D, rr, tt):
    """y : (B, M) complex64 -> (r_hat, th_hat), one atom per sample."""
    corr = y @ np.conj(D).T                          # (B, G)
    idx = np.argmax(np.abs(corr), axis=1)
    return rr[idx].copy(), tt[idx].copy()


def polar_omp_refine(y, D, rr, tt, M, rounds=3, shrink=0.25, n_grid=41):
    """Coarse grid match followed by coarse-to-fine local refinement."""
    r_hat, th_hat = polar_omp(y, D, rr, tt)
    r_span  = (C.R_MAX - C.R_MIN) * 0.25
    th_span = (C.TH_MAX - C.TH_MIN) * 0.25
    for _ in range(rounds):
        nr = max(3, n_grid); nt = max(3, n_grid)
        rs  = np.linspace(-r_span,  r_span,  nr, dtype=np.float32)
        ths = np.linspace(-th_span, th_span, nt, dtype=np.float32)
        best_val = np.full(len(r_hat), -1.0, dtype=np.float32)
        br = r_hat.copy(); bt = th_hat.copy()
        for a in rs:
            cand_r = np.clip(r_hat + a, C.R_MIN, C.R_MAX)
            for b in ths:
                cand_t = np.clip(th_hat + b, C.TH_MIN, C.TH_MAX)
                Hc = C.channel_from_params(cand_r, cand_t, M)
                Hn = Hc / np.linalg.norm(Hc, axis=1, keepdims=True)
                val = np.abs(np.sum(np.conj(Hn) * y, axis=1)).astype(np.float32)
                upd = val > best_val
                best_val[upd] = val[upd]
                br[upd] = cand_r[upd]; bt[upd] = cand_t[upd]
        r_hat, th_hat = br, bt
        r_span *= shrink; th_span *= shrink
    return r_hat, th_hat


def lmmse(y, snr_db, Ch, M):
    """Per-sample LMMSE using the prior covariance Ch (M x M)."""
    # Ch is complex Hermitian; eigh handles it natively. Casting to float64
    # silently drops the imaginary part (see the ComplexWarning) and yields a
    # real orthogonal U instead of a unitary one.
    w, U = np.linalg.eigh(Ch)
    w = np.clip(w, 0.0, None)
    p = np.mean(np.abs(y) ** 2, axis=1)
    snr = 10.0 ** (np.asarray(snr_db, np.float64) / 10.0)
    var = p / snr                                     # (B,)
    out = np.empty_like(y)
    Uy = U.conj().T @ y.T                             # (M, B)
    for i in range(y.shape[0]):
        out[i] = (U @ (w / (w + var[i]) * Uy[:, i]))
    return out


def score(r_hat, th_hat, h_true, M, y=None):
    """NMSE of the reconstructed channel.

    Two variants are returned:
      nmse_raw  : reconstruct phi(r_hat, th_hat) directly (no gain fit)
      nmse_fit  : reconstruct alpha * phi(r_hat, th_hat) with a LS gain fit
    The raw variant is dominated by the common-phase error induced by any
    range error; the fitted variant isolates the shape mismatch.
    """
    phi = C.channel_from_params(r_hat, th_hat, M)
    out = {"nmse_raw": C.nmse(phi, h_true)}
    if y is not None:
        out["nmse_fit"] = C.nmse(C.fit_gain_and_reconstruct(r_hat, th_hat, y, M), h_true)
    return out


# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="F:/capa_data/capa_M256")
    ap.add_argument("--n-eval", type=int, default=2000)
    ap.add_argument("--grid", default="50,100")
    ap.add_argument("--dense-grid", default="100,200")
    ap.add_argument("--out", default="runs/baselines.json")
    ap.add_argument("--snr", type=float, default=10.0)
    args = ap.parse_args()

    meta = json.load(open(args.data + "_meta.json"))
    M = int(meta["M"])
    x = np.load(args.data + "_x.npy", mmap_mode="r")
    ylab = np.load(args.data + "_y.npy", mmap_mode="r")

    n = min(args.n_eval, x.shape[0])
    raw = np.asarray(x[:n])
    h_true = (raw[:, :M] + 1j * raw[:, M:]).astype(np.complex64)
    r_true = ylab[:n, 0].astype(np.float32)
    th_true = ylab[:n, 1].astype(np.float32)

    rng = np.random.RandomState(7)
    y_obs = C.add_noise(h_true, np.full(n, args.snr, np.float32), rng)

    res = {"M": M, "n_eval": n, "snr_db": args.snr}
    t0 = time.time()

    # B1  LS
    res["B1_LS"] = {"nmse": C.nmse(y_obs, h_true), "time_s": time.time() - t0}
    print("B1 LS            NMSE %.4f" % res["B1_LS"]["nmse"], flush=True)

    # B2  LMMSE
    t1 = time.time()
    Ch = (h_true.conj().T @ h_true) / n
    h_lmmse = lmmse(y_obs, np.full(n, args.snr), Ch, M)
    res["B2_LMMSE"] = {"nmse": C.nmse(h_lmmse, h_true), "time_s": time.time() - t1}
    print("B2 LMMSE         NMSE %.4f  (%.1fs)" %
          (res["B2_LMMSE"]["nmse"], res["B2_LMMSE"]["time_s"]), flush=True)

    def report(tag, r_h, t_h, extra):
        sc = score(r_h, t_h, h_true, M, y=y_obs)
        sc["rmse_r"] = float(np.sqrt(np.mean((r_h - r_true) ** 2)))
        sc["rmse_th"] = float(np.sqrt(np.mean((t_h - th_true) ** 2)))
        sc.update(extra)
        res[tag] = sc
        print("%-16s NMSEraw %.4f   NMSEfit %.5f   rmse_r %.3f m  rmse_th %.5f rad  (%.1fs)"
              % (tag, sc["nmse_raw"], sc["nmse_fit"], sc["rmse_r"], sc["rmse_th"],
                 sc["time_s"]), flush=True)

    # B3  polar OMP
    t1 = time.time()
    nr, nth = [int(v) for v in args.grid.split(",")]
    D, rr, tt = build_dictionary(M, nr, nth)
    tdict = time.time() - t1
    t1 = time.time(); r3, t3 = polar_omp(y_obs, D, rr, tt)
    report("B3_OMP", r3, t3, {"grid": [nr, nth], "time_s": time.time() - t1,
                              "dict_time_s": tdict})

    # B4  polar OMP + refinement
    t1 = time.time(); r4, t4 = polar_omp_refine(y_obs, D, rr, tt, M, rounds=2)
    report("B4_OMP_refine", r4, t4, {"time_s": time.time() - t1})

    # B5  dense grid OMP
    t1 = time.time()
    nr2, nth2 = [int(v) for v in args.dense_grid.split(",")]
    D2, rr2, tt2 = build_dictionary(M, nr2, nth2)
    tdict2 = time.time() - t1
    t1 = time.time(); r5, t5 = polar_omp(y_obs, D2, rr2, tt2)
    report("B5_OMP_dense", r5, t5, {"grid": [nr2, nth2], "time_s": time.time() - t1,
                                    "dict_time_s": tdict2})

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(res, open(args.out, "w"), indent=2)
    print("saved", args.out, flush=True)


if __name__ == "__main__":
    main()
