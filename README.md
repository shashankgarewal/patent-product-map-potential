# Patent–Product Intelligence Engine

An AI-assisted IP & technical intelligence system built with **Google ADK (Agent Development Kit)**, **Gemini (`gemini-3.8-flash` & `text-embedding-004`)**, **Google BigQuery (`patents-public-data.patents.publications`)**, **AlloyDB (`pgvector` / `alloydb_scann`)**, and the **Medium Model Context Protocol (MCP) Server (`medium-2`)**.

The engine performs preliminary technical screening and commercial investigation prioritization between:
1. A **Client Company's patent portfolio** (retrieved via a 3-stage BigQuery funnel + dynamic `VECTOR_SEARCH`), and
2. A **Target Company's publicly documented products, technologies, and engineering capabilities** (retrieved from an offline pre-fetched AlloyDB vector store populated via the Medium MCP Server and approved technical documentation).

> **Positioning & Non-Infringement Guardrail**  
> This system is designed strictly for **preliminary technical screening and investigation prioritization**, not legal infringement determination or royalty/damages calculation. Every output enforces non-infringement screening terminology (*"potential technical overlap"*, *"candidate for investigation"*, *"evidence identified"*, *"requires expert/legal review"*) and preserves verbatim source provenance.

---

## Core Architecture

The platform is architected into **three decoupled pipelines** orchestrated via Google ADK `SequentialAgent` and `LlmAgent` hierarchies, with strict separation between **deterministic Python tools** (SQL queries, filtering, 20-year patent life math, vector cosine similarity, ranking formulas, guardrail enforcement) and **LLM reasoning** (claim-element interpretation, technical summarization, and evidence-grounded overlap explanations).

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          PATENT–PRODUCT INTELLIGENCE ENGINE                            │
├───────────────────────────────────────────┬────────────────────────────────────────────┤
│ 1. CLIENT PATENT PIPELINE (adk_pipeline/) │ 2. TARGET KNOWLEDGE PIPELINE               │
│                                           │    (target_prefetch/ & target_agent/)      │
│ • Source: BigQuery                        │ • Sources: Strict 5-Prefix Allowlist       │
│   patents-public-data.patents.publications│   - netflixtechblog.com (Medium MCP)       │
│ • Stage 1: Assignee Harmonization &       │   - netflixtechblog.medium.com (Medium MCP)│
│   Disambiguation                          │   - openconnect.netflix.com                │
│ • Stage 2: Metadata & CPC Screening       │   - research.netflix.com/publications      │
│   + Dynamic BigQuery VECTOR_SEARCH        │   - netflix.github.io                      │
│   (text-embedding-004, 768-d, 1–100 docs) │ • Ingestion: Medium MCP Server (JSON-RPC)  │
│ • Stage 3: Verbatim Independent Claim     │   + 180w/35w Overlapping Chunking          │
│   Extraction & Atomic Decomposition       │   + text-embedding-004 (vector(768))       │
│   (1A, 1B, 1C, 1D) + 20-Yr Term Math      │ • Storage: AlloyDB 2-Tier Schema           │
│                                           │   (documents + document_chunks ScaNN)      │
└─────────────────────┬─────────────────────┴──────────────────────┬─────────────────────┘
                      │                                            │
                      ▼                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. PATENT–TARGET MATCHING & COMMERCIAL AGENT PIPELINE (matching_agent/)                │
│                                                                                        │
│ • Part 1 — Technical Overlap Score (0–100):                                            │
│   Claim-element alignment (1A–1D) against verbatim target chunks via lexical +         │
│   text-embedding-004 (768-d) cosine similarity, explicitly surfacing evidence gaps.    │
│ • Part 2 — Potential Monetary Opportunity Signal (0–100, Orthogonal to Part 1):        │
│   Grounded in SEC Form 10-K disclosures ($33.7B–$39.0B revenue, 301.6M+ memberships),  │
│   subscription tier linkage, active patent status, and remaining patent life.          │
│ • Part 3 — Gatekeeper Investigation Priority (High / Medium / Low Priority):           │
│   Combines Part 1 & Part 2 with deterministic gatekeeper caps for expired patents or   │
│   low technical overlap, producing the 9-Column Ranked Intelligence Dossier Table.     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Capabilities

### 1. Client Patent Retrieval & Analysis Pipeline (`adk_pipeline/`)
- **3-Stage BigQuery Retrieval Funnel**:
  - **Stage 1 (`resolve_client_company_tool`)**: Resolves the user-supplied `client_company` (e.g., `Apple`, `Dolby Laboratories`, `Broadcom`, `Fraunhofer`, `Sony`, `Nokia`) against `assignee_harmonized.name` and raw assignee aliases. Returns disambiguation candidates if multiple distinct corporate entities match.
  - **Stage 2 (`retrieve_candidate_metadata_tool`)**: Screens utility grants (`B2`/`B1`) and published applications (`A1`) across title, abstract, and CPC subgroups (`H04N21/`, `G06F16/`, `G06N3/`, `H04N19/`, `H04L65/`). Supports **1 to 100 candidate patents (`max_candidates`)**.
  - **Dynamic BigQuery Vector Search (`dynamic_bigquery_patent_vector_search_tool`)**: Whenever the local mirror contains fewer candidates than `max_candidates` (or zero lexical matches), automatically executes BigQuery `VECTOR_SEARCH` using **768-dimensional `text-embedding-004`** embeddings to fetch, embed, and append additional matching patents sequentially.
  - **Stage 3 (`fetch_staged_patent_claims_tool` & `decompose_independent_claims_tool`)**: Extracts verbatim independent claims (`Claim 1`, etc.), decomposes them into atomic technical elements (`1A`, `1B`, `1C`, `1D`), embeds each patent and claim element with `text-embedding-004` (`768-d`), and strictly separates **Source Facts** from **AI Interpretation**.
- **Deterministic Patent Life Calculator (`calculate_patent_life_tool`)**:
  - Computes estimated remaining patent term in years based on the 20-year statutory baseline from earliest effective utility `filing_date` (35 U.S.C. § 154(a)(2)), never fabricating missing dates.

### 2. Offline Target Knowledge Prefetch & Medium MCP Server (`target_prefetch/`)
- **Configurable Prefetch Corpus (`sources_config.py`)**:
  - Controlled via `PREFETCH_DOCUMENT_COUNT` (default `10`), `PREFETCH_FOCUS_AREA` (default `"recommendation"`), `CHUNK_SIZE_WORDS=180` (~250 tokens), and `CHUNK_OVERLAP_WORDS=35` (~20% sliding window overlap).
- **Medium MCP Server Integration (`medium_mcp_server.py`)**:
  - Implements the Model Context Protocol (`2024-11-05` JSON-RPC 2.0) server specification for `medium-2` (`https://mcpmarket.com/server/medium-2`) over both local stdio (`MEDIUM_MCP_SERVER_CMD`) and HTTP (`MEDIUM_MCP_SERVER_URL="http://127.0.0.1:3000/api/mcp/medium"`).
  - Exposes standardized MCP tools:
    - `medium_list_publication_articles`
    - `medium_get_article_content`
    - `medium_search_publication`
  - Articles on `https://netflixtechblog.medium.com/` and `https://netflixtechblog.com/` are fetched via the Medium MCP Server rather than raw URL scraping, preserving headings (`<h1>`–`<h6>`) and `<pre><code>` blocks.
- **AlloyDB 2-Tier Parent–Child Vector Store (`db.py` & `pipeline.py`)**:
  - **`documents` (Parent Table)**: Stores canonical `document_id`, `company`, `title`, `source_url`, `source_type`, `published_date`, `author`, un-truncated `full_content`, `technology_area`, SHA-256 `content_hash`, `fetch_method`, and `mcp_tool_used`.
  - **`document_chunks` (Child Table)**: Stores overlapping 180-word chunks (`{document_id}_chunk_{index}`), **768-dimensional `text-embedding-004` dense vectors** (`vector(768)` indexed via AlloyDB `alloydb_scann`), and `candidate_tags`.
  - **`failed_documents` (Quarantine Table)**: Logs any out-of-allowlist URLs or parsing/fetch errors without halting ingestion.

### 3. Target Retrieval Agent & On-Demand Dynamic Ingestion (`target_agent/`)
- **Hybrid Multi-Query Retrieval (`search_target_knowledge`)**:
  - Combines **AlloyDB ScaNN `text-embedding-004` (768-d) cosine similarity (`0.40`)**, **keyword token density (`0.35`)**, and **metadata tag alignment (`0.25`)**.
- **On-Demand Dynamic Target Fetch & Embedding (`dynamic_fetch_and_embed_target_docs`)**:
  - If a user queries a specialized technical domain that has no match in the pre-fetched AlloyDB tables, the pipeline automatically queries the **Medium MCP Server** (`medium_search_publication` & `medium_get_article_content`) and approved Netflix source catalog, chunks the newly retrieved documentation (`180w / 35w`), embeds the chunks with `text-embedding-004` (`768-d`), and inserts them into AlloyDB so the new evidence is immediately used in the current analysis.

### 4. Patent–Target Matching & Commercial Prioritization Agent (`matching_agent/`)
- **Part 1 — Technical Overlap (`evaluate_claim_element_alignment_tool`)**:
  - Maps every decomposed claim element (`1A`, `1B`, `1C`, `1D`) against documented target capabilities and verbatim evidence chunks using lexical overlap + `text-embedding-004` (768-d) cosine similarity. Classifies each element as `EVIDENCE_IDENTIFIED`, `PARTIAL_ALIGNMENT`, or `NOT_DOCUMENTED_IN_PUBLIC_SOURCES`.
- **Part 2 — Potential Monetary Opportunity (`evaluate_commercial_opportunity_tool`)**:
  - Evaluates commercial significance using pre-fetched SEC Form 10-K disclosures (e.g., Netflix FY2024 $39.0B consolidated streaming revenue, 301.6M+ paid memberships, >80% catalog discovery driven by personalized recommendation). Explicitly notes when standalone subsystem revenue is not broken out in public filings.
- **Part 3 — Investigation Priority (`compute_investigation_priority_tool`)**:
  - Synthesizes Part 1 and Part 2 into `High Priority`, `Medium Priority`, or `Low Priority` with deterministic gatekeeper rules (e.g., expired patents are capped at `Low Priority (Expired Term)` regardless of technical overlap).

---

## Repository Structure

```text
├── server.ts                          # Express + Vite full-stack server, Gemini ADK enrichment & REST API
├── src/
│   ├── App.tsx                        # Main Dossier UI, 9-Column Ranked Matrix, Claim & Cluster Inspectors
│   ├── TargetPrefetchView.tsx         # AlloyDB 2-Tier Store, Medium MCP & text-embedding-004 Inspector
│   ├── TargetAgentView.tsx            # Interactive Google ADK Target Retrieval Agent Workbench
│   └── types.ts                       # TypeScript contracts for all pipelines and canonical JSON outputs
├── adk_pipeline/                      # Pipeline 1: Client Patent Retrieval & Analysis (Google ADK)
│   ├── agent.py                       # ADK SequentialAgent (retrieval -> analysis -> ranking)
│   ├── tools.py                       # 3-Stage BigQuery tools, dynamic VECTOR_SEARCH & 20-yr term math
│   ├── dataset_mirror.py              # Local BigQuery mirror (patents-public-data.patents.publications)
│   ├── schema_inspector.py            # BigQuery schema verifier
│   └── cli.py                         # CLI entrypoint (python3 -m adk_pipeline.cli)
├── target_prefetch/                   # Pipeline 2A: Offline Target Knowledge Prefetch & AlloyDB Store
│   ├── sources_config.py              # Strict 5-prefix allowlist, PREFETCH_DOCUMENT_COUNT & Netflix corpus
│   ├── medium_mcp_server.py           # Local Medium MCP Server (medium-2) — JSON-RPC 2.0 (stdio & HTTP)
│   ├── db.py                          # AlloyDB / SQLite 2-tier schema (documents, document_chunks, etc.)
│   ├── pipeline.py                    # Chunking (180w/35w), text-embedding-004 (768-d) & dynamic fetch
│   └── cli.py                         # CLI entrypoint (python3 -m target_prefetch.cli)
└── matching_agent/                    # Pipeline 3: Patent–Target Matching & Commercial Agent
    ├── agent.py                       # ADK SequentialAgent (technical -> commercial -> priority)
    ├── tools.py                       # Claim-element alignment, SEC 10-K commercial scoring & guardrails
    └── cli.py                         # CLI entrypoint (python3 -m matching_agent.cli)
```

---

## Environment Variables

Configuration defaults are provided in `.env.example`:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | *(Managed by AI Studio)* | Gemini API key for server-side ADK LLM synthesis (`gemini-3.8-flash`) |
| `PREFETCH_DOCUMENT_COUNT` | `10` | Number of valid Netflix documents to pre-fetch into AlloyDB on initialization |
| `PREFETCH_FOCUS_AREA` | `recommendation` | Primary domain prioritized during initial target knowledge prefetch |
| `EMBEDDING_MODEL_NAME` | `text-embedding-004` | Embedding model (`768-d`) used for AlloyDB chunks and patent vectors |
| `PREFETCH_CHUNK_SIZE_WORDS` | `180` | Target chunk length in words (~250 tokens) for `text-embedding-004` |
| `PREFETCH_CHUNK_OVERLAP_WORDS` | `35` | Sliding-window word overlap (~20%) between consecutive chunks |
| `MEDIUM_MCP_SERVER_URL` | `http://127.0.0.1:3000/api/mcp/medium` | Local HTTP JSON-RPC 2.0 endpoint for the Medium MCP Server (`medium-2`) |
| `MEDIUM_MCP_SERVER_CMD` | `python3 -m target_prefetch.medium_mcp_server --stdio` | Local stdio JSON-RPC 2.0 command for the Medium MCP Server |

---

## Running & Testing the Pipelines

### 1. Start the Full-Stack Application
```bash
npm install
npm run dev
```
The server starts on `http://0.0.0.0:3000`.

### 2. Run Individual Python ADK Pipelines via CLI

- **Run Offline Target Knowledge Prefetch (AlloyDB + Medium MCP + `text-embedding-004`)**:
  ```bash
  python3 -m target_prefetch.cli --action run_prefetch --mode initial
  ```

- **Run Client Patent Retrieval & Analysis Pipeline (1 to 100 Patents)**:
  ```bash
  python3 -m adk_pipeline.cli --action run_pipeline --client_company "Apple" --technology_area "content recommendation" --max_candidates 15
  ```

- **Run End-to-End Patent–Target Matching & Commercial Prioritization**:
  ```bash
  python3 -m matching_agent.cli --action run_matching --payload_json '{"client_company":"Apple","target_company":"Netflix","technology_area":"content recommendation","max_candidates":15}'
  ```

- **Query the Local Medium MCP Server (`medium-2`) via JSON-RPC 2.0**:
  ```bash
  python3 -m target_prefetch.medium_mcp_server --rpc '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
  ```

---

## REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/analyze-client-patents` | Executes the unified Client Patent ADK Pipeline + Target Retrieval + Patent–Target Matching (`max_candidates`: 1–100) |
| `POST` | `/api/analyze-target-company` | Executes the standalone Google ADK Target Retrieval & Analysis Agent |
| `POST` | `/api/analyze-patent-target-matching` | Executes the standalone Patent–Target Matching & Commercial Opportunity Agent |
| `GET` | `/api/target-knowledge` | Inspects the AlloyDB 2-tier target knowledge store (`documents`, `document_chunks`, `failed_documents`) |
| `POST` | `/api/target-knowledge/prefetch` | Triggers initial, incremental, or custom-document target knowledge ingestion |
| `GET/POST` | `/api/mcp/medium` | Local Medium MCP Server (`medium-2`) JSON-RPC 2.0 endpoint (`initialize`, `tools/list`, `tools/call`) |
| `GET` | `/api/schema` | Inspects the `patents-public-data.patents.publications` BigQuery schema |
