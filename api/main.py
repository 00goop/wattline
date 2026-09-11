"""WATTLINE API — read-only, serves precomputed JSON (rule D-006).
Contract: BUILD-PLAN §3, frozen in mocks/.

Data resolution: data/processed/<name>.json wins if it exists, else
mocks/<name>.json. Swapping mock -> real = drop files into data/processed/
with the SAME shapes and restart. No endpoint computes anything per request.

Run: uvicorn api.main:app --reload
"""
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent


SOURCES: dict[str, str] = {}


def valid_shape(name, data):
    """Reject parseable but unusable top-level payloads before serving them."""
    if not isinstance(data, dict):
        return False
    if name == 'npus':
        return data.get('type') == 'FeatureCollection' and isinstance(data.get('features'), list)
    if name == 'sites':
        return isinstance(data.get('sites'), list)
    if name == 'exposure':
        return all(isinstance(data.get(str(hour)), dict)
                   and data[str(hour)].get('hour') == hour
                   and isinstance(data[str(hour)].get('npus'), list) for hour in range(25))
    if name == 'stats':
        return all(isinstance(data.get(key), (int, float)) and not isinstance(data[key], bool)
                   and data[key] >= 0 for key in ('georgia_total', 'metro_atlanta_total'))
    return False


def load(name: str):
    """First readable source wins. A malformed data/processed/ drop falls back
    to mocks rather than killing the service mid-demo (D-007)."""
    for base in (ROOT / "data" / "processed", ROOT / "mocks"):
        p = base / f"{name}.json"
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not valid_shape(name, data):
            continue
        SOURCES[name] = base.name
        return data
    raise RuntimeError(f"no data source for '{name}' — run scripts/make_mocks.py")


app = FastAPI(title="WATTLINE API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

NPUS = load("npus")
EXPOSURE = load("exposure")   # dict keyed by hour as string, "0".."24"
SITES = load("sites")
STATS = load("stats")


@app.get("/")
def root():
    return {"service": "WATTLINE API", "docs": "/docs", "health": "/api/health",
            "endpoints": ["/api/npus", "/api/exposure?hour=N",
                          "/api/exposure/all", "/api/sites", "/api/stats"]}


@app.get("/api/health")
def health():
    """Render health check target. Proves the payloads actually loaded, and
    reports whether each is real (data/processed) or mock."""
    return {"status": "ok", "sources": SOURCES,
            "npu_features": len(NPUS.get("features", [])),
            "exposure_hours": len(EXPOSURE),
            "sites": len(SITES.get("sites", []))}


@app.get("/api/npus")
def npus():
    return NPUS


@app.get("/api/exposure")
def exposure(hour: int = 0):
    if not 0 <= hour <= 24:
        raise HTTPException(status_code=422, detail="hour must be in 0..24")
    try:
        return EXPOSURE[str(hour)]
    except KeyError:
        raise HTTPException(status_code=404, detail=f"no series for hour {hour}")


@app.get("/api/exposure/all")
def exposure_all():
    """All 25 hours in one response — the scrubber prefetches on mount and a
    laggy scrub costs Design points. Same precomputed payload, one round trip."""
    return EXPOSURE


@app.get("/api/sites")
def sites():
    return SITES


@app.get("/api/stats")
def stats():
    return STATS
