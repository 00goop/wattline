# WATTLINE

**When the power goes out, some people are on a clock. Nobody is counting.**

[**Live demo**](https://wattline-web.onrender.com) · Built at Hack RenderATL, August 2026

![Wattline Outage Exposure Map](docs/demo.png)

## The problem

A portable oxygen concentrator runs under an hour on battery. Georgia Power
tells customers to prepare for three days without electricity, and their entire
published guidance for medical equipment is one line: "Keep your phones and
medical devices charged."

After Hurricane Helene, parts of Augusta were dark for nine days. Richmond
County has 1,647 people on electricity-dependent medical equipment. Statewide:
92,233.

We read Georgia Power's $912M storm cost recovery case (GA PSC Docket 44280) —
all data-request responses, the May 2026 stipulation, and the Commission's
order. The words *medical*, *ventilator*, *oxygen*, and *vulnerable* appear
zero times.

## What WATTLINE does

**1. Identify.** Federal emPOWER data publishes at ZIP level — a ZIP can span a
senior tower and a golf course. We disaggregate onto Atlanta parcels and NPU
boundaries, weighted by housing units and tract-level age and disability rates.
Conserves exactly against the 92,233 state total.

**2. Exposure gap.** Not a prediction — a subtraction. Utility restoration ETA
minus the manufacturer's published minimum runtime for the devices counted in
that area.

**3. Reach.** Charging capacity at libraries, fire stations, and rec centers,
assigned to the highest-gap neighborhoods — constrained by MARTA transit
reachability, because a household with no vehicle cannot reach a site no bus
serves.

## What it does not do

It does not touch utility restoration order. Georgia Power restores hospitals,
then the highest-customer-count repairs — that is correct. A crew on a feeder
restores 3,000 customers; the same crew on a lateral restores one house.
WATTLINE uses a different resource pool: buildings, not crews.

## API

Four read-only endpoints, everything precomputed — nothing calculates per
request. Shapes are frozen; `mocks/` is the contract source of truth until
real data lands.

| Endpoint | Returns |
|---|---|
| `GET /api/npus` | NPU polygons + disaggregated population (GeoJSON) |
| `GET /api/exposure?hour=N` | Per-NPU exposure gap and tier at outage hour N (0–24) |
| `GET /api/sites` | Charging sites with transit reachability and assignments |
| `GET /api/stats` | Header numbers |

## Data sources

| Source | Use |
|---|---|
| [HHS emPOWER](https://empowerprogram.hhs.gov/) | De-identified counts of electricity-dependent Medicare beneficiaries |
| [Atlanta Regional Commission Open Data](https://opendata.atlantaregional.com/) | Parcels, building footprints |
| [City of Atlanta DPCD](https://dpcd-coaplangis.opendata.arcgis.com/) | NPU boundaries, public facilities |
| [MARTA GTFS](https://www.itsmarta.com/app-developer-resources.aspx) | Transit reachability |
| [Census ACS](https://www.census.gov/data/developers/data-sets/acs-5year.html) | B01001 (age), B18101 (disability), B08201 (vehicle access) |
| GA PSC Docket 44280 | Storm restoration record |

## Architecture

Python ingest → precomputed tables → FastAPI (read-only) → React + MapLibre GL

Every stage writes its own output, and the API only reads. Nothing is computed
per request — the 25-hour exposure series ships as a single payload so the
timeline scrubber never waits on the network.

Deployed on Render as a Blueprint: a Python web service for the API and a
static site for the frontend, both auto-deploying from `main`.

```
wattline/
├── scripts/         source fetchers — emPOWER, ARC tracts, MARTA GTFS
├── pipeline/        Atlanta layers · disaggregation · sites · exposure series
├── data/            raw pulls + device runtime floors
│   └── processed/   pipeline output — what the API actually serves
├── mocks/           frozen API contract, and the offline fallback
├── api/             FastAPI, read-only
├── workflows/       ingest DAG (Render Workflows)
└── web/             React + Vite + MapLibre GL
```

## Running locally

```bash
# API — needs no database and no environment at all
pip install -r requirements.txt
uvicorn api.main:app --reload        # serves data/processed/, else mocks/

# Frontend
cd web && npm install && npm run dev

# Regenerate the pipeline from source data (optional)
python pipeline/run_full_pipeline.py # rewrites data/processed/
python scripts/make_mocks.py         # regenerates mocks/*.json
```

## Limitations

- **emPOWER is Medicare-only.** It excludes private insurance, Medicaid-only,
  military coverage, and long-term care residents, and undercounts under-65
  disabled people. 92,233 is a floor, not a ceiling.
- **Lookback windows** are 13 months for most DME, 36 months for oxygen
  concentrators, 5 years for implanted cardiac devices. This is "filed a claim,"
  not "currently uses."
- **HHS suppresses small cells** — values 1–10 are published as 11. We treat
  these as intervals and test containment, not equality.
- **ZIP codes do not nest inside counties.** Only 109 of Georgia's 159 counties
  reconcile, so we conserve against the state total.
- Output is a **scenario-based neighborhood priority surface**, not a claim
  about where specific individuals live.
- Battery runtimes are manufacturer published minimums. An assistive technology
  specialist at Georgia Tech CIDI confirmed to us that no one in the field will
  commit to hard runtime numbers — charge state, battery age, and defects all
  vary, and every factor makes it worse. Our gap is the optimistic case.

## Acknowledgments

Georgia Council on Developmental Disabilities and Tools for Life / Center for
Inclusive Design & Innovation at Georgia Tech both responded to our questions
during the build.

## Team

Vinh Le · Niko · Guttu · Kareem

## License

MIT

## Fork modernization and verification

This portfolio branch belongs to **00goop/wattline**, a fork of
[vinhbin/wattline](https://github.com/vinhbin/wattline). The original team and
architecture are preserved. Guttu owned API/Render/Devpost, Kareem Atlanta layers,
sites and exposure work, Niko emPOWER/disaggregation, and Vinh the frontend.

Run `python -m pytest tests -q` after installing both requirements files and `httpx`.
Run `npm ci && npm run build` inside `web/`. CI checks the existing pipeline
invariants plus API hours 0–24, read-only methods, source selection and invalid-data
fallback. A parsed but invalid top-level processed payload now falls back to mocks;
health reports which source loaded. This is contract validation, not a complete
geospatial data-quality certification. No pipeline work runs in request handlers.

The linked deployment is historical and has not been redeployed by this branch.
The award and contribution descriptions in the supplied resume remain attributed
to the original team; later verification work does not establish historical authorship.

The frontend uses patched MapLibre 6 with a bundled module worker and loads the
map only when requested. Initial JavaScript build output decreased from 1.24 MB to
211 KB uncompressed in the local verification build (not a measured page-load time).
A street-basemap failure falls back to a plain background and retains local overlays.
See [MapLibre advisory](https://github.com/maplibre/maplibre-gl-js/security/advisories/GHSA-jrc7-96c5-q579).
