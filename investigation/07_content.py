"""Content profiling of the PMM domain graph: projects, species, organs, platforms, files."""

import sys, json
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sparql import rows

G = "http://metadb.riken.jp/db/plantMetabolomics"
PM = "http://metadb.riken.jp/ontology/plantMetabolomics/0.1/"
GR = f"GRAPH <{G}>"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"


def q(body):
    return f"SELECT {body}"


print("========== PROJECTS ==========")
print("distinct Projects:", rows(
    f"SELECT (COUNT(DISTINCT ?p) AS ?n) WHERE {{ {GR} {{ ?p a <{PM}Project> }} }}"))
r = rows(f"""SELECT ?p ?label ?date WHERE {{ {GR} {{ ?p a <{PM}Project> }}
  OPTIONAL {{ ?p <{RDFS}label> ?label }}
  OPTIONAL {{ ?p <{PM}publicRelaseDate> ?date }} }} ORDER BY ?p""")
print("project rows (may include multilingual dupes):", len(r))
ids = sorted({x["p"].split("/")[-1] for x in r})
print(f"project ids ({len(ids)}):", ", ".join(ids))
json.dump(r, open("projects.json", "w"), indent=1)
dates = sorted(x["date"][:10] for x in r if x.get("date"))
print(f"release dates present: {len(dates)}/{len(ids)}; min={dates[0] if dates else '-'} max={dates[-1] if dates else '-'}")
print("  first 6:", dates[:6])

print("\n========== SPECIES (RO_0002162 -> NCBITaxon) ==========")
for x in rows(f"""SELECT ?tax ?label (COUNT(?s) AS ?n) WHERE {{ {GR} {{
  ?s <http://purl.obolibrary.org/obo/RO_0002162> ?tax
  OPTIONAL {{ ?tax <{RDFS}label> ?label }} }} }}
  GROUP BY ?tax ?label ORDER BY DESC(?n) LIMIT 30"""):
    print(f"  {x['n']:>6}  {x['tax'].split('/')[-1]:<28} {x.get('label','')}")

print("\n========== PLANT ORGAN (pmm:plantOrgan) ==========")
for x in rows(f"""SELECT ?o (COUNT(?s) AS ?n) WHERE {{ {GR} {{ ?s <{PM}plantOrgan> ?o }} }}
  GROUP BY ?o ORDER BY DESC(?n) LIMIT 25"""):
    print(f"  {x['n']:>6}  {x['o']}")
print("PlantOrgan instances defined:",
      rows(f"SELECT (COUNT(*) AS ?n) WHERE {{ {GR} {{ ?x a <{PM}PlantOrgan> }} }}"))

print("\n========== TECHNOLOGY / PLATFORM ==========")
for pred in ["technologyType", "technologyPlatform", "measurementType", "experimentType", "ionMode"]:
    print(f"  -- pmm:{pred}")
    for x in rows(f"""SELECT ?o (COUNT(?s) AS ?n) WHERE {{ {GR} {{ ?s <{PM}{pred}> ?o }} }}
      GROUP BY ?o ORDER BY DESC(?n) LIMIT 12"""):
        print(f"     {x['n']:>5}  {str(x['o'])[:95]}")

print("\n========== FILE LAYER ==========")
for body, t in [
    (f"(COUNT(DISTINCT ?f) AS ?n) WHERE {{ {GR} {{ ?f a <{PM}File> }} }}", "distinct Files"),
    (f"(COUNT(*) AS ?n) WHERE {{ {GR} {{ ?f <{PM}md5> ?m }} }}", "md5 statements"),
    (f"(COUNT(*) AS ?n) WHERE {{ {GR} {{ ?f <{PM}downloadURL> ?u }} }}", "downloadURL statements"),
    (f"(COUNT(*) AS ?n) WHERE {{ {GR} {{ ?f <{PM}fileFormat> ?x }} }}", "fileFormat statements"),
]:
    print(f"  {t:<26}", rows("SELECT " + body))

print("  -- fileFormat values")
for x in rows(f"""SELECT ?o (COUNT(?s) AS ?n) WHERE {{ {GR} {{ ?s <{PM}fileFormat> ?o }} }}
  GROUP BY ?o ORDER BY DESC(?n) LIMIT 20"""):
    print(f"     {x['n']:>5}  {x['o'].split('/')[-1]:<22} {x['o']}")

print("  -- sample downloadURLs")
for x in rows(f"SELECT ?u WHERE {{ {GR} {{ ?s <{PM}downloadURL> ?u }} }} LIMIT 8"):
    print("     ", x["u"])

print("\n========== CROSS-REFERENCES ==========")
for pred, name in [("http://purl.org/dc/terms/references", "dcterms:references"),
                   ("http://purl.org/dc/terms/isReferencedBy", "dcterms:isReferencedBy"),
                   ("http://purl.org/dc/terms/identifier", "dcterms:identifier"),
                   ("http://www.w3.org/2000/01/rdf-schema#seeAlso", "rdfs:seeAlso"),
                   ("http://www.w3.org/2004/02/skos/core#related", "skos:related"),
                   ("http://purl.org/dc/terms/description", "dcterms:description"),
                   ("http://purl.org/dc/terms/creator", "dcterms:creator")]:
    print(f"  {name:<24}", rows(f"SELECT (COUNT(*) AS ?n) WHERE {{ {GR} {{ ?s <{pred}> ?o }} }}")[0]["n"])

print("\n========== PEOPLE / ORGS ==========")
print("  top principal investigators")
for x in rows(f"""SELECT ?p (COUNT(?s) AS ?n) WHERE {{ {GR} {{ ?s <{PM}principalInvestigator> ?p }} }}
  GROUP BY ?p ORDER BY DESC(?n) LIMIT 12"""):
    print(f"     {x['n']:>4}  {x['p']}")
for x in rows(f"""SELECT ?s ?fn ?ln WHERE {{ {GR} {{ ?s a <{PM}Person> }}
  OPTIONAL {{ ?s <http://xmlns.com/foaf/0.1/firstName> ?fn }}
  OPTIONAL {{ ?s <http://xmlns.com/foaf/0.1/familyName> ?ln }} }} LIMIT 10"""):
    print("   person:", x)

print("\n========== PROPERTY POPULATION (coverage) IN PMM GRAPH ==========")
r = rows(f"SELECT ?p (COUNT(*) AS ?n) WHERE {{ {GR} {{ ?s ?p ?o }} }} GROUP BY ?p ORDER BY DESC(?n)")
pmm = [(x["p"], int(x["n"])) for x in r if x["p"].startswith(PM)]
print(f"  pmm-namespace properties actually used: {len(pmm)}")
print("  least-populated (bottom 18):")
for p, n in sorted(pmm, key=lambda t: t[1])[:18]:
    print(f"    {n:>5}  {p.replace(PM, 'pmm:')}")
