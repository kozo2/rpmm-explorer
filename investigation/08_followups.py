"""Follow-ups: species label resolution, release dates, dcterms usage, link checks."""

import sys, json, urllib.request
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sparql import rows

G = "http://metadb.riken.jp/db/plantMetabolomics"
PM = "http://metadb.riken.jp/ontology/plantMetabolomics/0.1/"
GR = f"GRAPH <{G}>"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"

print("========== SPECIES LABEL RESOLUTION ==========")
taxa = [x["tax"] for x in rows(f"""SELECT DISTINCT ?tax WHERE {{ {GR} {{
  ?s <http://purl.obolibrary.org/obo/RO_0002162> ?tax }} }}""")]
print("distinct taxa used:", len(taxa))
print("sample taxon IRIs:", taxa[:5])
one = taxa[0]
print(f"\nall statements about <{one}> in the whole store:")
for x in rows(f"SELECT ?g ?p ?o WHERE {{ GRAPH ?g {{ <{one}> ?p ?o }} }} LIMIT 20"):
    print("   ", x)
print("\nsearching any label-ish property for taxon 3702 across store:")
for x in rows("""SELECT ?g ?p ?o WHERE { GRAPH ?g { ?s ?p ?o . FILTER(?p IN (
   <http://www.w3.org/2000/01/rdf-schema#label>, <http://www.w3.org/2004/02/skos/core#prefLabel>))
   FILTER(CONTAINS(STR(?s),'NCBITaxon_3702')) } } LIMIT 10"""):
    print("   ", x)

print("\n========== RELEASE-DATE-LIKE PROPERTIES IN PMM GRAPH ==========")
for x in rows(f"""SELECT ?p (COUNT(*) AS ?n) WHERE {{ {GR} {{ ?s ?p ?o }}
  FILTER(CONTAINS(LCASE(STR(?p)),'date') || CONTAINS(LCASE(STR(?p)),'release')) }}
  GROUP BY ?p ORDER BY DESC(?n)"""):
    print(f"   {x['n']:>6}  {x['p']}")
print("  sample values:")
for x in rows(f"""SELECT ?p ?o WHERE {{ {GR} {{ ?s ?p ?o }}
  FILTER(CONTAINS(LCASE(STR(?p)),'date') || CONTAINS(LCASE(STR(?p)),'release')) }} LIMIT 12"""):
    print("   ", x)

print("\n========== dcterms / dcmitype USAGE IN PMM GRAPH ==========")
for x in rows(f"""SELECT ?p (COUNT(*) AS ?n) WHERE {{ {GR} {{ ?s ?p ?o }}
  FILTER(CONTAINS(STR(?p),'purl.org/dc')) }} GROUP BY ?p ORDER BY DESC(?n)"""):
    print(f"   {x['n']:>6}  {x['p']}")

print("\n========== label PREDICATES USED IN PMM GRAPH ==========")
for x in rows(f"""SELECT ?p (COUNT(*) AS ?n) WHERE {{ {GR} {{ ?s ?p ?o }}
  FILTER(CONTAINS(LCASE(STR(?p)),'label') || CONTAINS(LCASE(STR(?p)),'name')) }}
  GROUP BY ?p ORDER BY DESC(?n) LIMIT 20"""):
    print(f"   {x['n']:>6}  {x['p']}")

print("\n========== PROJECT-LEVEL TRIPLES (one example, RPMM0037) ==========")
for x in rows(f"""SELECT ?p ?o WHERE {{ <{PM.replace('/ontology/','/db/')}Project/RPMM0037> ?p ?o }}"""):
    print(f"   {x['p'].replace(PM,'pmm:')} = {str(x['o'])[:100]}")

print("\n========== LINK LIVENESS (HTTP HEAD on sample download URLs) ==========")
for x in rows(f"SELECT ?u WHERE {{ {GR} {{ ?s <{PM}downloadURL> ?u }} }} LIMIT 6"):
    u = x["u"]
    try:
        req = urllib.request.Request(u, method="HEAD")
        with urllib.request.urlopen(req, timeout=25) as r:
            print(f"   {r.status}  {r.headers.get('content-length','?'):>10}  {u}")
    except Exception as e:
        print(f"   ERR {type(e).__name__}: {e}  {u}")

print("\n========== GRAPH TRIPLE SUM CHECK ==========")
gt = json.load(open("graph_triples.json"))
print("non-empty graphs:", len(gt), " sum:", sum(int(x["n"]) for x in gt))
print("union total:", rows("SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }")[0]["n"])
