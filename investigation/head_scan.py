"""HEAD-scan every URL in downloadurls_final4.txt to get sizes and status."""

import concurrent.futures as cf
import json
import urllib.request
import urllib.error
import csv

URLS = [u.strip() for u in open("downloadurls_final4.txt", encoding="utf-8") if u.strip()]
print("urls:", len(URLS))


def head(u):
    req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "curl/8.7"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return u, r.status, int(r.headers.get("content-length") or 0), r.headers.get("content-type", "")
    except urllib.error.HTTPError as e:
        return u, e.code, 0, f"HTTPError {e}"
    except Exception as e:
        return u, -1, 0, f"{type(e).__name__}: {e}"


results = []
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for res in ex.map(head, URLS):
        results.append(res)

ok = [r for r in results if r[1] == 200]
bad = [r for r in results if r[1] != 200]
total = sum(r[2] for r in ok)
print(f"200 OK: {len(ok)}   non-200: {len(bad)}")
print(f"total bytes: {total:,}  ({total/1e6:.1f} MB, {total/2**30:.2f} GiB)")
print("\nlargest 15:")
for u, s, n, ct in sorted(ok, key=lambda x: -x[2])[:15]:
    print(f"  {n/1e6:9.2f} MB  {u}")
print("\nnon-200:")
for u, s, n, ct in bad:
    print(f"  {s}  {u}  ({ct[:60]})")

with open("head_scan.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["url", "status", "bytes", "content_type"])
    w.writerows(results)
json.dump({"ok": len(ok), "bad": len(bad), "total_bytes": total}, open("head_summary.json", "w"), indent=1)
