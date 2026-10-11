"""
CAPA near-field channel model, preprocessing, models, and dataset utilities.

Physics
-------
One-dimensional continuous aperture of length D, discretized at M points.
User k at polar coordinates (r_k, theta_k).  Distance from aperture point s:

    d_k(s) = sqrt( r_k^2 + s^2 - 2 r_k s sin(theta_k) )

Spherical-wave (near-field) channel response:

    h_k(s) = exp( -j 2 pi d_k(s) / lambda ) / d_k(s)

The channel is fully determined by (r_k, theta_k), i.e. 2 real parameters,
regardless of the discretization density M.  This is the structure exploited
by the learned estimator.
"""
import os, math, time
import numpy as np

LAMBDA   = 0.1                      # wavelength, 3 GHz
D_APER   = 1.0                      # aperture length (m)
R_MIN, R_MAX   = 5.0, 18.0          # user distance range (m)
TH_MIN, TH_MAX = -math.pi / 2.0, math.pi / 2.0
RAYLEIGH = 2.0 * D_APER ** 2 / LAMBDA     # 20 m

SCALE = 10.0                        # fixed input scaling (|h| ~ 1/d ~ 0.05-0.2)


def aperture_grid(M, D=D_APER):
    return np.linspace(-D / 2.0, D / 2.0, M, dtype=np.float32)


def channel_from_params(r, th, M, s=None):
    """r, th : (N,) arrays  ->  h : (N, M) complex64 (noiseless)."""
    if s is None:
        s = aperture_grid(M)
    r = np.asarray(r, np.float32).reshape(-1, 1)
    th = np.asarray(th, np.float32).reshape(-1, 1)
    s2 = s.reshape(1, -1)
    d = np.sqrt(r * r + s2 * s2 - 2.0 * r * s2 * np.sin(th))
    h = np.exp(-1j * 2.0 * np.pi * d / LAMBDA) / d
    return h.astype(np.complex64)


def n_input_channels(mode, M=None):
    """Number of feature channels produced by preprocess (flattened dim is this * M)."""
    return {"raw": 2, "phase": 2, "phase_mag": 3}[mode]


def preprocess(y, mode):
    """y : (B, M) complex64 noisy observation -> features (B, C, M) float32.

    raw       : [Re(y), Im(y)] * SCALE           (keeps absolute scale)
    phase     : [cos dphi, sin dphi] vs centre   (common phase removed)
    phase_mag : phase + normalised magnitude
    """
    B, M = y.shape
    if mode == "raw":
        return np.stack([y.real * SCALE, y.imag * SCALE], axis=1).astype(np.float32)

    ref = y[:, M // 2]
    z = y * np.conj(ref)[:, None]
    z = z / (np.abs(z) + 1e-12)
    feats = [z.real, z.imag]
    if mode == "phase_mag":
        mag = np.abs(y)
        mag = mag / (mag.mean(axis=1, keepdims=True) + 1e-12)
        feats.append(mag)
    elif mode != "phase":
        raise ValueError("unknown mode " + mode)
    return np.stack(feats, axis=1).astype(np.float32)


# ----------------------------------------------------------------------
#  Dataset: stores NOISELESS channels + ground-truth parameters.
#  Noise is injected on the fly during training.
# ----------------------------------------------------------------------

def make_dataset(prefix, N, M, seed=0, chunk=200_000):
    rng = np.random.RandomState(seed)
    s = aperture_grid(M)
    xr = np.lib.format.open_memmap(prefix + "_x.npy", mode="w+",
                                   dtype=np.float32, shape=(N, 2 * M))
    yy = np.lib.format.open_memmap(prefix + "_y.npy", mode="w+",
                                   dtype=np.float32, shape=(N, 2))
    done = 0
    t0 = time.time()
    while done < N:
        c = min(chunk, N - done)
        r  = rng.uniform(R_MIN, R_MAX, size=c).astype(np.float32)
        th = rng.uniform(TH_MIN, TH_MAX, size=c).astype(np.float32)
        h = channel_from_params(r, th, M, s)
        xr[done:done + c, :M] = h.real
        xr[done:done + c, M:] = h.imag
        yy[done:done + c, 0] = r
        yy[done:done + c, 1] = th
        done += c
    xr.flush(); yy.flush()
    return time.time() - t0


_NRNG = np.random.default_rng(20260101)


def add_noise(h, snr_db, rng=None):
    """h : (B, M) complex64  ->  noisy copy at the given per-sample SNR (dB).

    SNR is defined per sample as  mean_s |h(s)|^2 / sigma^2 .

    Performance notes: the previous implementation used the legacy
    RandomState and built a complex128 intermediate, costing ~30 ms per
    1024-batch.  Using PCG64 with dtype=float32 and assembling the complex64
    array in place cuts this by roughly 4x.
    """
    p = np.mean(h.real * h.real + h.imag * h.imag, axis=1, keepdims=True)
    snr = 10.0 ** (np.asarray(snr_db, np.float32).reshape(-1, 1) / 10.0)
    sig = np.sqrt(p / snr / 2.0).astype(np.float32)
    # 必须优先使用调用方传入的 rng：否则评估不可复现（见第三轮复查）。
    # 仅在未传 rng 时回退到模块级全局流，供训练循环抽取新噪声使用。
    src = rng if rng is not None else _NRNG
    n = np.empty(h.shape, dtype=np.complex64)
    if isinstance(src, np.random.RandomState):
        n.real = src.standard_normal(h.shape).astype(np.float32)
        n.imag = src.standard_normal(h.shape).astype(np.float32)
    else:
        n.real = src.standard_normal(h.shape, dtype=np.float32)
        n.imag = src.standard_normal(h.shape, dtype=np.float32)
    n *= sig
    return h + n


def reconstruct_np(r, th, M, s=None):
    """Inverse of channel_from_params for arrays of estimates."""
    return channel_from_params(r, th, M, s)


def resample_channel(h, M_from, M_to, D=D_APER):
    """Resample an (N, M_from) channel onto an M_to-point aperture grid.

    Both grids are linspace(-D/2, D/2, M); real and imaginary parts are
    interpolated linearly.  This is what makes a network trained at one
    discretization density directly usable at another, which is the
    discretization-agnostic property claimed for the parametric estimator.
    """
    if M_from == M_to:
        return h
    s_from = aperture_grid(M_from, D)
    s_to = aperture_grid(M_to, D)
    out = np.empty((h.shape[0], M_to), dtype=np.complex64)
    out.real = np.stack([np.interp(s_to, s_from, h[i].real) for i in range(h.shape[0])])
    out.imag = np.stack([np.interp(s_to, s_from, h[i].imag) for i in range(h.shape[0])])
    return out


def fit_gain_and_reconstruct(r_hat, th_hat, y, M, s=None):
    """Estimate the channel as alpha * phi(r_hat, th_hat), with the complex gain
    alpha obtained by a least-squares fit to the observation y.

    Rationale (central to this work): a range error dr shifts the reconstructed
    phase by -2 pi dr / lambda UNIFORMLY across the aperture, because
    d(d_k(s))/dr = (r - s sin theta)/d ~ 1 for s << r.  Without gain fitting this
    common-phase error alone drives the channel NMSE to ~2 even when the
    parameters are estimated well.  Fitting alpha removes this nuisance
    parameter, so that only the *shape* mismatch (governed by the angle and by
    the wavefront curvature) contributes to the error.
    """
    phi = channel_from_params(r_hat, th_hat, M, s)
    num = np.sum(np.conj(phi) * y, axis=1)
    den = np.sum(np.abs(phi) ** 2, axis=1)
    alpha = num / np.maximum(den, 1e-30)
    return (alpha[:, None] * phi).astype(np.complex64)


def nmse(h_hat, h_true):
    num = np.sum(np.abs(h_hat - h_true) ** 2)
    den = np.sum(np.abs(h_true) ** 2)
    return float(num / den)
