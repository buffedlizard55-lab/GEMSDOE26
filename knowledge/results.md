# GEMS DOE 26 results and scientific decision — 2026-10-03

## Outcome first

**Do not spend a weekly slot on any tested candidate.** The latest screen, H27-SRCOH-v1, failed all 15 fixed promotion rules and emitted no SRCOH TIFF. The earlier H27-DILCOND OOF TIFF is still the newest available H27 research file, but its own gate failed; it is not promoted by SRCOH. H26-XEDGE-v1 and H26-SSL also remain blocked. No competition upload, leaderboard access, or weekly slot occurred in these experiments. None provides evidence of exceeding the owner-reported H25-1 **0.2477** or the dated leaderboard snapshot **0.3195**.

### Latest experiment: H27-SRCOH-v1 — failed; no TIFF

The SRCOH screen completed at **2026-10-02 23:43:47 UTC**. Its label-free feature receipt records completion at 23:41:58 UTC; the first label-pixel access was 23:42:31 UTC. All 15 preregistered gate rules are false. The feature uses a multiscale edge-coherence transform of three strain-named owner-mirror channels; their aliases and units remain unauthenticated. The experiment is a reused-catalogue spatial sensitivity screen, not independent hidden-fault truth or an official score.

| Confirmation arm | Dense pooled local DTI | Mean pooled sparse DTI (offsets 150–179) |
|---|---:|---:|
| Historical H25-1, as emitted | 0.171825 | 0.096849 |
| Fixed H26-XEDGE OOF | 0.133141 | 0.075839 |
| Matched raw-feature head | 0.136243 | 0.077166 |
| **H27-SRCOH head** | **0.126771** | **0.072414** |

SRCOH trails raw by **−0.009472 dense / −0.004752 sparse**, XEDGE by **−0.006370 / −0.003424**, and H25 by **−0.045054 / −0.024435**. The raw control's 52nd feature is fixed at zero; both heads had 5,505 parameters and identical fold seeds, training examples and schedules. The preregistered gate also considered a separate 30-draw seed-offset group; neither group reached the required +0.005 margin, and fold-win rules failed. Do not retune the revealed folds.

No H27-SRCOH GeoTIFF was generated. The H27-SRCOH result note, all 60 selection/confirmation draws, and stage receipts are in `knowledge/h27-srcoh-result-20261002.md` and `evidence/h27_srcoh_*.json`. **Provenance boundary:** this PR checkout was initialized at `cee5eb0` and later integrated current `main`, but does not contain the experiment-time SRCOH slate/code commit objects in the receipts. The pinned protocol, input and code hashes match; commit ancestry is not reauthenticated here. A prior checkout review recorded that ancestry check historically, not as a check this clone can reproduce. No replay or workaround was attempted.

### Earlier experiment: H26-XEDGE-v1

The ranked slate was committed as `876c0b2` at **21:39:31 UTC**, before XEDGE implementation; the exact v1 transform, including zero-score tie handling, was frozen in `fce3f74` at **21:48:21 UTC**, before feature construction/evaluation. XEDGE combines signed cross-scale (300/600/1,200 m) magnetic RTP and isostatic-gravity edge-normal agreement, with orientation persistence. It used only the prepared label-free feature stack, masks and footprint for feature construction. Receipt timestamps put feature construction at **21:50:06–21:50:19 UTC** and first label-pixel access at **21:52:13 UTC**. This is an auditable software record, not hardware attestation.

| Confirmation arm | Dense pooled DTI | Mean pooled sparse DTI | Contrast |
|---|---:|---:|---|
| Historical H25-1, as emitted | 0.171825 | 0.096432 | Owner-reported hidden score remains 0.2477; catalogue-leaky local reference |
| Matched raw-feature head | 0.131911 | 0.073836 | Fresh four-quadrant OOF control |
| **XEDGE + raw-feature head** | **0.133141** | **0.074969** | +0.001230 dense / +0.001132 sparse vs raw; −0.038684 dense / −0.021464 sparse vs H25 |
| XEDGE edge-only ablation | 0.078320 | 0.044497 | Fixed-budget edge score without a trained head |

The gate required at least **+0.005 pooled sparse DTI over both H25 and raw in selection and confirmation**, at least 3/4 confirmation-quadrant wins against both, dense non-inferiority within −0.005, the labels-first nuisance condition, and strict TIFF validation. XEDGE gained only **+0.001132** sparse DTI over raw in confirmation and lost to H25 in **all four** quadrants. Dense DTI was **0.038684 below H25**. It therefore fails the principal performance conditions; passing the nuisance and format checks does not rescue it. Against raw it won 3/4 confirmation quadrants, but the margin rule still fails.

The 30 selection and 30 confirmation draws reuse the same known catalogue and spatial quadrants; changing draw seeds does not create independent truth. The historical H25 file is compared as emitted and carries all-catalogue-mask leakage. XEDGE is **not validated on novel faults**, not a probability/fault map, and not evidence for geothermal vents.

The research-only OOF mosaic is `docs/downloads/gems26-xedge-oof-v1-20261002-5147f8a58ddd-nan.tif` (476,670 bytes; SHA256 `527cd3247208a80a17439ac4e72e08a55829bb2fe201b16aa328ae86eba6dfbd`). It is a four-model out-of-fold field, not a full-data fit, and is explicitly **BLOCKED_DO_NOT_SUBMIT**. Strict exact-grid checks pass: one float32 band, 3,292×3,730, EPSG:32611, exact owner-mirrored template transform, finite [0,1] across the 5,167,373 footprint pixels and NaN outside. This establishes file structure/range only, not organizer provenance or server acceptance. The unique note is recorded in `evidence/xedge_holdout.json` and beside the TIFF.

The matched raw-head dense value reproduces the archived value **exactly** (delta 0.0), a useful control that the XEDGE comparison did not silently change the raw baseline. Full feature/build/selection/confirmation/nuisance/format receipts: `evidence/xedge_feature.json`, `evidence/xedge_selection.json`, `evidence/xedge_confirmation.json`, and `evidence/xedge_holdout.json`.

### Earlier H26-SSL-v1 artifact

The separate H26-SSL research artifact remains:
`docs/downloads/gems26-ssl-v1-20261002-4fdde73c40a7-nan.tif`
(SHA256 `34f590461ae021830d98521567a2b1fcdfd60eeb9032e70de9bb000618ec4d35`).
It contains 60,068 binary confidence pixels and passes all format/range checks, but its own frozen holdout failed. **Format pass ≠ scientific release.** The label-free-error ablation is likewise research-only. The historical H25 file is copied byte-for-byte for reference and is **not a new submission**.

## What actually ran

- Data restored automatically from public, immutable owner-mirrored GitHub assets; combined full feature raster SHA256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`. This establishes mirror integrity, not organizer authentication.
- Preregistration committed as `02a8bad` **before** implementation. No outer-fold mixture, threshold, budget or epoch tuning followed the result.
- All 19 bands retained at the full 100 m grid. Per-band median and robust scale fitted only to unlabeled footprint values. Values and missingness stored as memory maps.
- Six exhaustive passes, **1,384 tiles per pass**, each visiting **5,167,373** footprint pixels. Random 4×4 spatial patches, 75% masking; last pass forces any previously unmasked patch. Every footprint pixel was visited and masked. **3,061** in-footprint cells have no observed channel and therefore cannot supply a reconstruction target; they were not invented or imputed into targets.
- Mean masked training Huber loss **0.29933 → 0.15645** (47.7% reduction). This is a training reconstruction measurement, not held-out fault accuracy or an SSL validation-set estimate.
- 183 overlapping inference tiles, 16-pixel halos, globally aligned complementary masks. Each inference pixel hidden in **three** masks, visible in one. Errors are from **masked predictions**, not clean self-copy reconstruction.
- Encoder/decoder frozen; parameter hash unchanged before/after supervised training: `evidence/holdout.json`. Cached embeddings cannot receive fault-label gradients.
- First label-raster access **18:47:49 UTC**, after pretraining, representation inference and the label-free anomaly branch completed. Script receipts and control-flow enforce that order; this is an auditable software record, not a hardware attestation of every system read.
- Four outer quadrants, 1.5 km Euclidean exclusion collar; minimum sampled train/test gap **16 pixels (1.6 km)**; whole-component exclusion; no train/test sample overlap. Known positives = **60,988 / 5,167,373 = 1.1803%**.
- Same final-head hidden widths, samples, seeds, training schedule and emission operator in the raw and SSL arms. SSL has more input weights because it has more features; **no random-encoder control was preregistered**, so even a win would not isolate the causal contribution of pretraining from extra spatial features/capacity.
- Primary fixed policy: 90% percentile-rank SSL head, 10% percentile-rank coherent label-free error; spacing ≥1.5 pixels, fixed footprint-fraction budget. Independent per-quadrant rounding yields **60,068**, one fewer than the historical 60,069; no post-hoc padding/change.
- 30 selection and 30 disjoint-seed confirmation component-thinning draws (20% components). All are sensitivity simulations of the **same known catalogue**, not independent hidden-fault truth.

## Comparable local measurements

Primary statistic = pooled DTI within each draw, then mean across draws; dense = one pooled DTI. Do not compare these pooled values to older sites' arithmetic fold means as if they were the same quantity.

| Arm | Pooled dense DTI | Mean pooled sparse DTI (confirmation) | Interpretation |
|---|---:|---:|---|
| Historical H25-1 D1.5 | **0.171825** | **0.096261** | Exact as-emitted historical reference; all-catalogue exclusion leak acknowledged |
| Historical H19-5 parent | 0.166252 | 0.071466 | Same detector before dot thinning |
| Matched raw-feature final head | **0.131911** | **0.074744** | Fresh buffered OOF control |
| Frozen SSL head | 0.123590 | 0.070184 | More features, but no improvement |
| **Primary H26-SSL-v1 fusion** | **0.122164** | **0.069039** | **Reject / do not submit** |
| Label-free error alone | 0.079130 | 0.044787 | No fault-specific performance established |

Primary sparse difference = **−0.027223** vs H25, **−0.005706** vs raw; dense difference = **−0.049662** vs H25, **−0.009748** vs raw. It loses **all four** confirmation quadrants to each comparator. Required +0.005 sparse margins and dense non-inferiority both fail. It also fails selection, so no fishing for a favourable confirmation seed.

Exact selection/confirmation components and seeds: `evidence/holdout_selection.json`, `evidence/holdout_confirmation.json`; release logic: `src/gems26/holdout.py`; final gate: `evidence/holdout.json`.

## What we learned about reconstruction errors

After freezing the independent branch, a balanced known-fault/background diagnostic has anomaly AUC **0.53436**. This is weak known-catalogue separation; it does **not** demonstrate elevated errors specifically at unknown faults. Patch-phase mean-MSE max/min ratio = **1.084**; mean MSE ranges **0.238–0.591** among the four **derived** acquisition blocks. Regional geology, survey characteristics, smoothing and missingness are alternative explanations; block means do not establish an instrument cause.

The anomaly branch is **label-independent**, not statistically independent of the learned head: the head uses related features and errors. A reconstruction model can reconstruct real faults well, and uncommon lithology or noise can reconstruct badly. MAE/Prithvi transfer evidence does not eliminate this ambiguity.

## Nuisance diagnostic, labels first

Road, closed-claim and derived-block classifier mean fold AUCs: labels **0.50737**; H25 **0.53169**; H26 primary **0.48591**; error-only **0.50844**. The primary passes the preregistered *relative* association gate (absolute distance from chance not worse than reference by >0.01). This does not rescue failed DTI. Different samples/estimators explain why these AUCs need not equal GEMSDOE24's reported AUCs. **Association is not causation**, and chance classification is not a geological quality certificate.

## Why the reported H25 score is the strongest

1. **The file is a label-free subset transformation of the already stronger H19-5 detector.** It is not a new learned geological representation. The upstream deterministic BFS/geodesic Poisson thinning uses 1.5-pixel minimum Euclidean separation. Our forensic script reproduced it pixel-for-pixel: **121,131 → 60,069 (49.590% retained)**, no added pixel, each parent pixel within **141.42 m** of a retained one. This distance bound applies to parent predictions, not unknown truth. See `evidence/reference_forensics.json`.
2. **It removes redundancy within the 300 m kernel.** For ground-truth pixels, credit is the maximum nearby probability times `max(1−d/3,0)`; close neighbouring predictions do not add TP credit to the same truth pixel. FP mass is charged separately for every emitted prediction according to its distance to truth.
3. **The exact metric is** `DTI = T / (0.2(T+F) + 0.8G)`, where `T=TPw`, `F=FPw`, `G=|truth|`. Crucially, `T+F` is **not generally emitted pixel count**: T sums over truth, F over predictions. The older slogan “each pixel costs 0.2” is a sparse-FP-dominant approximation, not an exact identity.
4. For thinning with `T'=rT`, `F'=cF`, improvement requires `0.2(r−c)F > 0.8(1−r)G`. Thus reducing FP faster than coverage credit is lost works particularly when hidden truth is sparse. This follows from the official metric; hidden `T,F,G` are not available here.
5. The owner reports **0.1922 → 0.2477 (+28.88%)** for H19-5→H25-1. Our paired local sparse diagnostic improves **0.071466 → 0.096261 (+34.69%)**, with a small dense improvement. In the exact paired **local dense** calculation, weighted TP credit decreases **12,192.20 → 10,626.80 (87.16% retained)**, while weighted FP mass decreases **110,534.70 → 54,653.72 (49.44% retained)**. Sparse-draw means likewise retain about 87% TP credit for about 49.6% FP mass. This is direct local evidence for the emission-efficiency mechanism, but not a platform-receipt-bound causal decomposition of hidden performance.
6. Other cited sites emitted much more mass, repeatedly followed known traces, or recommended failed/weak proxies. These are **associations across confounded experiments**, not proof that a named geological mechanism caused their score differences. Shared prediction fingerprints/renamings must not be counted as independent successes.

The official leaderboard snapshot showed **DARD 0.3195**, and an account **wbg1 0.2477**. It did not bind that row to an H25 filename. The brief provides the file/score mapping; no authenticated competition receipt was accessed. GEMSDOE24 still describes its file as unscored and reports a stale owner best of 0.1922. Both discrepancies are flagged rather than silently “verified.”

## Can we exceed 0.2477 or 0.3195?

**It is possible in principle, but this experiment provides no evidence of it.** 0.3195 is 0.0718 above 0.2477 (28.99% relative). More thinning of the same detections cannot create missed geological information and may hurt Phase 2 coverage. Uniformly reducing every confidence is not equivalent to thinning: with positive G, `DTI(c)=cT/(0.2c(T+F)+0.8G)` increases with c, so blanket down-scaling cannot help this metric.

At current DTI `s`, small additions need `δT/δF > 0.2s/(1−0.2s)` for positive δF. At 0.2477 this is approximately **0.05212 weighted TP per weighted FP**. This is a decision condition, not an estimated hit rate or permission to use hidden labels. The next scientific objective is new high-credit structure at fixed FP budget, not another file name or a bigger emission halo.

A single blind lattice score does **not identify hidden truth density** without assumptions about phase, orientation, public-subset emission density, clustering, catalogue masking and FP approximation. Treat the older ~0.24% estimate as a conditional model/sensitivity, not a measured geological fact. Proxy/live rank correlation is weak in the sibling evidence; an offline win is necessary under the owner rule, not sufficient for leaderboard superiority.

## Next session — priority, no retrospective rescue

0. **H28 is a research proposal only, not authorized in this PR.** In a future approved session, one could specify a principled binarization of a fixed detector score field and compare `historical_dot_thin` (`scripts/analyze_reference.py`) with `poisson_emit`. Preregister the exact transform, controls and promotion gate before any run. H25's exact subset relation motivates measuring this operator difference, but XEDGE/DILCOND's sub-gate gains and SRCOH's loss to raw do not establish that an operator change will improve results; no H28 implementation or validation exists.
1. **Do not retune the XEDGE, DILCOND or SRCOH runs on their revealed outer folds.** Preserve all failed gates and exact artifacts. Freeze any new experiment separately; obtain an untouched spatial/external confirmation source or disclose that the catalogue has already been reused extensively.
2. Resolve feature aliases from original official metadata: the mirror describes `tc` as “tilt angle or total curvature,” while official sources use TC for different quantities (radiometric counts, thermal conductivity). GDR 1390 describes *thermal* conductivity, but does not prove which `tc` band this bridge contains. `depth_to_base_surf` is described as basement depth in the mirror, while the organizer lists depth to a **conductive base**. Do not interpret scalar geodetic strain as a full stress tensor. The official reference-solution notebook (`github.com/drivendataorg/gems-prize-reference-solution`) corroborates the `band_name`/`data_category`/`data_type`/`description` tag *schema* itself — see `sources/band_tags_official.csv` — but does not independently confirm the physical meaning of ambiguous short codes like `tc`.
3. **H26-XEDGE-v1, H27-DILCOND-v1 and H27-SRCOH-v1 are all preregistered negative results** and must not be retuned on these revealed folds. The slate remains historical prospecting, not a queue of approved submissions: H27-SEISMIC-LINEAMENT and H27-ALTERATION are deferred on confirmed sandbox network-egress grounds (`evidence/egress_check.json`); DRAIN is deferred until official 1-m bytes/coverage are verified; STRAIN/CBASE require original semantics. Before another feature-hunting run, prefer H28 (item 0) or design genuinely untouched spatial/external confirmation, then rank a fresh slate with explicit controls.
4. For representation research, add a random-frozen-encoder control, matched parameter budget, and spatially held-out *unlabelled reconstruction* assessment. Six full passes establish coverage, not convergence or foundation-model quality. The 100 m interpolated channels and small receptive field may not encode the native 1 m scarp signal that drove the stronger historical detector.
5. For **H26-DRAIN**, the official TNM API lists concrete public-domain 1 m GeoTIFFs, but a direct binary HEAD and direct API calls fail TLS in this sandbox. **Metadata availability is not downloaded-data availability.** Do not call the candidate executable here until official tile bytes, datum, coverage, seams and computational storage are checked on an unrestricted runner. Current quantized lidar summaries are insufficient for drainage profiles.
6. Independent unknown-fault labels, native lidar processing, geological/contact controls and human/expert validation remain the real bottlenecks. More GPU compute is optional for a larger MAE, not a blocker to the completed CPU prototype.
7. The target is faults. Prioritizing **geothermal vents/resources** additionally requires collocated heat, permeability and fluid evidence (Siler & Faulds, https://www.osti.gov/servlets/purl/1110515). Faults can also be barriers (Hermant et al., https://pangea.stanford.edu/ERE/db/GeoConf/papers/SGW/2025/Hermant.pdf). No list of confirmed new vents can be honestly produced from these predictions alone.

## Compliance and automation limits

No new automatic DrivenData reads after its Terms were discovered; no scraper or auto-upload. Initial requested review was tool-retrieved, **not human-read**. Permitted USGS metadata APIs can be refreshed by a daily Pages workflow; failed requests retain the last good record with visible timestamps/errors. A leaderboard snapshot is not a current feed. Organizer-authenticated data provenance, eligibility attestations and an eventual account-holder upload cannot be completed without lawful account-holder participation. Never request passwords/tokens.

## H27-DILCOND-v1 result (2026-10-03) — frozen BEFORE implementation, tested, BLOCKED

Preregistered in `knowledge/hypothesis-slate-20261003.md` (commit `a282a242a34612aeb06621f16de04b7686b33704`) as the #1-ranked candidate of a 5-item slate. Spec frozen before code: bands `geod_dilaterate` (zero-based 7) and `cond_surf` (zero-based 16), σ∈{3,6,12} px local-minus-4σ-regional background, **positive-residual-only** (extensional dilatation coincident with elevated conductivity — a sign-aware physical coincidence test, not a generic edge/gradient operator and not the magnetic/gravity bands XEDGE already used), geometric-mean joint rank across scales, 48 px erosion halo. Label-free feature build (`scripts/build_dilcond.py`) completed and was hashed (`evidence/dilcond_feature.json`) before any label-pixel access (`started_label_pixel_access_utc: 2026-10-02T22:54:45Z`, after feature completion), exactly like XEDGE.

**A genuine implementation bug was found and fixed during review before this result was finalized** (see "Pixel-level scoring defect found and fixed" below). The numbers in this table are from the corrected code; an earlier, buggy run produced smaller margins and is superseded, not blended in.

| Arm | Pooled dense DTI | Mean pooled sparse DTI (confirmation) | Interpretation |
|---|---:|---:|---|
| Historical H25-1 D1.5 | **0.171825** | **0.096432** | As-emitted historical reference |
| Matched raw-feature final head | 0.131911 | 0.073836 | Fresh buffered OOF control, same architecture as DILCOND head |
| **H27-DILCOND-v1 head (raw + coincidence feature)** | **0.137279** | **0.077035** | **BLOCKED_DO_NOT_SUBMIT** |
| Coincidence-score-only ablation | 0.050201 | 0.033463 | The new feature alone is far weaker than the full raw-feature head |

DILCOND **beat the matched raw head** on both metrics (+0.005367 pooled dense, +0.003198 pooled sparse at confirmation; won **4/4** confirmation quadrants — up from 3/4 before the bug fix), but the pooled sparse margin is still **below the preregistered +0.005 gate** on both selection (+0.003407) and confirmation (+0.003198), so `selection_vs_raw_head_sparse_margin_0.005` and `confirmation_vs_raw_head_sparse_margin_0.005` both evaluate **false**. It also still loses **all four** quadrants to H25 (pooled sparse −0.019398, pooled dense −0.034547). Nuisance audit passes (`relative_association_not_worse_by_over_0.01: true`, labels audited first). Full receipts: `evidence/dilcond_feature.json`, `evidence/dilcond_selection.json`, `evidence/dilcond_confirmation.json`, `evidence/dilcond_holdout.json`. Gate decision: **`BLOCKED_DO_NOT_SUBMIT`** — no weekly submission slot spent, matching the user's explicit standing instruction.

### Pixel-level scoring defect found and fixed (same session, before interpreting results)

During the review pass, a unit test (`tests/test_dilcond.py::test_dilcond_zero_signal_stays_zero_not_an_average_rank_tie`) caught that the original `src/gems26/dilcond.py` combined per-scale joint scores via `exp(mean(log(joint + 1e-6)))`. The additive `1e-6` epsilon meant pixels that were non-anomalous (zero joint) at **every** scale did not get an exact-zero combined score; instead they all tied at the same tiny-but-positive floor value, which `percentile_rank`'s average-rank tie-breaking then spread across the **middle** of the score distribution rather than the bottom — directly contradicting the frozen spec ("positive-residual-only... zeroed where either residual ≤0"). This is a real correctness bug, not a design choice, and it likely suppressed the feature's true discriminative power since a large, uninformative "null" block of pixels was competing for mid-range rank against genuinely weak-but-real anomalies.

**Fix:** replaced the log-sum-exp-with-epsilon combination with a direct product of per-scale joint scores followed by an exact `n`-th root (`src/gems26/dilcond.py`, function `build_dilcond_score`). Any scale with an exact-zero joint now forces the combined score to exactly zero, with no epsilon artifact. This is a bug fix to match the already-frozen spec, not a retune of a threshold or a response to confirmation-fold results — the original (buggy) run had already failed the same gate, so there was no incentive to "rescue" it, and the fix was applied and tests added before `build_dilcond.py`/`run_dilcond_holdout.py` were re-run. Both the feature artifact and the full holdout were regenerated from scratch after the fix (new `score_sha256`, new OOF artifact SHA); the pre-fix numbers (dense 0.133808 / sparse 0.075398, 3/4 confirmation wins vs raw) are superseded by the corrected numbers above (dense 0.137279 / sparse 0.077035, 4/4 confirmation wins vs raw) and are not cited elsewhere as the operative result.

### The pattern across the pre-SRCOH feature tests is evidence, not proof

XEDGE (cross-scale magnetic/gravity edge persistence) and DILCOND (dilatation×conductivity coincidence) were two mechanistically unrelated, independently preregistered physical hypotheses. **Both produced a small (~+0.0011–0.0054 pooled) improvement over the matched raw-feature head — still below the +0.005 sparse gate — and both remain roughly 0.02–0.04 pooled DTI below H25.** The later SRCOH screen underperformed its matched raw control. Taken together, these results do not prove an emission-operator bottleneck; they provide no evidence that a further untested feature will win, and leave a separately preregistered operator test as a research option, not an approved next model.

**Unvalidated H28 proposal (not authorized, implemented or validated by this PR):** `scripts/analyze_reference.py` already contains a pixel-exact, label-free reproduction of the *historical* H19→H25 operator (`historical_dot_thin`: one-representative-per-connected-component via row-first BFS, not a fixed-radius greedy-by-score Poisson-disk selection). Our own pipeline's emission step (`src/gems26/emission.py: ridge_nms` + `poisson_emit`) is a **different, newly authored** operator: greedy highest-score-first selection under a fixed 1.5 px exclusion radius and a fixed total budget. These two thinning algorithms are not interchangeable — `historical_dot_thin` collapses an entire spatially-contiguous candidate blob to one point regardless of score gradient within it, while `poisson_emit` can retain several points along a single ridge as long as they clear 1.5 px separation. The H19-5 parent itself (dense DTI 0.166, more than our raw head's 0.132) was also a stronger *detector*, not just differently thinned, which confirms both axes (detector quality and emission-operator choice) contribute to the gap and have not yet been separately tested.

A possible future experiment would hold a DILCOND (or XEDGE) raw-feature-head score field fixed and compare `historical_dot_thin`-style component thinning with `poisson_emit`. Because `historical_dot_thin` consumes a binary mask, this first requires a preregistered ridge/skeleton binarization rule. It would measure an emission-operator contrast, not prove that emission is the cause of the H25 gap or guarantee a score improvement. XEDGE/DILCOND's small sub-gate gains and SRCOH's underperformance do not establish an operator bottleneck. This idea is not authorized, implemented or validated here; any future test needs a fresh gate and an independent or untouched confirmation design. It is recorded as one research option, not an approved next candidate.

### Sandbox network egress reconfirmed (2026-10-02T22:58 UTC)

`evidence/egress_check.json` is a locally-computed connectivity receipt (not a claim about any external service's correctness): direct `curl` attempts to `earthquake.usgs.gov`, `osti.gov`, `raw.githubusercontent.com` and `sentinel-cogs.s3.us-west-2.amazonaws.com` all fail with `SSL_ERROR_SYSCALL` before any HTTP response; `pypi.org` and `api.github.com` both return `200`. This reconfirms (does not newly discover) that H27-SEISMIC-LINEAMENT (USGS ANSS FDSN event catalog) and H27-ALTERATION (Sentinel-2 SWIR via AWS Open Data / Earth Search STAC) are **named, specific, genuinely free/official sources that are viable in principle but not obtainable from this sandbox**, and so remain correctly deferred rather than implemented against synthetic/absent data.

## H27-DILCOND-v1 publication verification

PR [#6](https://github.com/buffedlizard55-lab/GEMSDOE26/pull/6) from the assigned branch `arena/01a0fec1-gemsdoe26` merged as **e22fffa** at 2026-10-02 23:19:06 UTC after its PR checks passed (run [37076832240](https://github.com/buffedlizard55-lab/GEMSDOE26/actions/runs/37076832240)). The post-merge "Verify and publish Pages" workflow on `main` (run [37076991258](https://github.com/buffedlizard55-lab/GEMSDOE26/actions/runs/37076991258)) passed both jobs (`Scientific and website checks`, `Publish verified research site`), and the separate `pages build and deployment` run (37076990017) succeeded. A cache-busted fetch of the live public `docs/data/current.json` confirms `latest_candidate.run = "H27-DILCOND-v1" at that earlier deployed state`, the correct filename/SHA256, `scientific_decision = "BLOCKED_DO_NOT_SUBMIT"`, and a `previous_candidate` block for XEDGE — i.e. the actual deployed Pages site matches this repository's state, not merely the local build. As with the XEDGE release, the deployed TIFF's exact remote bytes were not independently re-downloaded and hashed from this sandbox (no general HTTPS egress to the Pages host beyond the one `fetch_page` tool call used above); local and CI artifact bytes remain the verified source of truth. Full release record intentionally not duplicated into a separate JSON this time; this paragraph is the record.

## Publication verification

The prior publication release (PRs #1–#3, earlier branch `arena/01a0fdd8-gemsdoe26`) remains in `evidence/publication.json`. XEDGE PR [#4](https://github.com/buffedlizard55-lab/GEMSDOE26/pull/4) from the assigned branch `arena/01a0fe8a-gemsdoe26` merged as **33ed13e** at 2026-10-02 22:13:47 UTC. Its PR checks passed (run [37071227432](https://github.com/buffedlizard55-lab/GEMSDOE26/actions/runs/37071227432)); post-merge scientific/site checks and verified-site publication passed (run [37071346730](https://github.com/buffedlizard55-lab/GEMSDOE26/actions/runs/37071346730)); the GitHub Pages artifact deployment also passed (run [37071345832](https://github.com/buffedlizard55-lab/GEMSDOE26/actions/runs/37071345832)). Cache-busted reads of the **actual public Pages** root, executive guide and current JSON confirmed the XEDGE filename, blocked warning, checksum and current result. The deployed TIFF's exact remote bytes could not be checked from this sandbox: `curl` failed TLS before download (`SSL_ERROR_SYSCALL`). Local and CI checks verified the 476,670-byte file and SHA256 `527cd3247208a80a17439ac4e72e08a55829bb2fe201b16aa328ae86eba6dfbd`; do not misstate this as a remote byte check or organizer acceptance. Full release record: `evidence/xedge_publication.json`. The earlier 21:02 metadata refresh remains a separate historical result; metadata availability still does not prove native 1 m binary coverage, independent fault validation or a new leaderboard score.
