# Standing project instructions

Read the ENTIRE README (including its full owner prompt), knowledge/preregistration.md,
knowledge/hypothesis-slate-20261002.md, knowledge/results.md, evidence/xedge_holdout.json,
and the latest evidence/reviews.json at the beginning of EVERY session. Maximize P(Win),
Own the Outcome, preserve inconvenient evidence. `evidence/review_passes.json` is a stale
historical filename; the active three-pass log is `evidence/reviews.json`.

- Work only on the Arena session branch assigned by the environment; never switch to main.
- Check git status, fetch origin, inspect open PRs and ongoing work before editing.
- Hypotheses and confirmatory protocol must be committed BEFORE their run; any amendment
  is dated and may not retroactively promote a failed experiment. No retuning on outer folds.
- Pretrain on the entire UNLABELLED raster before opening labels. Preparation/pretraining/
  representation inference must NOT import or read labels or template prediction values.
- Freeze encoder AND decoder before supervised head fitting; record/check parameter hashes.
- Whole-raster SSL is transductive; label-based training must be spatially separated and buffered.
- Compare with the CURRENT comparable holdout best and a matched no-SSL control, not a weak
  baseline selected after seeing results. Historical as-emitted rasters are not fresh OOF controls.
- No weekly submission unless all promotion conditions pass. A downloadable research TIFF
  is not an upload recommendation. Never automate competition uploads.
- No automated access to drivendata.org or its leaderboard; terms forbid it. The initial
  requested review was tool-retrieved, NOT a human snapshot. Do not misdescribe its provenance.
  Refresh only permitted official APIs. Preserve errors and timestamps; no fabricated live feed.
- Label-free anomaly errors may reflect contacts, roughness, missing data or acquisition seams,
  not faults. No claim of hidden-fault or geothermal-vent discovery without independent evidence.
- Keep official-source statements, owner-reported scores, local computations and hypotheses
  distinct. Mirror SHA integrity does NOT authenticate organizer provenance.
- Raw TIFF band descriptions have physical ambiguities (tc, earthquake bands, conductive-base
  depth). Do not convert guessed semantics into physics claims; all bands still enter SSL.
- Audit labels before exact-file predictions for roads, closed claims, derived acquisition blocks.
  Derived blocks are NOT official-coordinate polygons. Association is not causation.
- Validate float32 single-band TIFFs against template CRS, shape, transform, finite [0,1]
  in footprint and NaN outside, then re-read. Never silently clip arbitrary invalid predictions.
- Keep bulk inputs and tensor/checkpoint caches ignored. Publish small exact artifacts and receipts.
- Run and document THREE review passes; test pathological/missing inputs and site links.
- No secrets in chat or files. If GitHub authentication fails, ask for Arena reconnection,
  not passwords/tokens. Verify PR merge and Pages deployment before claiming either.
- Read the September 2026 official rules, retain AI disclosure and eligibility/reproduction limits.
