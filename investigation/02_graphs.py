"""Named-graph inventory: full list, sizes, and subject counts per graph."""

import sys, json
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sparql import rows, show

graphs = [r["g"] for r in rows("SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }")]
print(f"TOTAL GRAPHS: {len(graphs)}")
for g in sorted(graphs):
    print("  ", g)
json.dump(sorted(graphs), open("graphs.json", "w"), indent=1)

print("\n===== TRIPLES PER GRAPH =====")
vals = " ".join(f"<{g}>" for g in graphs)
q = f"""SELECT ?g (COUNT(*) AS ?n) WHERE {{
  VALUES ?g {{ {vals} }} GRAPH ?g {{ ?s ?p ?o }} }} GROUP BY ?g ORDER BY DESC(?n)"""
res = rows(q)
for r in res:
    print(f"  {r['n']:>10}  {r['g']}")
json.dump(res, open("graph_triples.json", "w"), indent=1)

print("\n===== DISTINCT SUBJECTS PER GRAPH =====")
q2 = f"""SELECT ?g (COUNT(DISTINCT ?s) AS ?n) WHERE {{
  VALUES ?g {{ {vals} }} GRAPH ?g {{ ?s ?p ?o }} }} GROUP BY ?g ORDER BY DESC(?n)"""
res2 = rows(q2)
for r in res2:
    print(f"  {r['n']:>10}  {r['g']}")
json.dump(res2, open("graph_subjects.json", "w"), indent=1)
