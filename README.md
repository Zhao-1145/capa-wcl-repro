# Reproduction package

**Manuscript.** "Range Errors as Uniform Phase Rotations in Continuous Aperture
Arrays: Consequences for Near-Field Channel Estimation."

This package contains the manuscript sources, the archived result files, the
verification scripts, and the pipeline that produced the results. Every
quantitative claim in the letter is recomputed from the archived JSON files by
`verify_paper.py`, so the numeric claims can be checked **without any training
and without any dataset download**.

## Quick check (CPU only, a few seconds)

Run from this directory:

```
python verify_paper.py        # recomputes every reported number -> expect 301/301 PASS
python check_figs.py          # figure presence / geometry / legibility   (needs numpy, matplotlib)
python audit_format.py        # IEEE WCL format checks
python latex_static_check.py  # LaTeX static checks
python zcode_ref_integrity.py # bibliography integrity (25 entries)
python scan_nonascii.py       # manuscript source is pure ASCII
```

`verify_paper.py` exits 0 when every check passes. It reads the manuscript
source, the supplementary source, and the archived JSON files under `figs/`;
it uses the **Python standard library only** -- no numpy, no network and no GPU.
Of the remaining checks, only `check_figs.py` needs third-party packages
(`numpy` and `matplotlib`, Agg backend); the rest are standard library too.
See `requirements.txt`.

## Layout

```
paper_CAPA_deep_estimation.tex   manuscript source (IEEEtran, 5 pages)
Supplemental_Material.md         supplementary material source (S1-S25)
verify_paper.py                  per-number verification against figs/*.json
check_figs.py                    figure checks
audit_format.py                  format checks
latex_static_check.py            LaTeX static checks
zcode_ref_integrity.py           reference integrity
scan_nonascii.py                 ASCII check
figs/*.json                      archived result files (authoritative record)
figs/*.pdf                       figures embedded in the letter
data/                            holdout labels + metadata (see below)
models/                          trained checkpoints, three reported seeds
src/                             pipeline that produced the results
```

### The independent holdout is regenerated, not shipped

Every headline number is evaluated on a holdout generated with seed 999999 that
was never used for training or for checkpoint selection. Its **channel matrix**
(6000 x 512 float32, 12.3 MB) is *not* shipped, to keep the archive small. It is
reproduced **bit-exactly** by the generator in this package:

```
python src/make_holdouts.py      # writes data/test_M256_holdout2_{x,y}.npy
```

This needs only numpy and takes well under a second; `data/` already contains the
matching labels (`test_M256_holdout2_y.npy`) and metadata, so you can confirm your
regenerated copy agrees:

```
python -c "import numpy as np; x=np.load('data/test_M256_holdout2_x.npy'); \
print(x.shape, x.dtype, x[0,:3])"     # expect (6000, 512) float32, [-0.09715 -0.10147 -0.10513]
```


## Full pipeline (GPU recommended)

The experiment pipeline is in `src/`. The dataset generator and the trainer are
self-contained; the main steps are:

```
python src/make_data.py  --M 256 --N 2000000 --out DATA/tr_M256 --seed 0
python src/make_holdouts.py                       # independent holdout, seed 999999
python src/train.py      --head cls --mode raw --hidden 1024,512,256 \
                         --batch 2048 --n-train 1000000 --max-steps 4000 \
                         --data DATA/tr_M256 --out runs/main_cls_raw
python src/reeval_holdout_full2.py                # main table (3 seeds, holdout)
python src/rerun_baselines_n2000.py               # LS / LMMSE / refined dictionary
python src/compute_crb.py                         # Cramer-Rao bounds, calibers A/B/C
```

See `src/README.md` for the exact protocol, and Sections S7, S16 and S19 of the
supplementary material for the full description. The training set is large
(10^6 noiseless channels); all headline numbers use the independent holdout
generated with seed 999999 and are never used for training or model selection.

## Environment

Python 3.11, numpy, torch. See `requirements.txt`. The verification scripts run
on CPU; training the estimator benefits from a CUDA GPU.

## License / citation

MIT (see `LICENSE`); citation metadata in `CITATION.cff`.
