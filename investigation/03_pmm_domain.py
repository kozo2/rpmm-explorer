"""Deep dive: the PMM domain graph (db/plantMetabolomics + its structure graph)."""

import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sparql import rows, show

G = "http://metadb.riken.jp/db/plantMetabolomics"
S = "http://metadb.riken.jp/structure/plantMetabolomics"
PM = "http://metadb.riken.jp/ontology/plantMetabolomics/0.1/"


def pre(u):
    return u.replace(PM, "pmm:").replace("http://www.w3.org/1999/02/22-rdf-syntax-ns#", "rdf:")


print("========== PMM DOMAIN GRAPH ==========")

show("Classes used by instances (domain graph)", f"""
SELECT ?c (COUNT(?s) AS ?n) WHERE {{ GRAPH <{G}> {{ ?s a ?c }} }}
GROUP BY ?c ORDER BY DESC(?n) LIMIT 50""")

show("Predicates in domain graph (top 70)", f"""
SELECT ?p (COUNT(*) AS ?n) WHERE {{ GRAPH <{G}> {{ ?s ?p ?o }} }}
GROUP BY ?p ORDER BY DESC(?n) LIMIT 70""")

show("Structure graph: classes", f"""
SELECT ?c (COUNT(?s) AS ?n) WHERE {{ GRAPH <{S}> {{ ?s a ?c }} }}
GROUP BY ?c ORDER BY DESC(?n) LIMIT 30""")

show("Structure graph: predicates", f"""
SELECT ?p (COUNT(*) AS ?n) WHERE {{ GRAPH <{S}> {{ ?s ?p ?o }} }}
GROUP BY ?p ORDER BY DESC(?n) LIMIT 40""")

# --- how are datasets / samples identified?
show("Named individuals in PMM ontology namespace (count by local type)", f"""
SELECT ?c (COUNT(DISTINCT ?s) AS ?n) WHERE {{ ?s a ?c . FILTER(STRSTARTS(STR(?s),"{PM}")) }}
GROUP BY ?c ORDER BY DESC(?n) LIMIT 30""")

# --- top-level structural triples for one of each major class
print("\n===== SAMPLE ENTITY DESCRIPTIONS =====")
for cls in ["RawDataset", "Sample", "Measurement", "File", "Project",
            "Experiment", "Compound", "DataAnalysis", "MassSpectralFile"]:
    iri = PM + cls
    r = show(f"Example {cls}: resources + label", f"""
    SELECT ?s ?label WHERE {{ ?s a <{iri}> OPTIONAL {{ ?s <http://www.w3.org/2000/01/rdf-schema#label> ?label }} }} LIMIT 6""")
