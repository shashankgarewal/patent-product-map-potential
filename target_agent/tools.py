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

from target_prefetch.pipeline import (
    DB_PATH,
    init_target_knowledge_db,
    run_prefetch_pipeline,
    generate_chunk_embedding,
)


# Domain query expansion rules to generate multiple retrieval queries from client patent concepts
CONCEPT_QUERY_EXPANSIONS: Dict[str, List[str]] = {
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
    Ensures the local pre-fetched SQLite database is initialized before searching.
    Never performs runtime web crawling.
    """
    init_target_knowledge_db(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM document_chunks")
        count = cur.fetchone()[0]
    finally:
        conn.close()

    if count == 0:
        run_prefetch_pipeline(mode="initial", db_path=DB_PATH)


def search_target_knowledge(
    target_company: str,
    query: str,
    technology_area: Optional[str] = None,
    top_k: int = 5,
    source_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Deterministic database search tool for the Target Retrieval Agent.
    Searches the pre-fetched `target_knowledge.sqlite` database using hybrid:
    1. Keyword / lexical matching across title, content, and candidate_tags
    2. Semantic 32-d vector cosine similarity (`embedding_json`)
    3. Metadata filtering (`target_company`, optional `technology_area` soft/hard boost)
    4. Optional `source_type` filtering
    """
    ensure_knowledge_base_seeded()

    company_norm = (target_company or "").strip()
    # Clean common suffixes like "Netflix, Inc." -> "Netflix"
    company_base = re.sub(r",?\s*(?:inc\.?|corp\.?|corporation|ltd\.?|llc)$", "", company_norm, flags=re.IGNORECASE).strip()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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

    q_emb = generate_chunk_embedding(q_clean) if q_clean else None
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

        # 2. Vector embedding cosine similarity (32-d)
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
            "matched_tokens": matched_tokens,
            "matched_query": query,
        })

    scored_results.sort(key=lambda x: x["retrieval_score"], reverse=True)
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
        if "streaming" in area_clean.lower():
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
