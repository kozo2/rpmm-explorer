# RIKEN PMM (Plant Metabolome Metadatabase) SPARQL Endpoint — Data Investigation

**Endpoint:** `http://metabobank.riken.jp/pmm/endpoint` → redirects to `https://metabobank.riken.jp/pmm/sparql`
**Query date:** 2026-10-15
**Investigation method:** ~60 SPARQL queries via `urllib` (GET + `format` parameter), plus HTTP header probing and link checks. Scripts and raw outputs are in [`investigation/`](investigation/).

---

## 1. Executive summary

| Question | Finding |
|---|---|
| Is it live? | **Yes.** HTTP 200, Virtuoso 07.20.3230, answers ASK/SELECT/CONSTRUCT/DESCRIBE. |
| How big? | **26,910,989 triples**, 4,166,619 subjects, 545 distinct predicates, 8,428,740 distinct objects. |
| What is it? | A **union store of 42 non-empty named graphs**: 37 imported reference ontologies (88.8% of triples) + 5 RIKEN database graphs (11.2%). |
| The headline domain | **RIKEN Plant Metabolome Metadatabase (RPMM / Metabolonote)**: 152 curated projects, 12,712 measurements, 14,026 data files with MD5 + live download URLs, spanning 169 plant taxa. |
| The catch | The PMM domain data is only **1.46% of the store** (392,791 triples / 62,865 subjects). The rest is noise from the caller's perspective — you must scope every query with `GRAPH <…/db/plantMetabolomics>`. |
| Biggest data-quality issue | Domain metadata uses the **`purl.org/dc/dcmitype/` namespace for properties** (`dcmitype:identifier`, `dcmitype:description`, `dcmitype:creator`, `dcmitype:references`) — a namespace misuse that breaks standard `dcterms` consumers. 10,554 + 5,717 + 100 + 103 statements affected. |

---

## 2. Access, protocol, and gotchas

Verified against the live server:

| Property | Behaviour |
|---|---|
| HTTP method | **GET only.** `POST` returns **405**. |
| Output format | Selected by the **`format` query parameter**, *not* the `Accept` header. `Accept` alone yields `text/html`. |
| Server | `Virtuoso/07.20.3230 (Linux) x86_64-unknown-linux-gnu` (evidence: `Server` header; `virtrdf#` graph; `SP030` error codes). |
| CORS | `Access-Control-Allow-Origin: http://phenomodel.riken.jp` on data responses (the HTML console page sends `*`). |
| Supported forms | SELECT, ASK, CONSTRUCT, DESCRIBE (all verified 200). |
| Error style | Plain text, e.g. `Virtuoso 37000 Error SP030: SPARQL compiler, line 3: syntax error…` |
| Redirect chain | `http://…/pmm/endpoint` →301→ `https://…/pmm/endpoint` →302→ `https://…/pmm/sparql` |

**Minimal working query:**

```bash
curl -sS -G 'https://metabobank.riken.jp/pmm/sparql' \
  --data-urlencode 'format=application/sparql-results+json' \
  --data-urlencode 'query=SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }'
```

```python
from SPARQLWrapper import SPARQLWrapper, JSON
w = SPARQLWrapper("https://metabobank.riken.jp/pmm/sparql", returnFormat=JSON)
w.setMethod("GET")
w.addParameter("format", "application/sparql-results+json")  # mandatory here
w.setQuery("SELECT (COUNT(*) AS ?n) WHERE { GRAPH <http://metadb.riken.jp/db/plantMetabolomics> { ?s ?p ?o } }")
print(w.query().convert())
```

> `SPARQLWrapper` with only `returnFormat=JSON` **fails** with `unknown response content type 'text/html'`. The `addParameter("format", …)` call is required.

---

## 3. Store architecture

### 3.1 Graph inventory

The store is Virtuoso with **58 registered graph IRIs but only 42 non-empty**. Sixteen graphs are declared-but-empty — including all four `structure/*` and all four `system/*` graphs. Note that an *unbound* `GRAPH ?g { ?s ?p ?o }` enumeration **returns the empty graph IRIs too**, which is misleading; always verify with `ASK { GRAPH <g> { ?s ?p ?o } }`.

An important, comforting result: the **default (union) graph equals the exact sum of the 42 non-empty graphs**:

```
sum of 42 per-graph counts = 26,910,989
default-graph COUNT(*)     = 26,910,989   ✓
```

### 3.2 Composition by layer

| Layer | Graph IRIs | Triples | Share |
|---|---:|---:|---:|
| Imported reference ontologies (`/ontology/*`) | 37 | 23,900,516 | **88.8%** |
| RIKEN databases (`/db/*`) | 5 | 3,010,473 | **11.2%** |
| **Total** | **42** | **26,910,989** | 100% |

### 3.3 Largest graphs

| Graph | Triples | % | Subjects | What it is |
|---|---:|---:|---:|---|
| `…/ontology/NCBITaxon` | 12,846,956 | 47.7 | 1,409,906 | NCBI Taxonomy (2018ab) |
| `…/ontology/ChEBI` | 3,858,582 | 14.3 | 619,603 | Chemical Entities of Biological Interest (v122) |
| `…/ontology/EFO` | 1,966,302 | 7.3 | 313,398 | Experimental Factor Ontology (3.8.0) |
| `…/db/SciNetS_ria269i` | 1,888,738 | 7.0 | 433,536 | TAIR GO annotation dataset (legacy SciNetS schema) |
| `…/ontology/GO` | 1,566,090 | 5.8 | 270,499 | Gene Ontology (2017-06-27) |
| `…/ontology/CLO` | 1,207,714 | 4.5 | 389,583 | Cell Line Ontology (2.1.106) |
| `…/ontology/ORDO` | 917,618 | 3.4 | 249,885 | Orphanet Rare Disease (2.3) |
| `…/db/lexvo_org` | 726,674 | 2.7 | 128,945 | Lexvo language/script/character data |
| `…/ontology/UBERON` | 690,041 | 2.6 | 131,475 | Uber-anatomy ontology |
| **`…/db/plantMetabolomics`** | **392,791** | **1.5** | **62,865** | **★ the actual PMM domain data** |
| `…/ontology/MP` | 334,776 | 1.2 | 90,302 | Mammalian Phenotype |
| `…/ontology/ZFA` | 82,469 | 0.3 | 15,435 | Zebrafish Anatomy |

The full list of 42 non-empty graphs and the 16 empty ones is in the appendix.

### 3.4 The 16 registered-but-empty graphs

```
http://localhost:8890/DAV/                          http://metadb.riken.jp/system
http://localhost:8890/sparql                        http://metadb.riken.jp/system/db
http://metadb.riken.jp/db/brainMindsTest            http://metadb.riken.jp/system/ontology
http://metadb.riken.jp/db/brc_jcm                   http://metadb.riken.jp/system/user
http://metadb.riken.jp/db/brc_nbrp_rat              http://www.openlinksw.com/schemas/virtrdf#
http://metadb.riken.jp/structure/DBCatalog          http://www.w3.org/2002/07/owl#
http://metadb.riken.jp/structure/SciNetS_ria269i    http://www.w3.org/ns/ldp#
http://metadb.riken.jp/structure/SciNetS_ria390i
http://metadb.riken.jp/structure/plantMetabolomics
```

**Consequence:** the PMM schema (class/property definitions) lives *inside* `db/plantMetabolomics`, **not** in the `structure/plantMetabolomics` graph, despite the name. Do not query the `structure/*` graphs.

---

## 4. The PMM domain model (`db/plantMetabolomics`)

### 4.1 Schema

The graph contains its own ontology, namespace `http://metadb.riken.jp/ontology/plantMetabolomics/0.1/` (prefix `pmm:`, version **0.1**):

- **89 `rdfs:Class` declarations** (69 in the `pmm:` namespace)
- **137 `rdfs:Property` declarations** (121 in `pmm:`; 127 distinct `pmm:` predicates are actually used in data)
- **25 declared properties are never used**, and **17 declared classes are never instantiated** (see §7)

Class and property definitions carry **bilingual `rdfs:label`s** (`@en` + `@ja`) — e.g. `pmm:Sample` → `"Sample"` / `"サンプル"`.

### 4.2 Core entity chain

The model is a clean ISA-style experimental provenance chain:

```
Project (152)
 ├─ dcmitype:identifier / description / creator / references
 ├─ pmm:principalInvestigator, contactPerson, submitter, fundedBy
 └─ pmm:experiment ──▶ Experiment (175)
                        ├─ pmm:technologyType / technologyPlatform / experimentType
                        ├─ pmm:experimentalDesign ──▶ ExperimentalDesign (166)
                        ├─ pmm:measurement ──▶ Measurement (12,712)
                        │                      ├─ pmm:sampleMeasured ──▶ Sample (9,723)
                        │                      ├─ pmm:measurementCondition ──▶ MeasurementCondition (215)
                        │                      └─ pmm:rawDataset ──▶ RawDataset (8,801)
                        │                                            └─ pmm:file ──▶ File (14,026)
                        └─ pmm:dataAnalysis ──▶ DataAnalysis (208)
                                                 └─ pmm:preProcessing, statisticalDataAnalysis

Sample (9,723) ──pmm:biologicalSample──▶ BiologicalSample (9,109)
   BiologicalSample: speciesName, RO_0002162 (in taxon), plantOrgan (PO),
   cultivar/genotype/mutant/transgenicLine, growthCondition, growthSupport,
   growthLocation, dayLength/darkLength, temperature, lightCondition,
   nutritionalRegime, samplingDate/samplingTime, treatment (PO/Treatment)
RawDataset (8,801) ──pmm:file──▶ File (14,026)
   File: downloadURL, md5, fileFormat   (+ subclass MassSpectralFile 1,410)
```

### 4.3 Instance counts (PMM graph)

| Class | Instances | | Class | Instances |
|---|---:|---|---|---:|
| `pmm:File` | 14,026 | | `pmm:DataAnalysis` | 208 |
| `pmm:Measurement` | 12,712 | | `pmm:MassSpectrometry` | 197 |
| `pmm:Sample` | 9,723 | | `pmm:SamplePreparation` | 187 |
| `pmm:BiologicalSample` | 9,109 | | `pmm:Experiment` | 175 |
| `pmm:RawDataset` | 8,801 | | `pmm:ExperimentalDesign` | 166 |
| `pmm:MassSpectralFile` | 1,410 | | `pmm:Chromatography` | 163 |
| `pmm:Temperature` | 288 | | `pmm:Project` | 152 |
| `pmm:MeasurementCondition` | 215 | | `pmm:Compound` | 115 |

### 4.4 Two project families

The 152 projects split into two structurally different families:

| Family | Projects | Experiments | Measurements | Files | Publications |
|---|---:|---:|---:|---:|---:|
| `RPMM####` | 64 | 85 | 9,676 | **14,026** | 65 |
| `MN_SE###` | 88 | 88 | 3,014 | **0** | 5 |
| **Total** | **152** | **175** | **12,712** | **14,026** | **70** |

- **`RPMM`** projects are the full curated layer: they carry data files, MD5 hashes, download URLs, instrument metadata, and publication links.
- **`MN_SE`** projects (from the *Metabolonote* system) carry measurement/sample metadata but **no files** — they are metadata-only entries.

Projects are also cross-referenced to **80 distinct PubMed records** (`http://rdf.ncbi.nlm.nih.gov/pubmed/…`). Project titles are full publication titles and contain embedded HTML (`<i>`, `<sup>`) — consumers must strip markup.

### 4.5 Biological content

**Species: 169 distinct taxa** (`RO_0002162` → `purl.bioontology.org/ontology/NCBITAXON/<id>`). Top taxa:

| Samples | Taxon ID | Species |
|---:|---|---|
| 3,694 | 3702 | *Arabidopsis thaliana* |
| 2,125 | 4530 | *Oryza sativa* (rice) |
| 1,252 | 4081 | *Solanum lycopersicum* (tomato) |
| 221 | 157934 | *Ophiorrhiza pumila* |
| 199 | 4236 | *Lactuca sativa* (lettuce) |
| 175 | 15368 | *Brachypodium distachyon* |
| 170 | 3847 | *Glycine max* (soybean) |
| 99 | 3708 | *Brassica napus* |
| 87 | 1148 | *Synechocystis* sp. PCC 6803 |
| 80 | 47664 | *Populus tremula* × *P. tremuloides* |

A parallel free-text property `pmm:speciesName` (9,091 statements) duplicates this as **HTML-italicised strings** (`"<i>Arabidopsis thaliana</i>"`), with trailing-space inconsistencies (`"<i> Arabidopsis thaliana</i>"`, 49×) and typos (`"Physalis alkekengi i var. franchetii"`). Prefer `RO_0002162` + `skos:prefLabel` joins over the literal.

**Plant organs** use Plant Ontology IRIs (`pmm:plantOrgan` → `PO_*`). Top: `PO_0009006` shoot system (3,031), `PO_0025034` leaf (981), `PO_0009001` fruit (937), `PO_0000003` whole plant (727), `PO_0009005` root (514). The `pmm:PlantOrgan` class is declared but has **0 instances** — organs are referenced as external PO IRIs only.

**Analytical platforms** (`pmm:technologyPlatform`, 262): GC-MS (62), MS (88), chromatography (87), LC-MS (23), CE-MS (1), LC-PDA (1). `pmm:massAnalyser`: FT-ICR (93), TOF (50), Q-TOF (30), LTQ-Orbitrap (14), QqQ (7). **23 distinct instruments**, e.g. `MN_MS_FT1` (91), `MN_HPLC1` (73), `GC_Agilent6890N` (47).

### 4.6 Data files — verifiably real

| Metric | Value |
|---|---:|
| Files | 14,026 |
| Files with `md5` / `downloadURL` / `fileFormat` | 15,414 subjects each |
| Distinct download URLs | 15,414 |
| **Live HTTP HEAD check on 6 random URLs** | **all `200 OK`, ~102 MB each** |

Formats: `application/x-cdf` (9,108, GC-MS NetCDF), `application/x-abf` (5,931, AB SCIEX), `text/plain` (215), `application/zip` (79), `text/csv` (70), `application/vnd.ms-excel` (16).

Download URLs follow `http://metabobank.riken.jp/data/RPMM####/RawDataset/<name>.cdf` (note: data host `metabobank`, IRI namespace host `metadb`). Effortless to dereference.

### 4.7 Units and quantities

753 quantity nodes use the **QUDT** pattern (`qudt:unit` + `rdf:value`). Units are mixed between authoritative UO IRIs (`UO_0000027`, `UO_0000018`, …) and locally minted ones (`…/plantMetabolomics/0.1/Unit/milliliter_per_minute`, `…/Unit/kilo_electronvolt`).

---

## 5. The other non-ontology databases

| Graph | Triples | Content |
|---|---:|---|
| `…/db/SciNetS_ria269i` | 1,888,738 | **TAIR GO annotations** for *Arabidopsis* genes. Legacy SciNetS encoding: opaque property IRIs `pria269u1i`–`u6i` (locus, evidenceCode, relationshipType, GO, GOslimTerm, reference). Class `…/cria269s1i` has 181,900 instances. |
| `…/db/lexvo_org` | 726,674 | Lexvo: languages, scripts, geographic regions, characters. Source of most of the store's 300+ language tags. |
| `…/db/DBCatalog` | 2,178 | The **RIKEN Database Catalog** ("理研データベース電話帳"): 128 `void:Dataset` records, 90 PubMed refs, 26 RIKEN organisations, BioTarget/BioDataType vocabularies. 269 dataset rows after multilingual expansion. |
| `…/db/SciNetS_ria390i` | 92 | Tiny SciNetS fragment. |

The `DBCatalog` is a **catalog of RIKEN's broader database landscape** (FANTOM3, AtGenExpress, BRC biResources, IMPC, NBRP medaka, …) with Japanese/English `rdfs:label`s and `dcterms:description`s. It is *not* PMM-specific.

---

## 6. Vocabulary and provenance

### 6.1 Predicate namespaces (top, whole store)

| Namespace | Predicates | Triples |
|---|---:|---:|
| `rdf:` | 4 | 4,450,275 |
| `bioportal…/umls/` | 3 | 4,229,994 |
| `owl:` | 34 | 4,203,808 |
| `rdfs:` | 11 | 3,182,257 |
| `skos:` | 6 | 2,979,243 |
| `purl.bioontology.org/ontology/NCBITAXON/` | 2 | 2,819,528 |
| `oboInOwl#` | 92 | 2,761,436 |
| **`…/ontology/plantMetabolomics/0.1/`** | **127** | **247,214** |
| `lexvo.org/ontology#` | 13 | 394,217 |
| `purl.obolibrary.org/obo/` | 90 | 373,044 |

### 6.2 Ontology provenance

Most ontology graphs carry an `owl:Ontology` header with `owl:versionIRI`/`versionInfo`, showing **2017-era snapshots**:

| Graph | Version / release |
|---|---|
| NCBITaxon | 2018ab |
| ChEBI | 122 |
| EFO | 3.8.0 |
| GO | `go/releases/2017-06-27` |
| UBERON | `releases/2017-05-29` |
| CL | `releases/2017-04-14` |
| MP | `releases/2017-06-21` |
| MA | `releases/2016-12-21` |
| RO | `releases/2017-06-15` |
| ZFA | `releases/2017-06-06` |
| CMO / MMO | 2.40 / 2.27 |
| ORDO | 2.3 |
| CLO / SIO / STATO | 2.1.106 / 1.36.0 / 1.2 |
| MCCV / MEO / MPO / CSSO | 0.96b / 0.7 / 0.5a / 0.6 |

**No licence metadata** (`dcterms:license`) and almost no ontology-level `dcterms:date` is present. The site footer applies **CC BY 4.0** to the PMM work.

### 6.3 Language tags

Whole store: 11,697,450 untagged, **2,071,549 `@en`**, 3,334 `@ja`, then a long tail of 300+ languages from Lexvo.

PMM graph specifically: 130,428 untagged, **57,735 `@en`**, **1,295 `@ja`**. Bilingual labels exist for classes/properties, but the *data* (project titles, descriptions) is overwhelmingly English-only.

### 6.4 Datatypes (PMM graph)

`xsd:string` 111,255 · plain 59,030 · `xsd:anyURI` 15,615 · `xsd:date` 2,805 · `xsd:float` 753.

---

## 7. Data-quality and interoperability findings

Ordered by severity for a downstream consumer:

1. **DC namespace misuse (high).** Domain metadata uses `http://purl.org/dc/dcmitype/` for *properties*: `dcmitype:identifier` (10,554), `dcmitype:description` (5,717), `dcmitype:references` (103), `dcmitype:creator` (100). `dcmitype` is the DCMI *Type* vocabulary (`dcmitype:Dataset`, `dcmitype:Image`); these should be `dcterms:identifier` etc. Any standard Dublin Core consumer will miss all core PMM metadata.

2. **Date typed as `xsd:date` but valued as datetime.** `pmm:dateOfPlantEstablishment` (1,598) and `pmm:samplingDate` (1,207) return values like `"2006-04-04+09:00"`, which is not a valid `xsd:date` lexical form. Date arithmetic will fail.

3. **Schema/data drift in URIs.** `RawDataSet` (2,776) vs `RawDataset` (79); `MassSpectraFile` (426) vs `MassSpectralFile`; `MassSpectometry` (60) — typos persisted as class names. Instance types use `RawDataset`/`MassSpectralFile`, while paths use the other spellings, so string-matching on either is unsafe.

4. **Casing inconsistency in values.** `pmm:ionMode`: `"Positive"` 157, `"positive"` 13, `"Positive and Negative"` 2, `"positive and negative"` 3. `fileFormat`: `application/x-abf` 5,931 vs `application/x-ABF` 77.

5. **Duplicate-but-divergent labels / multilingual duplication.** Some catalog resources carry 2–6 `rdfs:label`s (en/ja variants); naive `?s rdfs:label ?l` joins multiply rows. The `DBCatalog` expands 128 datasets to 269 rows.

6. **HTML fragment literals.** Project titles/descriptions and `pmm:speciesName` contain raw `<i>`, `<sup>`, `<sub>` markup.

7. **Declared-but-unused schema (25 properties, 17 classes).** Unused properties include `publicRelaseDate`, `qualityControl`, `subProject`, `material`, `plantTissue`, `orcid`, `normalisationDataMatrixFile`. Unused classes include `Dataset`, `Folder`, `Material`, `Person`, `Organization`, **and misspelled declarations** `Metarial`, `ExperimenalFactor`, `SampleExtractionProtorol`, `StatisticalDataAnalsis`, `MassSpectometry`, `NormalisationDataMatrixFile`, `Orcid`, `Pressure`.

8. **Orphan subjects.** 301,501 distinct subjects in the store have **no `rdf:type`** — 7.2% of all subjects.

9. **Empty declared graphs.** 16 graph IRIs (including all `structure/*` and `system/*`) exist in the registry but contain no triples, and unbound `GRAPH ?g` enumeration silently includes them.

10. **`pmm:Person` vs `foaf:Person`.** Person resources are typed `foaf:Person` (168), while the schema declares an unused `pmm:Person` class; subject paths use `/Person/`. Same pattern for organisations (`org:Organization`, 82).

11. **File typing is incomplete.** Only 14,026 resources are typed `pmm:File`, but 15,414 subjects carry `md5`/`downloadURL`/`fileFormat`, and 14,046 files are reachable via the `experiment/measurement/rawDataset/file` chain. Relying on `?f a pmm:File` therefore **undercounts the data files by ~1,400**.

---

## 8. Coverage and gaps

- **Metadata-only projects.** 88 of 152 projects (`MN_SE*`) have zero associated files — 58% of projects are metadata-only.
- **Sparse optional fields.** Bottom of the property-population distribution: `summarisationType` (1), `flowRateCondition` (4), `summarisation` (6), `massAccuracy` (6), `parameters` (7), `experimenter` (10), `orcid` (0 — declared unused).
- **No licence/attribution triples** inside PMM data despite CC BY 4.0 on the site.
- **Ontology freshness.** Reference ontologies are ~2017–2018 snapshots; ChEBI v122 and NCBITaxon 2018ab are both years behind current releases. Expect stale chemical/taxonomic resolution.
- **Publication coverage.** 70 project→PubMed links across 152 projects, i.e. **~46% of projects have a linked paper** (65/64 RPMM, 5/88 MN_SE).

---

## 9. Practical recipes

**Scope every query to the domain graph** — otherwise you query 26.9M triples of imported ontology.

```sparql
# Projects with their title, species and file count
PREFIX pmm: <http://metadb.riken.jp/ontology/plantMetabolomics/0.1/>
SELECT ?project ?title ?prefLabel (COUNT(DISTINCT ?file) AS ?files) WHERE {
  GRAPH <http://metadb.riken.jp/db/plantMetabolomics> {
    ?project a pmm:Project ; rdfs:label ?title ;
             pmm:experiment ?experiment .
    OPTIONAL {
      ?experiment pmm:measurement ?measurement .
      ?measurement pmm:sampleMeasured ?sample .
      ?sample pmm:biologicalSample ?bs .
      ?bs pmm:speciesName ?prefLabel .
    }
    OPTIONAL {
      ?experiment pmm:measurement ?m2 .
      ?m2 pmm:rawDataset ?raw .
      ?raw pmm:file ?file .
    }
  }
} GROUP BY ?project ?title ?prefLabel ORDER BY DESC(?files) LIMIT 20
```

> Verified: the project→file traversal is `pmm:experiment / pmm:measurement / pmm:rawDataset / pmm:file`
> (reachable files: 14,046). Do **not** use `pmm:resultantRowDataset` — it is declared in the schema but unused.
> Project/experiment/measurement counts in this report come from `?p a pmm:Project ; pmm:experiment/pmm:measurement ?m`.

**Resolve species names (join the ontology graph):**

```sparql
SELECT ?prefLabel (COUNT(?sample) AS ?n) WHERE {
  GRAPH <http://metadb.riken.jp/db/plantMetabolomics> {
    ?sample <http://purl.obolibrary.org/obo/RO_0002162> ?taxon }
  GRAPH <http://metadb.riken.jp/ontology/NCBITaxon> {
    ?taxon <http://www.w3.org/2004/02/skos/core#prefLabel> ?prefLabel }
} GROUP BY ?prefLabel ORDER BY DESC(?n)
```

**Harvest downloadable files:**

```sparql
SELECT ?file ?url ?md5 ?format WHERE {
  GRAPH <http://metadb.riken.jp/db/plantMetabolomics> {
    ?file a <http://metadb.riken.jp/ontology/plantMetabolomics/0.1/File> ;
          <http://metadb.riken.jp/ontology/plantMetabolomics/0.1/downloadURL> ?url ;
          <http://metadb.riken.jp/ontology/plantMetabolomics/0.1/md5> ?md5 .
    OPTIONAL { ?file <…/fileFormat> ?format } } }
```

**Pitfalls to encode in your client:**
- Always pass `format=application/sparql-results+json`; use GET.
- Wrap the domain graph explicitly; do not rely on the default graph.
- Treat `pmm:identifier`/`pmm:description` as living under `dc/dcmitype/`, not `dcterms`.
- Do not filter `pmm:publicRelaseDate` (unused); use `pmm:samplingDate` / `pmm:dateOfPlantEstablishment`.

---

## 10. Reproducibility

All scripts and raw outputs are in the workspace:

| File | Purpose |
|---|---|
| [investigation/sparql.py](investigation/sparql.py) | Query harness (GET + `format` param, on-disk cache, retries) |
| [investigation/01_recon.py](investigation/01_recon.py) | Scale, predicates, classes, graphs |
| [investigation/02_graphs.py](investigation/02_graphs.py) | Graph inventory and sizes |
| [investigation/03_pmm_domain.py](investigation/03_pmm_domain.py) | PMM domain graph deep dive |
| [investigation/04_structure_catalog.py](investigation/04_structure_catalog.py) | Structure/catalog/system graphs |
| [investigation/05_vocab_literals.py](investigation/05_vocab_literals.py) | Vocabulary, literals, languages, datatypes |
| [investigation/06_catalog_schema.py](investigation/06_catalog_schema.py) | Dataset catalog + PMM schema inventory |
| [investigation/07_content.py](investigation/07_content.py) | Projects, species, organs, platforms, files |
| [investigation/08_followups.py](investigation/08_followups.py) | Species labels, dates, link liveness |
| [investigation/09_report_data.py](investigation/09_report_data.py) | Report aggregates |
| [investigation/10_final.py](investigation/10_final.py) | Family comparison, unused terms, versions |
| `investigation/out0*.txt` | Captured outputs |

Environment: `.venv-sparql` created with `/Users/knishida/.local/bin/uv` (`UV_CACHE_DIR` redirected into the workspace). Run with `../.venv-sparql/bin/python <script>` from `investigation/`.

---

## 11. Verdict

The endpoint is a **healthy, high-value, but sharply skewed** data source. It is best understood as *"a bag of RIKEN reference ontologies with the Plant Metabolome Metadatabase tucked inside"*.

For PMM work it is genuinely useful: 152 curated projects, ~12.7k measurements, ~9.1k characterised biological samples across 169 plant taxa, and 14k data files with verified MD5s and **live** download links. The main risks are practical, not structural: you must scope queries to `db/plantMetabolomics`, tolerate the `dc/dcmitype` namespace misuse, and normalise casing and URI-spelling drift before trusting aggregates.

---

## Appendix A — Full non-empty graph list (42)

```
TRIPLES     GRAPH
12846956    http://metadb.riken.jp/ontology/NCBITaxon
 3858582    http://metadb.riken.jp/ontology/ChEBI
 1966302    http://metadb.riken.jp/ontology/EFO
 1888738    http://metadb.riken.jp/db/SciNetS_ria269i
 1566090    http://metadb.riken.jp/ontology/GO
 1207714    http://metadb.riken.jp/ontology/CLO
  917618    http://metadb.riken.jp/ontology/ORDO
  726674    http://metadb.riken.jp/db/lexvo_org
  690041    http://metadb.riken.jp/ontology/UBERON
  392791    http://metadb.riken.jp/db/plantMetabolomics
  334776    http://metadb.riken.jp/ontology/MP
   82469    http://metadb.riken.jp/ontology/ZFA
   69810    http://metadb.riken.jp/ontology/CL
   65242    http://metadb.riken.jp/ontology/ZP
   44460    http://metadb.riken.jp/ontology/CHMO
   41276    http://metadb.riken.jp/ontology/CMO
   40757    http://metadb.riken.jp/ontology/SO
   35119    http://metadb.riken.jp/ontology/MFO
   28880    http://metadb.riken.jp/ontology/PATO
   25413    http://metadb.riken.jp/ontology/MA
   13846    http://metadb.riken.jp/ontology/STATO
   11986    http://metadb.riken.jp/ontology/MPATH
   10514    http://metadb.riken.jp/ontology/SIO
    8213    http://metadb.riken.jp/ontology/MMO
    7051    http://metadb.riken.jp/ontology/EO
    5012    http://metadb.riken.jp/ontology/UO
    4697    http://metadb.riken.jp/ontology/PCT
    4468    http://metadb.riken.jp/ontology/MEO
    4425    http://metadb.riken.jp/ontology/RO
    3478    http://metadb.riken.jp/ontology/CSSO
    2178    http://metadb.riken.jp/db/DBCatalog
    1551    http://metadb.riken.jp/ontology/MPO
    1229    http://metadb.riken.jp/ontology/BFO
     781    http://metadb.riken.jp/ontology/ISA
     781    http://metadb.riken.jp/ontology/manufacturing
     707    http://metadb.riken.jp/ontology/MCCV
     232    http://metadb.riken.jp/ontology/FALDO
      92    http://metadb.riken.jp/db/SciNetS_ria390i
      37    http://metadb.riken.jp/ontology/LU
       1    http://metadb.riken.jp/ontology/OBI
       1    http://metadb.riken.jp/ontology/ENVO
       1    http://metadb.riken.jp/ontology/PO
```

## Appendix B — PMM entity-chain predicates (used, by frequency)

```
62885  rdf:type                        44982  rdfs:label
15499  pmm:md5                         15499  pmm:downloadURL
15499  pmm:fileFormat                  14878  pmm:file
12786  pmm:sampleMeasured              12690  pmm:measurement
12413  pmm:measurementCondition        10554  dc/dcmitype:identifier
 9890  pmm:biologicalSample             9154  pmm:rawDataset
 9108  RO_0002162 (in taxon)            9091  pmm:speciesName
 8872  pmm:plantOrgan                   8730  pmm:samplePreparation
 7127  pmm:growthCondition              6808  pmm:growthSupport
 6802  pmm:developmentStage             6415  rdfs:comment
 6284  pmm:growthLocation               5864  pmm:dayLength
 5720  pmm:darkLength                   5717  dc/dcmitype:description
 5312  pmm:metabolismQuenchingMethod    4950  pmm:sampleStorage
 4822  pmm:genotype                     4256  pmm:lightCondition
 4110  pmm:temperature                  3957  pmm:nutritionalRegime
 3615  pmm:cultivar                     3153  rdfs:seeAlso
 2562  pmm:samplingLocation             2475  pmm:wateringRegime
 1933  pmm:mutant                       1876  pmm:samplingTime
```
