"""Endpoint-wide vocabulary / literal / language / datatype profiling."""

import json, sys, collections, re
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sparql import rows

def ns(iri):
    m = re.match(r"^(.*?[#/])([^#/]*)$", iri)
    return m.group(1) if m else iri

print("===== ALL 545 PREDICATES, AGGREGATED BY NAMESPACE =====")
preds = rows("""SELECT ?p (COUNT(*) AS ?n) WHERE { ?s ?p ?o }
                GROUP BY ?p ORDER BY DESC(?n)""")
print("predicate count:", len(preds))
json.dump(preds, open("predicates.json", "w"), indent=1)
agg = collections.Counter()
cnt = collections.Counter()
for r in preds:
    a = ns(r["p"])
    agg[a] += 1
    cnt[a] += int(r["n"])
print(f"\n{'namespace':<62} {'preds':>6} {'triples':>12}")
for a, n in cnt.most_common(30):
    print(f"{a:<62} {agg[a]:>6} {n:>12,}")

print("\n===== OBJECT LITERAL/LANGUAGE PROFILE (whole store) =====")
try:
    r = rows("""SELECT ?lang (COUNT(*) AS ?n) WHERE {
                  ?s ?p ?o . FILTER(isLiteral(?o))
                  BIND(LANG(?o) AS ?lang) } GROUP BY ?lang ORDER BY DESC(?n)""", timeout=300)
    for x in r:
        tag = x["lang"] or "(no language tag)"
        print(f"   {x['n']:>10}  {tag}")
except Exception as e:
    print("   whole-store lang query failed:", e)

print("\n===== LITERAL PROFILE IN PMM DOMAIN GRAPH =====")
G = "http://metadb.riken.jp/db/plantMetabolomics"
r = rows(f"""SELECT ?lang (COUNT(*) AS ?n) WHERE {{
   GRAPH <{G}> {{ ?s ?p ?o . FILTER(isLiteral(?o)) BIND(LANG(?o) AS ?lang) }}
}} GROUP BY ?lang ORDER BY DESC(?n)""")
for x in r:
    print(f"   {x['n']:>8}  {x['lang'] or '(none)'}")

print("\n===== DATATYPES IN PMM DOMAIN GRAPH =====")
r = rows(f"""SELECT ?dt (COUNT(*) AS ?n) WHERE {{
   GRAPH <{G}> {{ ?s ?p ?o . FILTER(isLiteral(?o)) BIND(DATATYPE(?o) AS ?dt) }}
}} GROUP BY ?dt ORDER BY DESC(?n) LIMIT 20""")
for x in r:
    print(f"   {x['n']:>8}  {x.get('dt', '(none/plain)')}")

print("\n===== QUANTITY / UNIT USAGE (qudt) =====")
for r_ in rows(f"""SELECT ?unit (COUNT(*) AS ?n) WHERE {{
   GRAPH <{G}> {{ ?s <http://qudt.org/schema/qudtunit> ?unit }} }} GROUP BY ?unit ORDER BY DESC(?n) LIMIT 15"""):
    print("   ", r_)

print("\n===== SUBJECT URI PATTERNS IN PMM GRAPH =====")
r = rows(f"""SELECT ?s (COUNT(*) AS ?n) WHERE {{ GRAPH <{G}> {{ ?s ?p ?o }} }} GROUP BY ?s LIMIT 20000""", timeout=300)
segs = collections.Counter()
for x in r:
    parts = x["s"].split("/")
    if len(parts) >= 6 and "db" in parts:
        segs["/".join(parts[4:7])] += 1
    else:
        segs["<other>"] += 1
print("   (sampled distinct subjects within PMM graph)")
for k, v in segs.most_common(25):
    print(f"   {v:>6}  {k}")
