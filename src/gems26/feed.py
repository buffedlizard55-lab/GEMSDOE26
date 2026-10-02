"""Permitted official metadata feed. Never access DrivenData automatically."""
from __future__ import annotations

import hashlib
from urllib.parse import urlparse

import requests

from .common import utcnow

ALLOWED_HOSTS = {"www.sciencebase.gov", "tnmaccess.nationalmap.gov", "api.datacite.org"}
ENDPOINTS = {
    "geodawn": "https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7?format=json",
    "3dep": "https://tnmaccess.nationalmap.gov/api/v1/products?bbox=-119.5,39.5,-119.4,39.6&datasets=Digital%20Elevation%20Model%20%28DEM%29%201%20meter&max=2",
    "gdr_registry": "https://api.datacite.org/dois/10.15121/1881483",
}


def assert_permitted(url: str) -> None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    if host == "drivendata.org" or host.endswith(".drivendata.org"):
        raise ValueError("DrivenData automatic access is prohibited")
    if parsed.scheme != "https" or host not in ALLOWED_HOSTS or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("Only allowlisted HTTPS official metadata APIs permitted")


def extract(source: str, data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Official API did not return an object")
    if source == "geodawn":
        if data.get("id") != "657e1d85d34e23d3533209f7" or not isinstance(data.get("title"), str):
            raise ValueError("Unexpected ScienceBase identity/title")
        provenance = data.get("provenance")
        if not isinstance(provenance, dict):
            raise ValueError("Missing ScienceBase provenance object")
        updated = provenance.get("lastUpdated")
        if not isinstance(updated, str):
            raise ValueError("Missing ScienceBase update timestamp")
        return {"title": data["title"], "source_last_updated": updated, "dataset_id": data["id"]}
    if source == "3dep":
        if not isinstance(data.get("total"), int) or data["total"] < 0 or not isinstance(data.get("items"), list):
            raise ValueError("Unexpected National Map catalog schema")
        return {"title": "USGS 3DEP 1 m catalog sample", "sample_bbox": [-119.5, 39.5, -119.4, 39.6],
                "matching_items": data["total"], "returned_items": len(data["items"]),
                "scope": "Metadata query only, not binary tile availability or full region coverage"}
    if source == "gdr_registry":
        record = data.get("data")
        if not isinstance(record, dict) or not isinstance(record.get("attributes"), dict):
            raise ValueError("Missing DOI record/attributes")
        attributes = record["attributes"]
        if record.get("id") != "10.15121/1881483" or attributes.get("doi") != "10.15121/1881483":
            raise ValueError("Unexpected INGENIOUS DOI")
        titles = attributes.get("titles", [])
        updated = attributes.get("updated")
        if not isinstance(titles, list) or not titles or not isinstance(titles[0], dict) or not isinstance(titles[0].get("title"), str) or not isinstance(updated, str):
            raise ValueError("Missing DOI title/update timestamp")
        return {"title": titles[0]["title"], "doi": attributes["doi"], "registry_last_updated": updated,
                "scope": "DOE publisher-deposited DOI metadata, not a check of GDR portal files or binary availability"}
    raise ValueError("Unknown source")


def refresh(previous: dict, get=requests.get) -> dict:
    now = utcnow()
    result = {"schema_version": 1, "attempted_utc": now, "automation_scope": "Allowlisted USGS metadata and DOE-deposited DataCite DOI metadata only; no competition site access",
              "leaderboard": previous.get("leaderboard", {}), "items": {}}
    old = previous.get("items", {})
    for source, url in ENDPOINTS.items():
        assert_permitted(url)
        row = {"url": url, "attempted_utc": now, "last_good": old.get(source, {}).get("last_good")}
        try:
            response = get(url, timeout=(10, 20), allow_redirects=False,
                           headers={"User-Agent": "GEMSDOE26 official metadata checker; github.com/buffedlizard55-lab/GEMSDOE26"})
            if response.status_code != 200:
                raise ValueError(f"HTTP {response.status_code}; redirects are not followed")
            if len(response.content) > 2_000_000:
                raise ValueError("Metadata response unexpectedly exceeds 2 MB")
            values = extract(source, response.json())
            row.update(status="ok", last_good={"checked_utc": now, "method": "allowlisted_api_request", **values,
                                                "response_sha256": hashlib.sha256(response.content).hexdigest()})
        except (requests.RequestException, ValueError, KeyError, TypeError) as e:
            row.update(status="error_last_good_retained", error=str(e)[:400])
        result["items"][source] = row
    result["all_refreshes_succeeded"] = all(r["status"] == "ok" for r in result["items"].values())
    return result
