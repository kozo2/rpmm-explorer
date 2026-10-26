"""Report essentials: labelled species, project families, publications, instruments."""

import sys, collections, re
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sparql import rows

G = "http://metadb.riken.jp/db/plantMetabolomics"
PM = "http://metadb.riken.jp/ontology/plantMetabolomics/0.1/"
GR = f"GRAPH <{G}>"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"

print("========== SPECIES WITH LABELS (join NCBITaxon prefLabel) ==========")
r = rows(f"""SELECT ?tax ?pref (COUNT(?s) AS ?n) WHERE {{ {GR} {{
   ?s <http://purl.obolibrary.org/obo/RO_0002162> ?tax }}
   OPTIONAL {{ ?tax <http://www.w3.org/2004/02/skos/core#prefLabel> ?pref }} }}
   GROUP BY ?tax ?pref ORDER BY DESC(?n) LIMIT 30""")
for x in r:
    print(f"  {x['n']:>5}  {x['tax'].split('/')[-1]:<9} {x.get('pref','(no label)')}")

print("\n========== pmm:speciesName (free-text) ==========")
for x in rows(f"""SELECT ?v (COUNT(?s) AS ?n) WHERE {{ {GR} {{ ?s <{PM}speciesName> ?v }} }}
  GROUP BY ?v ORDER BY DESC(?n) LIMIT 25"""):
    print(f"  {x['n']:>5}  {x['v']}")

print("\n========== PROJECT FAMILIES ==========")
ids = [x["p"].split("/")[-1] for x in rows(f"SELECT DISTINCT ?p WHERE {{ {GR} {{ ?p a <{PM}Project> }} }}")]
fam = collections.Counter(re.match(r"^([A-Za-z_]+)", i).group(1) for i in ids)
print("  families:", dict(fam), " total:", len(ids))
print("  sample MN_SE labels:")
for x in rows(f"""SELECT ?p ?l WHERE {{ {GR} {{
  ?p a <{PM}Project> . ?p <{RDFS}label> ?l .
  FILTER(CONTAINS(STR(?p),'MN_SE')) }} }} LIMIT 5"""):
    print("   ", x["p"].split("/")[-1], "|", x["l"][:100])

print("\n========== PUBLICATIONS REFERENCED ==========")
r = rows(f"""SELECT (COUNT(DISTINCT ?ref) AS ?n) WHERE {{ {GR} {{
  ?s <http://purl.org/dc/dcmitype/references> ?ref }} }}""")
print("  distinct references:", r)
for x in rows(f"""SELECT ?ref (COUNT(?s) AS ?n) WHERE {{ {GR} {{
  ?s <http://purl.org/dc/dcmitype/references> ?ref }} }} GROUP BY ?ref ORDER BY DESC(?n) LIMIT 10"""):
    print("   ", x)

print("\n========== INSTRUMENTS / ANALYSERS ==========")
for pred in ["instrument", "massAnalyser", "manufacturer"]:
    print(f"  -- pmm:{pred}")
    for x in rows(f"""SELECT ?o (COUNT(?s) AS ?n) WHERE {{ {GR} {{ ?s <{PM}{pred}> ?o }} }}
      GROUP BY ?o ORDER BY DESC(?n) LIMIT 12"""):
        print(f"     {x['n']:>4}  {str(x['o'])[:95]}")

print("\n========== DATA-VOLUME INDICATORS ==========")
for cls in ["Project", "Experiment", "Measurement", "Sample", "BiologicalSample",
            "RawDataset", "File", "MassSpectralFile", "DataAnalysis", "PeakFile",
            "NormalisedDataMatrixFile", "Compound", "Person"]:
    n = rows(f"SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE {{ {GR} {{ ?s a <{PM}{cls}> }} }}")[0]["n"]
    print(f"  {cls:<26} {n}")

print("\n========== m/z, RT, METADATA COMPLETENESS ON FILES ==========")
n_files = int(rows(f"SELECT (COUNT(DISTINCT ?f) AS ?n) WHERE {{ {GR} {{ ?f a <{PM}File> }} }}")[0]["n"])
n_md5 = int(rows(f"SELECT (COUNT(DISTINCT ?f) AS ?n) WHERE {{ {GR} {{ ?f <{PM}md5> ?m }} }}")[0]["n"])
n_url = int(rows(f"SELECT (COUNT(DISTINCT ?f) AS ?n) WHERE {{ {GR} {{ ?f <{PM}downloadURL> ?u }} }}")[0]["n"])
n_fmt = int(rows(f"SELECT (COUNT(DISTINCT ?f) AS ?n) WHERE {{ {GR} {{ ?f <{PM}fileFormat> ?x }} }}")[0]["n"])
print(f"  Files={n_files}  with md5={n_md5}  with URL={n_url}  with format={n_fmt}")

print("\n========== TOP-LEVEL NAMESPACE CENSUS (subjects by host) ==========")
r = rows("""SELECT ?s WHERE { ?s ?p ?o } GROUP BY ?s LIMIT 400000""", timeout=600)
hosts = collections.Counter()
for x in r:
    m = re.match(r"^https?://([^/]+)/", x["s"])
    hosts[m.group(1) if m else x["s"][:40]] += 1
total = len(r)
print(f"  (sampled {total} distinct subjects)")
for h, c in hosts.most_common(20):
    print(f"  {c:>7}  {h}")
