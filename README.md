# GEMSDOE26 · learn the region before learning the faults

**Read this entire README, including the complete owner prompt below, at the start of every session.** Maximize P(Win). Own the Outcome. Preserve failures, protect weekly slots, and never turn a format pass into an invented performance claim.

## Latest candidate: XEDGE-v1 OOF diagnostic — research only

**[Download the XEDGE four-fold OOF GeoTIFF](https://buffedlizard55-lab.github.io/GEMSDOE26/docs/downloads/gems26-xedge-oof-v1-20261002-5147f8a58ddd-nan.tif)** · [Site](https://buffedlizard55-lab.github.io/GEMSDOE26/) · [Executive guide](docs/executive-summary.html)

> **BLOCKED_DO_NOT_SUBMIT.** XEDGE-v1 failed the preregistered performance gate. This is an out-of-fold research mosaic, not a full-data final model. No competition upload or weekly slot was used; do not submit this file.

- File: `docs/downloads/gems26-xedge-oof-v1-20261002-5147f8a58ddd-nan.tif`, **476,670 bytes / 60,068 selected cells**.
- SHA256: `527cd3247208a80a17439ac4e72e08a55829bb2fe201b16aa328ae86eba6dfbd`.
- Note: `GEMS26 XEDGE-v1 OOF | 300/600/1200m RTP+gravity edge persistence; four buffered folds; research-only OOF, not full-fit; unscored`.
- Strict file-format checks pass: one float32 band, **3,292×3,730**, EPSG:32611, exact owner-mirrored template transform, finite `[0,1]` in all **5,167,373** footprint pixels, NaN outside, and raw/masked read-back. This is **format validation only**, not scientific release or server acceptance.

| Frozen confirmation arm | Dense pooled local DTI | Mean pooled sparse local DTI |
|---|---:|---:|
| H25-1 historical reference | 0.171825 | 0.096432 |
| Matched raw-feature head | 0.131911 | 0.073836 |
| **XEDGE head (candidate)** | **0.133141** | **0.074969** |
| XEDGE edge-only ablation | 0.078320 | 0.044497 |

XEDGE gained only **+0.001132 sparse DTI** over the fresh raw control (the frozen gate required **+0.005**) and lost **−0.021464** to H25. Its dense score was **−0.038684** below H25, beyond the permitted −0.005. It won 3/4 confirmation quadrants versus raw but 0/4 versus H25; that is not enough to pass. All draws reuse the same known catalogue and are not hidden-fault evidence. See [`evidence/xedge_holdout.json`](evidence/xedge_holdout.json), the [screen protocol](knowledge/hypothesis-slate-20261002.md), and [`knowledge/results.md`](knowledge/results.md).

The owner-reported H25-1 score **0.2477** and supplied leaderboard snapshot **0.3195** remain unrefreshed. No result here beats or authenticates either external score. The earlier SSL and label-free-error TIFFs remain separately identified research artifacts; the historical H25 TIFF is **identical old bytes, not a new submission; do not resubmit**.

## Earlier H26-SSL run — retained negative evidence

The section below records the earlier SSL candidate and remains part of the scientific history; it is not the latest candidate.

Data placement is resolved: all **14 pinned owner-mirrored inputs** restored automatically. All **19 supplied bands** were retained numerically on the full footprint. Six exhaustive masked-pretraining passes visited/masked every footprint pixel, before any label-raster pixel access. **3,061** blank cells cannot furnish reconstruction targets. Masked Huber training loss fell 0.29933→0.15645; that is not fault accuracy.

Frozen masked-error inference and the coherent label-free anomaly finished before first label access **2026-10-02 18:47:49 UTC**. Only final heads were then trained on component-grouped, 1.5 km-buffered spatial folds. No confirmation tuning; encoder parameter hash unchanged. The small convolutional MAE-inspired model ran on **CPU**, not GPU/Prithvi weights.

| Arm | Dense pooled local DTI | Mean pooled sparse confirmation DTI |
|---|---:|---:|
| Historical H25-1 D1.5 | **0.171825** | **0.096261** |
| Historical H19-5 parent | 0.166252 | 0.071466 |
| Matched raw-feature head | **0.131911** | **0.074744** |
| Frozen SSL head | 0.123590 | 0.070184 |
| **Primary SSL + error** | **0.122164** | **0.069039 — REJECT** |
| Label-free error only | 0.079130 | 0.044787 |

These are known-catalogue density-sensitivity simulations, **not independent unknown-fault truth or live leaderboard scores**. Historical H25 catalogue masking leaks held-out geometry; the matched raw head is the fresh buffered OOF control. There is no random-encoder causal control and SSL has more input parameters. The anomaly is label-independent, **not statistically independent** or established fault-specific evidence.

### Why the reported 0.2477 file is stronger

We exactly reproduced the historical label-free BFS/D1.5 thinning: **121,131→60,069** points, no added pixel, maximum parent-to-kept distance **141.42 m**. In the paired local dense calculation it retains **87.16% weighted TP credit** but only **49.44% weighted FP mass**. This explains how reduced redundancy can improve the metric without a new detector. `TP+FP` is **not** generally the emitted count.

The owner reports H19-5 **0.1922→H25-1 0.2477** (+28.88%); no authenticated filename/score receipt is accessible. The initial requested official snapshot showed DARD **0.3195** and an account at .2477, not a TIFF binding; it is **not a live feed**. See [scientific interpretation](knowledge/results.md), [exact forensics](evidence/reference_forensics.json), [historical review](knowledge/sibling-review.md).

## Evidence, standing rules & limitations

- [Original four-hypothesis preregistration](knowledge/preregistration.md), committed **02a8bad before H26-SSL implementation**, remains unchanged. The [XEDGE/DRAIN/STRAIN/CBASE slate](knowledge/hypothesis-slate-20261002.md) was committed as **876c0b2 before XEDGE implementation**; the exact v1 transform, including zero-score tie handling, was frozen in **fce3f74 before feature/label evaluation**. XEDGE is tested and blocked; DRAIN remains deferred pending verified official bytes/coverage, and strain/CBASE remain semantics-limited.
- [Latest XEDGE feature receipt](evidence/xedge_feature.json), [selection draws](evidence/xedge_selection.json), [confirmation draws](evidence/xedge_confirmation.json), and [full gate/audit](evidence/xedge_holdout.json). The earlier [SSL gate](evidence/holdout.json), [labels-first nuisance audit](evidence/accessibility_audit.json), and [error diagnostics](evidence/error_diagnostics.json) remain separate.
- [Primary-source ledger](sources/catalog.json), [central claim ledger](sources/claims.json), [19-band inventory](sources/data_inventory.csv), [all reported scores](sources/reported_scores.csv), [requirement matrix](knowledge/requirement-matrix.md), [three review passes](evidence/reviews.json).
- Full-unlabeled training is **transductive**. Catalogue thinning and reused quadrants do not independently validate unknown faults. Do not retune the failed run on revealed confirmation folds.
- `tc`, earthquake aliases and conductive-base/basement naming remain ambiguous in the mirror. Do not infer full stress/MT tensors from scalar channels or declare radiometrics absent from uncertified tags.
- The mirror example contains **60,988 positives and exactly matches known labels**, contrary to the described absence example. No example pixel values were used in label-free preparation, pretraining, inference, anomaly or XEDGE feature construction; supervised labels were opened only after those stages. Header/NaN footprint checks are separate. Hash integrity does not authenticate organizer provenance.
- Target = **fault locations**, not confirmed geothermal vents/resources. Useful resource discovery requires additional heat, permeability/fluid, stress/lithology and field/well evidence.
- [DrivenData Terms](https://www.drivendata.org/termsofuse/) prohibit automatic site access. The initial requested review was tool-retrieved **before discovering that term**, not human-read. No later competition scraping, automated login or upload is implemented. Eligibility/account-holder attestations cannot be supplied by an agent; never request credentials.
- [Official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) read through its final section: 3 submissions/week, 1 selected final entry across both rounds, eligibility, finalist reproduction assets and AI disclosure. [AI assistance disclosure](AI_DISCLOSURE.md).
- Daily workflow refreshes permitted **USGS metadata and DOE-deposited DataCite DOI metadata**, with visible timestamps/errors and cache-retained last good records, not a live leaderboard or model-training service. No automated branch commits. Failed source requests do not become fabricated successful checks.

## Reproduction

This checkout originally had only an 11-byte title README; the previous ready-to-train/GPU-needed statement in the owner prompt did not describe existing code here. The complete CPU implementation and real artifacts now exist. Large raw data/checkpoints/tensor caches are ignored; pinned code, recipes, receipts and the small final TIFFs are versioned.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
# If the CPU index is TLS-blocked, the default PyPI wheel also runs on CPU,
# but includes much larger CUDA dependencies: pip install -r requirements-train.txt

# Automatic restore → prepare → original SSL → masked inference → anomaly → heads/holdout/TIFF
# This cold replication is for the earlier SSL run, not independent XEDGE validation.
# The XEDGE OOF result/receipt is already frozen; do not retune its revealed folds.
# Isolated fixed-parameter replication preserves the published failed receipts:
.venv/bin/python scripts/reproduce.py
# Uses ignored .cache/reproduction and shared ignored data/raw; no Git branch changes.
# Repeating it verifies the completed replica without refitting. No parameter sweep.

# Independent format-only check of the latest XEDGE OOF research TIFF:
.venv/bin/python scripts/validate_submission.py docs/downloads/gems26-xedge-oof-v1-20261002-5147f8a58ddd-nan.tif
.venv/bin/python -m pytest -q
npm ci --ignore-scripts
npm test
node scripts/browser_export_check.mjs .cache/browser-export.tif
.venv/bin/python scripts/verify_browser_export.py .cache/browser-export.tif
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/verify_site.py
.venv/bin/python scripts/stage_site.py
node scripts/browser_check.mjs
# Serve only the public allowlist, never .git/raw inputs/environment/caches:
.venv/bin/python -m http.server 8080 --bind 0.0.0.0 --directory .cache/pages-site
```

The original per-stage entry points remain available: `bash scripts/download_competition_data.sh`, `prepare_data.py`, `pretrain.py`, `infer_representation.py`, **`build_anomaly.py`**, and `run_holdout.py`. XEDGE construction/evaluation uses `scripts/build_xedge.py` and the frozen one-shot `scripts/run_xedge_holdout.py`; its archived run refuses a second fit on the revealed folds. Use isolated `reproduce.py` for the earlier SSL replication, not deletion/editing of evidence. Requires Python≥3.11, Node≥22, `gh` or public GitHub API read access and several GB of ignored cache storage. Chromium test libraries are extracted from the integrity-pinned npm package; no root/apt install or credentials needed.

## Next session — most important first

1. Reread this full prompt, preserve both negative holdout receipts, do not retune the revealed XEDGE folds, and do not resubmit renamed/OOF fields.
2. Resolve original organizer band semantics and template provenance; prioritize genuinely untouched spatial or independent geological fault truth. The repeated known-catalogue screens are not independent validation.
3. Keep H26-DRAIN deferred until official 1 m tile bytes, full footprint coverage, datum and seams are verified; do not substitute another unverified alias for XEDGE.
4. For any new representation research, add random-frozen-encoder/matched-parameter controls and held-out **unlabeled reconstruction** evaluation; do not equate reconstruction loss with fault specificity.
5. Re-rank a new 3–5 hypothesis slate only after a defensible independent test design and official data semantics/availability are resolved. H26-XEDGE failed; the remaining listed ideas are not validated candidates.
6. Eligibility, deadline confirmation and any eventual **approved** upload are lawful account-holder tasks. No current candidate is approved for a slot.

---

## Complete owner prompt — permanent project starting point

<details>
<summary>Full request, including repeated sections and supplied scores</summary>

Review the repo. 

There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.

Pretrain on the entire unlabeled raster before ever touching the sparse labels. With faults covering roughly 1% of the area, the bottleneck may be scarce representation, not only scarce positive labels: a model trained end-to-end on the labeled task alone never sees most of the raster's variation in unfaulted terrain, and so may fail to recognize a genuinely novel signal as unusual because it never learned what "usual" looks like across the region's full geological diversity. He et al.'s Masked Autoencoder approach (CVPR 2022) and its direct geospatial precedent, Prithvi — the NASA/IBM foundation model (Jakubik et al., 2023) pretrained by masked autoencoding on satellite imagery before fine-tuning on small labeled sets for flood and burn-scar mapping — show that self-supervised pretraining on the full unlabeled stack, not just labeled patches, produces a materially richer representation exactly when labels are this scarce. Apply the same logic: pretrain an encoder by masking random patches of the complete GeoDAWN feature stack (magnetics, gravity, DEM, strain, conductivity) across the whole study area and training it to reconstruct what was masked, then fine-tune only the final layers on the sparse fault labels; a representation that genuinely learned the region's normal variation should show elevated reconstruction error specifically over subtle anomalies, which gives you a second, independent anomaly signal that never touched a fault label and so cannot inherit the catalogue's own incompleteness.

Here are the results from submissions into the competition, separated by ....:

[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)

gems-submission-20260925T001403Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)

gems6_hgb88-topk03_33cec71ff0: 0.0286

....

[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)

pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193

pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830

pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152

....

[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)

gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560

....

[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)

gems-submission-20260926T163915Z-237f0063: 0.0343

....

[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)

gems-submission-20260926T175114Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)

lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461

....

[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)

Hedge-v2_submission: 0.1563

....

[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)

2314b599: 0.0107

....

[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)

gems-structural-area06-v1: 0.0202

....

[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)

r7-nms3-dem10-scarp_0c9199f14e62:0.1294

r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294

....

[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)

gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782

....

[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)

GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020

....

[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)

17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187

....

[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)

H19-C_20260930T212401Z_c11e495e: 0.0297

....

[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)

h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894

h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922

....

[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)

h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461

h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921

H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280

h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839

....

[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)

20261001_r13-lattice-s5_v2_nan-outside:0.0904

....

[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)

h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855

h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976

h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360

....

[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)

h19-4-reference-20260930-691e4dfa: 0.1894

....

[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)

h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890

h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan:

....

[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)

h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002

h23-b-dti-optimal-emission-10pct-20261002-86176698-nan: 

....

[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)

....

[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)

h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477

....

25GEMSDOE SCORE:

....

26GEMSDOE SCORE:

....

27GEMSDOE SCORE:

....

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

24GEMSDOE SCORE:

h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2477?

Answer the question using Phd level experience, knowledge, and judgement. 

The following is the leaderboard for the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

We need to quickly look at the results and results from the GEMSDOE websites above.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.    

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above.  We need to come up with distinct and unique strategies to score higher in this competition leaderboard.  We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents.  We should store all of our information and knowledge that we can gather from official verified sources.  This will serve as a starting point for other projects as well.  We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for.  So it's important to be contrarian but be smart about it.  We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents.  We need to do deep research and critical thinking and come up with new hypothesis to test.

The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.

[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)

gems-submission-20260925T001403Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)

gems6_hgb88-topk03_33cec71ff0: 0.0286

....

[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)

pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193

pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830

pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152

....

[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)

gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560

....

[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)

gems-submission-20260926T163915Z-237f0063: 0.0343

....

[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)

gems-submission-20260926T175114Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)

lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461

....

[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)

Hedge-v2_submission: 0.1563

....

[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)

2314b599: 0.0107

....

[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)

gems-structural-area06-v1: 0.0202

....

[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)

r7-nms3-dem10-scarp_0c9199f14e62:0.1294

r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294

....

[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)

gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782

....

[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)

GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020

....

[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)

17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187

....

[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)

H19-C_20260930T212401Z_c11e495e: 0.0297

....

[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)

h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894

h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922

....

[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)

h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461

h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921

H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280

h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839

....

[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)

20261001_r13-lattice-s5_v2_nan-outside:0.0904

....

[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)

h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855

h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976

h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360

....

[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)

h19-4-reference-20260930-691e4dfa: 0.1894

....

[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)

h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890

h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan:

....

[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)

h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002

h23-b-dti-optimal-emission-10pct-20261002-86176698-nan: 

....

[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)

....

[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)

h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477

....

25GEMSDOE SCORE:

....

26GEMSDOE SCORE:

....

27GEMSDOE SCORE:

....

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

24GEMSDOE SCORE:

h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2477?

Answer the question using Phd level experience, knowledge, and judgement. 

The following is the leaderboard for the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

0.3195 is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.

Review the repo.

The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.

Our Core Values

Maximize P(Win)

“Maximize the Probability of Winning”: our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). “Maximize P(Win)” frees us from constraints and clarifies that we must put Arena first.

Own the Outcome

We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We need to focus on being able to generate a submission into the competition.

The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the submission form:

"Predicted values must be in range [0, 1]"

Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Here is the submission page when i click submit file

New submission

File to submitNo file chosen

You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first.

Note (optional)

A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition.  The following is the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)

We need to create a project that can compete and place top of the leaderboard.  We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.

This is the guidelines we need to follow.[https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/)

Get familiar with the problem through the overview and problem description,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). You might also want to reference additional resources available on the about page,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/).

Download the data from the data,[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), tab.

Create and train your own model. This reference solution,[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) implements a simple approach.

Use your model to generate predictions that match the submission format.

Tell me what are you limitations and what you need access to during this project.  We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.

this pdf outlines how submissions must be entered into the competition.

[https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information.  this must be done autonomously and must be constantly reviewed and improved upon.  Provide suggestions and improvements and implement them.

❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from [https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (verified redirect to login)

See below for links from the above site.  See attached files for links from the above site.

[https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)

Download competition data from [https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (requires login) to data/

See links below for competition data:

[https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0)

[https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0)

[https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0)

[https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0)

[https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0)

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Site creation

Create a github page for this repo that has clean ui, user friendly, simple and easy to use.  It should be organized and clean.

It should include all relevant information in an easy to read format with official verified links as sources for review.  Work line by line verify everything no hallucinations.

**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU).

you need to complete the above task by yourself.  Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Run this task through multiple passes.

Pass 1: Implement the task completely and verify the result.

Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.

Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.

Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request.  Work line by line verify everything no hallucinations.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.  It should be worked on in this next session or the next session.  Work line by line verify everything no hallucinations.

</details>
