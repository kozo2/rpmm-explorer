"""Minimal SPARQL client for the RIKEN PMM endpoint.

The server picks the result format from the `format` query parameter (not the
Accept header) and needs GET, so we drive it directly with urllib.
"""

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://metabobank.riken.jp/pmm/sparql"
JSON_CT = "application/sparql-results+json"
CACHE = Path(__file__).parent / "cache"
CACHE.mkdir(exist_ok=True)


def sparql(query, fmt=JSON_CT, timeout=120, retries=2, use_cache=True):
    """Return (status, content_type, body_text)."""
    key = CACHE / (str(abs(hash((query, fmt)))) + ".json")
    if use_cache and key.exists():
        body = key.read_text(encoding="utf-8")
        return 200, JSON_CT, body
    params = urllib.parse.urlencode({"format": fmt, "query": query})
    url = f"{ENDPOINT}?{params}"
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"Accept": fmt})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
            if use_cache:
                key.write_text(body, encoding="utf-8")
            return 200, fmt, body
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"query failed: {last}\n{query[:200]}")


def rows(query, **kw):
    """Return list of dicts {var: value} for a SELECT."""
    _, _, body = sparql(query, **kw)
    data = json.loads(body)
    if "results" not in data:
        raise ValueError(f"not a SELECT result: {json.dumps(data)[:300]}")
    return [{k: v["value"] for k, v in b.items()} for b in data["results"]["bindings"]]


def ask(query, **kw):
    _, _, body = sparql(query, **kw)
    return json.loads(body).get("boolean")


def show(title, query, limit=None, **kw):
    print(f"\n### {title}")
    print(f"# {query}")
    try:
        r = rows(query, **kw)
    except Exception as e:  # noqa: BLE001
        print(f"!! {e}")
        return []
    if limit:
        r = r[:limit]
    for x in r:
        print("   ", x)
    print(f"    ({len(r)} shown)")
    return r
