# Criminal Network Analysis System

**Smart India Hackathon 2026 · Problem ID 26189 · Ministry of Home Affairs (NCRB)**

An AI-powered platform that unifies FIRs, call detail records, financial
transactions and criminal records into a single knowledge graph — then uses
network analysis and a large language model to surface hidden connections,
rank suspects by risk, flag anomalies, and answer investigators' questions in
plain language, backed by evidence.

---

## Table of contents

- [The problem](#the-problem)
- [What this system does](#what-this-system-does)
- [How it works](#how-it-works)
- [Architecture](#architecture)
- [Setup — from a fresh machine](#setup--from-a-fresh-machine)
- [Starting and stopping](#starting-and-stopping)
- [Loading demo data](#loading-demo-data)
- [Using the dashboard](#using-the-dashboard)
- [Running without Docker](#running-without-docker)
- [Functionality reference](#functionality-reference)
- [API reference](#api-reference)
- [How risk scoring works](#how-risk-scoring-works)
- [Sample data](#sample-data)
- [Troubleshooting](#troubleshooting)
- [Repository layout](#repository-layout)

---

## The problem

Police data is siloed. An FIR filed in Mumbai, a call record dump from a
telecom operator, and a bank statement each live in a separate system. Nobody
can see that a phone number named in the Mumbai FIR called a number belonging
to a suspect in an unrelated Delhi case — so the link between the two
investigations is never found, or is found months later by hand.

Cross-referencing that manually takes weeks per case, and it does not scale to
the volume of records a real investigation produces.

## What this system does

It pulls every source into **one graph**. People, phones, vehicles, bank
accounts, locations, organisations and cases all become nodes; every
relationship between them becomes an edge.

Once the data is a graph, questions that used to take weeks become queries:

- *Who connects these two cases?* → shortest path between two nodes
- *Who is the most important person in this network?* → centrality
- *Which people form a group?* → community detection
- *Which transactions look like laundering?* → anomaly detection
- *How is A connected to B?* → asked in plain English, answered from evidence

**The core trick** — and the thing worth understanding before a demo — is the
*person projection*. The analysis service collapses the full graph so that
**two people are linked if they share *any* intermediate entity**: a phone, an
FIR, a bank account.

> Two men never called each other and were never charged together. But both
> used the same handset. The projection links them. **That edge is the
> finding.**

---

## How it works

An investigator drags one FIR into the dashboard. That single action drives
the entire chain:

**1 · Ingest** — the **backend** (`:8000`) saves the raw file to disk, extracts
its text (PDF or plain text), and creates a database record. The original file
is always kept, so evidence is never lost to a parsing bug.

**2 · Extract** — the **NLP service** (`:8001`) reads the text and pulls out
entities using two complementary methods:

| Method | Finds | Why |
|---|---|---|
| **Regex** | phones, vehicle plates, PAN, Aadhaar, bank accounts, IFSC, IPC sections, amounts | Structured formats — near-perfect precision |
| **spaCy NER** | person names, locations, organisations | Unstructured language — no fixed pattern exists |

It also infers each person's **role** from surrounding words: *"arrested"* →
accused, *"complainant"* → victim, *"witness"* → witness.

**3 · Clean and resolve** — the backend corrects what NER gets wrong before
anything reaches the graph. It drops candidates containing digits or matching
a registration plate, drops names that only ever appear behind a locative cue
("resident of X", "Police Station: X"), drops the investigating officer, reads
the complainant from the FIR's own wording, and attributes each phone and
account to **the person named nearest to it in the text** — not to whoever
happened to be named first.

**4 · Build the graph** — the **graph service** (`:8002`) writes it into Neo4j:

```cypher
(Ravi Kumar)-[:USES_PHONE]->(9876543210)
(Ravi Kumar)-[:ACCUSED_IN]->(FIR 001/2024)
(Suresh Patel)-[:COMPLAINANT_IN]->(FIR 001/2024)
(Anita Roy)-[:OWNS_ACCOUNT]->(918273645510)
(9876543210)-[:CALLED {count: 3}]->(9765432108)
(Ravi Kumar)-[:CO_ACCUSED_WITH]->(Mohammad Ali)
```

Everyone named in the same FIR is automatically cross-linked as co-accused.

**5 · Analyse** — the **analysis service** (`:8003`) loads the graph into
NetworkX and runs centrality, community detection, anomaly detection and risk
scoring.

**6 · Answer** — the **AI service** (`:8004`) classifies what the investigator
is asking, retrieves only the relevant evidence from the graph and the
analysis service in parallel, and hands it to Gemini under a strict
*"answer only from this evidence"* instruction.

### Node and relationship types

| Nodes | Relationships |
|---|---|
| `Person` `Phone` `Vehicle` `BankAccount` `Location` `Organization` `FIR` `Case` | `USES_PHONE` `OWNS_ACCOUNT` `CALLED` `TRANSFERRED_TO` `ACCUSED_IN` `COMPLAINANT_IN` `WITNESS_IN` `CO_ACCUSED_WITH` `MENTIONED_IN` `RELATED_TO` |

---

## Architecture

```
                        INVESTIGATOR'S BROWSER
                    React Dashboard (M5) — :5173
        [Network Graph] [Risk Table] [Cases] [Upload] [AI Chat]
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
  Backend (M1)            Graph Service (M3)        AI Service (M6)
  :8000                   :8002                     :8004
  FastAPI + Postgres      FastAPI + Neo4j           FastAPI + Gemini
        │                        │                        │
        ▼                        ▼                        │
  NLP Service (M2) ────────> Analysis Service (M4) <───────┘
  :8001                     :8003
  spaCy + regex             NetworkX + scikit-learn
        │
        ▼
  ┌──────────────────────────────────────┐
  │ PostgreSQL  structured evidence      │
  │ MongoDB     raw documents            │
  │ Neo4j       the knowledge graph      │
  │ Redis       caching                  │
  └──────────────────────────────────────┘
```

| Member | Service | Directory | Port | Stack |
|--------|---------|-----------|------|-------|
| 1 | Backend & Ingestion | `backend/` | 8000 | FastAPI · SQLAlchemy · PostgreSQL |
| 2 | NLP & Entity Extraction | `nlp_service/` | 8001 | FastAPI · spaCy · regex |
| 3 | Knowledge Graph | `graph_service/` | 8002 | FastAPI · Neo4j |
| 4 | Network Analysis & ML | `analysis_service/` | 8003 | FastAPI · NetworkX · scikit-learn |
| 5 | Dashboard | `frontend/` | 5173 | React · Vite · Cytoscape.js |
| 6 | AI Assistant | `ai_service/` | 8004 | FastAPI · Gemini · ChromaDB |

Infrastructure ports: PostgreSQL `5432`, MongoDB `27017`, Neo4j bolt `7687`
and browser `7474`, Redis `6379`.

Every service exposes `/health` and interactive API docs at `/docs`.

---

## Setup — from a fresh machine

### 1 · Prerequisites

| Tool | Version | Needed for |
|---|---|---|
| **Docker Desktop** | 20.10+ | Everything. This is the only hard requirement. |
| Python | 3.11+ | Running `health_check.py` / `data_pipeline.py` on the host |
| Node.js | 20+ | Only if running the frontend outside Docker |
| Git | any | Cloning |

Verify Docker is installed **and running** — this trips people up, because
the CLI works while the daemon is stopped:

```bash
docker --version
docker compose version
docker info > /dev/null && echo "Docker daemon OK" || echo "Start Docker Desktop"
```

### 2 · Get the code

```bash
git clone <your-repo-url>
cd the-criminal-record-analysis-main
```

### 3 · Create your environment file

```bash
cp .env.example .env
```

Open `.env` and set one value:

```env
GEMINI_API_KEY=your-key-here
```

Get a free key at **https://aistudio.google.com/**.

> **Only the AI chat needs this key.** Ingestion, the knowledge graph,
> analytics and the dashboard all work fully without one — the assistant will
> just reply that it is not configured. Nothing else breaks.

Every other value in `.env` already points at the containers Docker starts, so
leave them alone unless you are running services on the host.

### 4 · Build and start

```bash
docker compose up --build -d
```

The first build downloads Python images, spaCy models and PyTorch. **Expect
5–15 minutes.** Later starts take seconds.

### 5 · Wait for Neo4j, then verify

Neo4j needs roughly 30 seconds before it accepts connections, and the backend,
graph and analysis services wait on its health check. Then:

```bash
python integration/health_check.py
```

Expected:

```
[OK]   Backend (M1): running at http://localhost:8000/health
[OK]   NLP (M2): running at http://localhost:8001/health
[OK]   Graph (M3): running at http://localhost:8002/health
[OK]   Analysis (M4): running at http://localhost:8003/health
[OK]   Frontend (M5): running at http://localhost:5173
[OK]   AI Chat (M6): running at http://localhost:8004/health

ALL SYSTEMS GO
```

If `requests` is missing on your host:
`pip install requests`, or run `docker compose ps` to check container state
instead.

### 6 · Load data and open the dashboard

```bash
python integration/data_pipeline.py
```

Then open **http://localhost:5173**.

---

## Starting and stopping

A `Makefile` wraps the common commands — run `make help` to list them.

| Command | What it does |
|---|---|
| `make up` | Build if needed and start everything, detached |
| `make down` | Stop all containers. **Your data survives.** |
| `make ps` | Show container status |
| `make logs` | Tail logs from every service |
| `make health` | Check all six `/health` endpoints |
| `make pipeline` | Load the sample scenario end to end |
| `make infra` | Start only the databases (Neo4j, Postgres, Mongo, Redis) |
| `make restart` | Rebuild and restart everything |
| `make clean` | Stop **and delete all data volumes** — a full reset |

Equivalent Docker commands if you prefer them:

```bash
docker compose up -d                    # start
docker compose down                     # stop, keep data
docker compose down -v                  # stop, WIPE all data
docker compose logs -f graph_service    # follow one service
docker compose up -d --build backend    # rebuild one service after a code change
docker compose restart analysis_service # restart without rebuilding
```

### After changing code

- **Frontend** — nothing to do. The source is live-mounted and Vite hot-reloads.
- **Any Python service** — `docker compose up -d --build <service>`.

### Data persistence

Postgres, Mongo and Neo4j write to Docker volumes, so data survives `make down`
and machine restarts. Only `make clean` (`docker compose down -v`) erases it —
after which `make pipeline` reloads the sample scenario.

---

## Loading demo data

```bash
make pipeline
```

This runs the full investigator flow and prints what each stage produced:
creates a case, uploads two FIRs plus call records and transactions, verifies
the graph, runs the analysis, and asks the AI a question.

With the bundled sample data it yields roughly:

```
Nodes: 48   Relationships: 86
  Phone 13 · BankAccount 10 · Person 8 · Location 7 · Organization 7 · FIR 2 · Vehicle 1

Communities: 2      Transactions flagged: 12      Call patterns flagged: 11

Mohammad Ali    94.0  CRITICAL     ← named in BOTH FIRs; the bridge
Imran Sheikh    57.8  HIGH
Farhan Qureshi  37.8  MEDIUM
Ravi Kumar      28.2  MEDIUM
Suresh Patel     3.2  LOW          ← correctly identified as the victim
```

To reset and reload:

```bash
make clean && make up && make pipeline
```

---

## Using the dashboard

Open **http://localhost:5173**.

| Page | What it shows |
|---|---|
| **Overview** `/` | Stat cards, ranked risk table, detected groups, network panel |
| **Network Graph** `/graph` | Type a name to centre the graph; click any node to re-centre |
| **Cases** `/cases` | Case list with FIR / call / transaction counts |
| **Upload** `/upload` | Drag-and-drop FIRs, CDR CSVs and transaction CSVs |
| **AI Chat** `/chat` | Ask questions in plain English |
| **Map** `/map` | Currently empty — see note below |

**Searching names is forgiving.** `imran`, `IMRAN` and `sheikh` all resolve to
`Imran Sheikh`. Exact, case-insensitive and partial matches are tried in that
order; a genuine miss returns the available names as suggestions.

Questions worth asking the AI:

```
Who are the top suspects in this network?
How is Ravi Kumar connected to Imran Sheikh?
What suspicious financial patterns exist?
Show me the criminal groups detected.
```

> **The Map page is intentionally blank.** `MapPage.jsx` has a hardcoded
> `locations = []`. `Location` nodes exist in the graph but nothing geocodes
> them into coordinates yet — this feature is unbuilt, not broken.

---

## Running without Docker

Each service is a standalone FastAPI app. You still need Neo4j:

```bash
docker compose up -d neo4j postgres      # or just neo4j
```

Then, in separate terminals:

```bash
# Backend — falls back to a local SQLite file if DATABASE_URL is unset
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# NLP — installs the spaCy model from a pinned URL
cd nlp_service && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Graph
cd graph_service && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002

# Analysis
cd analysis_service && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003

# AI assistant
cd ai_service && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8004

# Dashboard
cd frontend && npm install && npm run dev
```

Copy each service's `.env.example` to `.env` first. The frontend reads
`VITE_*` variables if you need to repoint it at non-default hosts.

---

## Functionality reference

### Backend — evidence ingestion (`:8000`)
- Case create / list / read / delete, with auto-generated case numbers
- FIR upload (PDF and plain text), CDR upload, transaction upload
- CSV parsing that tolerates varied headers — `caller` / `a_party` / `from`
  and `amount` / `value` / `txn_amount` all work
- Raw files preserved on disk under `uploads/`
- Entity cleanup: officer, place-name and non-person filtering
- Phone and account attribution by text proximity
- Read-only record APIs consumed by the analysis service
- Degrades gracefully: if NLP or the graph is down, the upload still succeeds
  and the response carries an explicit warning

### NLP — entity extraction (`:8001`)
- Nine regex extractors: phone, vehicle, Aadhaar, PAN, bank account, IFSC,
  email, amount, date
- spaCy NER for persons, locations, organisations, dates
- IPC section detection and crime-keyword matching
- Role inference (accused / victim / witness / associate)
- FIR header parsing (FIR number, police station)
- CDR pattern analysis, and a batch endpoint for bulk documents
- Runs without the spaCy model installed — regex extraction continues working

### Graph — knowledge graph (`:8002`)
- Builders for Person, Phone, Case, FIR, BankAccount nodes
- Ego-network retrieval at depth 1–4
- Shortest path between any two people
- Fuzzy entity search across every named node
- Node and relationship statistics
- Automatic co-accused cross-linking
- Shared-identifier detection (two people, one handset)
- Legacy `/analytics/*` routes powering the standalone HTML dashboard

### Analysis — network science and ML (`:8003`)
- **Four centrality measures**, each answering a different question:
  *degree* (busiest), *betweenness* (brokers and couriers), *closeness*
  (fastest reach), *eigenvector* (connected to other important people, with a
  PageRank fallback when it will not converge)
- **Community detection** via greedy modularity maximisation, reporting group
  size, cohesion and the likely ringleader
- **Transaction anomalies** — see the flags below
- **Communication anomalies** — `HUB_NUMBER`, `HIGH_FREQUENCY`,
  `ODD_HOUR_PATTERN`, `BURST_SHORT_CALLS`
- **Explainable risk scoring** for every person
- Graph is cached briefly, since the dashboard hits several endpoints at once

**Transaction flags** — rules *and* ML, deliberately. The rules are
defensible in court; the model catches shapes the rules do not describe.

| Flag | Meaning |
|---|---|
| `STRUCTURING_BELOW_THRESHOLD` | ₹9–10 lakh — deliberately under the reporting limit |
| `PASS_THROUGH_ACCOUNT` | Money in ≈ money out — a mule |
| `LARGE_VALUE` | At or above ₹10,00,000 |
| `STATISTICAL_OUTLIER` | Above mean + 2σ |
| `ODD_HOUR_TRANSFER` | Between 00:00 and 05:59 |
| `ML_ANOMALY` | IsolationForest over amount, hour and account flow volumes |

### AI assistant — grounded Q&A (`:8004`)
- Intent classification routes each question to the right data sources
- Parallel retrieval from graph, analysis and backend
- Optional semantic search over free-text evidence (ChromaDB + sentence
  transformers), degrading silently if unavailable
- Multi-turn chat with per-conversation memory, so concurrent users do not
  corrupt each other's history
- System prompt forbids inventing facts and requires citing the source

---

## API reference

**Backend — `:8000`**
```
GET    /health
POST   /cases/                      create a case
GET    /cases/                      list cases
GET    /cases/{id}                  one case
GET    /cases/{id}/summary          case with evidence counts
DELETE /cases/{id}
POST   /upload/fir                  upload an FIR — drives the whole pipeline
POST   /upload/call-records         upload a CDR CSV
POST   /upload/transactions         upload a transactions CSV
GET    /records/calls
GET    /records/transactions
GET    /records/firs
GET    /records/entities
```

**NLP — `:8001`**
```
GET    /health
POST   /extract/text                entities from raw text
POST   /extract/fir/{fir_id}        full structured FIR extraction
POST   /extract/phones
POST   /extract/cdr
POST   /extract/batch
```

**Graph — `:8002`**
```
GET    /health                      includes neo4j_connected
GET    /graph/stats                 node and relationship counts
GET    /graph/search?q=             find any entity by name
GET    /graph/person/{name}/network?depth=2
GET    /graph/shortest-path?person1=&person2=
GET    /graph/full
POST   /graph/build/from-extraction NLP output -> graph
POST   /graph/transaction
```

**Analysis — `:8003`**
```
GET    /health                      includes neo4j_connected
GET    /analysis/centrality
GET    /analysis/communities
GET    /analysis/anomalies/transactions
GET    /analysis/anomalies/calls
GET    /analysis/risk/all
GET    /analysis/risk/{person_name}
POST   /analysis/run-full-analysis
```

**AI — `:8004`**
```
GET    /health
POST   /chat/                       multi-turn chat with memory
POST   /chat/ask                    single question
POST   /chat/reset
GET    /chat/sample-questions
```

---

## How risk scoring works

Each person gets a 0–100 score, and **every score is explainable** — the
response lists the factors that produced it. That matters because *"the model
said so"* is not something an investigator can put in a case file.

| Weight | Component | Signal |
|-------:|-----------|--------|
| 35 | Network position | degree and betweenness centrality |
| 25 | Criminal record | FIRs and cases linked in the graph |
| 20 | Financial activity | flagged transactions on linked accounts |
| 20 | Communication | suspicious calling patterns on linked phones |
| +8 | Shared handset | shares a phone with another suspect |

`CRITICAL ≥ 75 · HIGH ≥ 50 · MEDIUM ≥ 25 · LOW < 25`

**Roles matter.** Being named in an FIR is not evidence of criminality.
Anyone recorded as a victim or complainant is multiplied by `0.15`, and
witnesses by `0.2` — otherwise a victim who reported a large robbery outranks
the accused simply because they are well connected to the case.

---

## Sample data

`sample_data/` contains one linked scenario — the same people, phones and
accounts recur across the files, so the graph has real structure to find:

- `sample_fir.txt` — Andheri (Mumbai) robbery FIR: four people, two phones,
  a vehicle, a bank account
- `sample_fir_delhi.txt` — Karol Bagh (Delhi) fraud FIR sharing two people
  with the Mumbai case. **This overlap is the point**: with a single FIR every
  person links through one node and community detection has nothing to
  separate. Two overlapping cases produce two groups joined by a bridge —
  exactly the hidden connection the tool exists to surface.
- `sample_call_records.csv` — 24 calls including a hub number, a 3am burst
  and short coded calls
- `sample_transactions.csv` — 20 transfers including structuring just below
  the ₹10,00,000 threshold and a pass-through mule chain

### A note on entity extraction quality

`en_core_web_sm` is trained on general English news, not Indian police
reports. Left unfiltered it tags "Karol Bagh" as a person, the vehicle
"Maruti Swift" as a person, and the actual suspect "Rakesh Gupta" as a
location — and a place name or the investigating officer then appears in the
risk table, which is the fastest way to lose an investigator's trust.

The backend therefore cleans NER output before anything reaches the graph
(`backend/app/routers/upload.py`). For production the right upgrade is a
fine-tuned NER model or a gazetteer of Indian place names — these rules are a
pragmatic stand-in, not a substitute for one.

**Practical consequence:** if a suspect goes missing from the graph after an
upload, spaCy most likely mislabelled them. Rewording so the name appears as
the subject of a sentence ("Rakesh Gupta arranged...") usually recovers them.

---

## Troubleshooting

**`docker compose` fails immediately**
The daemon is not running. Start Docker Desktop and check with `docker info`.

**A service reports `neo4j_connected: false`**
Neo4j takes ~30 seconds on first start. Check with
`docker compose logs neo4j`, then `docker compose restart graph_service analysis_service`.

**Dashboard shows "Backend not reachable (port 8000)"**
Run `make health`. If the backend is down, `docker compose logs backend`.

**Graph search says "No one matching …"**
That name is not in the graph. The error lists the names that are. Load data
with `make pipeline` if the graph is empty.

**NLP returns no persons or locations**
The spaCy model is not installed. The service keeps running by design — regex
extraction still finds phones, vehicles and accounts. Fix with
`python -m spacy download en_core_web_sm`, or rebuild the container.

**AI replies "GEMINI_API_KEY is not set"**
Add the key to `.env`, then `docker compose up -d ai_service`.

**Port already in use**
`lsof -i :8000` (substitute the port) to find the process, then stop it or
change the mapping in `docker-compose.yml`.

**Everything is behaving strangely**
Full reset: `make clean && make up && make pipeline`.

---

## Repository layout

```
.
├── backend/                M1 · ingestion, storage, upload APIs
│   └── app/
│       ├── routers/        cases, upload, records
│       ├── services/       file parsing, pipeline orchestration
│       └── models.py       SQLAlchemy schema
├── nlp_service/            M2 · spaCy NER + regex extractors
│   └── app/extractors/     pattern, NER, FIR, CDR
├── graph_service/          M3 · Neo4j builders, resolvers, /graph API
│   └── app/
│       ├── builders/       person, phone, case
│       ├── resolvers/      entity resolution, analytics
│       └── routers/        the /graph contract
├── analysis_service/       M4 · centrality, communities, anomalies, risk
│   └── app/analyzers/
├── frontend/               M5 · React dashboard
│   └── src/
│       ├── components/     graph, dashboard, upload, chat, map
│       └── pages/
├── ai_service/             M6 · Gemini RAG assistant
│   └── app/
│       ├── llm/            Gemini client, prompt builder
│       ├── retrieval/      graph, DB and vector retrievers
│       └── services/       QA orchestration
├── integration/            health_check.py · data_pipeline.py
├── sample_data/            linked demo scenario
├── uploads/                raw uploaded evidence (gitignored)
├── docker-compose.yml      full stack
├── Makefile                shortcuts — run `make help`
└── .env.example
```
