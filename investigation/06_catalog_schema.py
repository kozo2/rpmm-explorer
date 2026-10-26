"""Dataset catalog, SciNetS databases, ontology provenance, PMM schema inventory."""

import sys, collections
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sparql import rows, show

print("========== DBCatalog: registered datasets ==========")
r = rows("""SELECT ?d ?label ?desc ?home ?n WHERE {
  GRAPH <http://metadb.riken.jp/db/DBCatalog> { ?d a <http://rdfs.org/ns/void#Dataset> }
  OPTIONAL { ?d <http://www.w3.org/2000/01/rdf-schema#label> ?label }
  OPTIONAL { ?d <http://purl.org/dc/terms/description> ?desc }
  OPTIONAL { ?d <http://xmlns.com/foaf/0.1/homepage> ?home }
  OPTIONAL { ?d <http://rdfs.org/ns/void#triples> ?n }
} ORDER BY ?d""")
print("datasets:", len(r))
for x in r:
    print("  -", x.get("d"))
    if x.get("label"): print("      label:", x["label"][:90])
    if x.get("desc"):  print("      desc :", x["desc"][:110])
    if x.get("home"):  print("      home :", x["home"])
    if x.get("n"):     print("      triples:", x["n"])

print("\n========== properties used on catalog datasets ==========")
show("catalog predicates", """SELECT ?p (COUNT(*) AS ?n) WHERE {
  GRAPH <http://metadb.riken.jp/db/DBCatalog> { ?s ?p ?o } } GROUP BY ?p ORDER BY DESC(?n) LIMIT 40""")

print("\n========== SciNetS_ria269i: what is it? ==========")
SG = "http://metadb.riken.jp/db/SciNetS_ria269i"
show("classes", f"""SELECT ?c (COUNT(?s) AS ?n) WHERE {{ GRAPH <{SG}> {{ ?s a ?c }} }}
  GROUP BY ?c ORDER BY DESC(?n) LIMIT 20""")
show("sample subjects + labels", f"""SELECT ?s ?label WHERE {{ GRAPH <{SG}> {{ ?s a ?c }}
  OPTIONAL {{ ?s <http://www.w3.org/2000/01/rdf-schema#label> ?label }} }} LIMIT 12""")
show("what labels exist", f"""SELECT ?label (COUNT(*) AS ?n) WHERE {{ GRAPH <{SG}> {{
  ?s <http://www.w3.org/2000/01/rdf-schema#label> ?label }} }} GROUP BY ?label ORDER BY DESC(?n) LIMIT 15""")

print("\n========== SciNetS_ria390i ==========")
show("classes", """SELECT ?c (COUNT(?s) AS ?n) WHERE {
  GRAPH <http://metadb.riken.jp/db/SciNetS_ria390i> { ?s a ?c } } GROUP BY ?c ORDER BY DESC(?n) LIMIT 15""")

print("\n========== other db graphs ==========")
for g in ["brc_jcm", "brc_nbrp_rat", "brainMindsTest"]:
    print(f"\n--- {g}")
    show("classes", f"""SELECT ?c (COUNT(?s) AS ?n) WHERE {{
      GRAPH <http://metadb.riken.jp/db/{g}> {{ ?s a ?c }} }} GROUP BY ?c ORDER BY DESC(?n) LIMIT 12""")

print("\n========== ONTOLOGY GRAPH PROVENANCE ==========")
show("version/date/licence predicates across ontology graphs", """
SELECT ?g ?p (COUNT(*) AS ?n) WHERE {
  GRAPH ?g { ?s ?p ?o }
  FILTER(?p IN (<http://www.w3.org/2002/07/owl#versionInfo>,
                <http://www.w3.org/2002/07/owl#versionIRI>,
                <http://purl.org/dc/terms/date>,
                <http://purl.org/dc/terms/license>,
                <http://purl.org/dc/elements/1.1/date>,
                <http://www.w3.org/2000/01/rdf-schema#comment>))
} GROUP BY ?g ?p ORDER BY DESC(?n) LIMIT 40""")

print("\n========== PMM ONTOLOGY SCHEMA (classes with en/ja labels) ==========")
r = rows("""SELECT ?c ?en ?ja WHERE {
  ?c a <http://www.w3.org/2000/01/rdf-schema#Class>
  OPTIONAL { ?c <http://www.w3.org/2000/01/rdf-schema#label> ?en FILTER(LANG(?en)='en') }
  OPTIONAL { ?c <http://www.w3.org/2000/01/rdf-schema#label> ?ja FILTER(LANG(?ja)='ja') }
} ORDER BY ?c""")
print("PMM classes defined:", len(r))
for x in r:
    print(f"  {x['c'].split('/')[-1]:<38} en={str(x.get('en'))[:44]:<46} ja={x.get('ja')}")

print("\n========== PMM ONTOLOGY SCHEMA (properties) ==========")
r = rows("""SELECT ?p ?en ?ja ?domain ?range WHERE {
  ?p a <http://www.w3.org/1999/02/22-rdf-syntax-ns#Property>
  OPTIONAL { ?p <http://www.w3.org/2000/01/rdf-schema#label> ?en FILTER(LANG(?en)='en') }
  OPTIONAL { ?p <http://www.w3.org/2000/01/rdf-schema#label> ?ja FILTER(LANG(?ja)='ja') }
  OPTIONAL { ?p <http://www.w3.org/2000/01/rdf-schema#domain> ?domain }
  OPTIONAL { ?p <http://www.w3.org/2000/01/rdf-schema#range> ?range }
} ORDER BY ?p""")
print("PMM properties defined:", len(r))
for x in r:
    print(f"  {x['p'].split('/')[-1]:<34} dom={str(x.get('domain','-')).split('/')[-1]:<22} "
          f"rng={str(x.get('range','-')).split('/')[-1]:<22} en={str(x.get('en'))[:40]}")
