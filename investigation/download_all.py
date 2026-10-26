"""Download every File downloadURL in downloadurls_final4.tsv.

- follows redirects
- verifies the MD5 recorded in the endpoint against the bytes received
- preserves the remote directory structure under ./downloads/
- writes manifest.csv summarising every file
"""

import concurrent.futures as cf
import csv
import hashlib
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = (HERE / "downloads").resolve()
ROOT.mkdir(exist_ok=True)

# The endpoint records "AraMetLeaves.Rdata" but the server only serves ".RData".
URL_FIXES = {
    "http://metabobank.riken.jp/data/RPMM0001/AnalysedDataset/AraMetLeaves.Rdata":
        "http://metabobank.riken.jp/data/RPMM0001/AnalysedDataset/AraMetLeaves.RData",
}


def local_path(url):
    """Map a URL to a safe path under ROOT."""
    path = urllib.parse.unquote(urllib.parse.urlparse(url).path)
    path = path.rstrip()                      # drops the stray trailing space
    rel = path.lstrip("/")
    target = (ROOT / rel).resolve()
    if not str(target).startswith(str(ROOT) + os.sep):
        raise ValueError(f"refusing path outside download root: {target}")
    return target


def fetch(row):
    url = row["downloadURL"]
    real = URL_FIXES.get(url, url)
    dest = local_path(url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "url": url, "requested": real, "local_path": str(dest.relative_to(ROOT)),
        "status": "", "bytes": 0, "md5_expected": row.get("md5", ""),
        "md5_actual": "", "md5_match": "", "error": "",
    }
    if dest.exists() and dest.stat().st_size > 0:
        pass  # re-verify below
    try:
        req = urllib.request.Request(real, headers={"User-Agent": "curl/8.7"})
        with urllib.request.urlopen(req, timeout=180) as r, open(dest, "wb") as fh:
            h = hashlib.md5()
            n = 0
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                fh.write(chunk)
                h.update(chunk)
                n += len(chunk)
        out["status"] = "ok"
        out["bytes"] = n
        out["md5_actual"] = h.hexdigest()
        exp = row.get("md5", "")
        out["md5_match"] = ("yes" if exp == out["md5_actual"] else
                            "no" if exp else "no-md5-in-endpoint")
    except urllib.error.HTTPError as e:
        out["status"] = f"HTTP {e.code}"
        out["error"] = str(e)
    except Exception as e:  # noqa: BLE001
        out["status"] = "error"
        out["error"] = f"{type(e).__name__}: {e}"
    return out


def main():
    rows = list(csv.DictReader(open(HERE / "downloadurls_final4.tsv", encoding="utf-8"), delimiter="\t"))
    print(f"rows: {len(rows)}  ->  {ROOT}", flush=True)
    results = []
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for i, res in enumerate(ex.map(fetch, rows), 1):
            results.append(res)
            if i % 25 == 0 or i == len(rows):
                ok = sum(1 for r in results if r["status"] == "ok")
                print(f"  [{i}/{len(rows)}] ok={ok}", flush=True)

    with open(HERE / "manifest.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    ok = [r for r in results if r["status"] == "ok"]
    bad = [r for r in results if r["status"] != "ok"]
    match = [r for r in ok if r["md5_match"] == "yes"]
    mismatch = [r for r in ok if r["md5_match"] == "no"]
    print(f"\nDONE  ok={len(ok)}  failed={len(bad)}")
    print(f"bytes: {sum(r['bytes'] for r in ok):,}")
    print(f"md5 matched: {len(match)}  mismatched: {len(mismatch)}")
    for r in bad:
        print(f"  FAIL {r['status']} {r['url']} {r['error'][:80]}")
    for r in mismatch:
        print(f"  MISMATCH {r['url']} expected={r['md5_expected']} got={r['md5_actual']}")


if __name__ == "__main__":
    main()
