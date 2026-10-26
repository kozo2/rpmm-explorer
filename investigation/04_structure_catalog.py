"""Structure graphs, DBCatalog, and system graphs; verify the VALUES/count discrepancy."""

import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sparql import rows, show, ask

print("========== GRAPH PRESENCE vs COUNT ==========")
for g in ["http://metadb.riken.jp/structure/plantMetabolomics",
          "http://metadb.riken.jp/structure/DBCatalog",
          "http://metadb.riken.jp/structure/SciNetS_ria269i",
          "http://metadb.riken.jp/system",
          "http://metadb.riken.jp/system/db",
          "http://metadb.riken.jp/system/ontology",
          "http://www.openlinksw.com/schemas/virtrdf#",
          "http://www.w3.org/2002/07/owl#"]:
    a = ask(f"ASK {{ GRAPH <{g}> {{ ?s ?p ?o }} }}")
    n = rows(f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{g}> {{ ?s ?p ?o }} }}")[0]["n"]
    print(f"  ASK={a}  COUNT={n:>9}  {g}")

print("\n===== structure/plantMetabolomics CONTENT =====")
show("predicates", """SELECT ?p (COUNT(*) AS ?n) WHERE {
  GRAPH <http://metadb.riken.jp/structure/plantMetabolomics> { ?s ?p ?o } } GROUP BY ?p ORDER BY DESC(?n)""")
show("sample triples", """SELECT ?s ?p ?o WHERE {
  GRAPH <http://metadb.riken.jp/structure/plantMetabolomics> { ?s ?p ?o } } LIMIT 25""")

print("\n===== structure/DBCatalog CONTENT =====")
show("predicates", """SELECT ?p (COUNT(*) AS ?n) WHERE {
  GRAPH <http://metadb.riken.jp/structure/DBCatalog> { ?s ?p ?o } } GROUP BY ?p ORDER BY DESC(?n)""")
show("sample triples", """SELECT ?s ?p ?o WHERE {
  GRAPH <http://metadb.riken.jp/structure/DBCatalog> { ?s ?p ?o } } LIMIT 20""")

print("\n===== DBCatalog graph (db/DBCatalog) =====")
show("classes", """SELECT ?c (COUNT(?s) AS ?n) WHERE {
  GRAPH <http://metadb.riken.jp/db/DBCatalog> { ?s a ?c } } GROUP BY ?c ORDER BY DESC(?n)""")
show("sample dataset records", """SELECT ?s ?p ?o WHERE {
  GRAPH <http://metadb.riken.jp/db/DBCatalog> { ?s ?p ?o } } LIMIT 40""")

for g in ["system", "system/db", "system/ontology", "system/user"]:
    print(f"\n===== {g} =====")
    show("predicates", f"""SELECT ?p (COUNT(*) AS ?n) WHERE {{
      GRAPH <http://metadb.riken.jp/{g}> {{ ?s ?p ?o }} }} GROUP BY ?p ORDER BY DESC(?n)""")
    show("sample", f"""SELECT ?s ?p ?o WHERE {{
      GRAPH <http://metadb.riken.jp/{g}> {{ ?s ?p ?o }} }} LIMIT 15""")
