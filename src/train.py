"""
Training for the deep parametric CAPA channel estimator.

DESIGN NOTE (important)
-----------------------
Direct regression of (r, theta) fails outright.  The channel manifold
    phi(r,theta)(s) = exp(-j 2 pi d(s)/lambda) / d(s)
oscillates in r with period lambda/2 = 0.05 m.  Over r in [5,18] m the phase
wraps ~260 times, so any channel-domain reconstruction loss is a
needle-in-a-haystack landscape for gradient descent; empirically the network
collapses to a constant boundary output (rmse_r = 7.53 m == always predicting
r = R_MIN).

We therefore formulate estimation as CLASSIFICATION over the parameter grid,
decoded by SOFT-ARGMAX.  Cross-entropy is smooth, and soft-argmax interpolates
between bin centres, so the continuous parameters are recovered without the
grid-mismatch error of hard dictionary matching.

Heads:  --head cls   (classification + soft-argmax)   [default]
        --head reg   (direct regression)              [ablation, known to fail]
"""
import os, sys, time, math, argparse, json, csv
import numpy as np
import torch
import torch.nn as nn

import capa_lib as C

torch.set_num_threads(os.cpu_count() or 8)

G_R, G_TH = 128, 256          # grid sizes
SIG_BINS   = 1.5              # soft-label width, in bins


# 布局约定：x = [real(h) | imag(h)]，两者都是 exp(-j 2 pi d/lambda)/d 的实/虚部。
# reconstruct() 返回同一布局，故 recon 损失可直接相减。
# ----------------------------------------------------------------------
class CAPANet(nn.Module):
    def __init__(self, in_dim, hidden, head="cls",
                 G_r=G_R, G_th=G_TH,
                 r_lo=C.R_MIN, r_hi=C.R_MAX, t_lo=C.TH_MIN, t_hi=C.TH_MAX):
        super().__init__()
        layers, prev = [], in_dim
        for h in hidden:
            layers += [nn.Linear(prev, h), nn.ReLU()]
            prev = h
        self.trunk = nn.Sequential(*layers)
        self.head_kind = head
        self.G_r, self.G_th = G_r, G_th
        out_r = G_r if head == "cls" else 1
        out_th = G_th if head == "cls" else 1
        self.head_r = nn.Linear(prev, out_r)
        self.head_th = nn.Linear(prev, out_th)
        self.register_buffer("c_r", torch.linspace(r_lo, r_hi, G_r))
        self.register_buffer("c_th", torch.linspace(t_lo, t_hi, G_th))
        self.register_buffer("r_lo", torch.tensor(float(r_lo)))
        self.register_buffer("r_hi", torch.tensor(float(r_hi)))
        self.register_buffer("t_lo", torch.tensor(float(t_lo)))
        self.register_buffer("t_hi", torch.tensor(float(t_hi)))
        self.d_aper = float(C.D_APER)

    def forward(self, x):
        return self.head_r(self.trunk(x)), self.head_th(self.trunk(x))

    def decode(self, lr, lt, tau=1.0):
        if self.head_kind == "reg":
            r = self.r_lo + (self.r_hi - self.r_lo) * torch.sigmoid(lr[:, 0])
            th = self.t_lo + (self.t_hi - self.t_lo) * torch.sigmoid(lt[:, 0])
            return r, th
        pr = torch.softmax(lr / tau, dim=-1)
        pt = torch.softmax(lt / tau, dim=-1)
        return (pr * self.c_r).sum(-1), (pt * self.c_th).sum(-1)

    def reconstruct(self, r, th, M):
        s = torch.linspace(-self.d_aper / 2, self.d_aper / 2, M,
                           device=r.device, dtype=r.dtype).unsqueeze(0)
        r = r.unsqueeze(1); th = th.unsqueeze(1)
        d = torch.sqrt(r * r + s * s - 2.0 * r * s * torch.sin(th) + 1e-12)
        ph = -2.0 * math.pi * d / C.LAMBDA
        return torch.cos(ph) / d, torch.sin(ph) / d


def count_params(m):
    return sum(p.numel() for p in m.parameters())


def load_dataset(prefix, max_gb=3.2, n_rows=None):
    """Load the dataset into RAM as float16 to avoid memmap random-access stalls.

    Reading 1024 random rows per batch from a 4 GB memmap thrashes the page
    cache and was measured at ~2.4 k samples/s, ~13x slower than the compute
    limit.  Holding the data in RAM as float16 costs half the memory and the
    per-batch cast to float32 is negligible.
    """
    x = np.load(prefix + "_x.npy", mmap_mode="r")
    y = np.load(prefix + "_y.npy", mmap_mode="r")
    n, d = x.shape
    # 只取训练真正用到的前缀：val_idx 与 [tr_lo, tr_hi) 都落在前 n_rows 行内。
    # 不这样做会把整个数据集读进内存，在内存吃紧的机器上触发换页。
    if n_rows is not None and 0 < n_rows < n:
        x = x[:n_rows]
        y = y[:n_rows]
        n = n_rows
    sz_gb = n * d * 2 / 1e9
    if sz_gb > max_gb:
        print("  dataset %.2f GB (fp16) exceeds cap %.2f GB -> using memmap" %
              (sz_gb, max_gb), flush=True)
        return x, y, False
    t0 = time.time()
    xa = np.asarray(x, dtype=np.float16)
    ya = np.asarray(y, dtype=np.float32)
    print("  loaded %d x %d into RAM as fp16 (%.2f GB) in %.1f s" %
          (n, d, sz_gb, time.time() - t0), flush=True)
    return xa, ya, True


def soft_target(v, centers, sigma):
    d = (v.unsqueeze(1) - centers.unsqueeze(0)) ** 2
    w = torch.exp(-d / (2.0 * sigma * sigma))
    return w / w.sum(dim=1, keepdim=True).clamp_min(1e-12)


# ----------------------------------------------------------------------
_INRAM = {"on": False}


def make_batch(xmm, idx, M, mode, rng, snr_lo=-5.0, snr_hi=20.0):
    if _INRAM["on"]:
        raw = xmm[idx].astype(np.float32)
    else:
        raw = np.asarray(xmm[idx])
    h_true = (raw[:, :M] + 1j * raw[:, M:]).astype(np.complex64)
    snr = rng.uniform(snr_lo, snr_hi, size=len(idx)).astype(np.float32)
    y = C.add_noise(h_true, snr, rng)
    return C.preprocess(y, mode), h_true


@torch.no_grad()
def evaluate(model, xmm, ymm, idx, M, mode, snr_db, max_n=3000, tau=1.0):
    model.eval()
    rng = np.random.RandomState(12345)
    n = min(max_n, len(idx)); sel = np.sort(idx[:n])
    raw = np.asarray(xmm[sel])
    h_true = (raw[:, :M] + 1j * raw[:, M:]).astype(np.complex64)
    yv = C.add_noise(h_true, np.full(n, snr_db, np.float32), rng)
    feat = C.preprocess(yv, mode)
    xt = torch.from_numpy(feat.reshape(n, -1))
    lr, lt = model(xt)
    r_hat, th_hat = model.decode(lr, lt, tau=tau)
    r_np = r_hat.numpy().astype(np.float64)
    t_np = th_hat.numpy().astype(np.float64)
    phi = C.channel_from_params(r_np, t_np, M)
    h_fit = C.fit_gain_and_reconstruct(r_np, t_np, yv, M)
    out = {"nmse": C.nmse(h_fit, h_true),
           "nmse_raw": C.nmse(phi, h_true),
           "rmse_r": float(np.sqrt(np.mean((r_np - ymm[sel, 0]) ** 2))),
           "rmse_th": float(np.sqrt(np.mean((t_np - ymm[sel, 1]) ** 2))),
           "ls_nmse": C.nmse(yv, h_true)}
    model.train()
    return out


# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="phase_mag")
    ap.add_argument("--head", default="cls", choices=["cls", "reg"])
    ap.add_argument("--hidden", default="1024,512,256")
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--minutes", type=float, default=10.0)
    ap.add_argument("--data", default="F:/capa_data/capa_M256")
    ap.add_argument("--out", default="runs/tmp")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--val-every", type=int, default=200)
    ap.add_argument("--loss", default="auto", choices=["auto", "recon"],
                    help="auto = cls uses cross-entropy, reg uses parameter MSE; "
                         "recon = regress (r,theta) against the RECONSTRUCTION loss.")
    ap.add_argument("--max-steps", type=int, default=10**9)
    ap.add_argument("--n-train", type=int, default=0,
                    help="cap the training pool size (0 = use all)")
    ap.add_argument("--w-th", type=float, default=1.0)
    ap.add_argument("--g-r", type=int, default=G_R)
    ap.add_argument("--sig-bins", type=float, default=SIG_BINS)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    rng = np.random.RandomState(args.seed)

    M = int(json.load(open(args.data + "_meta.json"))["M"])
    hidden = [int(v) for v in args.hidden.split(",")]
    # 先只读 npy 头拿到样本总数，据此决定要加载多少行（避免整库进内存）
    N = np.load(args.data + "_x.npy", mmap_mode="r").shape[0]
    n_val = min(10000, N // 5)
    tr_hi = N if args.n_train <= 0 else min(N, n_val + args.n_train)
    xmm, ymm, inram = load_dataset(args.data, n_rows=tr_hi)
    _INRAM["on"] = inram
    print("  memory: loading only the first %d rows (need up to tr_hi=%d)" % (xmm.shape[0], tr_hi), flush=True)
    val_idx = np.arange(n_val)
    tr_lo = n_val
    tr_idx = np.arange(tr_lo, tr_hi)
    print("  train pool: [%d, %d) = %d samples" % (tr_lo, tr_hi, tr_hi - tr_lo), flush=True)

    in_dim = C.n_input_channels(args.mode) * M
    model = CAPANet(in_dim, hidden, head=args.head, G_r=args.g_r)
    os.makedirs(args.out, exist_ok=True)
    logf = open(os.path.join(args.out, "log.csv"), "w", newline="")
    logw = csv.writer(logf)
    logw.writerow(["step", "epoch", "loss", "nmse_fit", "nmse_raw", "ls_nmse",
                   "rmse_r", "rmse_th", "elapsed_s", "sps", "lr"])
    json.dump(dict(vars(args), M=M, in_dim=in_dim, params=count_params(model), N=N),
              open(os.path.join(args.out, "config.json"), "w"), indent=2)
    print("head=%s mode=%s hidden=%s params=%d in_dim=%d M=%d N=%d" %
          (args.head, args.mode, hidden, count_params(model), in_dim, M, N), flush=True)

    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    est_steps = max(int(args.minutes * 60 * 30000 / args.batch), 10)
    # 若显式指定了 max_steps，让余弦调度恰好在该步数处走完（等步数比较必需）
    if args.max_steps < 10 ** 8:
        est_steps = max(args.max_steps, 10)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=est_steps,
                                                       eta_min=args.lr * 1e-2)
    sig_r = args.sig_bins * (C.R_MAX - C.R_MIN) / (args.g_r - 1)
    sig_t = args.sig_bins * (C.TH_MAX - C.TH_MIN) / (G_TH - 1)

    t0 = time.time(); deadline = t0 + args.minutes * 60.0
    step = epoch = 0; best = 1e9
    model.train()
    while True:
        if time.time() >= deadline or step >= args.max_steps:
            break
        epoch += 1
        n_batches = max(1, len(tr_idx) // args.batch)
        for _ in range(n_batches):
            if time.time() >= deadline or step >= args.max_steps:
                break
            # Direct random sampling instead of permuting the whole index
            # array: rng.permutation on ~2e6 indices cost 116 ms per epoch,
            # dwarfing the 215 ms model step.
            idx = rng.randint(tr_lo, tr_hi, size=args.batch)
            idx.sort()
            feat, _ = make_batch(xmm, idx, M, args.mode, rng)
            B = feat.shape[0]
            xt = torch.from_numpy(feat.reshape(B, -1))
            r_true = torch.from_numpy(ymm[idx, 0].astype(np.float32).copy())
            t_true = torch.from_numpy(ymm[idx, 1].astype(np.float32).copy())

            lr_, lt_ = model(xt)
            if args.head == "cls":
                tr_ = soft_target(r_true, model.c_r, sig_r)
                tt_ = soft_target(t_true, model.c_th, sig_t)
                l_r = -(tr_ * torch.log_softmax(lr_, -1)).sum(-1).mean()
                l_t = -(tt_ * torch.log_softmax(lt_, -1)).sum(-1).mean()
                loss = l_r + args.w_th * l_t
            elif args.loss == "recon":
                # 直接对重构损失做回归——正是论文 III-A 说会塌缩的那种训练。
                # 这个路径此前只存在于 pre-pipeline 的 smoke 运行里，无法从当前
                # 代码重放（ZCode P7）；补上后 7.53 m 可复现。
                rp, tp = model.decode(lr_, lt_)
                cr, ci = model.reconstruct(rp, tp, M)
                hrec = torch.cat([cr, ci], dim=1)                       # (B, 2M) = [real|imag]
                htrue = torch.from_numpy(xmm[idx].astype(np.float32).copy())
                loss = ((hrec - htrue) ** 2).mean()
            else:
                rp, tp = model.decode(lr_, lt_)
                loss = (((rp - r_true) / (C.R_MAX - C.R_MIN)) ** 2
                        + args.w_th * ((tp - t_true) / (C.TH_MAX - C.TH_MIN)) ** 2).mean()

            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            if step < est_steps:
                sched.step()
            step += 1

            if step % 50 == 0:
                el = time.time() - t0
                print("  step %6d ep %3d loss %.4f %.1f%% %.0f smp/s" %
                      (step, epoch, loss.item(), 100 * el / (args.minutes * 60),
                       step * args.batch / max(el, 1e-9)), flush=True)

            if step % args.val_every == 0:
                m = evaluate(model, xmm, ymm, val_idx, M, args.mode, 10.0)
                el = time.time() - t0
                logw.writerow([step, epoch, "%.4f" % loss.item(), "%.5f" % m["nmse"],
                               "%.5f" % m["nmse_raw"], "%.5f" % m["ls_nmse"],
                               "%.4f" % m["rmse_r"], "%.5f" % m["rmse_th"], "%.1f" % el,
                               "%.0f" % (step * args.batch / max(el, 1e-9)),
                               "%.2e" % opt.param_groups[0]["lr"]]); logf.flush()
                print("    [val 10dB] NMSEfit %.5f raw %.4f (LS %.4f)  rmse_r %.3f m  rmse_th %.5f rad" %
                      (m["nmse"], m["nmse_raw"], m["ls_nmse"], m["rmse_r"], m["rmse_th"]),
                      flush=True)
                if m["nmse"] < best:
                    best = m["nmse"]
                    torch.save({"model": model.state_dict(), "args": vars(args), "M": M,
                                "hidden": hidden, "mode": args.mode, "in_dim": in_dim,
                                "head": args.head, "step": step},
                               os.path.join(args.out, "best.pt"))

    torch.save({"model": model.state_dict(), "args": vars(args), "M": M,
                "hidden": hidden, "mode": args.mode, "in_dim": in_dim,
                "head": args.head, "step": step},
               os.path.join(args.out, "last.pt"))
    logf.close()
    fin = evaluate(model, xmm, ymm, val_idx, M, args.mode, 10.0)
    el = (time.time() - t0) / 60.0
    print("DONE steps=%d %.1fmin final NMSE %.4f (LS %.4f) best %.4f params=%d" %
          (step, el, fin["nmse"], fin["ls_nmse"], best, count_params(model)), flush=True)
    json.dump({"steps": step, "final_nmse": fin["nmse"], "ls_nmse": fin["ls_nmse"],
               "best_nmse": best, "rmse_r": fin["rmse_r"], "rmse_th": fin["rmse_th"],
               "params": count_params(model), "elapsed_min": el, "mode": args.mode,
               "head": args.head, "hidden": hidden},
              open(os.path.join(args.out, "result.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
