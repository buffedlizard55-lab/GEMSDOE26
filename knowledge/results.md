# H26 results and scientific decision — 2026-10-02

## Outcome first

**Do not spend a weekly slot on H26-SSL-v1.** It failed the frozen paired holdout against both the exact historical H25-1 file and the matched raw-feature head. There is no evidence from this run that it will exceed **0.2477**, much less **0.3195**. No file was uploaded to the contest.

The new, real, exact-grid research artifact is:
`docs/downloads/gems26-ssl-v1-20261002-4fdde73c40a7-nan.tif`
(SHA256 `34f590461ae021830d98521567a2b1fcdfd60eeb9032e70de9bb000618ec4d35`).
It contains 60,068 binary confidence pixels, has a unique prediction fingerprint, and passes all format/range checks. **Format pass ≠ scientific release.** The separately downloadable label-free-error ablation is also research-only. The historical H25 file is copied byte-for-byte for reference and is **not a new submission**.

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

1. **Do not retune this run on the same outer folds.** Preserve its failed gate and exact artifacts. Freeze any new experiment separately; obtain an untouched spatial/external confirmation source or disclose that the catalogue has already been reused extensively.
2. Resolve feature aliases from original official metadata: the mirror describes `tc` as “tilt angle or total curvature,” while official sources use TC for different quantities (radiometric counts, thermal conductivity). GDR 1390 describes *thermal* conductivity, but does not prove which `tc` band this bridge contains. `depth_to_base_surf` is described as basement depth in the mirror, while the organizer lists depth to a **conductive base**. Do not interpret scalar geodetic strain as a full stress tensor.
3. **H26-XEDGE** is the next lower-cost hypothesis: signed, cross-scale gravity–magnetic agreement under cover; predeclare scales and contact-vs-fault negative controls. Do not repeat the already-failed generic magnetic-low or marker-displacement hypotheses in 20GEMSDOE.
4. For representation research, add a random-frozen-encoder control, matched parameter budget, and spatially held-out *unlabelled reconstruction* assessment. Six full passes establish coverage, not convergence or foundation-model quality. The 100 m interpolated channels and small receptive field may not encode the native 1 m scarp signal that drove the stronger historical detector.
5. For **H26-DRAIN**, the official TNM API lists concrete public-domain 1 m GeoTIFFs, but a direct binary HEAD and direct API calls fail TLS in this sandbox. **Metadata availability is not downloaded-data availability.** Do not call the candidate executable here until official tile bytes, datum, coverage, seams and computational storage are checked on an unrestricted runner. Current quantized lidar summaries are insufficient for drainage profiles.
6. Independent unknown-fault labels, native lidar processing, geological/contact controls and human/expert validation remain the real bottlenecks. More GPU compute is optional for a larger MAE, not a blocker to the completed CPU prototype.
7. The target is faults. Prioritizing **geothermal vents/resources** additionally requires collocated heat, permeability and fluid evidence (Siler & Faulds, https://www.osti.gov/servlets/purl/1110515). Faults can also be barriers (Hermant et al., https://pangea.stanford.edu/ERE/db/GeoConf/papers/SGW/2025/Hermant.pdf). No list of confirmed new vents can be honestly produced from these predictions alone.

## Compliance and automation limits

No new automatic DrivenData reads after its Terms were discovered; no scraper or auto-upload. Initial requested review was tool-retrieved, **not human-read**. Permitted USGS metadata APIs can be refreshed by a daily Pages workflow; failed requests retain the last good record with visible timestamps/errors. A leaderboard snapshot is not a current feed. Organizer-authenticated data provenance, eligibility attestations and an eventual account-holder upload cannot be completed without lawful account-holder participation. Never request passwords/tokens.
