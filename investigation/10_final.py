"""Final checks: project-family structure, unused schema terms, ontology inventory."""

import sys, json, re, html, collections
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sparql import rows

G = "http://metadb.riken.jp/db/plantMetabolomics"
PM = "http://metadb.riken.jp/ontology/plantMetabolomics/0.1/"
GR = f"GRAPH <{G}>"

print("========== STRUCTURE: RPMM vs MN_SE PROJECTS ==========")
for fam in ["RPMM", "MN_SE"]:
    nproj = rows(f"""SELECT (COUNT(DISTINCT ?p) AS ?n) WHERE {{ {GR} {{
      ?p a <{PM}Project> FILTER(CONTAINS(STR(?p),'{fam}')) }} }}""")[0]["n"]
    nexp = rows(f"""SELECT (COUNT(DISTINCT ?e) AS ?n) WHERE {{ {GR} {{
      ?p a <{PM}Project> FILTER(CONTAINS(STR(?p),'{fam}'))
      ?p <{PM}experiment> ?e }} }}""")[0]["n"]
    nmeas = rows(f"""SELECT (COUNT(DISTINCT ?m) AS ?n) WHERE {{ {GR} {{
      ?e <{PM}measurement> ?m . ?p <{PM}experiment> ?e
      FILTER(CONTAINS(STR(?p),'{fam}')) }} }}""")[0]["n"]
    nfiles = rows(f"""SELECT (COUNT(DISTINCT ?f) AS ?n) WHERE {{ {GR} {{
      ?f a <{PM}File> FILTER(CONTAINS(STR(?f),'{fam}')) }} }}""")[0]["n"]
    npub = rows(f"""SELECT (COUNT(DISTINCT ?r) AS ?n) WHERE {{ {GR} {{
      ?p a <{PM}Project> FILTER(CONTAINS(STR(?p),'{fam}'))
      ?p <http://purl.org/dc/dcmitype/references> ?r }} }}""")[0]["n"]
    print(f"  {fam:<6} projects={nproj:<4} experiments={nexp:<5} measurements={nmeas:<6} files={nfiles:<6} publications={npub}")

print("\n========== SCHEMA TERMS DEFINED BUT NEVER INSTANTIATED ==========")
props = rows(f"""SELECT DISTINCT ?p WHERE {{ {GR} {{ ?p a <http://www.w3.org/1999/02/22-rdf-syntax-ns#Property> }} }}""")
used = {x["p"] for x in rows(f"SELECT DISTINCT ?p WHERE {{ {GR} {{ ?s ?p ?o }} }}")}
classes = rows(f"""SELECT DISTINCT ?c WHERE {{ {GR} {{ ?c a <http://www.w3.org/2000/01/rdf-schema#Class> }} }}""")
usedc = {x["o"] for x in rows(f"SELECT DISTINCT ?o WHERE {{ {GR} {{ ?s a ?o }} }}")}
unused_p = sorted(x["p"] for x in props if x["p"] not in used and x["p"].startswith(PM))
unused_c = sorted(x["c"] for x in classes if x["c"] not in usedc and x["c"].startswith(PM))
print(f"  pmm properties defined={len([x for x in props if x['p'].startswith(PM)])}  never used as predicate={len(unused_p)}")
for p in unused_p:
    print("    ", p.replace(PM, "pmm:"))
print(f"  pmm classes defined={len([x for x in classes if x['c'].startswith(PM)])}  never instantiated={len(unused_c)}")
for c in unused_c:
    print("    ", c.replace(PM, "pmm:"))

print("\n========== ONTOLOGY INVENTORY (from site front page) ==========")
t = open("front.html", encoding="utf-8", errors="replace").read()
pairs = re.findall(r'<a[^>]*href="([^"]*metadb\.riken\.jp/pmm/ontology[^"]*)"[^>]*>([^<]+)</a>', t)
if not pairs:
    pairs = re.findall(r'(http://metadb\.riken\.jp/pmm/ontology/\S+?)\s+([A-Za-z_]+)\s', html.unescape(t))
seen = {}
for u, name in pairs:
    seen[u] = name.strip()
print("  ontologies advertised:", len(seen))
for u, n in sorted(seen.items(), key=lambda x: x[1].lower()):
    print(f"    {n:<24} {u}")

print("\n========== LOADED ONTOLOGY GRAPH VERSIONS ==========")
for x in rows("""SELECT ?g ?version ?iri WHERE {
   GRAPH ?g { ?s a <http://www.w3.org/2002/07/owl#Ontology> }
   OPTIONAL { GRAPH ?g { ?s <http://www.w3.org/2002/07/owl#versionInfo> ?version } }
   OPTIONAL { GRAPH ?g { ?s <http://www.w3.org/2002/07/owl#versionIRI> ?iri } } }"""):
    print("   ", x)
print("  owl:Ontology headers found:")
for x in rows("""SELECT ?g ?s WHERE { GRAPH ?g { ?s a <http://www.w3.org/2002/07/owl#Ontology> } }"""):
    print("   ", x)
