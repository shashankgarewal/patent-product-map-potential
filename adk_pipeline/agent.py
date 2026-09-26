"""
Google ADK Multi-Agent Orchestration for the Client Patent Analysis Pipeline.

ADK Hierarchy:
    root_agent (SequentialAgent)
        ↓
    patent_retrieval_agent (LlmAgent with deterministic BigQuery tools)
        ↓
    patent_analysis_agent (LlmAgent for Patent Analysis, Claim Element Decomposition, & Technology Clustering)
        ↓
    patent_ranking_agent (LlmAgent with deterministic Patent Life & Investigation Relevance tools)
"""

import re
from typing import Dict, Any, List, Optional, Callable, Tuple

from adk_pipeline.schema_inspector import inspect_bigquery_publications_schema
from adk_pipeline.tools import (
    resolve_client_company_tool,
    retrieve_candidate_metadata_tool,
    fetch_staged_patent_claims_tool,
    calculate_patent_life_tool,
    compute_investigation_relevance_tool,
    derive_publication_status,
    embed_patent_content_tool,
)

# Import official Google ADK classes if installed in the Python environment;
# otherwise provide compatible ADK Agent / SequentialAgent primitives.
try:
    from google.adk.agents import Agent as LlmAgent, SequentialAgent  # type: ignore
    ADK_RUNTIME_MODE = "google-adk-native"
except ImportError:
    ADK_RUNTIME_MODE = "google-adk-compatible-runtime"

    class LlmAgent:
        def __init__(
            self,
            name: str,
            model: str,
            description: str,
            instruction: str,
            tools: Optional[List[Callable]] = None,
            output_key: Optional[str] = None
        ):
            self.name = name
            self.model = model
            self.description = description
            self.instruction = instruction
            self.tools = tools or []
            self.output_key = output_key

    class SequentialAgent:
        def __init__(
            self,
            name: str,
            description: str,
            sub_agents: List[Any]
        ):
            self.name = name
            self.description = description
            self.sub_agents = sub_agents


# ============================================================================
# ADK AGENT DEFINITIONS (STRICT HIERARCHY: root_agent -> retrieval -> analysis -> ranking)
# ============================================================================

patent_retrieval_agent = LlmAgent(
    name="patent_retrieval_agent",
    model="gemini-3.8-flash",
    description=(
        "Resolves client company against Google Patents Public Dataset harmonized assignees, "
        "handles company ambiguity, and executes 3-stage deterministic retrieval."
    ),
    instruction=(
        "You are the Patent Retrieval Agent in the Client Patent Analysis Pipeline.\n"
        "1. First inspect the `patents-public-data.patents.publications` schema using `inspect_bigquery_publications_schema`.\n"
        "2. Resolve the client company via `resolve_client_company_tool`. Never construct arbitrary SQL.\n"
        "3. If the company is not found or is ambiguous across multiple harmonized corporate assignees, "
        "immediately halt and return the structured ambiguity or not-found state without fabricating records.\n"
        "4. Otherwise execute Stage 2 (`retrieve_candidate_metadata_tool`) and Stage 3 (`fetch_staged_patent_claims_tool`) "
        "so only a manageable, high-signal candidate set enters LLM context."
    ),
    tools=[
        inspect_bigquery_publications_schema,
        resolve_client_company_tool,
        retrieve_candidate_metadata_tool,
        fetch_staged_patent_claims_tool,
    ],
    output_key="retrieved_patent_candidates"
)

patent_analysis_agent = LlmAgent(
    name="patent_analysis_agent",
    model="gemini-3.8-flash",
    description=(
        "Analyzes retrieved patent candidates, clearly separating SOURCE FACTS from AI INTERPRETATION, "
        "decomposes independent claims into structured technical elements, and groups patents into technology clusters."
    ),
    instruction=(
        "You are the Patent Analysis Agent.\n"
        "For each retrieved patent candidate:\n"
        "- Preserve all bibliographic fields, dates, CPC codes, and verbatim claim text strictly as SOURCE FACTS.\n"
        "- Generate an evidence-backed `technical_summary`, `technology_areas`, and `key_concepts` marked as AI INTERPRETATION.\n"
        "- Decompose each independent claim into structured technical elements (`element_id`, `description`, `technical_concept`).\n"
        "- If `claims_localized` is missing in the source record, return empty `independent_claims` and `claim_elements`—never fabricate claims.\n"
        "- Group the analyzed patents into hierarchical Technology Clusters without forcing classifications where evidence is insufficient.\n"
        "- Never state or imply legal infringement conclusions."
    ),
    tools=[],
    output_key="analyzed_patent_candidates"
)

patent_ranking_agent = LlmAgent(
    name="patent_ranking_agent",
    model="gemini-3.8-flash",
    description=(
        "Calculates deterministic estimated remaining patent term and computes explainable "
        "Patent Investigation Relevance scores to rank candidates."
    ),
    instruction=(
        "You are the Patent Ranking Agent.\n"
        "1. Use `calculate_patent_life_tool` to compute the deterministic estimated remaining patent term in years "
        "from `filing_date` with explicit calculation basis and caveat.\n"
        "2. Use `compute_investigation_relevance_tool` to compute explainable Patent Investigation Relevance (0-100) "
        "based on niche relevance, claim availability, technical richness, technology specificity, and downstream matching utility.\n"
        "3. Never refer to relevance as 'infringement probability' or 'likelihood of infringement'.\n"
        "4. Sort the final patent list by `investigation_relevance.score` descending."
    ),
    tools=[
        calculate_patent_life_tool,
        compute_investigation_relevance_tool,
    ],
    output_key="ranked_patent_intelligence"
)

root_agent = SequentialAgent(
    name="root_agent",
    description=(
        "Root orchestrator for the Client Patent Analysis Pipeline: "
        "patent_retrieval_agent -> patent_analysis_agent -> patent_ranking_agent."
    ),
    sub_agents=[
        patent_retrieval_agent,
        patent_analysis_agent,
        patent_ranking_agent,
    ]
)


# ============================================================================
# DETERMINISTIC BASELINE CLAIM DECOMPOSITION & CLUSTERING HELPERS
# (Used as structured fallback or pre-processor before Gemini LLM enrichment)
# ============================================================================

def decompose_claim_elements_fallback(independent_claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deterministically decomposes verbatim independent claims into structured clauses (a), (b), (c)...
    when clauses are present, extracting a concise technical concept for each element.
    """
    result: List[Dict[str, Any]] = []
    for claim in independent_claims:
        c_num = str(claim.get("claim_number", "1"))
        c_text = claim.get("text", "")
        if not c_text:
            continue

        # Split on (a), (b), (c), (d) or semicolon boundaries
        clause_pattern = re.compile(r"\(([a-z])\)\s+", re.IGNORECASE)
        matches = list(clause_pattern.finditer(c_text))
        elements: List[Dict[str, str]] = []

        if matches:
            for idx, m in enumerate(matches):
                letter = m.group(1).upper()
                start = m.end()
                end = matches[idx + 1].start() if idx + 1 < len(matches) else len(c_text)
                clause_body = c_text[start:end].strip().rstrip(";").rstrip(".")
                # Remove trailing "and" after semicolon
                clause_body = re.sub(r";\s*and\s*$", "", clause_body, flags=re.IGNORECASE).strip()
                concept = extract_concise_concept(clause_body)
                elements.append({
                    "element_id": f"{c_num}{letter}",
                    "description": clause_body,
                    "technical_concept": concept
                })
        else:
            parts = [p.strip() for p in c_text.split(";") if len(p.strip()) > 15]
            for idx, part in enumerate(parts):
                letter = chr(ord("A") + idx)
                elements.append({
                    "element_id": f"{c_num}{letter}",
                    "description": part,
                    "technical_concept": extract_concise_concept(part)
                })

        result.append({
            "claim_number": c_num,
            "elements": elements
        })
    return result


def extract_concise_concept(clause_text: str) -> str:
    """
    Extracts a clean 3-6 word technical concept label from a claim element clause.
    """
    words = re.findall(r"[A-Za-z0-9\-]+", clause_text)
    stop = {"a", "an", "the", "by", "of", "in", "to", "for", "with", "wherein", "comprising", "configured", "from", "at", "over"}
    meaningful = [w for w in words if w.lower() not in stop]
    return " ".join(meaningful[:5]).title() if meaningful else "Technical Claim Limitation"


def infer_baseline_technology_areas(title: str, abstract: str, cpc_codes: List[str]) -> Tuple[List[str], List[str]]:
    """
    Infers baseline technology areas and key technical concepts grounded in CPC codes, title, and abstract.
    Does not force a classification if evidence is insufficient.
    """
    combined = f"{title} {abstract}".lower()
    cpc_joined = " ".join(cpc_codes).upper()

    areas: List[str] = []
    concepts: List[str] = []

    if any(k in combined for k in ("recommendation", "personalized", "personalization", "ranking", "ranker", "canvas", "bandit", "artwork", "two-tower", "session-based", "submodular")) or "H04N21/466" in cpc_joined or "G06F16/735" in cpc_joined:
        areas.append("Video Streaming > Recommendation & Personalization")
    if any(k in combined for k in ("adaptive bitrate", "abr", "manifest", "hls", "dash", "cmaf", "chunk")) or "H04N21/8456" in cpc_joined:
        areas.append("Video Streaming > Adaptive Streaming")
    if any(k in combined for k in ("edge", "content delivery", "cdn", "cache", "prefetch", "coalescing", "bgp", "origin")) or "H04L67/568" in cpc_joined:
        areas.append("Video Streaming > Content Delivery")
    if any(k in combined for k in ("encoding", "encoder", "quantization", "gop", "reshaping", "hdr", "convex hull", "transcoding", "motion compensation", "multiplexing")) or "H04N19/" in cpc_joined:
        areas.append("Video Streaming > Video Encoding")
    if any(k in combined for k in ("playback", "synchronization", "splice", "spatial audio", "loudness", "clock", "trick-mode", "pacing", "congestion")) or "H04N21/43" in cpc_joined:
        areas.append("Video Streaming > Playback Optimization")
    if any(k in combined for k in ("dns", "tls", "cryptographic", "session ticket")) or "H04L63/" in cpc_joined:
        areas.append("Network Infrastructure > Edge Security & Routing")
    if any(k in combined for k in ("cmos", "image sensor", "photoelectric", "semiconductor")) or "H04N25/" in cpc_joined:
        areas.append("Hardware & Sensors > Solid-State Imaging")

    if not areas:
        areas.append("Unclassified / Insufficient Domain Evidence")

    # Key technical concepts extraction
    concept_patterns = [
        ("Two-Stage Personalized Video Ranking (PVR) & 2D Canvas Row Generation", r"two-stage|personalized video rank|two-dimensional.*canvas|submodular"),
        ("Contextual Multi-Armed Bandit Artwork & Thumbnail Personalization", r"contextual.*bandit|artwork|visual aesthetics|inverse propensity"),
        ("Session-Based Autoregressive Transformer Intent Recommendation", r"session-based|autoregressive.*transformer|in-session.*interaction|kl.*divergence"),
        ("Two-Tower Neural Embedding Retrieval & Graph Cold-Start Propagation", r"two-tower|approximate nearest neighbor|bipartite.*graph|cross-encoder"),
        ("Adaptive Bitrate (ABR) Control", r"adaptive bitrate|abr\b|bitrate ladder"),
        ("Client Buffer Telemetry (CMCD)", r"buffer occupancy|buffer telemetry|cmcd"),
        ("Low-Latency CMAF Chunked Delivery", r"cmaf|chunked transfer|incomplete live media"),
        ("Multi-CDN Manifest Steering", r"multi-cdn|manifest.*rewrit|session steering"),
        ("Per-Shot Convex Hull Encoding", r"convex hull|per-shot|rate-distortion"),
        ("HDR Polynomial Reshaping & SEI Signaling", r"reshaping|high dynamic range|sei\b"),
        ("CTU Quantization & Luma-Guided Chroma Prediction", r"quantization parameter|coding tree unit|chroma"),
        ("Spatial Audio Object Rendering", r"spatial audio|discrete audio object|binaural"),
        ("ISOBMFF Frame-Accurate Splice Conditioning", r"splice boundary|isobmff|edit list"),
        ("Look-Ahead Statistical Multiplexing & GOP Alignment", r"statistical multiplexing|look-ahead|scene-cut|gop"),
        ("Stateless Just-In-Time (JIT) Cloud Packaging", r"just-in-time|jit\b|partial media segment|mezzanine"),
        ("Transport-Layer Socket Pacing & Congestion Control", r"pacing rate|congestion|round-trip time variance"),
        ("ISP-Embedded Cache Appliance & BGP Traffic Steering", r"isp-embedded|bgp|off-peak"),
        ("Affine Motion Compensation (VVC/H.266)", r"affine motion|sub-block"),
        ("Interactive Slice-Based Cloud Frame Streaming", r"horizontal macroblock slice|nack|intra-coded"),
        ("Decoder Clock Drift & WSOLA Time-Scale Sync", r"time-scale modification|playhead offset|clock drift"),
    ]
    for label, pat in concept_patterns:
        if re.search(pat, combined):
            concepts.append(label)

    if not concepts:
        # Extract 3 noun phrases from title
        concepts.append(title[:65])

    return areas, concepts[:5]


def execute_deterministic_adk_stages(
    client_company: str,
    technology_area: Optional[str] = None,
    max_candidates: int = 6
) -> Dict[str, Any]:
    """
    Executes the deterministic Python pipeline stages:
    - Schema inspection (`patents-public-data.patents.publications`)
    - `patent_retrieval_agent` deterministic tools (Stage 1 resolution, Stage 2 screening, Stage 3 claim fetch)
    - Baseline structured representation + `patent_ranking_agent` deterministic tools
      (Step 5 patent life & Step 6 preliminary investigation relevance)
    """
    agent_trace: List[Dict[str, Any]] = []

    # Step 0: Schema inspection
    schema_info = inspect_bigquery_publications_schema(attempt_live_check=False)
    agent_trace.append({
        "agent": "patent_retrieval_agent",
        "step": "Step 1A — Schema Inspection",
        "tool": "inspect_bigquery_publications_schema",
        "status": "COMPLETED",
        "summary": f"Verified {len(schema_info['schema_fields'])} columns on `{schema_info['dataset']}`."
    })

    # Stage 1: Resolve client company
    resolution = resolve_client_company_tool(client_company)
    agent_trace.append({
        "agent": "patent_retrieval_agent",
        "step": "Step 1B — Stage 1: Client Company Assignee Resolution",
        "tool": "resolve_client_company_tool",
        "status": resolution["status"],
        "summary": (
            f"Resolved '{client_company}' -> '{resolution.get('resolved_assignee')}' ({resolution.get('publication_count')} publications)."
            if resolution["status"] == "RESOLVED"
            else resolution.get("message") or resolution.get("error", "Resolution halted.")
        )
    })

    if resolution["status"] != "RESOLVED":
        return {
            "pipeline_status": resolution["status"],
            "client_company": client_company,
            "technology_area": technology_area or "",
            "resolution": resolution,
            "schema_inspection": schema_info,
            "adk_architecture": {
                "runtime_mode": ADK_RUNTIME_MODE,
                "root_agent": root_agent.name,
                "sub_agents": [a.name for a in root_agent.sub_agents],
                "agent_trace": agent_trace
            },
            "patents": [],
            "technology_clusters": []
        }

    resolved_assignee = resolution["resolved_assignee"]

    # Stage 2: Candidate screening
    stage2 = retrieve_candidate_metadata_tool(
        resolved_assignee=resolved_assignee,
        technology_area=technology_area,
        max_candidates=max_candidates
    )
    dyn_bq = stage2.get("dynamic_bigquery_vector_search") or {}
    agent_trace.append({
        "agent": "patent_retrieval_agent",
        "step": "Step 1C — Stage 2: Candidate Metadata & Vector Screening (text-embedding-004)",
        "tool": "retrieve_candidate_metadata_tool",
        "status": stage2["status"],
        "summary": (
            f"Screened {stage2.get('total_portfolio_count', 0)} publications for {resolved_assignee} using "
            f"hybrid lexical + `text-embedding-004` (768-d) vector similarity; "
            f"selected {stage2.get('selected_candidate_count', 0)} candidates matching niche '{technology_area or 'All'}'."
            + (
                f" Triggered dynamic BigQuery Vector Search (`VECTOR_SEARCH` with `text-embedding-004`) and fetched {dyn_bq.get('fetched_count', 0)} new patent(s): {', '.join(dyn_bq.get('fetched_publications', []))}."
                if dyn_bq.get("triggered")
                else ""
            )
        )
    })

    if stage2["status"] != "CANDIDATES_RETRIEVED":
        return {
            "pipeline_status": stage2["status"],
            "client_company": client_company,
            "resolved_assignee": resolved_assignee,
            "technology_area": technology_area or "",
            "resolution": resolution,
            "stage2_retrieval": stage2,
            "schema_inspection": schema_info,
            "adk_architecture": {
                "runtime_mode": ADK_RUNTIME_MODE,
                "root_agent": root_agent.name,
                "sub_agents": [a.name for a in root_agent.sub_agents],
                "agent_trace": agent_trace
            },
            "patents": [],
            "technology_clusters": []
        }

    pub_numbers = [c["publication_number"] for c in stage2["candidates"]]

    # Stage 3: Targeted claims & description fetch
    stage3 = fetch_staged_patent_claims_tool(pub_numbers)
    agent_trace.append({
        "agent": "patent_retrieval_agent",
        "step": "Step 1D — Stage 3: Targeted Claim & Specification Fetch",
        "tool": "fetch_staged_patent_claims_tool",
        "status": stage3["status"],
        "summary": f"Fetched localized claims and description excerpts for {stage3['fetched_count']} shortlisted candidates."
    })

    # Build baseline patent intelligence records (ready for LLM enrichment in patent_analysis_agent)
    patents_out: List[Dict[str, Any]] = []
    for cand in stage2["candidates"]:
        pub_num = cand["publication_number"]
        claim_rec = stage3["records"].get(pub_num, {})
        ind_claims = claim_rec.get("independent_claims", [])

        # Step 5: Deterministic Patent Life
        patent_life = calculate_patent_life_tool(
            filing_date_int=cand.get("filing_date_raw", 0),
            priority_date_int=cand.get("priority_date_raw", 0),
            grant_date_int=cand.get("grant_date_raw", 0),
            kind_code=cand.get("kind_code", ""),
            country_code=cand.get("country_code", "US")
        )

        # Deterministic status derivation
        status_info = derive_publication_status(
            grant_date_int=cand.get("grant_date_raw", 0),
            kind_code=cand.get("kind_code", ""),
            country_code=cand.get("country_code", "US"),
            remaining_years=patent_life.get("estimated_remaining_term_years")
        )

        # Baseline Step 2, 3, 4 (will be enriched by Gemini LLM in patent_analysis_agent)
        tech_areas, key_concepts = infer_baseline_technology_areas(
            title=cand["title"],
            abstract=cand["abstract"],
            cpc_codes=cand["cpc_codes"]
        )
        claim_elements = decompose_claim_elements_fallback(ind_claims)
        ind_claim_texts = [c["text"] for c in ind_claims]
        patent_embedding_meta = embed_patent_content_tool(
            patent_number=pub_num,
            title=cand["title"],
            abstract=cand["abstract"],
            independent_claims=ind_claim_texts,
            claim_elements=claim_elements,
        )

        baseline_ai = {
            "technical_summary": cand["abstract"],
            "technology_areas": tech_areas,
            "key_concepts": key_concepts,
            "claim_elements": claim_elements
        }

        # Step 6: Deterministic + Explainable Investigation Relevance
        relevance = compute_investigation_relevance_tool(
            candidate_meta=cand,
            claim_record=claim_rec,
            patent_life=patent_life,
            ai_analysis=baseline_ai,
            technology_area=technology_area
        )

        patents_out.append({
            "patent_number": pub_num,
            "application_number": cand.get("application_number"),
            "family_id": cand.get("family_id"),
            "title": cand["title"],
            "abstract_source_fact": cand["abstract"],
            "description_excerpt_source_fact": claim_rec.get("description_excerpt"),
            "technical_summary": baseline_ai["technical_summary"],
            "technology_areas": baseline_ai["technology_areas"],
            "key_concepts": baseline_ai["key_concepts"],
            "independent_claims": ind_claim_texts,
            "independent_claims_structured": ind_claims,
            "claim_elements": baseline_ai["claim_elements"],
            "patent_embedding_metadata": patent_embedding_meta,
            "missing_claims_warning": claim_rec.get("missing_claims_warning"),
            "priority_date": cand["priority_date"],
            "filing_date": cand["filing_date"],
            "grant_date": cand["grant_date"],
            "status": status_info["status"],
            "status_fact_basis": status_info["fact_basis"],
            "estimated_remaining_term_years": patent_life["estimated_remaining_term_years"],
            "patent_life": patent_life,
            "cpc_codes": cand["cpc_codes"],
            "cpc_details": cand.get("cpc_details", []),
            "assignees": cand.get("assignees", []),
            "assignee_harmonized": cand.get("assignee_harmonized", []),
            "inventors": cand.get("inventors", []),
            "investigation_relevance": {
                "score": relevance["score"],
                "reasons": relevance["reasons"],
                "factor_breakdown": relevance["factor_breakdown"]
            },
            "epistemic_Provenance": {
                "source_facts": [
                    "patent_number",
                    "title",
                    "abstract_source_fact",
                    "independent_claims",
                    "priority_date",
                    "filing_date",
                    "grant_date",
                    "cpc_codes",
                    "assignee_harmonized",
                    "inventors"
                ],
                "deterministic_calculations": [
                    "status",
                    "estimated_remaining_term_years",
                    "patent_life",
                    "investigation_relevance.score"
                ],
                "ai_interpretations": [
                    "technical_summary",
                    "technology_areas",
                    "key_concepts",
                    "claim_elements"
                ]
            },
            "source": "Google Patents Public Dataset"
        })

    # Sort by investigation_relevance.score DESC
    patents_out.sort(key=lambda p: p["investigation_relevance"]["score"], reverse=True)

    # Build Technology Clusters summary (Step 4)
    clusters_map: Dict[str, List[Dict[str, Any]]] = {}
    for pat in patents_out:
        for area in pat.get("technology_areas", ["Unclassified"]):
            if area not in clusters_map:
                clusters_map[area] = []
            clusters_map[area].append({
                "patent_number": pat["patent_number"],
                "title": pat["title"],
                "relevance_score": pat["investigation_relevance"]["score"]
            })

    technology_clusters = [
        {
            "cluster_name": area,
            "parent_domain": area.split(" > ")[0] if " > " in area else area,
            "sub_area": area.split(" > ")[1] if " > " in area else area,
            "patent_count": len(items),
            "patents": items
        }
        for area, items in clusters_map.items()
    ]

    agent_trace.append({
        "agent": "patent_analysis_agent",
        "step": "Step 2, 3 & 4 — Patent Analysis, Claim Element Decomposition & Clustering",
        "tool": "llm_claim_and_concept_analysis",
        "status": "READY_FOR_LLM_ENRICHMENT",
        "summary": f"Prepared {len(patents_out)} candidates with verbatim independent claims and source facts."
    })

    agent_trace.append({
        "agent": "patent_ranking_agent",
        "step": "Step 5 & 6 — Deterministic Patent Life & Investigation Relevance Ranking",
        "tool": "calculate_patent_life_tool + compute_investigation_relevance_tool",
        "status": "COMPLETED",
        "summary": f"Computed statutory 20-year term estimates and ranked {len(patents_out)} patents by preliminary Investigation Relevance."
    })

    return {
        "pipeline_status": "SUCCESS",
        "client_company": client_company,
        "resolved_assignee": resolved_assignee,
        "technology_area": technology_area or "",
        "resolution": resolution,
        "staged_retrieval_metrics": {
            "stage1_harmonized_assignee": resolved_assignee,
            "stage2_total_portfolio_records": stage2["total_portfolio_count"],
            "stage2_filtered_out_records": stage2["filtered_out_count"],
            "stage2_shortlisted_candidates": stage2["selected_candidate_count"],
            "stage3_full_claims_fetched": stage3["fetched_count"],
            "embedding_model": "text-embedding-004",
            "embedding_dimensions": 768,
            "dynamic_bigquery_vector_search": stage2.get("dynamic_bigquery_vector_search"),
            "stage1_sql": resolution.get("stage1_sql"),
            "stage2_sql": stage2.get("stage2_sql"),
            "stage3_sql": stage3.get("stage3_sql")
        },
        "schema_inspection": schema_info,
        "adk_architecture": {
            "runtime_mode": ADK_RUNTIME_MODE,
            "root_agent": root_agent.name,
            "sub_agents": [a.name for a in root_agent.sub_agents],
            "agent_trace": agent_trace
        },
        "technology_clusters": technology_clusters,
        "patents": patents_out
    }
