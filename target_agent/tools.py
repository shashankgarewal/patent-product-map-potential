"""
Deterministic Database Search Tools for the Target Retrieval Agent (Google ADK).
Queries `target_prefetch/target_knowledge.sqlite` exclusively.
Supports:
- Keyword retrieval (exact phrase + token matching)
- Semantic / vector retrieval (32-d normalized embedding cosine similarity)
- Metadata filtering (company, technology_area / candidate_tags)
- Source filtering (source_type)
"""

import json
import re
import sqlite3
from typing import Dict, Any, List, Optional

from target_prefetch.db import get_db_connection
from target_prefetch.sources_config import (
    PREFETCH_DOCUMENT_COUNT,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_DIMENSIONS,
)
from target_prefetch.pipeline import (
    DB_PATH,
    init_target_knowledge_db,
    run_prefetch_pipeline,
    generate_chunk_embedding,
    dynamic_fetch_and_embed_target_docs,
)


# Domain query expansion rules to generate multiple retrieval queries from client patent concepts
CONCEPT_QUERY_EXPANSIONS: Dict[str, List[str]] = {
    "recommendation": [
        "Personalized Video Ranker PVR Top-N video ranker",
        "two-stage homepage page generation row ranking submodular diversity",
        "calibrated recommendations KL-divergence multi-objective ranking",
        "collaborative filtering two-tower neural candidate generation",
    ],
    "personalization": [
        "personalized homepage canvas row ranking PVR",
        "contextual bandits AVA artwork visual personalization",
        "session-based sequential recommendation short-term intent",
        "member retention utility multi-task Hydra ranking",
    ],
    "ranking": [
        "Personalized Video Ranker PVR Caret scoring",
        "Top-N Video Ranker head-of-catalog ranking",
        "two-dimensional page generation stage-wise row selection",
        "team-draft interleaving online ranking evaluation",
    ],
    "bandit": [
        "contextual bandits personalized artwork selection LinUCB Thompson sampling",
        "inverse propensity weighting IPW doubly robust offline evaluation",
        "AVA visual aesthetics frame selection explore-exploit",
    ],
    "artwork": [
        "contextual bandits personalized artwork thumbnail selection",
        "AVA Automated Visual Aesthetics visual metadata tagging",
        "actor genre visual preference matching",
    ],
    "session": [
        "session-based sequential recommendation real-time intent adaptation",
        "causal Transformer encoder in-session interaction events",
        "Axion Flink EVCache sub-second streaming feature store",
    ],
    "collaborative": [
        "matrix factorization ALS Bayesian Personalized Ranking BPR",
        "two-tower member and item embedding ScaNN HNSW retrieval",
        "bipartite user-title GraphSAGE GNN cold-start representation",
    ],
    "search": [
        "personalized lexical and semantic search query intent",
        "pre-query instant suggestions bi-encoder cross-encoder ranking",
        "multimodal title embeddings catalog discovery",
    ],
    "adaptive": [
        "adaptive streaming",
        "bitrate selection",
        "video delivery",
        "streaming quality",
        "playback optimization",
    ],
    "bitrate": [
        "adaptive bitrate ABR selection",
        "bitrate selection",
        "per-shot convex hull bitrate ladder",
        "streaming quality",
    ],
    "buffer": [
        "client playback buffer occupancy telemetry",
        "playback optimization",
        "rebuffering prevention",
    ],
    "cmaf": [
        "fragmented ISOBMFF CMAF media segments",
        "video delivery",
        "low-latency chunked streaming",
    ],
    "cdn": [
        "Open Connect Appliance content delivery",
        "BGP routing cache fill",
        "multi-appliance session steering",
    ],
    "content delivery": [
        "Open Connect content delivery network",
        "off-peak cache fill ISP appliance",
        "BGP prefix routing steering",
    ],
    "manifest": [
        "session-specific streaming manifest generation",
        "Open Connect pathway steering",
        "adaptive streaming",
    ],
    "encoding": [
        "per-title and per-shot convex hull video encoding",
        "Dynamic Optimizer perceptual VMAF encoding",
        "AV1 HEVC quantization parameter control",
    ],
    "hdr": [
        "10-bit HDR luminance reshaping SEI metadata",
        "Dolby Vision HDR10 tone mapping",
        "video encoding",
    ],
    "quantization": [
        "coding tree unit CTU delta quantization dQP contrast masking",
        "rate-distortion convex hull encoding",
    ],
    "audio": [
        "Dolby Atmos object-based spatial audio rendering",
        "dialogue-gated loudness normalization crossfading",
        "ISOBMFF presentation timestamp PTS audio-video sync",
    ],
    "synchronization": [
        "frame-accurate audio-video synchronization PTS edit-list",
        "playback optimization",
    ],
    "pacing": [
        "OCA transport-layer socket pacing RTT congestion control",
        "FreeBSD NGINX kTLS video segment transmission",
    ],
    "bgp": [
        "Open Connect BGP prefix announcements ISP cache fill",
        "regional demand forecasting catalog fill",
    ],
}


def ensure_knowledge_base_seeded() -> None:
    """
    Ensures the pre-fetched AlloyDB target knowledge store is initialized with the configured
    `PREFETCH_DOCUMENT_COUNT` corpus and 768-d `text-embedding-004` vectors before searching.
    """
    init_target_knowledge_db(DB_PATH)
    conn = get_db_connection(DB_PATH)
    needs_reseed = False
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM documents")
        count = int(cur.fetchone()["cnt"])
        if count == 0:
            needs_reseed = True
        else:
            cur.execute("SELECT embedding FROM document_chunks LIMIT 1")
            row = cur.fetchone()
            if not row:
                needs_reseed = True
            else:
                emb = json.loads(row["embedding"] or "[]")
                if len(emb) != EMBEDDING_DIMENSIONS:
                    needs_reseed = True
    finally:
        conn.close()

    if needs_reseed:
        run_prefetch_pipeline(mode="initial", db_path=DB_PATH)


def search_target_knowledge(
    target_company: str,
    query: str,
    technology_area: Optional[str] = None,
    top_k: int = 5,
    source_type: Optional[str] = None,
    _is_retry: bool = False,
) -> Dict[str, Any]:
    """
    Deterministic database search tool for the Target Retrieval Agent.
    Searches the AlloyDB knowledge store using hybrid:
    1. Keyword / lexical matching across title, content, and candidate_tags
    2. Semantic 768-d `text-embedding-004` vector cosine similarity (`embedding` ScaNN index)
    3. Metadata filtering (`target_company`, optional `technology_area` boost)
    4. Dynamic On-Demand Target Documentation Fetch & `text-embedding-004` AlloyDB Ingestion
       when the currently prefetched AlloyDB documents have no match for `query`.
    """
    ensure_knowledge_base_seeded()

    company_norm = (target_company or "").strip()
    # Clean common suffixes like "Netflix, Inc." -> "Netflix"
    company_base = re.sub(r",?\s*(?:inc\.?|corp\.?|corporation|ltd\.?|llc)$", "", company_norm, flags=re.IGNORECASE).strip()

    conn = get_db_connection(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                c.chunk_id,
                c.document_id,
                c.chunk_index,
                c.content,
                c.embedding,
                c.candidate_tags,
                d.company,
                d.title,
                d.source_url,
                d.source_type,
                d.published_date,
                d.author,
                d.full_content,
                d.technology_area,
                d.content_hash
            FROM document_chunks c
            INNER JOIN documents d ON d.document_id = c.document_id
            WHERE LOWER(d.company) = LOWER(?) OR LOWER(d.company) LIKE '%' || LOWER(?) || '%'
            """,
            (company_norm, company_base or company_norm),
        )
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    if not rows:
        return {
            "status": "COMPANY_NOT_IN_KNOWLEDGE_BASE",
            "target_company": target_company,
            "query": query,
            "technology_area": technology_area,
            "results": [],
        }

    q_clean = (query or "").strip().lower()
    q_tokens = [
        t for t in re.findall(r"[a-z0-9\-]{3,}", q_clean)
        if t not in {"the", "and", "for", "with", "from", "that", "this", "video", "system", "method"}
    ]
    if not q_tokens and q_clean:
        q_tokens = [t for t in re.findall(r"[a-z0-9\-]{2,}", q_clean)]

    q_emb = generate_chunk_embedding(q_clean, task_type="RETRIEVAL_QUERY") if q_clean else None
    tech_norm = (technology_area or "").strip().lower()
    tech_tokens = [t for t in re.findall(r"[a-z0-9\-]{3,}", tech_norm) if t not in {"optional", "all", "none"}]

    scored_results: List[Dict[str, Any]] = []

    for row in rows:
        if source_type and source_type.lower() not in ("all", "") and (row.get("source_type") or "").lower() != source_type.lower():
            continue

        tags: List[str] = json.loads(row.get("candidate_tags") or "[]")
        emb: List[float] = json.loads(row.get("embedding") or "[]")
        title_lower = (row.get("title") or "").lower()
        content_lower = (row.get("content") or "").lower()
        tags_lower = " ".join(tags).lower()
        full_text = f"{title_lower} {content_lower} {tags_lower}"

        # 1. Exact phrase & keyword token score
        phrase_hit = 1.0 if (q_clean and len(q_clean) >= 4 and q_clean in full_text) else 0.0
        matched_tokens = [tok for tok in q_tokens if tok in full_text]
        token_Coverage = (len(matched_tokens) / max(1, len(q_tokens))) if q_tokens else 0.0

        # 2. Vector embedding cosine similarity (768-d text-embedding-004)
        vector_sim = sum(a * b for a, b in zip(q_emb, emb)) if (q_emb and emb) else 0.0

        # 3. Technology area metadata alignment
        metadata_boost = 0.0
        if tech_tokens:
            if any(tt in tags_lower or tt in (row.get("technology_area") or "").lower() for tt in tech_tokens):
                metadata_boost = 0.18
            elif any(tt in full_text for tt in tech_tokens):
                metadata_boost = 0.08

        # Require actual lexical or strong semantic alignment so unrelated queries (e.g. "quantum propulsion")
        # do not return false positives from metadata boost alone
        if q_tokens and len(matched_tokens) == 0 and phrase_hit == 0.0 and vector_sim < 0.42:
            continue

        combined_score = round(
            (phrase_hit * 0.35)
            + (token_Coverage * 0.40)
            + (max(0.0, vector_sim) * 0.25)
            + metadata_boost,
            4,
        )

        # Threshold filter to avoid returning irrelevant noise when evidence is missing
        if combined_score < 0.22:
            continue

        scored_results.append({
            "chunk_id": row["chunk_id"],
            "document_id": row["document_id"],
            "company": row["company"],
            "title": row["title"],
            "source_url": row["source_url"],
            "source_type": row["source_type"],
            "published_date": row["published_date"],
            "author": row["author"],
            "content": row["content"],
            "technology_area": row["technology_area"],
            "candidate_tags": tags,
            "retrieval_score": combined_score,
            "keyword_score": round((phrase_hit * 0.4) + (token_Coverage * 0.6), 3),
            "vector_similarity": round(vector_sim, 3),
            "embedding_model": EMBEDDING_MODEL_NAME,
            "embedding_dimensions": len(emb) or EMBEDDING_DIMENSIONS,
            "matched_tokens": matched_tokens,
            "matched_query": query,
        })

    scored_results.sort(key=lambda x: x["retrieval_score"], reverse=True)

    # Dynamic On-Demand Target Documentation Fetch & text-embedding-004 AlloyDB Ingestion:
    # When the prefetched AlloyDB documents have no match (or weak match) for this query,
    # fetch relevant Netflix documentation, embed with text-embedding-004 (768-d) into AlloyDB, and re-query.
    if (
        not _is_retry
        and (company_base.lower() == "netflix" or "netflix" in company_norm.lower())
        and (len(scored_results) == 0 or scored_results[0]["retrieval_score"] < 0.36)
    ):
        dyn_res = dynamic_fetch_and_embed_target_docs(
            target_company=target_company,
            query=query,
            technology_area=technology_area,
            max_new_docs=3,
            db_path=DB_PATH,
        )
        if dyn_res.get("newly_ingested_count", 0) > 0:
            retry_out = search_target_knowledge(
                target_company=target_company,
                query=query,
                technology_area=technology_area,
                top_k=top_k,
                source_type=source_type,
                _is_retry=True,
            )
            retry_out["dynamic_prefetch_triggered"] = dyn_res
            retry_out["dynamic_fetch_and_embedding"] = dyn_res
            return retry_out

    top_results = scored_results[: max(1, int(top_k))]

    return {
        "status": "OK",
        "target_company": target_company,
        "query": query,
        "technology_area": technology_area,
        "top_k": top_k,
        "returned_count": len(top_results),
        "results": top_results,
    }


def build_multi_queries_from_patent_context(
    technology_area: Optional[str],
    client_patent_context: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """
    Constructs a diverse list of retrieval queries from the client patent candidates'
    `technology_areas` and `key_concepts` (never relying on a single query).
    """
    queries: List[Dict[str, str]] = []
    seen_queries = set()

    def add_query(q_str: str, rationale: str) -> None:
        norm = q_str.strip().lower()
        if not norm or norm in seen_queries:
            return
        seen_queries.add(norm)
        queries.append({"query": q_str.strip(), "rationale": rationale})

    # 1. Expand from requested technology_area if supplied
    if technology_area and technology_area.strip().lower() not in ("", "optional", "all"):
        area_clean = technology_area.strip()
        add_query(area_clean, f"Primary requested technology niche ('{area_clean}')")
        area_low = area_clean.lower()
        if "recommend" in area_low or "personal" in area_low or "ranking" in area_low or "discovery" in area_low:
            add_query("Personalized Video Ranker PVR Top-N", "Multi-query expansion for Netflix recommendation ranking")
            add_query("two-stage homepage page generation row ranking", "Multi-query expansion for 2D canvas personalization")
            add_query("contextual bandits personalized artwork AVA", "Multi-query expansion for visual artwork personalization")
            add_query("session-based sequential recommendation intent", "Multi-query expansion for real-time session Transformer")
            add_query("collaborative filtering two-tower embedding retrieval", "Multi-query expansion for neural candidate generation")
        if "streaming" in area_low or "video" in area_low:
            add_query("Personalized Video Ranker PVR recommendation", "Multi-query expansion for personalized video catalog ranking")
            add_query("adaptive streaming", "Multi-query expansion from video streaming niche")
            add_query("bitrate selection", "Multi-query expansion from adaptive bitrate concepts")
            add_query("video delivery", "Multi-query expansion for CDN / Open Connect delivery")
            add_query("streaming quality", "Multi-query expansion for perceptual quality & VMAF")
            add_query("playback optimization", "Multi-query expansion for client buffer & A/V sync")

    # 2. Extract and expand from client_patent_context items
    for pat in client_patent_context or []:
        pub_num = pat.get("patent_number", "Client Patent")
        for area in pat.get("technology_areas") or []:
            sub = area.split(" > ")[-1].strip()
            add_query(sub, f"Technology cluster from {pub_num}")

        for concept in pat.get("key_concepts") or []:
            add_query(concept, f"Key technical concept from {pub_num}")
            c_lower = concept.lower()
            for trigger, expansions in CONCEPT_QUERY_EXPANSIONS.items():
                if trigger in c_lower:
                    for exp_q in expansions[:2]:
                        add_query(exp_q, f"Semantic expansion of '{concept}' ({pub_num})")

    # Fallback default multi-query set if client_patent_context was empty
    if not queries:
        for default_q in [
            "adaptive streaming",
            "bitrate selection",
            "video delivery",
            "streaming quality",
            "playback optimization",
        ]:
            add_query(default_q, "Default streaming technical discovery query")

    return queries[:10]
