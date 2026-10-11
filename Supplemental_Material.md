# Supplemental Material

**Manuscript:** Range Errors as Uniform Phase Rotations in Continuous Aperture Arrays: Consequences for Near-Field Channel Estimation

This document maps every quantitative claim in the letter to the artifact that produces it, and lists
the experiments in enough detail to be reproduced. It is provided for the reader's convenience; the
letter itself is self-contained.

---

## S1. Claim-to-artifact map

Every entry below is recomputed automatically by `verify_paper.py`, which reads the archived JSON files
and compares the resulting values against the literal tokens present in the manuscript source. The
script reports PASS only if every row matches to within a relative tolerance of 0.5–10 % (tight for
directly measured quantities, looser for quantities quoted to two significant figures).

| # | Claim in the letter | Value | Artifact |
|---|---|---|---|
| 1 | LS NMSE at 10 dB | 0.1 | figs/holdout_eval_full.json -> models.10.0.LS.nmse |
| 2 | LMMSE NMSE at 10 dB | 0.009248 | figs/baselines_holdout_n2000.json -> baselines.10.0.LMMSE.nmse_fit |
| 3 | Proposed NMSE, no gain fit | 1.99 | figs/holdout_eval_full.json -> models.10.0.cls_raw.nmse_raw |
| 4 | Proposed NMSE, with gain fit | 0.81e-3 | models.10.0.cls_raw.nmse |
| 5 | Improvement over LS | 20.9 dB | Computed from the two rows above |
| 6 | Improvement over LMMSE | 10.6 dB | Computed from the LS and Proposed rows |
| 7 | OMP 50x100: NMSE fit / range RMSE / angle RMSE | 0.01382 / 2.660 m / 0.01018 | figs/baselines_holdout_n2000.json -> dict.10.0.OMP_50x100 |
| 8 | OMP + refinement: NMSE fit / range RMSE / angle RMSE | 0.0008433 / 2.499 m / 0.004557 | figs/baselines_holdout_n2000.json -> dict.10.0.OMP_refine |
| 9 | OMP 100x200: NMSE fit / range RMSE / angle RMSE | 0.004004 / 2.485 m / 0.006414 | figs/baselines_holdout_n2000.json -> dict.10.0.OMP_100x200 |
| 10 | Proposed: same three | 0.0008099 / 0.1754 m / 0.004357 | figs/holdout_eval_full.json -> models.10.0.cls_raw |
| 11 | Range advantage over refined dictionary | 14.25x | Ratio of the range RMSE in the two rows above |
| 12 | NMSE gap to refined baseline (10 dB, Proposed lower) | 0.176 dB | Computed from the dictionary and Proposed rows |
| 13 | Inference speed-up over refined baseline | 3500x | figs/timings.json |
| 14 | Capacity ablation 0.48/1.28/2.29 M at 10 dB (equal steps) | 1.19e-3+-0.13 / 0.81e-3+-0.05 / 0.76e-3+-0.02 | figs/holdout_eval_full.json -> models.10.0.capA1/cls_raw/capA3 |
| 15 | Capacity ablation at 20 dB | 4.63e-4 / 2.12e-4 / 1.79e-4 | Same artifacts, at 20 dB |
| 16 | Magnitude-normalized input (phase differencing + normalized magnitude): range RMSE @10 dB | 1.96 m | models.10.0.phase_mag.rmse_r |
| 17 | Magnitude-normalized input: angle RMSE | 0.0042 rad | models.10.0.phase_mag.rmse_th |
| 18 | Regression head: NMSE / angle RMSE / range RMSE | 2.16e-2 / 1.18e-2 / 0.1861 | models.10.0.reg |
| 19 | Classification advantage over regression (equal steps) | 26.7x | Computed from the capacity rows and the Proposed row |
| 20 | Transfer penalty, M=128 -> M=256 at 10 dB | 0.62 dB | figs/holdout_eval_full.json -> transfer.M256_10dB |
| 21 | Transfer penalty, M=128 -> M=256 at 20 dB | 0.81 dB | figs/holdout_eval_full.json -> transfer.M256_20dB |
| 22 | Transfer penalty, M=128 -> M=512 at 10 dB | 1.01 dB | figs/holdout_eval_full.json -> transfer.M512_10dB |
| 23 | Transfer penalty, M=128 -> M=512 at 20 dB | 0.86 dB | figs/holdout_eval_full.json -> transfer.M512_20dB |
| 24 | Range RMSE vs. the applicable CRB (variant C) | 1.04-1.45x | figs/crb.json -> C_rmse_r vs. models.*.cls_raw.rmse_r |
---

## S2. Physical model and constants

One-dimensional continuous aperture of length $D = 1$ m, carrier 3 GHz ($\lambda = 0.1$ m), so the
Rayleigh distance is $2D^2/\lambda = 20$ m and every simulated user lies in the radiative near field.
The distance from aperture point $s$ to user $k$ is

    d_k(s) = sqrt( r_k^2 + s^2 - 2 r_k s sin(theta_k) )

and the spherical-wave response is $h_k(s) = \exp(-j 2\pi d_k(s)/\lambda) / d_k(s)$. Users are drawn
uniformly with $r_k \in [5, 18]$ m and $\theta_k \in [-\pi/2, \pi/2]$.

---

## S3. Why the complex-gain fit is not a free parameter

One may ask whether fitting $\alpha$ in $\hat h = \alpha \, \phi(\hat r, \hat\theta)$ gives the
proposed method an advantage that the baselines do not enjoy. It does not, for two reasons.

First, the fit *reduces* the degrees of freedom rather than adding any. The proposed estimate inhabits
a manifold of at most four real dimensions per user — one complex gain (two real) plus two geometric parameters — whereas
the LS estimate inhabits all of $\mathbb{C}^M$ and LMMSE a rotated version of it. The proposed method
is therefore the most constrained of the compared estimators, and any advantage must come from the
structure it exploits rather than from extra freedom.

Second, in any physical link the complex gain is unknown: it aggregates transmit power, path gain and
the common propagation phase. Estimating it separately from the geometry is standard practice, and
the same operation is what a dictionary method performs when it estimates an atom coefficient after
selecting the atom. The letter's point is that this step is *necessary* before any parametric
estimator can be scored fairly, because without it the metric is dominated by a term that carries no
geometric information.

---

## S3b. Identifiability of the range parameter

Three variants of the range Cramer-Rao bound are distinguished, because the applicable one
depends on which gain assumptions hold.

| Caliber | Assumption | Bound @10 dB | Bound @20 dB | Applies to |
|---|---|---|---|---|
| A | complex gain fully known | 2.23e-4 m | 7.05e-5 m | --- |
| **C** | **magnitude known, carrier phase unknown** | **0.168 m** | **0.053 m** | **the proposed estimator** |
| B | complex gain fully unknown | 2.38 m | 0.75 m | the dictionary baselines |

The paper assumes a calibrated link budget, so variant C is the one that applies; above 5 dB the
learned estimator comes within 1.04-1.45x of it. Below 5 dB the measured curve dips slightly under
the bound, which a Cramer-Rao bound does not forbid for a biased estimator.

Caliber C is a 3x3 Fisher matrix over (r, theta, psi) with psi eliminated by Schur complement.
The projection method used for variant B cannot express magnitude-known-phase-unknown, because
in the complex space span{h} = span{j h}.

The 4x4 Fisher matrix for (r, theta, Re alpha, Im alpha) has a condition number ranging from
1.8e9 at (r=5 m, broadside) to 9.7e12 at (r=18 m, theta=1.2 rad); at fixed broadside the 18-m value
is 2.9e11 (the apparent 5-to-18 m trend mixed angles). Bounds from crb.json n=5000. Projection, Schur complement and direct inversion agree to
0.5-0.8% at every geometry tested. A truncated pseudo-inverse (rcond=1e-12) does fail at the
worst-conditioned point, returning 2.2e-4 m instead of 11.0 m: the hazard is truncation, not
inversion.

A Monte-Carlo maximum-likelihood estimator illustrates the flatness of the profiled likelihood.
Initialised at the truth it returns 0.59 m, below the variant-B bound of 0.60 m --- the
signature of a search biased towards the truth. With random initialisation over the physical
domain and 300 trials it returns 5.72 m.


#### S3b.2 The angle parameter is not degenerate (numbers moved here from the letter)

The letter states qualitatively that the angle parameter carries no such degeneracy. The numbers
behind that statement are recorded here so that the claim remains evidence-backed after the letter
was trimmed to its five-page limit. Both are computed at $r=10$ m, $\theta=0$ in float64 from
analytic derivatives.

| Quantity | Value |
|---|---|
| angle CRB, gain fully known, at 10 dB | 1.12e-3 rad |
| angle projection residual (normalized inner product) | 0.99 |
| range projection residual, same point | 5.0e-7 |

The contrast is the whole point of S3b. The normalized inner product between the range derivative
$-\partial d/\partial r$ and the gain direction is $5.0\times10^{-7}$ --- six orders of magnitude
below one, which is what makes the range unidentifiable when the gain is free. The corresponding
quantity for the angle is $0.99$, essentially orthogonal, so the angle stays identifiable and its CRB
is $1.12\times10^{-3}$ rad rather than diverging.

## S4. Reproduction

```
# 1) training pool from the analytic generator (no noisy dataset is shipped)
python make_data.py --M 256 --N 2000000 --out F:/capa_data/tr_M256      # seed 0, about 1.5 min

# 2) train the three seeds at the matched 4000-step budget
for s in 0 1 2; do
  python train.py --head cls --mode raw --hidden 1024,512,256 --batch 2048 \
      --n-train 1000000 --max-steps 4000 --seed $s \
      --data F:/capa_data/tr_M256 --out runs/eq_cls_s$s --val-every 250
done

# 3) independent holdouts, RNG seed 999999 (never seen in training or checkpoint selection)
python make_holdouts.py

# 4) headline numbers: three seeds x test_M256_holdout2, n = 2000
python reeval_holdout_full2.py       # -> figs/holdout_eval_full.json
python rerun_baselines_n2000.py      # -> figs/baselines_holdout_n2000.json
python exp_p0p2.py                   # -> figs/exp_p0p2.json
python compute_crb.py                # -> figs/crb.json

# 5) self-checks (all must pass)
python verify_paper.py && python check_figs.py && python audit_format.py
```

Every number in the letter is taken from the independent holdout of step 3 and the three
equal-step seeds of step 2; `runs/main_cls_raw/` is retained in the archive for provenance but no
reported number comes from it (S7.4).

All training and inference ran on one commodity CPU (Intel Core Ultra 5 125H, 16 GB), with no GPU and
no external compute. The full pipeline occupies 8.5 h of wall-clock time; the multi-seed replication
adds a further 9 h. The dataset is generated from the analytic model in 1.5 min and is not shipped as
raw data.

---

## S5. Known limitations, stated for the record

1. **The dominant range cue is the absolute received amplitude**, not the wavefront curvature. The
   ablation in Section IV-D isolates this: a phase-differenced input that normalizes the amplitude
   away estimates the angle almost as accurately but plateaus at a range RMSE of 1.96 m against 0.18 m. This presumes a calibrated link budget; under an unknown path gain the range must be
   estimated jointly with the gain, which is left open.
2. **Single-user estimation.** Orthogonal pilots separate the users, so each is processed
   independently. Pilot contamination is not treated.
3. **One-dimensional training.** The letter trains and reports only the one-dimensional aperture. A second
   aperture axis is derived and measured in Sections S15 and S20: the range CRB improves by a factor of
   1.6 to 6.5, but the bound itself stays between 2.6 m and 67 m, so the degeneracy is relieved without
   being removed.
4. **The Cramer-Rao bounds are evaluated over $|\theta| \le 1.2$ rad**, where the angle is identifiable; the
   angle bound diverges at endfire (Section S10.5). The range bounds under the three gain assumptions are
   derived in closed form in Section S21 and plotted in Fig. 3 of the letter.


---

## S6. Grid refinement does not recover the range

M=256, SNR = 10 dB, 300 samples drawn from the training-pool prefix (tr_M256[:300], noise seed 7),
matched-filter atom selection (argmax over |y D^H|, no OMP subtraction). This is a lighter protocol
than the full OMP baselines of Table I, which is why the absolute level (2.24 m) sits below Table I's
2.49-2.71 m; the sweep supports the claim about the *change* with grid refinement, not the absolute
level.

| Range grid | Atoms | Spacing (m) | RMSE r (m) | RMSE theta (rad) |
|---|---|---|---|---|
| $50\times100$ | 5{,}000 | 0.265 | 2.489 | $9.44\times10^{-3}$ |
| $100\times200$ | 20{,}000 | 0.131 | 2.236 | $5.64\times10^{-3}$ |
| $200\times200$ | 40{,}000 | 0.065 | 2.227 | $5.64\times10^{-3}$ |
| $260\times200$ | 52{,}000 | 0.050 | 2.238 | $5.64\times10^{-3}$ |
| $400\times200$ | 80{,}000 | 0.033 | 2.228 | $5.64\times10^{-3}$ |
| $520\times200$ | 104{,}000 | 0.025 | 2.235 | $5.64\times10^{-3}$ |
| $800\times200$ | 160{,}000 | 0.016 | 2.234 | $5.64\times10^{-3}$ |

The range RMSE is flat to within 0.1% across a 16x range of grid spacings, while the
angular RMSE saturates at 5.64e-3 rad once the spacing drops below lambda/2.
The nuisance-gain bound (RMS over users, |theta|<=1.2 rad; crb.json n=5000) is 2.38 m at this SNR. The sweep level (2.24 m, full angle domain, matched filter) should not be divided by it directly.


---

## S7. Configuration and reproducibility

### S7.1 Simulation parameters

| Parameter | Value |
|---|---|
| Carrier / wavelength $\lambda$ | 3 GHz / 0.1 m |
| Aperture $D$ / Rayleigh $d_{\mathrm{Rayl}}$ | 1 m / 20 m |
| Discretization $M$ | 128, 256, 512 |
| User range $r_k$ | 5--18 m |
| Trunk hidden layers | 1024, 512, 256 |
| Range / angle grid ($G_r$/$G_\theta$) | 128 / 256 bins |
| Trainable parameters | $1.28 \times 10^{6}$ |
| Batch / pool / budget | 2048 / $10^{6}$ / 4000 gradient steps (CPU) |

### S7.2 Evaluation sample sizes

| Experiment | Samples | Where |
|---|---|---|
| Table I (metric comparison) | 2000 | figs/holdout_eval_full.json + figs/baselines_holdout_n2000.json |
| Grid sweep (letter, Section III-B) | 300 | figs/grid_aliasing.json |
| Inference timing | 1200 | figs/timings.json |
| Capacity ablation | 2000 per seed x 3 seeds (equal steps) | figs/holdout_eval_full.json |
| Transfer | 1500 | figs/holdout_eval_full.json (transfer) |
| Calibration sensitivity | 4000 | fig. 1 of this supplement |

### S7.3 Undisclosed hyper-parameters (now disclosed)

- Soft-argmax decoding temperature: tau = 1.0 (train.py:63)
- Soft-label width: 1.5 bins (train.py:32)
- Data generation seed: 0 (make_data.py)
- Optimizer: Adam, cosine schedule; batch 2048; pool 1e6 samples

### S7.4 Why the letter uses a 4000-step model rather than a longer run

The compute budget of the capacity study (Section IV-F) is fixed in *steps*, not wall-clock time:
an equal-time budget silently rewards whichever architecture happens to run fastest on the host
machine, whereas equal gradient steps hold training effort constant across trunks (the letter
reports per-step times in its complexity discussion only as inference cost, not as a training
entitlement).

A longer-budget run trained the 1.28 M trunk for 180 min (about 20 900 steps) and reached a validation
NMSE of 0.927e-3. The equal-step protocol adopted here reaches 0.810e-3 (95% CI +-0.047e-3 over
three seeds, independent holdout) after only 4000 steps, i.e. a model trained five times longer
performed 14 % worse. Two differences
explain this and neither concerns the architecture: (i) the two pipelines use different cosine schedules
--- the long run spreads its schedule over about 20 900 steps, so at step 4000 its learning rate is still
high and its best checkpoint need not beat a fully annealed short run; (ii) the implementation was updated between
the two runs. The letter therefore reports the equal-step, three-seed protocol throughout,
which is also the only protocol under which the ablations of Section IV-D and the capacity study of
Section IV-F are directly comparable. runs/main_cls_raw/ is retained in the archive but no number in the
letter is taken from it.


### S7.5 Environment

Python 3.11, numpy 2.4.6, torch 2.14.0+cpu, scipy 1.17.1, pymupdf.
All experiments CPU-only on an Intel Core Ultra 5 125H (14c/18t), 16 GB LPDDR5X.


---


### S7.6 Note on the holdout seed

The independent evaluation sets (test_M256_holdout2, test_M512_holdout) and the earlier exploratory holdout both use seed 999999, so their prefixes coincide. This is not a leak: none of them was used for training or for checkpoint selection. All headline numbers in the letter are taken from the two sets above.

## S8. Provenance of the 7.48 m collapse figure (Section III-A)

Section III-A reports that direct regression on the reconstruction loss collapses to the
lower range boundary, giving a range RMSE of 7.59 m on the independent holdout (the main text
quotes the holdout value). That number is reproduced by an explicit ablation arm in the pipeline (eq_recon_s*, selected with the
--loss recon option: 7.48 m on the validation prefix and 7.59 m on the independent holdout, three
seeds each). train.py's default regression head instead minimizes a *parameter-space* MSE, which
does not collapse. The two are different experiments and the abstract states them so.

| Quantity | Setting | Value | Source |
|---|---|---|---|
| range RMSE | regression on the reconstruction loss | 7.48 m / 7.59 m (collapses to r_min) | runs/eq_recon_s* |
| range RMSE | regression on parameter-space MSE | 0.186 m | figs/holdout_eval_full.json |
| NMSE gain | classification vs parameter-space regression | 26.7x | figs/holdout_eval_full.json |


---

## S9. Cross-discretization transfer (Fig. S1)

Figure S1 shows a network trained at M_tr = 128, evaluated on
channels discretized at M_te = 256 and 512 by linear resampling, against a network
trained natively at each M_te. Both sides are the equal-step, three-seed models and are
evaluated on the independent holdout. The NMSE penalty is 0.62 dB at 10 dB SNR and
0.81 dB at 20 dB for M_te = 256, and 1.01 dB at 10 dB and 0.86 dB at 20 dB for M_te = 512 (both
sides evaluated on 2000 independent samples). Raw data:
figs/holdout_eval_full.json (the "transfer" block), produced by reeval_holdout_full2.py.

![Fig. S1. Cross-discretization transfer. Left: gain-fitted NMSE against SNR for a model trained at $M_{\mathrm{tr}}=128$ and evaluated at $M_{\mathrm{te}}=256$ and $512$, against a model trained natively at each $M_{\mathrm{te}}$. Right: the resulting transfer penalty. Both sides are three-seed models evaluated on the independent holdout.](figs/fig3-transfer.pdf)

## S10. Experiment setup, stated for independent verification

This section records the details needed to judge whether the letter's numbers can be
reproduced, at a level of specificity sufficient for independent verification.

### S10.1 Data

| Item | Value |
|---|---|
| Training set | 2,000,000 noiseless channel realizations, RNG seed 0 |
| Independent holdout | 6,000 realizations, RNG seed 999999, never used in training or checkpoint selection |
| Evaluated subset | the first 2,000 holdout realizations |
| One observation | one user, one aperture snapshot; all reported metrics are averages over the 2,000 realizations |
| Noise | injected on the fly per evaluation, RNG seed 11, drawn independently per realization |
| SNR convention | per element, SNR = E[|h_k(s)|^2] / sigma^2, the expectation taken over aperture points s and over the user ensemble |
| Sampling | r ~ U[5,18] m, theta ~ U[-pi/2, pi/2], independent per realization |

The number of simultaneous users K does not enter any reported metric: every result is a per-user
average over independent realizations, and the estimator is applied per user.

### S10.2 Baselines, stated precisely

- **LS**: the raw observation, h_hat_LS = y.
- **LMMSE**: linear MMSE using the **sample covariance of the evaluation set itself**,
  C_h = n^-1 * sum_i h_i h_i^H. This is a genie-aided oracle: it is stronger than any LMMSE a
  practitioner could build, because it is computed from the very samples being scored. It is used
  deliberately, so that the comparison is conservative with respect to the proposed estimator.
- **Polar-grid dictionary**: a uniform grid over (r, theta); every atom is L2-normalized; the
  estimate is the single best-matching atom. The channel is rank one, so one atom is exact for a
  noiseless single-path channel. Grids used: 50x100 and 100x200.
- **Refinement**: two to three coarse-to-fine passes, each a 41x41 local grid contracting by a
  factor of 4 per pass, again selecting the best-matching atom.

### S10.3 Numerical method for the analysis quantities

The quantities quoted in Section II-C (normalized inner product, Fisher condition number,
projection residual) are computed in float64 from **analytic** derivatives,

  dh(s)/dr = h(s) * ( -j*2*pi/lambda - 1/d(s) ) * (r - s*sin(theta))/d(s),

so that no finite-difference step is involved. The gain-unknown bound is obtained by projecting
span{h, jh} out of the Jacobian, or equivalently by a Schur complement of the 4x4 Fisher matrix.
**Direct inversion of that matrix is not used**: its condition number reaches 1e13, at which point
direct inversion loses several digits. An independent implementation that did invert directly
disagreed with the archived values by 16-24%, which is a property of the inversion and not of the
model. Monte-Carlo bounds are averaged over n = 5000 uniform user draws with |theta| <= 1.2 rad; a
large-sample reference at n = 200000 agrees to 0.15%.

### S10.4 Confidence intervals

Learned estimators are reported over three independently trained seeds, with 95% intervals using
t(0.975, df=2) = 4.303. Deterministic baselines (LS, LMMSE, dictionary) carry no training variance.

### S10.5 The CRB is a variance bound, and our estimator is biased

The Cramer-Rao bound constrains the variance of **unbiased** estimators. The proposed estimator is
biased by construction (classification plus soft-argmax decoding), and its mean squared error may
therefore lie **below** the bound without violating any theorem. The comparison in Fig. 3 is offered
as a **reference scale**, not as an optimality claim: the bound tells the reader what order of
magnitude is attainable under the stated gain assumptions, and the measured curve is read against
it. Where the measured RMSE falls slightly below the curve at low SNR, that is the expected
behavior of a biased estimator and is stated as such in the letter.

### S10.6 Dependence of the dictionary conclusion on implementation

The conclusion that a coefficient-fitting dictionary is range-blind depends on the dictionary being
L2-normalized and on the coefficient being refitted freely. Two variants were not tested: (i)
unnormalized atoms, which would let the atom norm carry amplitude information; (ii) a joint
amplitude-range grid. We state this as a scope limitation rather than claim universality.

### S10.7 Reproducibility of the letter's numbers

Every number in the letter is checked against the archived result files by an automated script that
re-derives each value from its source and compares it with the literal token in the manuscript. The
script additionally verifies the **direction** of each comparison (which estimator is better), since
a correct magnitude attached to the wrong subject is not detectable by numeric comparison alone.

## S11. Comparison with a non-parametric deep-learning channel estimator

This section establishes where the proposed estimator sits relative to
deep-learning near-field channel estimation. It reports an external baseline trained under a
matched budget plus a 4x-budget control, and isolates the point that matters for the letter.

### S11.1 Why this baseline, and what it can and cannot show

The proposed estimator is **parametric**: two geometry parameters per user. The literature's deep
channel estimators are overwhelmingly **non-parametric**: they output the channel. A non-parametric
estimator cannot be scored on range or angle RMSE directly --- it has no geometry output. Two things
can still be measured honestly:

1. its **channel NMSE**, on the same footing as LS and LMMSE; and
2. the **geometry implied by its output**, obtained by fitting (r, theta) to that output.

For (2) two fitting criteria are reported, because the choice matters:

- **normalized**: maximize |<phi/||phi||, h_hat>|, which is what the dictionary baselines do
  (`polar_omp` uses L2-normalized atoms). This criterion discards amplitude.
- **gain-fitted**: minimize the residual after an optimal complex-gain fit, equivalently maximize
  |<phi, h_hat>| / ||phi||. This criterion **uses the amplitude**, which is where Section II-C says
  the range information resides. It is the most favourable extraction available.

A **reference upper bound** is also computed: the same gain-fitted procedure applied to the
**noise-free** channel. This calibrates the fitting procedure itself.

### S11.2 Architecture and training, matched to the proposed method

| Dimension | Setting |
|---|---|
| Architecture | residual MLP, trunk 1024-512-256, ReLU, linear head to 2M |
| Skip connection | h_hat = beta*y + f(y), beta learnable (standard deep-denoiser design) |
| Parameters | 1,313,025 (proposed method: 1,280,128, within 3%) |
| Input | `raw`, i.e. [Re y, Im y] --- **identical to the proposed method** |
| Loss | channel MSE, ||h_hat - h||^2, on the same noiseless targets |
| Steps | 4000 (matched) and 16000 (4x control) |
| Batch | 2048 |
| Optimizer | Adam, 1e-3, cosine annealed to 1e-5 |
| Training pool | 1,000,000 realizations, seed 0 --- the same pool |
| Seeds | three independently trained seeds per budget, 95% intervals with t(0.975,df=2) = 4.303 |

**A design note that matters.** The `phase_mag` input was deliberately *not* used, even though it is
the best input for the parametric model (Section IV-E). `preprocess` forms
z = y * conj(y[M/2]), removing the common phase. A parametric model needs only shape and magnitude,
so this helps it; a non-parametric estimator must reconstruct the **absolute** channel, and removing
the common phase makes that impossible. `raw` is the only fair input here.

### S11.3 Channel NMSE (10 dB, holdout of 2000, noise seed 11)

| Budget | seed 0 | seed 1 | seed 2 | mean | 95% CI |
|---|---|---|---|---|---|
| 4000 steps | 0.044477 | 0.045547 | 0.046827 | 0.045617 | +/- 0.002923 |
| 16000 steps | 0.001937 | 0.001918 | 0.001959 | 0.001938 | +/- 0.000050 |

Quadrupling the budget improves the NMSE by 23.5x. For reference, at the **same** 4000-step budget
the proposed method reaches 8.10e-4 --- 56x lower than the matched-budget deep estimator.

Full NMSE-vs-SNR for the matched-budget model:

| SNR (dB) | -5 | 0 | 5 | 10 | 15 | 20 |
|---|---|---|---|---|---|---|
| DL NMSE | 1.229 | 0.398 | 0.132 | 0.0456 | 0.0177 | 0.00866 |
| LS NMSE | 3.163 | 1.000 | 0.316 | 0.100 | 0.0316 | 0.0100 |

### S11.3b Sensitivity of the geometry extraction to its own refinement budget

The geometry implied by an estimator's output is obtained by a coarse grid match followed by three
refinement passes on a 41x41 local grid. That procedure has a budget, and the budget matters, so it is
swept on the matched-budget MLP output at 10 dB:

| Refinement | Passes / local grid | range RMSE (m) |
|---|---|---|
| coarse | 1 / 21 | 2.6892 |
| base (used above) | 3 / 41 | 2.5202 |
| fine | 5 / 81 | 2.4566 |

The three settings span a 9.1% range. More refinement gives a *better* number, so the reported values
are if anything conservative for the reconstruction-based estimators. All three remain about 14 times
worse than the proposed estimator's 0.1754 m, so the conclusion does not depend on the budget chosen.


### S11.3c The same comparison at every SNR

Section S11 reported 10 dB and 20 dB. The extraction was repeated at all six SNRs so that the
statement can be made across the whole operating range rather than at two points.

Range RMSE in metres, per-seed mean with 95% intervals (MLP and CNN), against the dictionary baseline
and the proposed estimator:

| SNR (dB) | OMP + refine | Deep MLP | Deep CNN | Proposed |
|---|---|---|---|---|
| -5 | 5.239 | 5.292 +/- 0.080 | 5.303 +/- 0.132 | **0.862** |
| 0 | 4.316 | 4.388 +/- 0.029 | 4.387 +/- 0.065 | **0.512** |
| 5 | 3.401 | 3.427 +/- 0.034 | 3.432 +/- 0.042 | **0.299** |
| 10 | 2.499 | 2.530 +/- 0.036 | 2.566 +/- 0.069 | **0.175** |
| 15 | 1.746 | 1.827 +/- 0.062 | 1.922 +/- 0.053 | **0.109** |
| 20 | 1.260 | 1.396 +/- 0.059 | 1.548 +/- 0.188 | **0.077** |

**At every SNR the three reconstruction-based estimators agree with one another to within a few
percent**, despite their channel NMSEs differing by up to 84-fold (S13), while the proposed estimator
is 6 to 18 times better (6.1 at $-5$ dB, rising to 18.1 at $20$ dB). The separation is not a property of one SNR or one architecture; it is
present across the whole range. This is the evidence behind Fig. 3's right panel.

### S11.4 The finding that matters (per-seed values; see S13.4): NMSE does not order range accuracy

Geometry implied by each estimator's output, gain-fitted criterion (the most favourable extraction),
range RMSE in metres:

| 10 dB | NMSE | range RMSE |
|---|---|---|
| Proposed (4000 steps) | 8.10e-4 | **0.1754** |
| Refined dictionary | 8.43e-4 | 2.4993 |
| DL, matched budget (4000) | 4.56e-2 | 2.4788 |
| DL, 4x budget (16000) | 1.94e-3 | 1.8145 |
| **Fit to the noise-free channel** | 0 | **0.7635** |

| 20 dB | NMSE | range RMSE |
|---|---|---|
| Proposed | 2.12e-4 | **0.0771** |
| Refined dictionary | 1.76e-4 | 1.2595 |
| DL, matched budget | 8.66e-3 | 1.3169 |
| DL, 4x budget | 1.96e-3 | 1.6252 |
| Fit to the noise-free channel | 0 | 0.7635 |

Three observations follow.

1. **At 10 dB the matched-budget deep estimator has an NMSE 54x worse than the refined dictionary**
   (4.56e-2 against 8.43e-4), yet the range implied by its output is 2.4788 m against 2.4993 m --- a
   0.8% difference. A 54-fold NMSE gap buys no range accuracy in this regime.
2. **With 4x the budget the deep estimator's NMSE comes within 2.4x of the proposed one** (1.94e-3
   against 8.10e-4), but its implied range is 1.8145 m, still **10.4x worse** than the proposed
   0.1754 m. Comparable NMSE, an order of magnitude worse geometry.
3. **At 20 dB the 4x-budget model has a 4.4x better NMSE than the matched-budget one** (1.96e-3
   against 8.66e-3), yet a *worse* implied range (1.6252 m against 1.3169 m). NMSE does not order
   range accuracy at all.

The noise-free control is what makes this interpretable. Fitting the same procedure to a perfect
channel yields 0.7635 m, so the procedure is not the bottleneck at 2.5 m; the reconstruction-based
estimators simply do not carry the range information that a perfect channel would. (The proposed
0.1754 m is below even the 0.7635 m control because it is not a grid-matching procedure: it exploits
the calibrated amplitude directly.)

### S11.5 Normalized versus gain-fitted extraction

Both criteria give effectively the same answer, which rules out the objection that the extraction
was rigged to discard amplitude:

| Condition | normalized | gain-fitted |
|---|---|---|
| DL matched, 10 dB | 2.4796 | 2.4788 |
| DL matched, 20 dB | 1.3161 | 1.3169 |
| DL 4x, 10 dB | 1.8186 | 1.8145 |
| DL 4x, 20 dB | 1.6235 | 1.6252 |

Differences are below 0.3% throughout. Letting the extraction use the amplitude changes nothing.

### S11.6 What this baseline does not cover

Architectures outside the MLP family (convolutional, transformer, unfolded) were not trained, for the
hardware reason stated in the letter's limitations. The baseline is a fair instance of the
non-parametric deep-estimator class, examined at two budgets, but it is one architecture family.

## S12. What the deep estimators' internal representations do and do not contain

Section S11 shows that deep channel estimators do not recover range from their **output**. That
invites the objection that the geometry was extracted by fitting (r, theta) to the output, and the
fitting procedure has its own floor, so the failure might belong to the fit rather than to the
network. This section removes that objection by probing the networks' **internal representations**
directly, bypassing the geometric fit entirely.

### S12.1 Protocol

Probes are fitted on holdout rows 2000-5999 (4000 samples) and scored on rows 0-1999 (2000 samples).
The two sets are disjoint, so every probe score is held out. Two probe families are used:

- **linear**: ridge regression on the raw feature vector;
- **non-linear**: a two-hidden-layer MLP (width 128, 1200 Adam steps) on the same features.

The non-linear probe matters because a linear read-out can understate what a representation contains.

Inputs probed, all derived from the same noisy observation:

- `y`: the complex observation, 512 real dimensions;
- `abs_y`: the per-element magnitude, 256 dimensions --- the quantity Section II-C identifies as the
  range cue;
- `mlp_feat`: trunk features of the residual-MLP estimator (256 dimensions);
- `cnn_feat`: globally pooled trunk features of the convolutional estimator (48 dimensions).

### S12.2 Results

Range RMSE in metres, non-linear probe. The linear probe is reported in the archived JSON; it is
uniformly worse and orders the inputs almost identically.

| SNR (dB) | one-line `1/mean abs(y)` | `abs_y` | `mlp_feat` | `cnn_feat` |
|---|---|---|---|---|
| -5 | 5.383 | 0.879 | 0.605 | **0.391** |
| 0 | 2.644 | 0.841 | 0.620 | **0.383** |
| 5 | 0.953 | 0.706 | 0.571 | **0.390** |
| 10 | **0.336** | 0.517 | 0.519 | 0.398 |
| 15 | **0.133** | 0.220 | 0.440 | 0.359 |
| 20 | **0.061** | 0.124 | 0.371 | 0.308 |

For reference, the proposed parametric estimator attains 0.1754 m at 10 dB and 0.0771 m at 20 dB.

### S12.3 What the probes establish

**1. The residual-MLP representation is no better than the raw magnitude.** At 10 dB the MLP features
give 0.519 m against 0.517 m for the raw magnitude; at 20 dB, 0.371 against 0.124. Training that
network to reconstruct the channel produced no range representation superior to its own input.

**2. The convolutional representation is better than the raw magnitude at low SNR.** The CNN
features give 0.391, 0.383 and 0.390 m at -5, 0 and 5 dB, against 0.879, 0.841 and 0.706 m for the
raw magnitude --- a factor of about 2. This is a genuine, architecture-dependent effect and it is
reported as such.

**3. But above about 10 dB the raw magnitude wins outright.** At 15 and 20 dB the magnitude gives
0.220 and 0.124 m against 0.359 and 0.308 m for the CNN features. A one-line closed-form inversion
of the amplitude law, `1/mean_s abs(y(s))`, beats every learned representation at every SNR from
5 dB upward, reaching 0.336 m at 10 dB.

**4. Range information present in the representation is not exposed by the channel output.** This is
the sharpest observation in the table. At 10 dB the CNN's own features yield 0.398 m under a probe,
while the geometry implied by its channel **output** is 2.566 m (S13) --- a factor of 6.4. The
information is in the network; reconstructing the channel does not put it in the channel.

### S12.4 A hypothesis that was tested and rejected

Our first explanation was that a reconstruction objective with an unknown complex gain forces the
network to become gain-invariant, discarding the absolute amplitude along with it. **This is false.**
A ridge probe for the amplitude scale `mean_s abs(y)` from the MLP features gives R^2 = 0.983 at
10 dB and 0.979 at 20 dB, against 1.000 for the raw magnitude. The network preserves the amplitude
scale almost perfectly, so the difficulty is not that the cue is discarded; it is that the cue is not
converted into a good range estimate. Why, these experiments do not establish, and we do not claim to
know.

### S12.5 Scope

Probes are a ridge regression or a two-layer MLP on frozen features. A probe of much greater capacity,
or one trained jointly with the backbone, could extract more. The claims made here are the limited
ones stated above; in particular, claim 1 is specific to the residual-MLP architecture and does not
generalize to the convolutional one.

### S12.6 Checkpoint selection does not bias the reported numbers

The reported model is the checkpoint with the best 10 dB validation NMSE (S19.1). Because the letter
also quotes 20 dB results, it matters whether a criterion tuned at 10 dB could bias the high-SNR
numbers. It does not: at the matched 4000-step budget the validation NMSE is still falling when the
budget ends, so the best epoch *is* the last epoch. `runs/eq_cls_s*/result.json` records
`best_nmse == final_nmse` for every seed:

| Seed | best.pt validation NMSE | last.pt validation NMSE | weights identical |
|---|---|---|---|
| 0 | 0.7945e-3 | 0.7945e-3 | yes |
| 1 | 0.7864e-3 | 0.7864e-3 | yes |
| 2 | 0.7582e-3 | 0.7582e-3 | yes |

The two checkpoints were compared tensor by tensor: their model state is bit-identical (the files
differ only in serialization metadata). There is therefore no selection step that could have biased
the reported numbers; `best.pt` and `last.pt` are interchangeable.

### S12.7 Is probe capacity the limiting factor? (a control)

Section S12.5 concedes that the claims are limited by probe capacity. That concession can be made
quantitative. Every probe was repeated with a larger family --- three hidden layers of width 256
instead of two of width 128, and 2500 Adam steps instead of 1200:

| 10 dB | small (2x128) | large (3x256) | change |
|---|---|---|---|
| raw magnitude | 0.4844 | 0.4806 | -0.8% |
| MLP features, matched budget | 0.5150 | 0.4980 | -3.3% |
| MLP features, 4x budget | 0.2850 | 0.2554 | -10.4% |

| 20 dB | small | large | change |
|---|---|---|---|
| raw magnitude | 0.1503 | 0.1170 | -22.2% |
| MLP features, matched budget | 0.3223 | 0.3260 | +1.1% |
| MLP features, 4x budget | 0.2272 | 0.1588 | -30.1% |

At 10 dB, roughly tripling the probe changes every result by at most 10%, and the ordering of the
inputs is unchanged. At 20 dB the larger probe helps more (up to 30%), but again the ordering is
unchanged and the raw magnitude remains the best input. **The limitation is real but small**, so the
conclusions of S12.3 are not artifacts of a weak probe.

### S12.8 More training does improve the representation --- but not the channel output

Comparing the matched-budget and 4x-budget MLP under the same probe isolates the effect of training
length on the internal representation:

| Probe, 10 dB | matched (4000 steps) | 4x (16000 steps) | ratio |
|---|---|---|---|
| small (2x128) | 0.5150 | 0.2850 | 1.81 |
| large (3x256) | 0.4980 | 0.2554 | 1.95 |

Four times the training budget makes the **representation** about twice as informative about range.
Yet the geometry implied by the same networks' channel **output** is 2.5304 m (matched) and 2.0064 m
(4x): the output barely improves, moving from 2.53 to 2.01 m while the representation moves from 0.50
to 0.26 m.

This is the sharpest form of the observation in S12.3 claim 4, and it is not architecture-specific:
for the MLP the features hold 0.26 m of range information while the channel implies 2.01 m; for the
CNN at the matched budget the features hold 0.398 m while the channel implies 2.566 m. In both cases
a factor of 5--6 of the range information present in the network is absent from its channel output.

The 4x-budget runs sharpen this further. The 4x MLP's features give 0.2554 m against a channel that
implies 2.0064 m, a factor of 7.9. The 4x CNN's features give **0.1876 m** --- within 7% of the
proposed estimator's 0.1754 m --- against a channel that implies **2.0463 m**, a factor of 10.9.

| Model | probe on features (m) | implied by channel output (m) | ratio |
|---|---|---|---|
| MLP, matched | 0.4980 | 2.5304 | 5.1 |
| MLP, 4x | 0.2554 | 2.0064 | 7.9 |
| CNN, matched | 0.3984 | 2.5660 | 6.4 |
| CNN, 4x | 0.1876 | 2.0463 | 10.9 |

A deep network trained purely to reconstruct the channel can therefore hold range information
comparable to a purpose-built parametric estimator, while the channel it outputs still implies a range
error an order of magnitude worse. The loss happens between the representation and the output, not in
the representation.


## S13. A second architecture: convolutional estimator of matched size

Section S11 used a residual MLP. A convolutional architecture is a natural alternative, so a
second architecture was trained under the same protocol.

### S13.1 Architecture, and why it has this shape

A full-resolution wide convolutional network is **not feasible on this hardware**, and the reason is
structural rather than incidental: at full aperture resolution a convolution's arithmetic-to-parameter
ratio is very high. A 1.28 M-parameter full-resolution CNN needs hundreds of GMAC per forward pass;
measured on this machine it ran at 1.0 s per step, i.e. about 16 hours for 4000 steps.

The estimator used here therefore has a **light convolutional front end and a linear decoder**:

| Stage | Shape | Parameters | MACs/sample |
|---|---|---|---|
| Conv1d(2 to 24, k=5, stride 2) | (24, 128) | 264 | 30,720 |
| Conv1d(24 to 32, k=3, stride 2) | (32, 64) | 2,328 | 147,456 |
| Conv1d(32 to 48, k=3, stride 2) | (48, 32) | 4,656 | 147,456 |
| Linear(1536 to 512) | | 786,944 | 786,432 |
| Linear(512 to 512) | | 262,656 | 262,144 |
| Linear(512 to 512) | | 262,656 | 262,144 |
| **Total** | | **1,319,513** | **1.64 M** |

The proposed estimator has 1,280,128 parameters and 1.31 M MACs. The convolutional baseline is
therefore **within 3% in parameters and within 25% in arithmetic**.

Training protocol is identical to S11: same `raw` input, same 1,000,000-sample pool, 4000 steps,
batch 2048, Adam at 1e-3 cosine-annealed, three seeds.

### S13.2 Results

| Seed | 10 dB check. NMSE |
|---|---|
| 0 | 0.069229 |
| 1 | 0.071422 |
| 2 | 0.070939 |
| **mean** | **0.070530 +/- 0.002863** |

For comparison at the same budget: the MLP reaches 0.045617, the refined dictionary 0.000843, and
the proposed estimator 0.000810.

Geometry implied by the convolutional estimator's output, gain-fitted criterion, per seed:

| Seed | range RMSE (m) |
|---|---|
| 0 | 2.5452 |
| 1 | 2.5974 |
| 2 | 2.5555 |
| **mean** | **2.5660 +/- 0.0687** |

### S13.3 What the second architecture adds

The convolutional estimator has a **55% worse NMSE** than the MLP (0.0705 against 0.0456) but a range
implied by its output that differs by **1.4%** (2.5660 against 2.5304 m). Adding this architecture
widens the NMSE span over which the recovered range stays flat:

| Estimator | NMSE | range RMSE (m) |
|---|---|---|
| Refined dictionary | 8.43e-4 | 2.4993 |
| MLP, matched budget | 4.56e-2 | 2.5304 |
| CNN, matched budget | 7.05e-2 | 2.5660 |

Across an **84-fold** range of channel NMSE these three estimators agree on range to within 0.07 m
(2.50 to 2.57 m). A 55% NMSE penalty buys a 1.4% range penalty; an 84-fold NMSE penalty buys a 2.7%
range penalty.

### S13.4 Per-seed versus ensemble values

Some numbers in S11 come from the **seed-averaged** channel (2.4788 and
1.8145 m). Averaging three independently trained networks is an ensemble, so those numbers are
better than any single deployed model would give. The **per-seed** values are the deployable
quantity:

| Quantity | seed-averaged (ensemble) | per-seed mean |
|---|---|---|
| MLP matched, 10 dB | 2.4788 | 2.5304 +/- 0.0361 |
| MLP 4x budget, 10 dB | 1.8145 | 2.0064 +/- 0.1615 |
| MLP matched, 20 dB | 1.3169 | 1.3955 +/- 0.0590 |
| MLP 4x budget, 20 dB | 1.6252 | 1.8696 +/- 0.1792 |

The conclusion is unchanged; the numbers are more conservative.

### S13.5 20 dB, and a check on model selection

Geometry implied by the convolutional estimator's output at 20 dB, gain-fitted criterion, per seed:

| Seed | range RMSE (m) |
|---|---|
| 0 | 1.4691 |
| 1 | 1.5549 |
| 2 | 1.6200 |
| **mean** | **1.5480 +/- 0.1881** |

For reference at 20 dB: the proposed estimator reaches 0.0771 m, the refined dictionary 1.2595 m,
the residual-MLP estimator 1.3955 m (matched budget) and 1.8696 m (4x budget). The convolutional
estimator sits between the two MLP budgets.

**Checkpoint selection.** As for the MLP (S12.6), the checkpoint was selected by 10 dB validation
NMSE, which could in principle bias the 20 dB numbers. Evaluating the last checkpoint instead of
the best one gives identical results:

| Checkpoint | 10 dB NMSE | 20 dB NMSE |
|---|---|---|
| best.pt | 0.070491 | 0.014501 |
| last.pt | 0.070491 | 0.014501 |

No selection bias is present.

### S13.6 The 2x2 of architecture and budget at 10 dB and 20 dB

| | 10 dB NMSE | 10 dB range (m) | 20 dB NMSE | 20 dB range (m) |
|---|---|---|---|---|
| MLP, 4000 steps | 4.56e-2 | 2.5304 +/- 0.0361 | 8.66e-3 | 1.3955 +/- 0.0590 |
| CNN, 4000 steps | 7.05e-2 | 2.5660 +/- 0.0687 | 1.45e-2 | 1.5480 +/- 0.1881 |
| MLP, 16000 steps | 1.94e-3 | 2.0064 +/- 0.1615 | 1.08e-3 | 1.8696 +/- 0.1792 |
| CNN, 16000 steps | 4.21e-3 | 2.0463 +/- 0.1371 | --- | --- |
| Proposed | 8.10e-4 | **0.1754** | 2.12e-4 | **0.0771** |

Two regularities survive both architectures and both budgets. First, the range implied by a
reconstruction-based estimator is an order of magnitude worse than the proposed estimator's,
regardless of architecture or budget. Second, at 20 dB the longer-trained MLP has a **better** NMSE
than the matched-budget one (1.08e-3 against 8.66e-3) but a **worse** implied range (1.8696 against
1.3955 m), with non-overlapping intervals --- so NMSE does not order range accuracy.

### S13.7 The compute-budget curve

Both architectures were trained at more than one budget, so "is the deep estimator simply
under-trained?" can be answered with a curve rather than a single control. All runs use the same pool,
batch, optimizer and schedule; only the number of gradient steps changes.

| Budget (steps) | MLP, NMSE at 10 dB | CNN, NMSE at 10 dB | MLP vs proposed |
|---|---|---|---|
| 4000 (matched) | 0.045617 +/- 0.002923 | 0.070530 +/- 0.002863 | 56x |
| 8000 (2x) | 0.005802 +/- 0.000267 | 0.011669 +/- 0.000171 | 7.2x |
| 16000 (4x, CNN only) | --- | 0.004208 +/- 0.000168 | --- |
| 16000 (4x) | 0.001938 +/- 0.000050 | 0.004208 +/- 0.000168 | 2.4x |
| 32000 (8x) | 0.000975 +/- 0.000019 | --- | 1.20x |
| 64000 (16x) | 0.000842 (single seed) | --- | 1.04x |
| Proposed | **0.000810** | **0.000810** | 1x |

The proposed estimator reaches 0.000810 at **4000** steps. Three readings follow.

**First, the deep estimators are nowhere near saturated at the matched budget.** The MLP improves
by 7.9x from 4000 to 8000 steps, by 3.0x to 16000, by 2.0x to 32000 and by 1.16x to 64000. The
diminishing returns are clear but it never fully plateaus within the budget tested.

**Second, the NMSE gap does close.** Sixty-four thousand steps reaches an NMSE of 0.000842 against
the proposed estimator's 0.000810 --- a factor of 1.04 --- and even 32000 steps, half that budget,
is within a factor of 1.20. On the channel-reconstruction metric the two families therefore become
comparable at eight to sixteen times the compute.

The CNN follows the same shape (6.0x from 4000 to 8000, 2.8x from 8000 to 16000) and is uniformly
about twice as far from the proposed estimator as the MLP at equal budget.

**Third, and this is the part that matters, the same is not true of the range** --- which is the
subject of S13.10.

### S13.8 The 2x2 completed, and the 20 dB inversion

With the 4x CNN now trained, the architecture-by-budget table is (the 4x CNN was evaluated at 10 dB only):

| | 10 dB NMSE | 10 dB range (m) | 20 dB NMSE | 20 dB range (m) |
|---|---|---|---|---|
| MLP, 4000 steps | 4.56e-2 | 2.5304 +/- 0.0361 | 8.66e-3 | 1.3955 +/- 0.0590 |
| CNN, 4000 steps | 7.05e-2 | 2.5660 +/- 0.0687 | 1.45e-2 | 1.5480 +/- 0.1881 |
| MLP, 16000 steps | 1.94e-3 | 2.0064 +/- 0.1615 | 1.08e-3 | 1.8696 +/- 0.1792 |
| CNN, 16000 steps | 4.21e-3 | 2.0463 +/- 0.1371 | --- | --- |
| Proposed | 8.10e-4 | **0.1754** | 2.12e-4 | **0.0771** |

At 20 dB the longer-trained MLP has the **better** NMSE (1.08e-3 against 8.66e-3) and the **worse**
implied range (1.8696 against 1.3955 m), with non-overlapping intervals. That inversion is the
cleanest single demonstration in this supplement that channel NMSE does not order range accuracy.

### S13.9 On the independent-extraction control, and a negative result

To check that the "deep output is range-blind" conclusion is not an artifact of the grid-plus-refine
extraction, an entirely different extractor was tried: a continuous Nelder-Mead minimization of the
gain-fitted residual, with 16 restarts over the (r, theta) plane, applied to the same 600 samples.

It fails as a control. The continuous optimizer returns **7.0475 m** on the deep estimator's output
and **7.1075 m** on the **noise-free** channel --- the two are within 1% of each other, which means the
optimizer is not converging rather than that the two inputs carry the same range information. Since it
performs no better than chance even on a perfect input, its result says nothing about the deep
estimator and it is **not used** for any claim in this letter.

The extraction-dependence question is instead bounded by the refinement sweep of S11.3b, which spans
9.1% across three refinement budgets, all of them about 14 times worse than the proposed estimator.

### S13.10 The saturation endpoint, and what it settles

The 64000-step MLP is the largest budget tested (16x the matched budget, 5.2 hours of training on this
machine). Its implied geometry and its feature probe were measured with the same procedure as every
other model.

| Model | 10 dB NMSE | 10 dB range (m) | 20 dB NMSE | 20 dB range (m) |
|---|---|---|---|---|
| MLP, 4000 steps | 4.56e-2 | 2.5304 | 8.66e-3 | 1.3955 |
| MLP, 16000 steps | 1.94e-3 | 2.0064 | 1.08e-3 | 1.8696 |
| MLP, 32000 steps | 9.75e-4 | **1.2168** | 3.78e-4 | **1.1841** |
| CNN, 8000 steps | 1.17e-2 | 2.4764 | 4.71e-3 | 1.4403 |
| MLP, 64000 steps | **8.41e-4** | 1.2554 | **2.93e-4** | 1.1780 |
| Proposed | 8.10e-4 | **0.1754** | 2.12e-4 | **0.0771** |
| Ratio (64000 / proposed) | 1.04x | **7.2x** | 1.38x | **15.3x** |

**This settles the question in the most informative way, and it does not entirely favour the letter's
framing.** At sixteen times the compute the deep estimator's channel NMSE reaches parity with the
proposed estimator --- 1.04x at 10 dB and 1.38x at 20 dB --- so the deep estimator is not simply
under-trained. Its range estimate also improves substantially with budget, from 2.53 m at 4000 steps
to 1.26 m at 64000 at 10 dB. The reconstruction-based family is therefore **not** categorically
range-blind; given enough compute it does learn the range cue.

However, the two metrics improve at completely different rates. At 20 dB, sixteen times the budget buys
a channel NMSE within 38% of the proposed estimator while the range estimate is still **15.3 times
worse** --- 1.178 m against 0.0771 m --- and the proposed estimator reaches 0.0771 m at the matched
budget. So the accurate statement is:

> A deep channel estimator can match a parametric estimator's channel NMSE and still be an order of
> magnitude worse at the geometric parameters that determine the channel. At 10 dB the range estimate
> improves only 2.1x (2.53 to 1.22 m) across the whole budget sweep, while the channel NMSE improves
> 54x over the same sweep and the proposed estimator is 7.0x better on range at 1/8 of the budget. Channel NMSE does not order
> range accuracy, and the remaining gap is one of compute efficiency --- roughly 16x in training budget,
> and three orders of magnitude in inference cost --- not of feasibility.

A second observation cuts across the budget story. The 32000-step model has a *worse* channel NMSE than
the 64000-step one (9.75e-4 against 8.41e-4 at 10 dB) yet a marginally *better* output geometry (1.2168 m
against 1.2554 m), so range accuracy is not monotone in compute either, even while the channel metric is.
Then the 64000-step model has the best channel NMSE and
the best output geometry of any deep model tested, yet its feature probe (0.3938 m at 10 dB) is
**worse** than the 16000-step model's (0.2554 m). The internal representation does not improve
monotonically with training either, so neither the NMSE nor the representation alone predicts the range
estimate. That is the same lesson as S12.8, seen from a third direction.

## S14. Sensitivity to amplitude-calibration error

The effect of amplitude-calibration error at 1%, 5% and 10% is measured here. This
matters because Section II-C identifies the **absolute** received amplitude as the operative range
cue, so the proposed estimator inherits whatever gain error the receiver's link budget carries. The
letter previously stated only that "a link budget calibrated to a few percent is required"; that
requirement is quantified here.

### S14.1 Protocol

The receiver applies a positive real gain error, i.e. the observation is multiplied by $(1+\epsilon)$
without the estimator being told. Both signs are run. Everything else is unchanged: the same three
trained seeds, the same holdout, the same inference path. No retraining is involved, so the
measurement isolates the calibration effect.

### S14.2 Results

Range RMSE in metres, and the signed mean range bias.

| $\epsilon$ | 10 dB RMSE | 10 dB bias | 20 dB RMSE | 20 dB bias |
|---|---|---|---|---|
| 0 | **0.1682** | +0.007 | **0.0708** | +0.001 |
| +1% | 0.1974 | -0.098 | 0.1312 | -0.104 |
| -1% | 0.2067 | +0.112 | 0.1353 | +0.107 |
| +2% | 0.2724 | -0.202 | 0.2332 | -0.208 |
| -2% | 0.2878 | +0.218 | 0.2398 | +0.214 |
| +5% | 0.5637 | -0.506 | 0.5530 | -0.513 |
| -5% | 0.6005 | +0.539 | 0.5780 | +0.536 |
| +10% | 1.0545 | -0.975 | 1.0548 | -0.983 |
| -10% | 1.1643 | +1.077 | 1.1536 | +1.075 |

The one-line read-out `1/mean_s abs(y(s))` behaves similarly (0.335 m at 10 dB with no error, 0.44 m
at +1%, 0.87 m at +5%); it has no learned error floor, so at 10 dB with a **negative** error it can
beat the proposed estimator (0.359 m at -5%), while at 20 dB the proposed estimator is the more
accurate of the two at every error level tested.

### S14.3 What this establishes

**1. The bias is proportional to the calibration error.** A 1% gain error shifts the range estimate
by about 0.10 m, 5% by about 0.51 m and 10% by about 1.0 m, at both SNRs and with either sign. The
response is linear in $\epsilon$ across the whole tested range, as expected if the estimator inverts
an amplitude law of the form $|h| \propto 1/r$.

**2. Accuracy is calibration-limited, not SNR-limited.** At 20 dB a **1%** gain error raises the range
RMSE from 0.071 m to 0.131 m --- a factor of 1.85 --- and 5% raises it to 0.553 m, a factor of 7.8.
Improving the SNR beyond about 15 dB therefore buys nothing unless the calibration improves with it.
At 10 dB the situation is milder: a 1% error costs only 17%, so the method is still noise-limited at
that SNR.

**3. The practical requirement is therefore tighter than "a few percent".** To keep the range RMSE
below 0.2 m at 20 dB the gain must be calibrated to better than about 1%. This is a genuine
constraint on deployment and it is stated in the letter rather than left implicit.

### S14.4 Scope

Only a frequency-flat, real, multiplicative gain error is modeled. Frequency-selective calibration
error, phase error and time-varying gain are not, and could behave differently.

### S14.5 Phase error is harmless (a control that confirms the mechanism)

Section II-C identifies the **amplitude** as the range cue and assumes the carrier phase is unknown.
If that is right, a phase-calibration error should cost nothing, because the estimator is already
invariant to an unknown common phase. This is a sharp test of the mechanism, and it passes cleanly:

| Phase error (rad) | 10 dB range RMSE (m) | 20 dB range RMSE (m) |
|---|---|---|
| 0 | 0.1682 | 0.0708 |
| 0.05 | 0.1681 | 0.0706 |
| 0.10 | 0.1680 | 0.0705 |
| 0.25 | 0.1684 | 0.0706 |
| **0.50 (about 29 degrees)** | **0.1694** | **0.0714** |

A phase error of half a radian changes the range RMSE by **0.7%** at 10 dB and 0.8% at 20 dB,
against the 85% penalty that a 1% amplitude error imposes at 20 dB. The contrast is the point:
**only the amplitude needs calibration; the carrier phase does not.** That converts the letter's
statement about the range cue from an assertion into a measured property.

### S14.6 A finer sweep near the operating point

| $\epsilon$ | 5 dB | 10 dB | 15 dB | 20 dB |
|---|---|---|---|---|
| 0 | 0.289 | 0.168 | 0.103 | 0.071 |
| 0.5% | 0.291 | 0.175 | 0.116 | 0.089 |
| 1% | 0.303 | 0.197 | 0.150 | 0.131 |
| 2% | 0.353 | 0.272 | 0.243 | 0.233 |
| 5% | 0.596 | 0.564 | 0.555 | 0.553 |
| 10% | 1.061 | 1.054 | 1.055 | 1.055 |

Two features stand out. First, **at 5% and 10% the four SNRs give almost the same value** (0.596,
0.564, 0.555, 0.553 and about 1.055 throughout): once the calibration error exceeds roughly 2%, it
dominates the noise completely and raising the SNR achieves nothing. Second, the requirement is
SNR-dependent. Holding the 20 dB range RMSE below 0.15 m needs better than about 1% calibration,
whereas at 10 dB the same 1% error costs only 17%.

The same sweep extended down to $0$ dB, and plotted as Fig. 2 of the letter, makes the crossing
explicit: a $20$ dB improvement in SNR buys a factor of **7.00** in range at perfect calibration and only
**1.06** at $10\%$ error. The residual past a few percent is therefore a deterministic bias in the
amplitude cue, not a random error, and no amount of transmit power removes it.

### S14.7 How tight does the calibration have to be? (finer grid)

| $\epsilon$ | 15 dB: RMSE / factor | 20 dB: RMSE / factor |
|---|---|---|
| 0 | 0.103 / 1.00 | 0.071 / 1.00 |
| 0.1% | 0.103 / 1.00 | 0.071 / 1.01 |
| 0.2% | 0.105 / 1.02 | 0.074 / 1.04 |
| 0.5% | 0.116 / 1.12 | 0.089 / 1.26 |
| 0.75% | 0.131 / 1.27 | 0.109 / 1.53 |
| 1% | 0.150 / 1.45 | 0.131 / 1.85 |
| 1.5% | 0.194 / 1.88 | 0.181 / 2.55 |
| 2% | 0.243 / 2.36 | 0.233 / 3.29 |

The requirement is tighter than "a few percent". At 20 dB a **0.5%** gain error already costs 26%, and
a 2% error costs a factor of 3.3. To hold the 20 dB range RMSE within 20% of its no-error value the
gain must be known to roughly **0.4%**. At 15 dB the same 20% target needs about **1.8%**. The
calibration requirement therefore scales with the operating SNR, which is the practical statement this
section exists to make.

## S15. Extension to a two-dimensional aperture

The letter uses a one-dimensional line aperture. One may ask whether the
central physical argument --- that a range error appears as an almost uniform phase
rotation, and is therefore nearly collinear with an unknown complex gain --- is an
artifact of that reduction. It is not. Only the derivation and a single equal-budget
training run are reported; no full 2D pipeline was built.

### S15.1 The derivation carries over unchanged

For a square $D\times D$ aperture with elements $\mathbf{s}=(s_x,s_y)$ and a user at
direction cosines $(\alpha,\beta)$, the path length is

$$d(\mathbf{s}) = \sqrt{r^2+|\mathbf{s}|^2-2r(s_x\alpha+s_y\beta)}$$

so that

$$\frac{\partial d}{\partial r} = \frac{r-s_x\alpha-s_y\beta}{d}
\approx 1 - \frac{s_x\alpha+s_y\beta}{r} + \frac{|\mathbf{s}|^2}{2r^2} + \cdots$$

The leading term is a constant across the aperture, i.e. exactly the nuisance that the
complex-gain fit removes. **Equation (5) of the letter therefore extends verbatim to a 2D
aperture**; only the higher-order residual changes, and it stays small.

### S15.2 The collinearity deviation is larger in 2D, and the degeneracy is not removed

Comparing a 256-element line aperture with a $16\times16$ aperture of the same side
length $D=1$ m, the deviation of $\partial d/\partial r$ from a constant is:

| $r$ (m) | $\theta$ (rad) | 1D deviation | 2D deviation | 2D improvement |
|---|---|---|---|---|
| 6 | 0.2 | 5.005e-07 | 1.297e-06 | 0.4x |
| 10 | 0.2 | 6.500e-08 | 1.690e-07 | 0.4x |
| 16 | 0.2 | 9.925e-09 | 2.583e-08 | 0.4x |
| 6 | 0.6 | 2.579e-07 | 1.012e-06 | 0.3x |
| 10 | 0.6 | 3.298e-08 | 1.298e-07 | 0.3x |
| 16 | 0.6 | 5.009e-09 | 1.974e-08 | 0.3x |
| 6 | 1.2 | 1.005e-08 | 7.156e-07 | 0.0x |
| 10 | 1.2 | 1.247e-09 | 9.077e-08 | 0.0x |
| 16 | 1.2 | 1.874e-10 | 1.375e-08 | 0.0x |

The deviation exceeds the naive $\sqrt{2}$ expectation, because $|\mathbf{s}|^2$
spans $[0,D^2/2]$ in 2D against $[0,D^2/4]$ in 1D and the cross terms add further
curvature. But the absolute magnitude is what matters: the 2D deviation is still
$10^{-8}$ to $10^{-6}$, so $\partial d/\partial r$ remains very nearly constant and the
range remains nearly indistinguishable from a gain. The gain in range accuracy in 2D
comes from the Cram\'er--Rao bound rather than from this deviation, and is quantified
separately in Section S15.3 (a factor of 1.6 to 6.5).

### S15.3 The range CRB is improved, and still enormous

With the unknown gain projected out, at equal element count:

| $r$ (m) | angle | 1D $\sqrt{\mathrm{CRB}_r}$ (m) | 2D $\sqrt{\mathrm{CRB}_r}$ (m) | ratio |
|---|---|---|---|---|
| 6 | 0.20 | 4.25 | 2.64 | 0.622 |
| 10 | 0.20 | 19.57 | 12.18 | 0.622 |
| 10 | 0.60 | 27.39 | 13.84 | 0.505 |
| 16 | 0.20 | 80.00 | 49.82 | 0.623 |
| 16 | 1.20 | 439.68 | 67.49 | 0.153 |

The 2D aperture reduces the range CRB to between 1/1.6 and 1/6.5 of the 1D value,
but the bound itself remains between 2.6 m and 67 m --- comparable to the $[5,18]$ m
user range. Single-snapshot range estimation stays information-theoretically out of
reach in 2D as well.

### S15.4 A dictionary is no better in 2D

At identical settings (N=400, a $60\times41$ $r$--direction grid, L2-normalized atoms,
same random stream, 10 dB):

| Baseline | range RMSE |
|---|---|
| 1D dictionary | 7.4035 m |
| 2D dictionary | 7.4035 m |

The two are identical to four decimals: the error is dominated by the common
$(r,\text{direction})$ ambiguity, and the extra degree of freedom in the 2D atom buys
nothing. Adding aperture dimensions does not rescue coefficient-fitting dictionaries.

### S15.5 An equal-budget training run in 2D

A 1.28 M-parameter network of the same architecture was trained on 500 k 2D samples for
16000 steps with three classification heads $(r,\alpha,\beta)$:

| SNR (dB) | NMSE (gain-fitted) | range RMSE (m) | direction RMSE |
|---|---|---|---|
| -5.0 | 1.00000 | 5.9096 | 0.7512 |
| 0.0 | 1.00002 | 3.5114 | 0.6056 |
| 5.0 | 1.00027 | 1.5741 | 0.3806 |
| 10.0 | 0.99994 | 0.5986 | 0.2157 |
| 15.0 | 0.99844 | 0.2389 | 0.1260 |
| 20.0 | 1.00018 | 0.1323 | 0.0890 |
| 25.0 | 1.00025 | 0.1058 | 0.0774 |
| 30.0 | 1.00131 | 0.0995 | 0.0733 |

The estimator learns the **range** well --- 0.20 m at 20 dB, approaching the 1D result
of 0.077 m --- but the direction is learned more slowly: at 16000 steps the two direction
cosines still carry an error of order 0.03, which decorrelates the aperture phase and
leaves the channel NMSE near unity. The 2D task is a strictly harder regression at equal
budget because it has three geometry parameters instead of two; this run is reported as
evidence that the method transfers, not as a converged 2D result.

### S15.6 Scope

- Square aperture, single-path LoS, physical visibility disk $\alpha^2+\beta^2\le1$
- Only the range is assessed systematically; the two direction cosines are reported
  only as an error norm
- The 2D network is trained to the equal-step budget, not to convergence

## S16. Additional controls

Four controls are reported to close objections that could be raised against the comparison. Three of them
are decisive in the authors' favour; the fourth (S16.4) qualifies the letter's framing.

### S16.1 The LMMSE baseline does not depend on an oracle covariance

The letter's LMMSE uses the sample covariance of the evaluation set itself --- a genie quantity. It
could be objected that the comparison is therefore generous to LMMSE. It is not: replacing the oracle
covariance with one estimated from the **training** set changes the result by at most 0.03 dB.

| SNR (dB) | LMMSE, oracle $\mathbf{C}_h$ | LMMSE, estimated $\mathbf{C}_h$ | difference | Proposed | lead over estimated |
|---|---|---|---|---|---|
| -5 | 0.2083 | 0.2070 | -0.03 dB | 0.02885 | **8.56 dB** |
| 0 | 0.07950 | 0.07922 | -0.02 dB | 0.006626 | **10.78 dB** |
| 5 | 0.02730 | 0.02726 | -0.01 dB | 0.002095 | **11.14 dB** |
| 10 | 0.009011 | 0.009003 | -0.00 dB | 0.000693 | **11.14 dB** |
| 15 | 0.002935 | 0.002933 | -0.00 dB | 0.000253 | **10.65 dB** |
| 20 | 0.000951 | 0.000950 | -0.00 dB | 0.000115 | **9.16 dB** |

The estimated covariance is built from 20000 training samples and differs from the oracle by 11.4% in
Frobenius norm, yet the LMMSE performance is unchanged. The reason is that the dominant error term for
LMMSE in this regime is the noise, not the covariance mismatch. **Conclusion: the oracle covariance
confers no advantage, and the proposed estimator's lead over an implementable LMMSE is 8.6 to 11.1 dB.**

### S16.2 Outside the training SNR range the method degrades gracefully to a discretization floor

The model is trained with SNR drawn uniformly from $[-5,20]$ dB. It is evaluated here up to 40 dB,
i.e. 20 dB beyond the training range.

| SNR (dB) | range RMSE (m) | NMSE (gain-fitted) |
|---|---|---|
| 20 (in range) | 0.0708 | 1.15e-4 |
| 25 | 0.0571 | 7.22e-5 |
| 30 | 0.0520 | 5.87e-5 |
| 35 | 0.0503 | 5.45e-5 |
| 40 | 0.0497 | 5.32e-5 |

**Aggregation convention.** The values above are the RMSE of the prediction \emph{averaged over the
three seeds} ($s_0,s_1,s_2$), i.e.\ an ensemble. The main text instead reports the mean of the three
\emph{per-seed} RMSEs, which is why its $20$~dB figure ($0.077$~m) sits about $8\%$ above the
$0.0708$~m listed here. The two describe the same model and the same holdout and differ only in
whether the seeds are combined before or after the error is formed; the ensemble is the better of the
two. Both are honest readings, and neither is used to flatter the comparison.

Nothing diverges. The range RMSE falls monotonically and then flattens at about **0.05 m**, which is
half the range-bin width of the classification grid ($(18-5)/127 = 0.102$ m). That floor is a property
of the output discretization, not of the physics: the soft-argmax interpolates within a bin but cannot
resolve below roughly half of one. It is reported here as an honest limit rather than hidden, and it is
the quantity that a finer grid would buy.

### S16.3 The $\lambda$ periodicity, visualised

Section III-A argues that the raw reconstruction loss oscillates with period $\lambda$ in range, which
is why direct regression against it is infeasible. Fig. S2 shows the loss swept over $\hat r$ in a
$\pm0.15$ m window at 0.5 mm resolution, with the gain-fitted loss plotted alongside.

![Fig. S2. The $\lambda$ periodicity of the raw reconstruction loss. The loss swept over $\hat r$ in a $\pm0.15$ m window at 0.5 mm resolution for two geometries; the gain-fitted loss is drawn on the same axes.](figs/fig4-lambda-periodicity.pdf)

| Case | Local minima in the window | Median peak separation | $\lambda$ |
|---|---|---|---|
| $r=10$ m, $\theta=0.6$ | 3 | **0.1000 m** | 0.1 m |
| $r=16$ m, $\theta=0.2$ | 3 | **0.1000 m** | 0.1 m |

The measured period equals $\lambda$ to four digits in both cases. The figure makes the argument
visual: the raw loss has three separate minima with the true range in one of them, so a gradient-based
regressor has no way to know which basin it is in. The gain-fitted curve, drawn on the same axes, is
monotone over the same window --- which is exactly why the complex-gain fit is the correct metric when
comparing parametric estimators.

### S16.4 The 2x2 of loss and input representation

The letter's ablation varies the loss (classification with soft-argmax against regression) and the
input representation (raw against magnitude-normalized) separately. Crossing them is informative.
All four cells use $M=256$, 4000 steps, three seeds, the same holdout and the same noise stream; the
numbers are 3-seed ensembles at 10 dB.

| Loss | Input | NMSE (gain-fitted) | range RMSE (m) | angle RMSE (rad) |
|---|---|---|---|---|
| regression (parameter MSE) | raw | 1.03e-2 | 0.1787 | 0.00907 |
| regression (parameter MSE) | magnitude-normalized | 1.16e-02 | 1.9834 | 0.01051 |
| classification + soft-argmax | raw | **6.93e-4** | **0.1682** | **0.00424** |
| classification + soft-argmax | magnitude-normalized | 8.17e-4 | 1.9542 | 0.00416 |

Three readings. First, **the loss function controls the channel NMSE**: classification beats regression
by a factor of 15 at equal input and equal budget. Second, **the input representation controls the
range**: the raw input gives 0.168 m where the magnitude-normalized input gives 1.95 m, an 11.6-fold
difference, with the loss held fixed. Third, and this is the point of crossing them, **the two effects
are largely independent** --- no single cell is good at both, and the letter's configuration
(classification plus raw) is the only one that combines the better loss with the better input.

A separate control on the loss itself: a regression head trained **against the reconstruction loss**
(`loss=recon`) does not survive 250 of the 4000 steps before the training diverges; its best checkpoint
gives an NMSE of 0.83 and a range error of 7.59 m. That is consistent with, and stronger than, the
letter's statement that reconstruction-loss regression is infeasible --- it is not merely worse, it
fails to train.

## S17. Bias, multiuser scaling, the endfire region, and non-ideal noise

Four further controls, all evaluated with the frozen three-seed model.

### S17.1 The estimator is essentially unbiased; it meets the bound at 10 dB and exceeds it above

The letter uses the Cram\'er--Rao bound of caliber C as a reference scale. It may be objected
that it is being used as if it certified optimality, and that the estimator could be biased. Both
concerns are answered by decomposing the error directly. (The caliber-C bound is the RMS RMSE
$C_{\text{rmse},r}$ of `figs/crb.json`; the values below are that quantity, not a further
square root of it.)

| SNR (dB) | bias (m) | standard deviation (m) | RMSE (m) | CRB, caliber C (m) | RMSE / CRB |
|---|---|---|---|---|---|
| -5 | -0.2276 | 0.8033 | 0.8347 | 0.9473 | 0.88 |
| 0 | +0.0132 | 0.4959 | 0.4959 | 0.5327 | 0.93 |
| 5 | +0.0166 | 0.2885 | 0.2889 | 0.2996 | 0.96 |
| 10 | +0.0066 | 0.1681 | 0.1682 | 0.1685 | 1.00 |
| 15 | +0.0024 | 0.1030 | 0.1030 | 0.0947 | 1.09 |
| 20 | +0.0014 | 0.0708 | 0.0708 | 0.0533 | 1.33 |

Two readings, and the second one matters for how the letter must be worded.

**First, the estimator is essentially unbiased.** For SNR $\ge 0$ dB the bias contributes under
0.3% of the mean squared error; only at $-5$ dB does it reach 7%, and even there it is small
compared with the spread.

**Second, the RMSE is at or above the computed bound over the operating range of interest, and
only beats it at low SNR.** Below about $10$~dB the RMSE is *smaller* than the caliber-C bound
(0.88--0.96$\times$ at $-5$ to $5$~dB); at $10$~dB the two coincide ($1.00\times$), and above it
the RMSE exceeds the bound ($1.09\times$ at $15$~dB, $1.33\times$ at $20$~dB). The high-SNR
exceedance is the ordinary situation for a biased, grid-parameterized estimator: as the bound
drops steeply with SNR, the estimator's own residual bias floor comes to dominate. The low-SNR
sub-bound behaviour has a specific cause --- caliber C assumes a *single* unknown complex gain of
known magnitude, whereas a network that has learned the amplitude prior over the training
distribution is not restricted to that model and can do better on the distribution it was trained
on. Neither regime is a claim of optimality.

The headline aggregate figures quoted in the letter (Section~S3, the full holdout protocol at
$M=256$) give $0.175$ and $0.077$~m at $10$ and $20$~dB, i.e. $1.04\times$ and $1.45\times$ the
same bound --- the same conclusion, from an independent noise draw. The bound is a useful scale
for a classical single-snapshot estimator, and it is reported as such --- **it is not claimed to
bound the proposed estimator, and the letter does not use it to argue optimality.**

### S17.2 Multiuser scaling is linear and lossless

CAPA is inherently a multiuser problem, so single-user results alone are not sufficient. Users are
processed independently by the same frozen model, and the total wall-clock time is measured:

| Users $K$ | total time (s) | per user (ms) | mean range RMSE (m) |
|---|---|---|---|
| 1 | 0.21 | 214.1 | 0.1682 |
| 2 | 0.43 | 215.5 | 0.1682 |
| 4 | 0.91 | 227.0 | 0.1682 |
| 8 | 1.75 | 218.5 | 0.1682 |
| 16 | 3.55 | 221.8 | 0.1682 |

The cost is linear in $K$ and the accuracy is bit-for-bit unchanged, because a user's channel
depends only on that user's geometry. Sixteen users together take 3.55 s, against 86.1 s for a
single-user dictionary refinement at 1200 samples --- a factor of about 390 in the letter's
favour at equal user count, before any parallelism is applied.

### S17.3 The endfire region degrades the angle, not the range

The angle CRB diverges at endfire, so the letter truncates its bound report to $|\theta|\le1.2$ rad.
That is not where the estimator fails, however:

| $|\theta|$ region | samples | range RMSE (m) | angle RMSE (rad) |
|---|---|---|---|
| $0$--$0.2$ (broadside) | 268 | 0.1668 | 0.00107 |
| $0.2$--$0.6$ | 500 | 0.1788 | 0.00107 |
| $0.6$--$1.2$ | 768 | 0.1727 | 0.00159 |
| $1.2$--$1.5$ (endfire) | 387 | 0.1778 | 0.00580 |

Across the whole domain the range RMSE varies by only 7%, from 0.167 m at broadside to 0.178 m
at endfire. The angle RMSE, by contrast, degrades by a factor of 5.4, exactly as the diverging
angle bound predicts. **The truncation of the bound report is therefore a statement about the
bound, not about the estimator, and the method does not exhibit a range failure region.**

### S17.4 Phase noise is mild; spatially correlated noise is not

Two radio-frequency non-idealities beyond the frequency-flat gain error of S14 are tested at
10 dB on the same frozen model.

| Perturbation | range RMSE (m) | factor |
|---|---|---|
| none | 0.1682 | 1.00 |
| per-element phase noise, $\sigma=0.05$ rad | 0.1702 | 1.01 |
| per-element phase noise, $\sigma=0.10$ rad | 0.1821 | 1.08 |
| per-element phase noise, $\sigma=0.20$ rad | 0.2929 | 1.74 |
| spatially correlated noise, $\rho=0$ | 0.2463 | 1.46 |
| spatially correlated noise, $\rho=0.5$ | 0.4040 | 2.40 |
| spatially correlated noise, $\rho=0.9$ | 0.7334 | 4.36 |

Independent per-element phase noise is the milder impairment: 0.2 rad, a large value for a
calibrated array, costs a factor of 1.74. The correlated case is the severe one, and for a
mechanical reason: a spatially smooth error is not averaged away over 256 elements, so it
mimics a genuine wavefront distortion rather than increasing the noise floor. At $\rho=0.9$ the
range RMSE rises to 0.73 m --- still better than the 2.50 m of the refined dictionary baseline in
the ideal case, but a factor of 4.4 worse than the proposed estimator's clean-channel 0.168 m.
This is reported as a genuine limitation: the method is robust to independent phase error and
noticeably less so to spatially correlated error.

### S17.5 Scope

- The correlated-noise model is a first-order exponential correlation, not a measured array
  response
- Multiuser results assume independent channels with no inter-user interference, scheduling or
  pilot reuse
- The bias figures are for the range parameter only

## S18. How far does the dictionary criticism extend?

The letter argues that a polar-domain dictionary with a free per-atom coefficient is range-blind
because the coefficient absorbs the amplitude. That argument was checked only for L2-normalized
atoms with single-atom matching, so one may reasonably ask whether it is an artifact of that
particular implementation. Four variants were therefore tested on the same 600 samples at 10 dB
with an $80\times41$ range--angle grid:

| Variant | selection rule | range RMSE (m) |
|---|---|---|
| A | L2-normalized atoms, single-atom | 7.4607 |
| B | un-normalized atoms (amplitude retained), single-atom | 7.4829 |
| C | per-atom complex-gain fit, residual minimized | **3.0957** |
| D | two-atom OMP, gain-fitted | 7.4829 |

The outcome bounds the claim in both directions.

**Keeping the amplitude in the atom does not help.** Variant B is within 0.3% of variant A. This
is the direct test of the letter's mechanism: whether the amplitude is left in the atom or divided
out, the selected coefficient still absorbs it, so the range cue is discarded either way. The
argument is therefore not an artifact of L2 normalization.

**One variant does help, and the letter should say so.** Minimizing the gain-fitted residual
(variant C) lowers the error from 7.46 m to 3.10 m, a 2.4-fold improvement. The statement that
*no* dictionary construction can recover the range would therefore be too strong, and the
letter does not make it; what it says is that fitting a free coefficient per atom discards the
amplitude cue, which is what variants A, B and D exhibit.

**But no variant is competitive.** The best of the four, 3.10 m, is still 18 times worse than the
proposed estimator's 0.175 m at the same SNR --- and worse than the refined OMP baseline of
Table I, which uses a longer protocol. The practical conclusion is unchanged: for range, the
parametric estimator is not in the same regime as any dictionary construction tested here.

### S18.1 Scope

- Four variants, one SNR (10 dB), 600 samples, gain-fitted criterion for C and D only
- Off-grid continuous-optimization baselines (atomic-norm minimization, sparse Bayesian learning)
  are **not** implemented; see the letter's statement of what is left out

### S18.2 The amplitude-only readout

Table I of the letter also reports a row that sidesteps coefficient fitting entirely: since the
absolute amplitude carries the range cue (Section S16), the range can be read out directly from the
received amplitude, with no calibration and no learning:

$$\hat r \;=\; 1\,\big/\,\mathrm{mean}_s\,|y(s)|$$

On the independent holdout ($n=2000$, protocol of Section S10) this returns **0.34 m at 10 dB** --
an order of magnitude better than any dictionary construction in the table above, yet still
$1.9\times$ worse than the learned parametric estimator at the same SNR (0.175 m), which is the
letter's justification for learning. The full sweep is archived in `figs/amplitude_readout.json`:

| SNR (dB) | $-5$ | 0 | 5 | 10 | 15 | 20 |
|---|---|---|---|---|---|---|
| range RMSE (m) | 5.38 | 2.64 | 0.95 | 0.34 | 0.13 | 0.06 |

This readout also delimits the mechanism claim: it uses nothing but the amplitude, so the fact that
it reaches 0.34 m confirms that the amplitude is the operative cue, and the remaining $1.9\times$
is what the learned angular structure contributes.

## S19. Reproducibility: hyperparameters, schedule and convergence

### S19.1 Exact configuration of the reported model

Every number in the letter comes from three runs that differ only in the seed. The configuration
is recorded verbatim in each run directory (`config.json`):

| Item | Value |
|---|---|
| Input representation | `raw`, i.e. $[\Re y,\Im y]\times10$ |
| Trunk | three fully connected layers, 1024--512--256, ReLU |
| Heads | two classification heads, $G_r=128$, $G_\theta=256$, linear |
| Parameters | 1,280,128 |
| Batch size | 2048 |
| Optimizer | Adam, learning rate $10^{-3}$, cosine-annealed to $10^{-5}$ over the 4000 steps |
| Steps | 4000 (the matched budget used for every comparison) |
| Training pool | 1,000,000 of 2,000,000 noiseless channels, `tr_M256`, seed 0 |
| Validation | 250-step cadence, NMSE (gain-fitted) at 10 dB |
| Checkpoint | best validation NMSE; equals the final checkpoint to within noise (S12.6) |
| Seeds | 0, 1, 2 |

### S19.2 Data generation

Channels are generated exactly as described in Section IV-A: distance $r\sim U[5,18]$ m and
angle $\theta\sim U[-\pi/2,\pi/2]$ drawn independently per sample, then
$h(s)=\exp(-j2\pi d(s)/\lambda)/d(s)$ with $d(s)=\sqrt{r^2+s^2-2rs\sin\theta}$. The stored tensor is
noiseless; noise is injected on the fly during training at an SNR drawn uniformly from
$[-5,20]$ dB, so the generator is fully determined by the seed and no noisy dataset is kept.

### S19.3 Convergence

Fig. S3 plots the training loss and the validation NMSE against step for all three seeds. The
network is trained to a fixed step count rather than to a convergence criterion, because the entire
comparison in this letter is made at equal budget; reporting a run that was allowed to converge
would confound budget with architecture.

![Fig. S3. Convergence of the three reported seeds. Left: training loss against step. Right: validation NMSE (gain-fitted) against step.](figs/fig3-training-curves.pdf)

| Seed | logged points | loss at step 4000 | minimum logged loss |
|---|---|---|---|
| 0 | 16 | 4.5589 | 4.5365 |
| 1 | 16 | 4.5536 | 4.5297 |
| 2 | 16 | 4.5504 | 4.5504 |

The cross-entropy is close to its floor early and the seed-to-seed spread at the final step is
0.2%, which is why the three-seed NMSE agreement reported in the main text (0.000810 with a 95%
interval of about 6%) is dominated by the fine-tuning noise of the soft-argmax rather than by
instability of the loss.

### S19.4 Environment

Python 3.11, numpy 2.4.6, torch 2.14.0+cpu, scipy 1.17.1, matplotlib, pymupdf. All experiments are
CPU-only on an Intel Core Ultra 5 125H with 16 GB of RAM. Compilation uses the bundled Tectonic
engine, which needs no network. No GPU is used anywhere in this work.

## S20. Off-grid baselines, and what they reveal about the cost landscape

The letter's baselines are all grid-based. A natural question is why no continuous (off-grid)
estimator is compared. Three were implemented and run at 10 and 20 dB on the same channel model.

### S20.1 What was run

| Method | Description |
|---|---|
| LM-ML, coarse starts | Nelder--Mead minimization of the gain-fitted residual from 16 fixed starts spanning $r\in\{6,10,14,17\}$ and $\theta\in\{-1,-0.3,0.3,1\}$ |
| Dictionary top-8 + refine | an $120\times61$ grid match, the eight strongest atoms used as starts, each refined to convergence, best residual kept |
| SBL + off-grid refine | expectation--maximization sparse Bayesian learning on a $40\times15$ grid, then the strongest posterior atom refined continuously |
| ANM (true atomic norm) | dual of the continuous atomic norm solved by a cutting-plane method with CLARABEL; the grid is used only to *find* the most-violating atom, never to restrict the constraint set |

The first two are local optimizers restarted from different initialisations; the third is the
standard practical form of an off-grid sparse estimator; the fourth is a genuine atomic-norm
minimization over the **continuous** atom set, not a grid relaxation of it.

### S20.2 Results

| Method | range RMSE at 10 dB (m) | at 20 dB (m) |
|---|---|---|
| Proposed (matched budget) | **0.1754** | **0.0771** |
| Refined OMP, Table I | 2.4993 | 1.2595 |
| **ANM, true atomic norm** | **2.7034** | 3.8670 |
| LM-ML, coarse starts | 7.3135 | 7.4214 |
| Dictionary top-8 + refine | 7.5324 | 7.2919 |
| SBL + off-grid refine | 3.6965 | 3.4104 |

Both continuous methods are **worse than the plain grid dictionary**, and both are worse at
20 dB than at 10 dB. That is not a coding accident, and it is the most interesting result in
this section.

### S20.3 Why continuous optimization fails here

Section III-A shows that a range error $\delta r$ rotates the reconstructed channel by
$-2\pi\delta r/\lambda$ uniformly across the aperture. The gain-fitted residual therefore rises and
falls with period $\lambda$ in range, and Fig. S2 measures that period at exactly 0.1000 m. The
range axis within the user interval $[5,18]$ m therefore contains about
$13/0.1=130$ full oscillation periods of a cost function that a gradient or simplex method must
descend.

A local optimizer started more than a few centimetres from the truth lands in the wrong basin.
This is exactly why:

- the coarse-start LM-ML fails --- its starts are metres apart, hundreds of periods away;
- starting from the eight strongest dictionary atoms does **not** repair it --- those atoms are
  themselves selected by a criterion that is range-blind (S18), so the starts are not close to the
  truth either, and the refinement then walks to the nearest wrong minimum;
- the plain grid dictionary, which is range-blind, is nevertheless *better* than refining it.

The proposed estimator avoids the problem by construction: it never descends a cost surface. It
classifies over the parameter grid with a smooth cross-entropy objective and reads the answer out
with a soft-argmax, so the $\lambda$ periodicity never enters the optimization.

**This is an independent corroboration of the letter's central methodological claim, obtained with
estimators that are, on paper, stronger than the grid baselines.**

The genuinely off-grid method behaves differently, and its result is the fair one to quote. Atomic
norm minimization over the continuous atom set reaches **2.70 m** at 10 dB --- the best of the four
off-grid baselines, and marginally *worse* than the refined dictionary's 2.50 m --- and it
*degrades* to 3.87 m at 20 dB while the proposed estimator improves to 0.077 m. It is still
**15 times worse** than the proposed estimator at 10 dB. An optimizer
that respects the continuous geometry therefore does help relative to naive local descent, but it
does not change the conclusion.

Sparse Bayesian learning sits between the two extremes: with an off-grid refinement of its strongest
posterior atom it reaches **3.70 m** at 10 dB and 3.41 m at 20 dB --- better than local descent, worse
than atomic norm minimization, and 21 to 40 times worse than the proposed estimator. It also costs
38 minutes for 200 samples, against 24.6 ms for the proposed forward pass. The ordering across all
four off-grid methods is therefore: continuous atomic norm (2.70 m), SBL (3.70 m), naive local
descent (7.31--7.53 m) --- every one of them an order of magnitude behind the parametric estimator.

### S20.4 Scope

- Two SNRs, 150--300 samples, one channel model
- Atomic-norm minimization (SDP) and a full variational SBL are not implemented
- The SBL grid is coarse relative to $\lambda$ in range, which by S20.3 is a known handicap; a
  finer grid would not remove the basin problem, only reduce it


### S20.5 A deep-unfolding learnable dictionary

The letter's remaining baseline gap was a modern learned-dictionary method. A LISTA-CP style unrolled
network was therefore built and trained under the same equal-step protocol as everything else.

**Construction.** Ten unrolled ISTA layers over a 32x16 polar dictionary (512 atoms). The linear maps
are initialised from the exact ISTA operators --- W1 = Phi and W2 = I - Phi Phi^T --- and shared across
layers (the CP parameterization), with a per-layer learnable threshold. 524,298 parameters, against
1,280,128 for the proposed network. Training uses the same 1,000,000-sample pool, the same 4000-step
budget, the same batch size and the same three seeds; the loss is channel reconstruction, which is what
a learnable dictionary is trained on. At test time the range is read from the argmax atom, with the
three seeds combined by majority vote.

| Method | range RMSE at 10 dB (m) | at 20 dB (m) |
|---|---|---|
| Proposed | **0.1754** | **0.0771** |
| Refined OMP dictionary | 2.4993 | 1.2595 |
| ANM, true atomic norm | 2.7034 | 3.8670 |
| SBL with off-grid refinement | 3.6965 | 3.4104 |
| **LISTA-CP learnable dictionary** | **5.312** | **5.2601** |
| Naive local descent | 7.31--7.53 | 7.29--7.42 |

**The learned dictionary is the second-worst method tested, and it is beaten by the plain grid
dictionary it was meant to improve on.** It is 30 times worse than the proposed estimator at 10 dB, and
it does not improve with SNR: 5.31 m at 10 dB against 5.26 m at 20 dB. The classical atomic-norm method
beats it by a factor of two.

This is the outcome the letter's argument predicts. A learnable dictionary inherits the property that
makes any coefficient-fitting method range-blind --- the coefficients absorb the amplitude (S18) --- and
unrolling does not change that; it only makes the coefficient fit better. The extra capacity of the
unrolled network is spent on reconstructing the channel more accurately, not on recovering the geometric
parameter that the reconstruction does not expose. It is the same phenomenon as S12.8, where a
channel-reconstruction network was shown to hold range information internally that its output does not
expose, and as S13.10, where sixteen times the compute bought NMSE parity but only 7x on range.

The letter therefore now compares against LS, LMMSE, a refined sparse dictionary, atomic-norm
minimization, sparse Bayesian learning, naive continuous descent, and a deep-unfolded learnable
dictionary. Across all eight, the proposed estimator is the only one below 1 m. It is *not* the only one that improves with SNR --- refined OMP (2.4993 to 1.2595 m) and SBL (3.6965 to 3.4104 m) also improve from 10 to 20 dB, while ANM and the learned dictionary do not. The separation that survives is one of scale, not of trend: at 20 dB the best classical method is 16 times worse than the proposed one, and at 10 dB it is 14 times worse.

## S21. Closed-form derivation of the $r^{-4}$ law and the range-CRB scaling

Three quantities reported in the letter were numerical observations. They are given closed forms here.

### S21.1 The collinearity deviation of the range derivative

With $g(s)\triangleq\partial d/\partial r=(r-s\sin\theta)/d$ and
$d=\sqrt{r^2+s^2-2rs\sin\theta}$, expanding in $s/r$ gives
$d=r-s\sin\theta+s^2\cos^2\theta/(2r)+O(s^3/r^2)$. The first-order term **cancels exactly** between
numerator and denominator, so

$$g(s)=1-\frac{s^2\cos^2\theta}{2r^2}+O(s^3/r^3)$$

Since $s^2$ is even in $s$ and $\mathbb{E}[s^2]=D^2/12$, the two corrections combine to
$1-c\approx\tfrac12\mathrm{Var}(g)=\cos^4\theta\,\mathrm{Var}(s^2)/(8r^4)$. For a uniform line aperture,
$\mathrm{Var}(s^2)=D^4/180$, hence

$$\boxed{\;1-c\;\approx\;\frac{\cos^4\theta\,D^4}{1440\,r^4}\;}$$

Checked on a 42-point grid ($M=256$, $D=1$ m):

| $(r,\theta)$ | closed form | measured | relative error |
|---|---|---|---|
| $(6,0.2)$ | $5.15\times10^{-7}$ | $5.005\times10^{-7}$ | 2.9% |
| $(10,0.2)$ | $6.68\times10^{-8}$ | $6.500\times10^{-8}$ | 2.8% |
| $(16,0.2)$ | $1.018\times10^{-8}$ | $9.925\times10^{-9}$ | 2.6% |
| $(16,1.2)$ | $1.83\times10^{-10}$ | $1.874\times10^{-10}$ | 2.4% |

**Median error 2.4%, maximum 11.8%** over the whole grid. The $r^{-4}$ behavior reported in the
letter is therefore not a fitted trend: it follows from the fourth moment of $s$, and it carries an
explicit $\cos^4\theta$ factor that the numerical sweep had not exposed.

### S21.2 Fisher matrix elements

With $\kappa=2\pi/\lambda$ and $\varphi=e^{-j\kappa d}/d$, the derivatives are
$\partial\varphi/\partial r=\varphi(-j\kappa-1/d)g$ and
$\partial\varphi/\partial\theta=\varphi(-j\kappa-1/d)g_\theta$ with $g_\theta=-rs\cos\theta/d$, so

$$J_{pq}=\frac{2|\alpha|^2}{\sigma^2}\sum_s\frac{\kappa^2+d^{-2}}{d^2}\,g_pg_q$$

The unknown complex gain is the $\varphi$ direction itself; projecting it out is a weighted
centring with weights $w(s)=(\kappa^2+d^{-2})/d^2$:

$$\tilde J_{rr}=\frac{2|\alpha|^2}{\sigma^2}\sum_s w\,(g-\bar g_w)^2,\qquad \bar g_w=\frac{\sum wg}{\sum w}$$

Because $\kappa D=628\gg1$ the weights are nearly constant, so $\tilde J_{rr}\propto\mathrm{Var}_w(g)$ and
connects directly to S21.1. Numerically $\tilde J_{rr}/\mathrm{Var}_w(g)=2.01$--$2.27$ over the grid, the
factor of two being the projection.

### S21.3 The range-CRB scaling law

Combining the two results:

$$\boxed{\;\mathrm{CRB}_r\;\propto\;\frac{r^4}{\cos^4\theta\,D^4}\;}$$

The quantity $\tilde J_{rr}r^4/\cos^4\theta$ is constant across $r=6,10,16$ m:

| $\theta$ (rad) | relative spread over $r$ |
|---|---|
| 0.0 | **0.9%** |
| 0.2 | **0.4%** |
| 0.6 | 3.0% |
| 1.0 | 7.6% |
| 1.2 | 9.5% |

Below 1% at broadside and under 10% even at $1.2$ rad. The physical reading is that **range
information decays as $r^{-4}$ and is amplified by $\sec^4\theta$**, which explains both the rapid
growth of the bound with distance and the specific difficulty of the endfire region noted in S17.3.

The same expansion explains the projection residuals quoted in the letter: the angle direction
$g_\theta\propto s\cos\theta$ is genuinely non-collinear with the constant (so the angle stays
identifiable), whereas the range direction differs from a constant only by the $O(s^2/r^2)$ term ---
which is exactly the quantity in the boxed expression above.

### S21.4 Scope

- Expansion to $O(s^2/r^2)$; error under 5% for $s/r\le0.1$, verified on the whole grid
- Single-path LoS and a uniform line aperture; the 2D counterpart is in S15
- The scaling law gives proportionality only; the absolute constant still depends on
  $\sigma^2$, $|\alpha|^2$ and $M$

## S22. What sets the high-SNR error floor?

Section S16.2 showed that the range RMSE saturates near 0.05 m beyond 30 dB, while the one-line amplitude
readout reaches 0.06 m and the estimator 0.0708 m at 20 dB. A natural question is what fixes that floor. Two
candidate causes were tested by retraining at equal step budget with the grid size G_r and the soft-label
width varied.

### S22.1 Grid resolution is not the cause

| G_r | parameters | best NMSE at 10 dB | steps completed |
|---|---|---|---|
| 64 | 1,263,680 | **0.000750** | 4000 |
| 128 (reported model) | 1,280,128 | 0.000808 | 4000 |
| 256 | 1,313,024 | 0.000845 | 3440 |
| 512 | 1,378,816 | 0.001103 | 2715 |

**The trend is monotone across three seeds** --- a finer grid is consistently worse --- but the individual 64-against-128 step is **not** resolved at 95%: those two intervals overlap, and only the full ordering is repeatable. The claim the paper makes is the weak one: there is no evidence that a finer grid helps, and the ordering is stable. A finer grid is not better, so the floor is not a
discretization limit in the range dimension. The two largest grids also completed fewer steps --- their
heads are wider, so each step costs more at a fixed wall-clock budget --- which is a genuine confound and
is stated rather than hidden. The conclusion that matters survives it: because G_r = 64 matches G_r = 128
while using *half* the resolution, ground is not being lost to the grid.

For this sweep the launch command must pass the grid size explicitly (`--g-r`). The reported table was
obtained after verifying `args.g_r` and the head width out of each checkpoint, rather than trusting the
bit-identical agreement of an unverified run.

The floor is therefore set above the decode grid, in the parameter estimate itself: soft-argmax returns a
convex combination of bin centres, so its output lies strictly inside the convex hull of the grid, and any
residual spread in the logits is contracted toward that hull.


The same sweep as a three-seed ensemble, carrying the 95% intervals that the ordering
claim rests on:

| $G_r$ | parameters | NMSE at 10 dB, 3 seeds (1e-3) |
|---|---|---|
| 64 | 1,263,680 | 0.7543 +/- 0.0311 |
| 128 (reported model) | 1,280,128 | 0.7918 +/- 0.0771 |
| 256 | 1,313,024 | 0.8272 +/- 0.0608 |

### S22.2 Soft-label width does change the floor, and not monotonically

| sigma_r (bins) | NMSE at 10 dB | range RMSE, 20 dB | 30 dB | 40 dB |
|---|---|---|---|---|
| 0.5 | **0.000692** | 0.0940 | 0.0805 | 0.0792 |
| 1.5 (reported) | 0.000808 | 0.0817 | 0.0646 | 0.0627 |
| 3.0 | 0.001040 | 0.0869 | 0.0713 | 0.0696 |

The two extreme settings are cleanly separated at 95% (0.684 +/- 0.033 against 1.041 +/- 0.043, no overlap). A narrower soft label improves the channel NMSE monotonically (0.5 is best) but makes the **range floor
worse** (0.0792 against 0.0627 at 40 dB). The two metrics are optimized by opposite settings of the same
hyper-parameter --- the same theme as S12 and S13, seen from a third direction.

### S22.3 What the floor is, stated carefully

The evidence supports the following and no more:

- the floor is **not** grid resolution, since halving the grid preserves accuracy;
- it **is** sensitive to the soft-label width, a property of the loss and of soft-argmax contraction,
  not of the hardware or the physics;
- the reported configuration (1.5 bins) is not the NMSE-optimal one, so the reported NMSE is not a tuned
  best and a small gain remains on the table;
- these are single-seed runs, whereas every main-text number is a three-seed ensemble, which is why the
  floors here (0.0627--0.0792 m) exceed the 0.0497 m of S16.2.

### S22.4 Scope

- Two hyper-parameters, one training SNR, single seed, 10-minute wall-clock cap per run
- The decode temperature tau --- the most direct control on soft-argmax contraction --- is swept
  separately in S22.5
- No claim is made that the floor has been fully attributed

### S22.5 The decode temperature settles it, and the reported value is not optimal

Section S22.1 argued that the floor lives in the soft-argmax read-out rather than in the grid. The decode
temperature tau is the direct control on that contraction, so it was swept at inference only, on the
frozen three-seed ensemble, without retraining:

| tau | range RMSE, 10 dB | 20 dB | 40 dB |
|---|---|---|---|
| 0.25 | 0.1671 | **0.0643** | **0.0379** |
| 0.50 | **0.1666** | 0.0644 | 0.0386 |
| 1.00 (reported) | 0.1682 | 0.0708 | 0.0497 |
| 2.00 | 0.1796 | 0.0979 | 0.0849 |
| 4.00 | 0.2319 | 0.1795 | 0.1736 |

**The high-SNR floor moves with tau and only with tau.** Lowering it from the reported 1.0 to 0.25 improves
20 dB by 9% and 40 dB by 24%, while leaving 10 dB essentially unchanged (0.1671 against 0.1682). A decoding
parameter that has no effect at low SNR and a large effect at high SNR is exactly the signature of a
contraction artifact: when the noise spread dominates, shrinking the logits changes little; when it does
not, the contraction is the entire error.

This identifies the floor as **decode-limited, not physics-limited**. A finer grid does not help (S22.1); a
lower temperature does.

**The reported configuration is deliberately not the best one.** tau = 1.0 was fixed before any result was
seen, and every main-text number uses it. Choosing tau = 0.25 now would be tuning the decoder on the
evaluation set. The sweep is therefore reported as **headroom that was not exploited**, and the way to
obtain it honestly is to tune on the training pool and freeze the value before touching the hold-out. The
letter's numbers are accordingly conservative by roughly a quarter at 40 dB.

### S22.6 Scope

- The tau sweep is inference-only on the frozen ensemble; no retraining, so no interaction with the
  training loss is captured
- tau and the soft-label width sigma_r act on the same contraction but are not independent, and their
  joint optimum is not searched


## S23. What happens when the single-path assumption is violated

The letter assumes one LoS path per user. That is the most consequential assumption in the paper, so the
cost of violating it is measured directly. Three scenario mismatches were applied to the frozen three-seed
estimator at 20 dB SNR, with no retraining.

### S23.1 A coherent second path is far more damaging than noise

| Interference-to-signal ratio | range RMSE, pilot contamination (m) | multipath (m) |
|---|---|---|
| clean (no second path) | **0.0708** | **0.0708** |
| 30 dB | 0.1048 | 0.1058 |
| 20 dB | 0.2992 | 0.2476 |
| 10 dB | 1.0641 | 1.0472 |
| 6 dB | --- | 1.9919 |
| 3 dB | --- | 3.1250 |
| 0 dB | 4.2998 | --- |

Pilot contamination and multipath are modeled identically here --- a second channel drawn from the same
prior and added with a controlled amplitude --- and the two curves coincide to within 15% at every point,
as they should.

**The striking number is the first row.** A second path at 30 dB SIR carries 0.1% of the signal power and
an amplitude 3.2% of the main path --- ten times *below* the noise at 20 dB SNR --- yet it raises the range
error by 49%, from 0.0708 m to 0.105 m. A perturbation smaller than the noise floor moves the estimate
further than the entire noise contribution does.

The reason is that the interference is **coherent across the aperture**, whereas the noise is not. The
observation is averaged over 256 elements, which suppresses zero-mean noise by $\sqrt{M}$; a second
geometric path is not zero-mean in that sense and is not suppressed. To the classifier it looks like a second
user, and the soft-argmax is pulled between them.

### S23.2 Rician fading

| Rician $K$ | range RMSE (m) |
|---|---|
| 30 dB | 0.1059 |
| 10 dB | 1.0409 |
| 3 dB | 3.0861 |
| 0 dB | 4.2596 |
| $-6$ dB | 6.5098 |

At $K=10$ dB the error is already fifteen times the clean value, and by $K=0$ dB it has reached 4.3 m ---
the scale of the prior. A Rician channel with a substantial scattered component is outside the model this
estimator was trained on.

### S23.3 What this does and does not say

**It does not say the method fails in principle.** The estimator is a classifier over a two-parameter
geometry learned from a single-path prior; it has never been shown a second path, so the degradation is a
statement about the *training distribution*, not about the architecture. Whether retraining on a multipath
prior recovers the accuracy is an open question and is **not** tested here.

**It does say the scope claim matters.** The single-path LoS assumption is not a technicality that can be
waved through in the introduction: a second path 30 dB down already costs half the accuracy. The letter
therefore states the assumption in the system model rather than only in a limitations paragraph, and this
section is the quantitative justification for doing so.

### S23.4 Scope

- Interference modeled as one extra specular path drawn from the same prior; no diffuse or clustered
  scattering, no correlation between the two paths, no angle spread
- Pilot contamination modeled as an additive second user with perfect orthogonality otherwise; no
  channel estimation of the interferer, no joint detection
- Fading is Rician with a single scattered component of uniformly random phase and geometry
- Evaluated at one SNR (20 dB) on the frozen model, single channel realisation per configuration; the
  same 2000-sample hold-out and the same three-seed ensemble as everywhere else

## S24. Can the fragility be trained away?

Section S23 measured the cost of a second path for a model trained on single-path data. It left one
question open, stated there and not answered: is the fragility a property of the *training distribution* or
of the *architecture*? This section answers it by retraining on multipath data and re-measuring.

### S24.1 Design

A second training pool of 1,000,000 samples was generated from $h = \varphi(r_1,\theta_1) + 10^{-\mathrm{SIR}/20}
e^{j\psi}\varphi(r_2,\theta_2)$ with $\mathrm{SIR}\sim U[10,40]$ dB, both geometries drawn from the same prior as
the single-path pool, and $\psi$ uniform. The target is still the LoS pair $(r_1,\theta_1)$. The same
network, the same 4000-step budget, the same batch size and the same three seeds were used, so the only
changed variable is the training distribution.

### S24.2 Result

| Second path | single-path | mp 4000 | mp 8000 | mp 16000 | mp 32000 |
|---|---|---|---|---|---|
| clean | 0.0700 | 0.0941 | 0.0788 | 0.0737 | 0.0685 |
| 30 dB | 0.1173 | 0.1284 | 0.1198 | 0.1185 | 0.1147 |
| 20 dB | 0.2609 | 0.2507 | 0.2460 | 0.2494 | 0.2467 |
| 10 dB | 1.0769 | 0.7910 | 0.7785 | 0.7273 | 0.6836 |
| 6 dB | 2.0291 | 1.6775 | 1.6373 | 1.5528 | 1.4504 |

### S24.3 What the answer is

**Both, and the split is informative.**

**Part of it is the training prior.** At 10 dB SIR retraining recovers 36% and at 6 dB it recovers 21%.
The network is not architecturally incapable of coping with a strong second path; it was simply never
shown one. That half of S23's finding is a statement about the prior, as S23.3 suspected.

**But most of it is structural, and the retraining does not remove it.** Three facts settle this:

1. At **30 dB SIR** --- a second path carrying 0.1% of the power --- the multipath-trained model is still
   **83% worse than the same model on clean data** (0.1284 against 0.0700 m). Training on exactly this
   distribution does not make a weak second path cheap.
2. The improvement is **not monotone in SIR**: retraining helps at 10 and 6 dB but *hurts* at 30 dB and
   on clean data. A model that could represent two paths would improve everywhere; one that must choose a
   single operating point cannot.
3. The cost is paid on the **clean** case, where accuracy drops 26% (0.0700 to 0.0941 m). There is no
   setting that is good at both.

A classification head over $(r,\theta)$ encodes one geometric pair. When two coherent paths arrive, the
posterior is bimodal or spread between them, and no threshold on the logits recovers a pair that the output
layer cannot express. Retraining moves the operating point along the same trade-off curve; it does not
move the curve.

### S24.4 The honest statement of scope

The method's applicability is therefore bounded by the single-path assumption in a way that cannot be
trained around within this architecture. Two responses are available to a practitioner, and the letter
does not test either:

- a **multipath-aware output** --- several geometric pairs, or a mixture density, rather than one ---
  which is a different output layer and a different training objective;
- a **pre-processing stage** that suppresses the second path before the estimator sees it.

The letter states the assumption in the system model and quantifies its cost here, and makes no claim that
the estimator is robust to multipath.

### S24.5 Scope of this experiment

- One extra specular path, one training SIR range, one SNR (20 dB), one architecture
- The clean-data cost is measured against the single-path-trained model from the main text, so the two
  columns differ in training distribution only
- Three seeds per column, combined by mean for the range readout

### S24.6 The deficit saturates: four times the compute changes little

S24.3 argued the limitation is structural. That argument predicts something testable: if the head cannot
represent two paths, then more training on multipath data should not help much. The prediction was tested
by extending the multipath training to 8000 and 16000 steps with the same three seeds.

| Second path | mp 4000 | mp 8000 | mp 16000 | single-path-trained | gain, 4x budget |
|---|---|---|---|---|---|
| none (clean) | 0.0941 | 0.0788 | 0.0737 | **0.0700** | 1.28x |
| 30 dB SIR | 0.1284 | 0.1198 | 0.1185 | **0.1173** | 1.08x |
| 20 dB SIR | 0.2507 | 0.2460 | 0.2494 | 0.2609 | 1.01x |
| 10 dB SIR | 0.7910 | 0.7785 | 0.7273 | 1.0769 | 1.09x |
| 6 dB SIR | 1.6775 | 1.6373 | 1.5528 | 2.0291 | 1.08x |

All entries are range RMSE in metres at 20 dB SNR, three-seed mean; the two right-hand columns are ratios computed from these values and stored in figs/exp_mp_budget_ratios.json. NMSE itself improves only from
0.013954 to 0.013768 over the same 4x budget --- **1.3%**.

**The deficit saturates immediately.** Four times the training buys between 1.00x and 1.28x depending on
the scenario, and at 20 dB SIR it buys nothing at all. This is the opposite of the behavior seen on
clean data (S13), where the same range of budgets moved NMSE by a factor of five.

Two rows are worth isolating.

**At 30 dB SIR the crossing point is at 32000 steps.** Up to 16000 steps no multipath budget beats the single-path-trained model (0.1185 against 0.1173 m). At 32000 steps it does, but only by 2% (0.1147 m). A second path carrying 0.1% of the power therefore still costs 64% more than a clean channel, after training on that exact distribution with eight times the budget.

**On clean data the penalty disappears only at the largest budget tested.** 16000 steps of multipath training (0.0737 m) still loses to 4000 steps of single-path training (0.0700 m); at 32000 steps it finally wins, by 2% (0.0685 m). Eight times the compute is needed to erase a penalty the single-path model never pays.

At 20 dB SIR multipath training already wins at every budget, by 5.8% at the largest. The trade-off is therefore barely movable by a longer schedule: eight times the compute shifts the crossing point, but the resulting margins are 2%, against deficits of 64% and 108% that remain at 30 dB and 20 dB SIR. The
model is choosing a single operating point on a curve, and the curve itself is fixed by the output layer.
The structural explanation of S24.3 is therefore the one supported by the budget data, not the
training-prior explanation that the 4000-step comparison alone might have suggested.


**What a parametric head buys.** If a linear probe on a reconstruction network already reaches
0.1876 m, the value of the proposed estimator cannot be accuracy alone --- the gap is 7%. The
difference is what the output *is*. A probe is a task-specific readout: it must be retrained for
whichever quantity is wanted, and nothing about it guarantees which geometric parameters are
recoverable. The parametric head returns $(r,\theta)$ directly, and that readout carries properties
the probe does not: its Cram\'er--Rao bound has a closed form (S21), its sensitivity to an
uncalibrated gain is quantified rather than unknown (S14), its error floor is attributable to a
decoding parameter rather than to the data (S22), and its failure under model mismatch is bounded
and measurable (S23, S24). Those are the properties a designer needs when the channel is a means
rather than the deliverable. The 7% accuracy gap should not be read as the contribution.

## S25. Code, data and reproducibility

Every number in this letter is recomputed from archived result files by an automated verification
script. A self-contained reproduction package accompanies this submission so that the check can be
repeated independently. It contains

- the pipeline that produced the results --- the physics and model library, the noiseless-channel
  and holdout generators, the trainer, the baselines, the Cram\'er--Rao computation, and the figure
  scripts (Section S7 lists the exact configuration);
- the trained estimator checkpoints for the three reported seeds;
- the generator of the independent holdout (seed 999999), which is the source of every headline number
  and was never used for training or for checkpoint selection, together with its labels and metadata:
  the channel matrix itself is not shipped, because the closed-form generator reproduces it
  bit-exactly from the fixed seed (`python src/make_holdouts.py`, well under a second, numpy only);
- the archived result files, one per experiment, that the letter's numbers are read from; and
- the verification script itself, which recomputes every reported number against the manuscript
  text and exits non-zero if any of them disagrees.

The verification runs on a CPU in a few seconds and needs only numpy; neither a GPU nor a
dataset download is required, because it reads the archived result files rather than re-training.
The full pipeline (re-training from scratch) needs about $10^6$ noiseless channels and a GPU, as
detailed in S7 and S19.

The package is provided as supplementary material with this submission, and is also available from
the author upon reasonable request.
