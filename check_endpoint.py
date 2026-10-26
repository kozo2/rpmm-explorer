"""Liveness check for the RIKEN MetaBoBank PMM SPARQL endpoint.

The public URL http://metabobank.riken.jp/pmm/endpoint 301->302 redirects to the
query *UI* at https://metabobank.riken.jp/pmm/sparql . That same path is also the
query *API*, reached with GET ?format=...&query=... (see /pmm/js/endpoint.js).
"""

import json
import sys
import urllib.parse
import urllib.request

ENDPOINT = "http://metabobank.riken.jp/pmm/endpoint"

QUERIES = {
    "ASK (cheapest liveness probe)": "ASK { ?s ?p ?o }",
    "SELECT one triple": "SELECT * WHERE { ?s ?p ?o } LIMIT 1",
    "COUNT classes": "SELECT (COUNT(DISTINCT ?c) AS ?n) WHERE { [] a ?c }",
}


def run(query, fmt="application/sparql-results+json"):
    params = urllib.parse.urlencode({"format": fmt, "query": query})
    url = f"{ENDPOINT}?{params}"
    req = urllib.request.Request(url, headers={"Accept": fmt})
    with urllib.request.urlopen(req, timeout=45) as resp:
        raw = resp.read().decode("utf-8", "replace")
        return resp.status, resp.headers.get("content-type", ""), resp.url, raw


def main():
    ok = True
    for name, q in QUERIES.items():
        print(f"\n=== {name}")
        print(f"    query: {q}")
        try:
            status, ctype, final, raw = run(q)
            print(f"    HTTP {status}  content-type={ctype}")
            print(f"    final URL: {final[:110]}")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                print(f"    NOT JSON -> {raw[:200]!r}")
                ok = False
                continue
            if "boolean" in data:
                print(f"    -> boolean = {data['boolean']}")
            elif "results" in data:
                rows = data["results"]["bindings"]
                print(f"    -> {len(rows)} row(s): {json.dumps(rows[:3], ensure_ascii=False)}")
            else:
                print(f"    -> unexpected payload: {json.dumps(data)[:200]}")
        except Exception as e:
            print(f"    ERROR {type(e).__name__}: {e}")
            ok = False
    print("\nRESULT:", "ALIVE - endpoint answered SPARQL queries" if ok else "PROBLEM - see errors above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
