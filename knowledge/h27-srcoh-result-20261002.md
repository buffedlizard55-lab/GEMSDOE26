# H27-SRCOH-v1 frozen screen result

**Decision: `BLOCKED_DO_NOT_SUBMIT`.** The only authorized H27 candidate failed its preregistered, reused-catalogue spatial screen. It is not eligible for a contest slot, and no H27 GeoTIFF was exported. The separate H26-XEDGE OOF file remains a format-valid research artifact and remains blocked; this result does not change its status.

## Scope and frozen chronology

- Four distinct mechanisms were ranked in [`hypothesis-slate-20261002-v2.md`](hypothesis-slate-20261002-v2.md). H27-SRCOH alone was authorized. The other three candidates remain deferred and untested.
- The holdout receipt records quantitative-slate commit `140cbd5286cd9130c290772575c42ea1d862453c`, SHA-256 `64310e85a5b636e20f2a35165ee10c714e204dedf62c57d1afe88351b2ee06a7`, and code-freeze commit `3d696771fcd796d24f4b121ddbcb5f53321ec0a0`; code-freeze manifest SHA-256 `22a253b3f40e11185e0f233a1f4cabe6f65b1b256de16e43ede694fe3ae171ab`.
- **Current-checkout provenance boundary:** this PR clone starts at assigned base `cee5eb0982dad19be65181ecefaa05bc5d6d7844`; the experiment-time freeze commit objects are absent from its Git object database. The prior checkout's review record says the ancestry check passed then, but ancestry cannot be reauthenticated from this clone. The frozen protocol, input, and code-file hashes remain available for inspection; this is not an independent hardware attestation.
- Whole-footprint preparation completed at `2026-10-02T23:39:02Z`; six-pass label-free pretraining completed at `23:40:36Z`; frozen inference at `23:41:20Z`; the anomaly stage at `23:41:29Z`; the H27 feature at `23:41:58Z`; first label-pixel access for this H27 run at `23:42:31Z`. Every pre-label receipt states `labels_opened: false`; the feature receipt also states `template_opened: false`.
- The fixed footprint has 5,167,373 cells. H27 support is 4,272,494 cells (82.68%). The feature is one ranked scalar derived only from prepared zero-based bands `(3, 6, 7)`, their observation masks and the footprint. The mirror aliases are owner-supplied names; their physical semantics and units are not authenticated.
- This is transductive use of the complete unlabeled raster and a repeated, publicly known fault catalogue—not independent hidden-fault validation. The local DTI values below are not DrivenData scores.

## Measured results

Dense DTI is the pooled four-quadrant known-catalogue proxy. Sparse DTI is the mean of 30 pooled component-thinning draws within each prespecified seed-offset group. Bracketed values are the standard deviation across those 30 draws. The two groups reuse the same labels, components and quadrants.

| Emitted arm | Dense pooled local DTI | Sparse DTI, offsets 120–149 | Sparse DTI, offsets 150–179 |
|---|---:|---:|---:|
| Historical H25-1, as emitted | 0.171825 | 0.097701 [0.006259] | 0.096849 [0.004882] |
| Fixed H26-XEDGE OOF, as emitted | 0.133141 | 0.075165 [0.007525] | 0.075839 [0.006257] |
| Same-run raw head, 52 dimensions | 0.136243 | 0.076816 [0.007653] | 0.077166 [0.006224] |
| **H27-SRCOH head, 52 dimensions** | **0.126771** | **0.071865 [0.007098]** | **0.072414 [0.006073]** |

The raw control's 52nd feature is fixed at zero; the H27 head adds the one preregistered score. Both heads had 5,505 parameters and used identical fold seeds, 16 epochs, sample caps and training examples. Fold training/test minimum gaps were 15.13–16.00 pixels (1.51–1.60 km); each fold used 24,000 positive and 120,000 unlabeled-as-negative samples. H25's known all-catalogue-mask leakage was retained and disclosed.

| Comparator | H27 sparse delta, offsets 120–149 | H27 sparse delta, offsets 150–179 | H27 dense delta | Repeat fold wins for H27 |
|---|---:|---:|---:|---:|
| Matched raw head | −0.004950 | −0.004752 | −0.009472 | 0/4 |
| H26-XEDGE OOF | −0.003300 | −0.003424 | −0.006370 | 1/4 |
| H25-1 as emitted | −0.025835 | −0.024435 | −0.045054 | 0/4 |

The preregistered screen required at least `+0.005` sparse DTI versus **each** comparator in both groups, at least 3/4 repeat-fold wins against each, and dense DTI no worse than any comparator by more than 0.005. **All 15 component gate rules failed.** This is not a marginal pass, and the result does not support a leaderboard-score forecast.

## Evidence and reproduction boundary

- [`evidence/h27_srcoh_feature.json`](../evidence/h27_srcoh_feature.json) — hashes, code/protocol freeze, pre-label chronology, support and feature.
- [`evidence/h27_srcoh_holdout.json`](../evidence/h27_srcoh_holdout.json) — fold receipts, comparator pins, gate and decision.
- [`evidence/h27_srcoh_selection.json`](../evidence/h27_srcoh_selection.json) and [`evidence/h27_srcoh_confirmation.json`](../evidence/h27_srcoh_confirmation.json) — all 60 paired draws and fold/component metrics.
- [`evidence/h27_srcoh_preparation.json`](../evidence/h27_srcoh_preparation.json), [`evidence/h27_srcoh_pretraining.json`](../evidence/h27_srcoh_pretraining.json), [`evidence/h27_srcoh_representation.json`](../evidence/h27_srcoh_representation.json), [`evidence/h27_srcoh_anomaly.json`](../evidence/h27_srcoh_anomaly.json) — the separate, label-free prerequisite receipts. These are intentionally separate from the earlier H26 receipts.
- The feature array SHA-256 is `aae38d98d2ec54be199e2374e2eca759a431a91519a3faca76f599257960d37c`; its support SHA-256 is `f99761ff66b6375faa2c6aaff5a46c8f032ea28e9e858a0fea0071b3a1db9e31`. Large arrays remain ignored; source code, receipts and the raw-input manifest are retained for audit.

**Replay is not currently authorized or executable from this PR checkout.** The H27 runner deliberately requires the experiment-time slate/code commit objects, which are absent from the current clone. Do not work around that guard, rerun the holdout, regenerate an H27 TIFF or tune the revealed folds. The receipts and source hashes remain available for static review; if the original commit objects are restored in a future clean environment, the same frozen runner still refuses to overwrite the published holdout receipt. Any next candidate requires an independent/untouched validation design and a fresh preregistered slate. The owner-reported H25 `0.2477` and dated leaderboard snapshot `0.3195` remain unverified here; no local value should be represented as either score.
