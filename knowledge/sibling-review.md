# Historical site review — 2026-10-02

## Coverage and evidence class

`evidence/sibling_site_review.json` records **24 supplied sibling URLs**, pinned GitHub commit/path/SHA, UTC source-read times, opening text and relevant excerpts. Short root landing/redirects in GEMSDOE4, GEMSDOE10 and 17GEMSDOE were followed to their linked `docs/index.html` using the same immutable source commit; the initial path is retained. These are **source reads, not deployed HTTP checks or submission receipts**. Detailed code/source review concentrated on H19, H24, GEMSDOE10/16/20/22/23 and the actual 1.5-pixel thinning operator.

The original first historical list contains **32 numeric entries**, not 32 independently verified model runs. All 38 file/empty records including the named-but-unspecified 25/26/27 placeholders are preserved in `sources/reported_scores.json` and CSV. Exact spelling/case and supplied filenames are retained. Repeated copies of the historical list remain verbatim in README but are not counted again.

## Strongest-file forensics

- H19-5 parent: **121,131** prediction pixels; SHA256 `ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d`.
- H25-1: **60,069** pixels, no added point, **49.590% retained**; SHA256 `68d0e2e4fcc594f9a23f56c44b885fee733d026d39be55e18ad2a07289525310`.
- Independent, label-free reimplementation of pinned historical BFS/geodesic Poisson thinning exactly reproduces every point. Maximum parent→kept-point distance = **sqrt(2)×100 m = 141.42 m**. This is a geometry statement about parent detections, not a hidden-truth recall guarantee.
- Current comparable local dense TP: **12,192.20 → 10,626.80**, FP: **110,534.70 → 54,653.72**. Reduction of redundant FP outweighs lost credit under this metric. Sparse pooled local DTI **0.071466 → 0.096261**.
- Owner reports **0.1922 → 0.2477**; official initial tool snapshot shows an account at .2477, not a filename. No authenticated mapping or hidden TP/FP decomposition exists here.
- Historical rounded mean-fold DTI .1764 is independently recomputed as .176454, whereas pooled DTI is .171825. The agreement validates this local metric plumbing, not hidden performance.

Code provenance: https://github.com/buffedlizard55-lab/GEMSDOE24/blob/07345ea0604953d7efb858d9cfbc21e20c7aca0b/src/gems/thinning.py . Exact executable check: `scripts/analyze_reference.py`, `evidence/reference_forensics.json`.

## Cross-site lessons (not causal score decompositions)

1. **GEMSDOE10:** H16 continuation, native 10 m terrain channels, H25 context and H28 along-strike dot emission were previously tried. The owner reports .0461/.0921/.1280/.1839. Its own site documents both rejection of H19 confirmation and clean reproduction of previous reports. Its inference of private density from public scores requires modelling assumptions; source overlap with public catalogues does not prove every hidden fault type/data source is outside every public dataset. Do not recycle ordinary tilt, simple continuation, terrain slope/openness or dot thinning as new hypotheses.
2. **19GEMSDOE → GEMSDOE24:** strongest reused terrain/geophysical corroboration detector, then an emission-efficiency transformation. Potential-field edges and magnetic lows are not unique fault signatures; physical interpretation must be separated from DTI. The H25 site still says “unscored” and owner best .1922 even though the present brief reports .2477; retain that stale-source discrepancy.
3. **20GEMSDOE:** synthetic/case-control PU calibration is not an unbiased probability estimator. It already tested/rejected generic magnetic-low and marker-displacement ideas; a new signed cross-scale boundary proposal must have actual new transforms/controls. Its reported .1890 is not a proof of the prior-density assumptions.
4. **17GEMSDOE:** page reports D dense holdout .2795 and F ensemble proxy .1524, but the owner reports F live .0187. Proxy/counterfactual score claims do not establish new-fault transfer. The page calls all-finite outside-footprint exports “safe” and claims the earlier range-error cause; this conflicts with the explicit current NaN/null footprint rule and absent rejected-file trace. We do not inherit those assertions.
5. **GEMSDOE4:** published source discloses mixed-OOF union members and a 200-candidate selection argmax that underperforms on the untouched fold. Its raw catalogue/proxy context is not a guaranteed unbiased comparison to hidden expert faults. Its legacy narrative claims the range error specifically identifies interior NaNs; our supplied rejected file is unavailable, so we state the cause as unknown.
6. **GEMSDOE22/23:** high emission budgets or a renamed reference cannot redeem a failed blocked proxy/habitat gate. GEMSDOE22 retains an old “19GEMSDOE” title. Compare exact point fields, format and gate decisions—not page branding.
7. Repeated .1563 entries and common `7f00890a` fingerprints are repeated evidence, not multiple independent successful detectors. GEMSDOE21 explicitly reuses H19-4. NaN/all-finite variants in 12GEMSDOE share .1294 and must not be counted as an architecture ablation.
8. The .0904 lattice observation is not an identified hidden-label density. Geometry/phase, orientation, clustering, public-subset emission and the sparse-FP approximation are assumptions, not measured private facts.

Scores vary with detector, selection, population, emission budget, truth masking, code and date at once. No randomized causal attribution for the full cross-site ranking is possible. A clean comparable within-run holdout is the necessary owner rule; **it is not sufficient to prove transfer to hidden expert fault labels**.

## Irregularities that change current decisions

- Organizer-authenticated filenames, score receipts and final-selection state are not accessible here. Initial DrivenData reads were tool-retrieved before discovering its automatic-access prohibition; no later score scraper or upload exists.
- The restored mirrored example predicts the same 60,988 positive cells as known labels, not total absence. It matches prior siblings' reported irregularity. No template VALUES were used in SSL; strict export validates geometry/NaN footprint later.
- A corrupt footprint transport was detected by byte count/SHA and rejected; recovery used the immutable Git blob. Hash checks prevent silently accepting that transport corruption.
- `tc`, earthquake aliases and depth semantics remain unverified against original organizer metadata. In particular, a mirror's band-name tag is not enough to establish the absence of radiometrics or that a depth is basement rather than a conductive base.
- Derived acquisition blocks are approximate and not official coordinate polygons; one inherited line-km mapping comparison contains a large Tonopah mismatch. Treat association/error diagnostics as sensitivity, never acquisition-cause attribution.
- Old “GPU needed” / “data-placement blocker” claims are superseded by the completed automatic restore and CPU experiment here. A larger research architecture may benefit from GPU; the requested prototype did not need one.
- Deadline clocks in sibling prose differ from the rules Appendix A 5 p.m. ET statement. No newly automated competition check is performed to choose between them; eventual account-holder action must confirm the official deadline.

The original scientific gate in this repo **failed** and is not overridden by inherited optimism. See `knowledge/results.md`.
