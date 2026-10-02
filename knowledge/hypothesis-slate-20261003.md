# H27 hypothesis slate and frozen DILCOND protocol

**Prepared:** 2026-10-03 UTC, before any H27 code, new label access, or model fit in this document's
lineage. This slate is written after H26-XEDGE-v1 failed its preregistered gate (see
`knowledge/results.md`) and after re-confirming, directly from the pinned mirror's embedded GDAL
band tags (`band_name`, `data_category`, `data_type`, `description` — the same tag schema the
official reference notebook reads), that `tc` carries `data_category=magnetic_data`,
`geod_2ndinv`/`geod_shearrate`/`geod_dilaterate` carry `data_category=geodetic_strain`, and
`depth_to_base_surf`/`cond_surf` carry `data_category=subsurface`. See
`sources/band_tags_official.csv`, produced by reading `data/raw/training_features.tif` tags
directly (SHA256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`, pinned in
`data/input_manifest.json`). This is strong circumstantial corroboration of the mirror's semantic
labels (matching schema used by `drivendataorg/gems-prize-reference-solution`), **not** a
cryptographically signed organizer attestation; treat it as resolved-enough to use, not as absolute
certainty.

**Decision principle:** Maximize P(Win); own the scientific and engineering outcome. A candidate
earns no submission slot because it is novel-sounding, format-valid, or locally attractive — it must
beat the current holdout best (H25-1 local reference and the matched fresh raw-feature head) by the
preregistered margin on buffered spatial folds, with 3/4 confirmation-quadrant wins, before any
weekly slot is even considered. No weekly slot is spent in this document regardless of outcome: this
agent has no DrivenData account and must not automate uploads.

**Scope:** Fault-location competition target, not a map of confirmed geothermal vents. This is a
prospective screen on the already-used catalogue and spatial quadrants, not an independent
confirmation set. H26-SSL and H26-XEDGE-v1 remain rejected and are not retuned here.

## Ranked candidates

| Rank | Candidate / exact layers | Physical signature targeted | Why it could catch an uncatalogued fault | Difference from everything already implemented here | Expected DTI / cost / feasibility today |
|---|---|---|---|---|---|
| **1** | **H27-DILCOND** — `geod_dilaterate` (band 8, `geodetic_strain`) + `cond_surf` (band 17, `subsurface`), both already in the pinned mirror. | Spatially coincident **positive** (extensional) geodetic dilatation anomaly and **elevated** subsurface conductivity, ranked and combined at σ = 3/6/12 px (300/600/1,200 m), sign-aware (only extension × only high-conductivity, not the full unsigned magnitude used everywhere else in this repo). | Fault zones that currently or recently accommodated dilation develop fracture porosity; fractures that stay fluid/brine-charged raise bulk conductivity (Archie-law-type coupling). A fault can show this fluid/permeability signature with **no** mapped surface scarp, **no** magnetic or gravity density contrast (ruled out by XEDGE/CBASE), and **no** classic edge at all — exactly the structurally-permeable, fluid-charged-but-geometrically-quiet case documented for blind systems in Gabbs Valley (gravity high interpreted together with hydrothermal alteration, not a clean density/magnetic edge: [OSTI 1724114](https://www.osti.gov/biblio/1724114), [OSTI 1724114 full paper](https://www.osti.gov/servlets/purl/1724114); [USGS pub 70201803](https://pubs.usgs.gov/publication/70201803)) and the dilational-stepover geothermal play-fairway model (Faulds & Hinz, 2015, summarized in the Nevada Play Fairway ML dataset: [OSTI DataExplorer 1897036](https://www.osti.gov/dataexplorer/biblio/dataset/1897036), preliminary report [OSTI servlet 1999432](https://www.osti.gov/servlets/purl/1999432)). | XEDGE = unsigned gradient-**orientation** agreement between RTP magnetic and isostatic gravity (a geometric contact/edge test). STRAIN (ranked #3, not yet implemented) = strain **localization aligned with a potential-field edge** (kinematic + geometric). CBASE (ranked #4, not yet implemented) = conductivity/basement-depth **curvature** aligned with a gravity edge (geometric). DILCOND uses **no gradient/edge/curvature operator and no magnetic or gravity band at all**: it is a sign-aware **co-anomaly coincidence** of a strain-rate component and a subsurface electrical property, targeting fluid/permeability rather than density/magnetic/geometric contrast. | **Low cost (existing mirrored bands only, no new external data), implementable and holdout-testable today.** Physically plausible but unauthenticated at the pixel level (geodetic strain products are typically native at kilometer-scale and may be heavily oversmoothed at this 100 m grid; conductivity anomalies are equally explained by playa evaporite/clay/soil moisture with no tectonic cause). **Selected for the preregistered H27 screen below.** |
| **2** | **H27-SEISMIC-LINEAMENT** — raw USGS ANSS ComCat earthquake catalog (not the pre-baked `deq_n100a15`/`ieq_n100a15` distance/density bands, which only encode a single fixed radius/azimuth scalar). | Azimuthally-coherent alignment ("lineament") of background micro-seismicity epicenters via a Hough-transform-style line-density estimator, independent of any single fixed azimuth bin. | Background microseismicity commonly aligns along active basement faults even where there is no mapped surface trace; a static radial distance-to-nearest-event feature (already in the stack) cannot express *orientation* coherence, only proximity. | None of XEDGE/STRAIN/CBASE/DILCOND touch raw seismic event geometry; this is the only candidate using point-process event data instead of a pre-gridded raster. | **Free, official, and independently confirmed obtainable in principle** — USGS FDSN event web service, `https://earthquake.usgs.gov/fdsnws/event/1/query` (no auth, public domain) — but **binary/API network egress is unavailable in this sandbox**: `curl`, Python `requests`, and the National Map API all fail with `SSL_ERROR_SYSCALL`/`SSLZeroReturnError` to every tested external host except `pypi.org` and `api.github.com` (verified this session). `fetch_page`/`web_search` can retrieve small rendered text but cannot reliably bulk-ingest a multi-thousand-event GeoJSON catalog for 5.17M pixels without an unacceptable risk of transcription error. **Deferred to an unrestricted runner**, not implemented here. |
| **3** | **H27-ALTERATION** — free Sentinel-2 L2A surface reflectance (SWIR/VNIR band ratios for argillic/propylitic hydrothermal alteration and iron-oxide indices), official distribution via the public AWS Open Data "Sentinel-2 Cloud-Optimized GeoTIFFs" bucket indexed by Element84 Earth Search STAC (`https://earth-search.aws.element84.com/v1`, no login) or ESA Copernicus Data Space Ecosystem. | Clay/iron-oxide spectral alteration halos coincident with structural lineaments mapped from the existing stack, as a direct geothermal-vent-motivated signature (hydrothermal alteration is the classic Nevada Play Fairway exploration vector: [OSTI DataExplorer 1832126](https://www.osti.gov/dataexplorer/biblio/dataset/1832126)). | A hydrothermally altered zone can mark a blind upflow conduit with no mapped fault trace and no magnetic/gravity contrast large enough for XEDGE/CBASE; alteration mineralogy is an independent physical observable from everything in the 19-band stack (none of the 19 bands is multispectral reflectance). | Thematically the strongest fit to the prompt's explicit "geothermal vents" research emphasis; algorithmically wholly new data modality (passive optical/SWIR reflectance) for this repo. | **Free and official in principle (verified reachable in a general sense via public AWS/ESA documentation), but not fetchable from this sandbox**: this environment cannot pull COG tiles or raw imagery (the same network restriction as #2; `fetch_page` renders text/markdown, not satellite raster bytes). **Deferred to an unrestricted runner** with a named, obtainable, free, official source; not implementable here today. |
| **4** | **H26-STRAIN** (carried over, unimplemented) — `geod_2ndinv`, `geod_shearrate`, `geod_dilaterate` + `rtp`/`iso_grav_anom`. | Strain-rate contrast co-located with a potential-field edge. | Active segment lacking a mapped scarp but showing both present-day strain localization and a density/magnetic boundary. | Combines kinematics with a geometric edge test; distinct from DILCOND's no-edge fluid-coincidence design. | Now better-grounded (`geodetic_strain` category confirmed), but still low/uncertain and not implemented this session; lower priority than DILCOND because DILCOND targets a fault type STRAIN/XEDGE/CBASE would structurally miss (geodetically and potential-field "quiet" but fluid-charged). |
| **5** | **H26-CBASE** (carried over, unimplemented) — `cond_surf`, `depth_to_base_surf`, `iso_grav_anom*`, `rtp`. | Multi-scale curvature/displacement of a conductive-boundary surface aligned to a gravity edge. | Faulted sedimentary basin margin juxtaposing conductivity and density with no surface scarp. | Geometric curvature-alignment test (edge family), unlike DILCOND's coincidence-of-anomalies test. | Unimplemented; `subsurface` category confirmation reduces (does not eliminate) semantic risk versus the organizer's original definitions. |

### What would be needed to make #2/#3 viable

Both are genuinely free and officially sourced, but this specific sandboxed agent environment has
**no general outbound HTTPS egress** beyond `pypi.org` (pip) and `api.github.com` (`gh`/git); this was
re-verified this session: `curl https://www.google.com`, `curl https://www.osti.gov`,
`curl https://earthquake.usgs.gov`, `curl https://raw.githubusercontent.com`, and
`requests.get("https://earthquake.usgs.gov/...")` all fail with `SSL_ERROR_SYSCALL` /
`SSLZeroReturnError`, while `pip install` and `gh api` succeed. A human operator or an unrestricted
CI runner can fetch these sources directly; no credential or paid API is required for either.

## Frozen H27-DILCOND v1 screen

### Inputs and order of operations

1. Verify pinned input bytes and the 100 m grid. Restore/prepare the full feature raster using the
   existing label-free pipeline (`prepare_data.py` → `pretrain.py` → `infer_representation.py` →
   `build_anomaly.py`); the DILCOND feature itself only reads `data/prepared/values.npy`,
   `observed.npy`, and `footprint.npy`, never labels, template, or SSL latents.
2. Use 0-based feature-array bands **7** (`geod_dilaterate`) and **16** (`cond_surf`), i.e. 1-based
   bands 8 and 17 in the pinned preparation receipt. Use the already robust-normalized, clipped
   `[-8,8]` values and their observed masks.
3. Define valid support as the joint observed mask eroded by **48 pixels** (4× the largest σ) with a
   3×3 all-true structuring element, identical to XEDGE's halo rule for comparability.
4. For each σ ∈ {3, 6, 12} px: Gaussian-smooth each field, subtract a **regional background**
   Gaussian-smoothed at 4σ (so the score responds to a *local* anomaly relative to the surrounding
   trend, not the absolute field value — this directly guards against geodetic strain products being
   smoother/coarser than the 100 m grid). Keep only the **positive** (extensional) dilatation
   residual and the **positive** (elevated) conductivity residual; negative residuals are clipped to
   zero before ranking (signed/asymmetric, unlike XEDGE's unsigned alignment).
5. Percentile-rank each positive residual over the valid support at each σ; joint per-scale score
   `cσ = sqrt(rank_dilation⁺ · rank_cond⁺)`. Combine scales by geometric mean:
   `S = exp(meanσ(log(cσ + 1e-6)))`. No orientation/persistence term (this is a coincidence test, not
   an edge-direction test). Percentile-rank `S` on support for the final feature; zero-valued ties are
   forced to rank 0 (never an artificial 0.5), exactly as XEDGE handles ties.
6. Save exact input hashes, transform configuration, support count, feature hash, and a
   no-label-before-completion receipt before the first label read, exactly as `build_xedge.py` does
   for XEDGE, gated on this document's own commit (recorded once committed) rather than the XEDGE
   slate commit.

### Spatial validation and release gate (identical protocol to the frozen XEDGE screen)

- Four NW/NE/SW/SE quadrant folds, 1.5 km exclusion collar, whole-connected-component exclusion,
  same fixed training sample caps/seeds, same 16-epoch `FaultHead` schedule, same raw 51-feature
  input plus the one new DILCOND feature (52nd).
- Score the identical historical H25-1 raster as an as-emitted, catalogue-leaky local comparator, and
  a matched fresh raw-feature head as the non-historical comparator. 30 selection draws (seed offset
  60) and 30 confirmation draws (seed offset 90), 20% component thinning, pooled DTI per the exact
  official metric (`src/gems26/metric.py`).
- **Necessary gate, reused unchanged from the XEDGE protocol:** DILCOND head must beat both H25 and
  the raw head by **≥ 0.005 pooled sparse DTI** at both the selection and confirmation stages; win
  **≥ 3/4 confirmation quadrants** against both; be no worse than either by more than **0.005 pooled
  dense DTI**; pass the labels-first nuisance/road/claim/acquisition-block relative-association check;
  and pass the strict exact-grid float32 `[0,1]` TIFF validation. Failing any one of these fails the
  whole screen; no threshold is chosen after seeing a result.
- A pass is **necessary, not sufficient**: it would still only be a reused-catalogue sensitivity
  screen, not independent hidden-fault truth, and would still require a human account-holder to
  actually upload anything. No file from this run may consume a weekly slot regardless of outcome.

## What this slate does not claim

- DILCOND has not yet been shown to exceed the official hidden-label score, and may well fail its own
  gate exactly as XEDGE did; a hypothesis being physically well-motivated is not evidence it clears a
  fixed empirical bar.
- DILCOND's score is a coincidence-of-anomalies feature, not a calibrated probability, fault map, or
  confirmed geothermal vent map.
- Elevated conductivity + positive dilatation can equally reflect playa evaporite deposits, irrigated
  agriculture, perched groundwater, or geodetic processing noise with no tectonic cause whatsoever.
- H27-SEISMIC-LINEAMENT and H27-ALTERATION name real, free, official sources, but this agent's sandbox
  cannot fetch their bytes; they remain unimplemented and must not be described as validated or even
  attempted beyond this documentation.
- "National Laboratory of the Rockies" (NLR) was independently confirmed this session as the renamed
  National Renewable Energy Laboratory (NREL), effective 2025-12-01, administering American-Made/GEMS:
  [ThinkGeoEnergy](https://www.thinkgeoenergy.com/us-doe-announces-prize-challenge-for-discovery-of-hidden-geothermal-systems/),
  [Ethanol Producer Magazine](https://ethanolproducer.com/articles/doe-renames-national-renewable-energy-laboratory-as-national-laboratory-of-the-rockies),
  [NLR research-hub record of the official rules](https://research-hub.nlr.gov/en/publications/geologic-enhanced-mapping-system-gems-prize-official-rules/)
  (DOI [10.2172/3818146](https://doi.org/10.2172/3818146)). This resolves earlier sessions' flag that
  `docs.nlr.gov` looked like an unfamiliar domain; it is a legitimate, newly renamed DOE national lab
  domain, not a hallucinated or fraudulent source. The `docs.nlr.gov` PDF link itself still could not
  be fetched directly from this sandbox (`SSL_ERROR_SYSCALL`); the Dropbox mirror and the NLR
  research-hub abstract were used as corroborating independent copies instead of the primary link.
