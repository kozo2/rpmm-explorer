"""Recon: capabilities, graphs, scale, predicate/class distributions."""

import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sparql import rows, show, ask, sparql

print("========== CAPABILITY / RECON ==========")

show("Named graphs", "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } } LIMIT 50")
show("Total triples (exact)", "SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }")
show("Distinct subjects", "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s ?p ?o }")
show("Distinct predicates", "SELECT (COUNT(DISTINCT ?p) AS ?n) WHERE { ?s ?p ?o }")
show("Distinct objects", "SELECT (COUNT(DISTINCT ?o) AS ?n) WHERE { ?s ?p ?o }")
show("Triples where object is literal", "SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o FILTER(isLiteral(?o)) }")
show("Triples where object is IRI", "SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o FILTER(isIRI(?o)) }")
show("ASK subquery support", "ASK { SELECT ?s WHERE { ?s ?p ?o } LIMIT 1 }")
show("Service/federation probe", "SELECT ?s WHERE { SERVICE <https://dbpedia.org/sparql> { ?s a ?c } } LIMIT 1", use_cache=False)

print("\n===== PREDICATE FREQUENCY (top 60) =====")
preds = show(
    "Predicates by triple count",
    """SELECT ?p (COUNT(*) AS ?n) WHERE { ?s ?p ?o }
       GROUP BY ?p ORDER BY DESC(?n) LIMIT 60""",
    limit=60,
)

print("\n===== CLASS FREQUENCY (top 60) =====")
show(
    "Classes by instance count",
    """SELECT ?c (COUNT(?s) AS ?n) WHERE { ?s a ?c }
       GROUP BY ?c ORDER BY DESC(?n) LIMIT 60""",
    limit=60,
)

print("\n===== INSTANCE COUNTS WITHOUT TYPE =====")
show("Subjects lacking rdf:type", "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s ?p ?o FILTER NOT EXISTS { ?s a ?c } }")
