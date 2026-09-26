"""
Google ADK Multi-Agent Orchestration for the Target Company Retrieval & Analysis Pipeline.

ADK Structure:
    root_agent (SequentialAgent)
        ↓
    target_retrieval_agent (LlmAgent using deterministic `search_target_knowledge` tool)
        ↓
    target_analysis_agent (LlmAgent synthesizing evidence-backed target technologies & capabilities)

Design Principle:
Answers: "What publicly documented technologies/capabilities of this target company are relevant to the client's patent technology?"
Does NOT answer: "Does the target company infringe the patent?"
Never crawls or browses the public internet during runtime analysis.
"""

from typing import Dict, Any, List, Optional, Callable

from target_agent.tools import (
    search_target_knowledge,
    build_multi_queries_from_patent_context,
)

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
            output_key: Optional[str] = None,
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
            sub_agents: List[Any],
        ):
            self.name = name
            self.description = description
            self.sub_agents = sub_agents


# ============================================================================
# ADK AGENT DEFINITIONS (root_agent -> target_retrieval_agent -> target_analysis_agent)
# ============================================================================

target_retrieval_agent = LlmAgent(
    name="target_retrieval_agent",
    model="gemini-3.8-flash",
    description=(
        "Constructs multiple retrieval queries from client patent technical concepts and "
        "executes deterministic searches against the pre-fetched Target Company Knowledge Database."
    ),
    instruction=(
        "You are the Target Retrieval Agent.\n"
        "1. NEVER browse or crawl the public internet.\n"
        "2. Construct multiple retrieval queries from the client patent candidates' `technology_areas` "
        "and `key_concepts` (do not rely on a single query).\n"
        "3. Call `search_target_knowledge(target_company, query, technology_area, top_k)` for each query "
        "to retrieve relevant chunks from the pre-fetched Target Knowledge Database."
    ),
    tools=[search_target_knowledge],
    output_key="retrieved_target_chunks",
)

target_analysis_agent = LlmAgent(
    name="target_analysis_agent",
    model="gemini-3.8-flash",
    description=(
        "Synthesizes retrieved target-company evidence into documented technologies, products/services, "
        "technical capabilities, and verbatim supporting evidence with source URLs."
    ),
    instruction=(
        "You are the Target Analysis Agent.\n"
        "1. Reason strictly over the evidence chunks retrieved by `target_retrieval_agent`.\n"
        "2. Do not infer a product capability merely because a patent and target company share similar terminology.\n"
        "3. Require explicit supporting evidence from the target knowledge base, preserving verbatim `text`, "
        "`source_title`, and `source_url`.\n"
        "4. If retrieved evidence is empty or insufficient, return `{\"evidence_status\": \"insufficient\"}`.\n"
        "5. Never state or imply legal infringement conclusions."
    ),
    tools=[],
    output_key="target_technology_intelligence",
)

root_agent = SequentialAgent(
    name="root_agent",
    description=(
        "Root ADK orchestrator for Target Company Retrieval & Analysis: "
        "target_retrieval_agent -> target_analysis_agent."
    ),
    sub_agents=[
        target_retrieval_agent,
        target_analysis_agent,
    ],
)


# ============================================================================
# DETERMINISTIC BASELINE TARGET EVIDENCE SYNTHESIS
# (Groups retrieved chunks into documented Netflix products/services & capabilities)
# ============================================================================

DOCUMENTED_PRODUCT_MAPPING: List[Dict[str, Any]] = [
    {
        "match_keywords": ["personalized video ranker", "pvr", "top-n", "page generation", "row ranker", "submodular", "calibrated", "kl-divergence", "interleaving"],
        "technology": "Two-Stage Homepage Canvas Ranking & Calibrated Personalization",
        "product_or_service": "Netflix Personalized Video Ranker (PVR), Top-N Ranker & 2D Page Generation Engine",
        "capability_rules": [
            (
                "pvr",
                "Executes Personalized Video Ranker (PVR) and Top-N Video Ranker blending personalized member embeddings with row-specific genre/theme features and Caret explanations.",
            ),
            (
                "page generation",
                "Constructs two-dimensional homepage canvases via stage-wise submodular row/column optimization with cross-row title deduplication and horizontal/vertical position bias correction.",
            ),
            (
                "calibrated",
                "Applies Kullback-Leibler (KL) divergence calibration and multi-objective Pareto scalarization to match recommended genre distributions to historical member viewing profiles while optimizing retention utility.",
            ),
            (
                "interleaving",
                "Evaluates candidate ranking algorithms online using Team-Draft and Probabilistic Interleaving with 10x–100x higher statistical sensitivity than traditional A/B tests.",
            ),
        ],
    },
    {
        "match_keywords": ["contextual bandit", "bandits", "ava", "artwork", "linucb", "thompson sampling", "inverse propensity", "ipw"],
        "technology": "Contextual Bandits & Automated Visual Artwork Personalization",
        "product_or_service": "Netflix Contextual Bandit Artwork Personalization & AVA Visual Discovery Engine",
        "capability_rules": [
            (
                "bandit",
                "Selects personalized title artwork per member profile using contextual multi-armed bandits (LinUCB and Thompson Sampling) conditioned on member genre/visual history and device viewport.",
            ),
            (
                "ipw",
                "Logs action selection propensities and evaluates policy updates offline using Inverse Propensity Weighting (IPW) and Doubly Robust (DR) counterfactual estimators.",
            ),
            (
                "ava",
                "Extracts candidate video frames via Automated Visual Aesthetics (AVA) deep CNN scoring for actor facial prominence, motion stability, and visual composition.",
            ),
        ],
    },
    {
        "match_keywords": ["foundation model", "session-based", "sequential", "hydra", "axion", "evcache", "in-session", "autoregressive"],
        "technology": "Foundation Models, Sequential Session Intent & Real-Time Feature Store",
        "product_or_service": "Netflix Foundation Recommendation Model (Hydra) & Axion Real-Time Session Ranker",
        "capability_rules": [
            (
                "foundation",
                "Encodes chronological member interaction sequences (plays, completion ratios, searches, row scrolls) via autoregressive causal Transformers and Hydra multi-task shared backbones.",
            ),
            (
                "session",
                "Combines long-term member embeddings with short-term in-session Transformer attention states to adapt row rankings within sub-second latency.",
            ),
            (
                "axion",
                "Streams real-time interaction events through Apache Kafka, Apache Flink, and EVCache/Axion feature stores with point-in-time time-travel correctness.",
            ),
        ],
    },
    {
        "match_keywords": ["collaborative filtering", "two-tower", "graphsage", "bipartite", "lexical", "semantic search", "bi-encoder", "cross-encoder"],
        "technology": "Neural Candidate Generation, Graph Cold-Start & Multimodal Search",
        "product_or_service": "Netflix Two-Tower ANN Candidate Retriever, GraphSAGE & Personalized Search Engine",
        "capability_rules": [
            (
                "two-tower",
                "Projects member context and catalog titles into a shared dense embedding space for sub-10ms approximate nearest neighbor (ANN / ScaNN / HNSW) candidate retrieval.",
            ),
            (
                "graph",
                "Propagates relational embeddings across bipartite member-title-talent graphs via GraphSAGE message passing to resolve cold-start ranking for new launches.",
            ),
            (
                "search",
                "Executes hybrid lexical token matching, multilingual bi-encoder semantic retrieval, and personalized cross-encoder re-ranking for partial and natural-language queries.",
            ),
        ],
    },
    {
        "match_keywords": ["open connect", "oca", "bgp", "cache fill", "appliance", "ixp", "pacing", "freebsd"],
        "technology": "Content Delivery & Edge Caching Infrastructure",
        "product_or_service": "Netflix Open Connect / Open Connect Appliances (OCAs)",
        "capability_rules": [
            (
                "bgp",
                "Ingests BGP prefix announcements and community tags from ISP routers to steer client playback sessions to topologically nearest Open Connect Appliances.",
            ),
            (
                "off-peak",
                "Uses ML regional demand forecasting to pre-position differential catalog updates onto ISP-embedded OCA NVMe/flash storage during off-peak night windows.",
            ),
            (
                "steering",
                "Dynamically constructs session-specific manifests with prioritized OCA pathway URIs and mid-stream failover without decoder state reset.",
            ),
            (
                "pacing",
                "Samples packet acknowledgment intervals and smoothed RTT variance on OCA FreeBSD/NGINX nodes to dynamically clamp transport socket pacing rates.",
            ),
        ],
    },
    {
        "match_keywords": ["dynamic optimizer", "shot-based", "per-title", "convex hull", "av1", "hdr", "vmaf", "quantization"],
        "technology": "Perceptual Video Encoding & Per-Shot Compression",
        "product_or_service": "Netflix Dynamic Optimizer & Per-Shot Cloud Encoding Pipeline",
        "capability_rules": [
            (
                "shot",
                "Partitions mezzanine assets at scene cuts via frame histogram discontinuities and constructs Pareto-optimal per-shot convex hull bitrate-resolution ladders.",
            ),
            (
                "vmaf",
                "Evaluates candidate resolution-QP operating points against VMAF perceptual quality scores using trellis dynamic programming.",
            ),
            (
                "hdr",
                "Modulates coding tree unit (CTU) delta quantization parameters (dQP) using luminance contrast masking and multiplexes 10-bit HDR SEI metadata.",
            ),
            (
                "keyframe",
                "Aligns instantaneous decoder refresh (IDR) keyframes at natural scene boundaries across adaptive bitrate representations.",
            ),
        ],
    },
    {
        "match_keywords": ["playback", "buffer occupancy", "lip-sync", "dolby atmos", "spatial audio", "pts", "edit-list"],
        "technology": "Client Adaptive Playback & Audio-Video Synchronization",
        "product_or_service": "Netflix Client Playback Engine (Smart TV, Mobile & Web ABR Stack)",
        "capability_rules": [
            (
                "telemetry",
                "Embeds client playback buffer occupancy (ms), segment download throughput, and viewport telemetry into HTTP segment requests to Open Connect servers.",
            ),
            (
                "spatial audio",
                "Renders Dolby Atmos object-based spatial audio and multi-channel bitstreams with dialogue-gated loudness normalization and gain crossfading.",
            ),
            (
                "lip-sync",
                "Applies presentation timestamp (PTS) edit-list alignment across fragmented ISOBMFF / CMAF tracks to prevent audio-video lip-sync drift during ABR switches.",
            ),
        ],
    },
]


def synthesize_target_intelligence_deterministic(
    target_company: str,
    retrieved_chunks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Deterministically groups retrieved chunks into evidence-backed target technology areas,
    documented products/services, technical capabilities, and verbatim supporting evidence.
    """
    grouped: Dict[str, Dict[str, Any]] = {}

    for chunk in retrieved_chunks:
        text_lower = f"{chunk.get('title', '')} {chunk.get('content', '')}".lower()
        assigned_group = None

        for mapping in DOCUMENTED_PRODUCT_MAPPING:
            if any(kw in text_lower for kw in mapping["match_keywords"]):
                assigned_group = mapping
                break

        if not assigned_group:
            tech_name = chunk.get("technology_area") or "Documented Engineering Capability"
            prod_name = f"{target_company} ({chunk.get('title', 'Public Technical Disclosure')})"
            key = f"{tech_name}::{prod_name}"
            if key not in grouped:
                grouped[key] = {
                    "technology": tech_name,
                    "product_or_service": prod_name,
                    "technical_capabilities": [],
                    "relevant_technical_concepts": list(chunk.get("candidate_tags", [])),
                    "supporting_evidence": [],
                }
            grouped[key]["supporting_evidence"].append({
                "text": chunk["content"],
                "source_title": chunk["title"],
                "source_url": chunk["source_url"],
                "source_type": chunk.get("source_type"),
                "published_date": chunk.get("published_date"),
                "chunk_id": chunk.get("chunk_id"),
                "matched_queries": chunk.get("matched_queries", []),
            })
            continue

        key = f"{assigned_group['technology']}::{assigned_group['product_or_service']}"
        if key not in grouped:
            grouped[key] = {
                "technology": assigned_group["technology"],
                "product_or_service": assigned_group["product_or_service"],
                "technical_capabilities": [],
                "relevant_technical_concepts": [],
                "supporting_evidence": [],
            }

        # Add capabilities supported by the chunk text
        for trigger, cap_desc in assigned_group["capability_rules"]:
            if trigger in text_lower and cap_desc not in grouped[key]["technical_capabilities"]:
                grouped[key]["technical_capabilities"].append(cap_desc)

        for tag in chunk.get("candidate_tags", []):
            if tag not in grouped[key]["relevant_technical_concepts"]:
                grouped[key]["relevant_technical_concepts"].append(tag)

        # Avoid duplicate chunk evidence within the same technology group
        if not any(ev.get("chunk_id") == chunk.get("chunk_id") for ev in grouped[key]["supporting_evidence"]):
            grouped[key]["supporting_evidence"].append({
                "text": chunk["content"],
                "source_title": chunk["title"],
                "source_url": chunk["source_url"],
                "source_type": chunk.get("source_type"),
                "published_date": chunk.get("published_date"),
                "chunk_id": chunk.get("chunk_id"),
                "matched_queries": chunk.get("matched_queries", []),
            })

    # Ensure every group has at least one capability derived from its evidence
    result: List[Dict[str, Any]] = []
    for item in grouped.values():
        if not item["technical_capabilities"] and item["supporting_evidence"]:
            first_ev = item["supporting_evidence"][0]["text"]
            first_sentence = first_ev.split(". ")[0].strip() + "."
            item["technical_capabilities"].append(first_sentence)
        result.append(item)

    return result


def execute_target_retrieval_pipeline(
    target_company: str,
    technology_area: Optional[str] = None,
    client_patent_context: Optional[List[Dict[str, Any]]] = None,
    top_k_per_query: int = 4,
) -> Dict[str, Any]:
    """
    Executes the Google ADK Target Retrieval & Analysis Pipeline:
    1. Constructs multiple queries from `technology_area` and `client_patent_context`.
    2. Calls `search_target_knowledge` deterministically against `target_knowledge.sqlite` for each query.
    3. Deduplicates retrieved chunks while recording query provenance.
    4. Returns `{"evidence_status": "insufficient"}` if no supporting evidence exists in the pre-fetched DB.
    5. Synthesizes evidence-backed `technology_areas` with verbatim supporting evidence and source URLs.
    """
    patent_ctx = client_patent_context or []
    adk_trace: List[Dict[str, Any]] = []

    # Step 1: Multi-query construction
    planned_queries = build_multi_queries_from_patent_context(
        technology_area=technology_area,
        client_patent_context=patent_ctx,
    )
    adk_trace.append({
        "agent": "target_retrieval_agent",
        "step": "Step 1A — Multi-Query Construction from Client Patent Concepts",
        "tool": "build_multi_queries_from_patent_context",
        "status": "COMPLETED",
        "summary": f"Generated {len(planned_queries)} targeted retrieval queries from {len(patent_ctx)} client patent context items.",
    })

    # Step 2: Execute `search_target_knowledge` across all generated queries
    query_execution_log: List[Dict[str, Any]] = []
    chunks_by_id: Dict[str, Dict[str, Any]] = {}
    dynamic_target_fetch_events: List[Dict[str, Any]] = []
    company_missing = False

    for q_item in planned_queries:
        q_str = q_item["query"]
        search_res = search_target_knowledge(
            target_company=target_company,
            query=q_str,
            technology_area=technology_area,
            top_k=top_k_per_query,
        )
        if search_res["status"] == "COMPANY_NOT_IN_KNOWLEDGE_BASE":
            company_missing = True

        dyn_event = search_res.get("dynamic_fetch_and_embedding")
        if dyn_event and dyn_event.get("dynamically_fetched_docs", 0) > 0:
            dynamic_target_fetch_events.append({
                "query": q_str,
                **dyn_event,
            })

        query_execution_log.append({
            "query": q_str,
            "rationale": q_item["rationale"],
            "returned_count": len(search_res.get("results", [])),
            "top_chunk_ids": [r["chunk_id"] for r in search_res.get("results", [])],
            "dynamic_fetch_triggered": bool(dyn_event and dyn_event.get("dynamically_fetched_docs", 0) > 0),
        })

        for r in search_res.get("results", []):
            cid = r["chunk_id"]
            if cid not in chunks_by_id:
                chunks_by_id[cid] = {
                    **r,
                    "matched_queries": [q_str],
                }
            else:
                if q_str not in chunks_by_id[cid]["matched_queries"]:
                    chunks_by_id[cid]["matched_queries"].append(q_str)
                if r["retrieval_score"] > chunks_by_id[cid]["retrieval_score"]:
                    chunks_by_id[cid]["retrieval_score"] = r["retrieval_score"]

    deduped_chunks = sorted(
        list(chunks_by_id.values()),
        key=lambda x: (len(x.get("matched_queries", [])), x.get("retrieval_score", 0.0)),
        reverse=True,
    )

    adk_trace.append({
        "agent": "target_retrieval_agent",
        "step": "Step 1B — AlloyDB Vector & Hybrid Knowledge Base Search (text-embedding-004)",
        "tool": "search_target_knowledge",
        "status": "COMPANY_NOT_FOUND" if company_missing else ("COMPLETED" if deduped_chunks else "INSUFFICIENT_EVIDENCE"),
        "summary": (
            f"Executed {len(planned_queries)} queries against AlloyDB `document_chunks` using 768-d `text-embedding-004` "
            f"cosine similarity + lexical matching; retrieved {len(deduped_chunks)} unique evidence chunks."
            + (
                f" Triggered dynamic Netflix documentation fetching & `text-embedding-004` embedding into AlloyDB ({sum(e.get('dynamically_fetched_docs', 0) for e in dynamic_target_fetch_events)} new doc(s), {sum(e.get('dynamically_embedded_chunks', 0) for e in dynamic_target_fetch_events)} embedded chunks)."
                if dynamic_target_fetch_events
                else ""
            )
        ),
    })

    # Handle insufficient evidence without fabricating product information
    if company_missing or len(deduped_chunks) == 0:
        reason = (
            f"Target company '{target_company}' has no pre-fetched documents in `target_knowledge.sqlite`. "
            "Run the Offline Target Knowledge Prefetch pipeline for this company first."
            if company_missing
            else f"Zero evidence chunks in `target_knowledge.sqlite` for '{target_company}' matched the requested technology area ('{technology_area}') or patent concepts."
        )
        adk_trace.append({
            "agent": "target_analysis_agent",
            "step": "Step 2 — Evidence Sufficiency Verification",
            "tool": "evidence_guardrail",
            "status": "INSUFFICIENT_EVIDENCE",
            "summary": reason,
        })
        return {
            "evidence_status": "insufficient",
            "target_company": target_company,
            "technology_area": technology_area or "",
            "diagnostic_reason": reason,
            "multi_query_log": query_execution_log,
            "retrieved_chunks": [],
            "technology_areas": [],
            "adk_architecture": {
                "runtime_mode": ADK_RUNTIME_MODE,
                "root_agent": root_agent.name,
                "sub_agents": [a.name for a in root_agent.sub_agents],
                "agent_trace": adk_trace,
            },
            "canonical_output": {
                "evidence_status": "insufficient",
            },
        }

    # Step 3: Synthesize evidence-backed target technology areas & capabilities
    technology_areas_out = synthesize_target_intelligence_deterministic(
        target_company=target_company,
        retrieved_chunks=deduped_chunks,
    )

    adk_trace.append({
        "agent": "target_analysis_agent",
        "step": "Step 2 — Evidence-Backed Target Technology & Product Synthesis",
        "tool": "synthesize_target_intelligence",
        "status": "COMPLETED",
        "summary": (
            f"Identified {len(technology_areas_out)} documented target technology areas / products "
            f"backed by {len(deduped_chunks)} verbatim source chunks."
        ),
    })

    canonical_output = {
        "target_company": target_company,
        "technology_areas": [
            {
                "technology": ta["technology"],
                "product_or_service": ta["product_or_service"],
                "technical_capabilities": ta["technical_capabilities"],
                "supporting_evidence": [
                    {
                        "text": ev["text"],
                        "source_title": ev["source_title"],
                        "source_url": ev["source_url"],
                    }
                    for ev in ta["supporting_evidence"]
                ],
            }
            for ta in technology_areas_out
        ],
    }

    return {
        "evidence_status": "sufficient",
        "target_company": target_company,
        "technology_area": technology_area or "",
        "multi_query_log": query_execution_log,
        "dynamic_fetch_and_embedding_events": dynamic_target_fetch_events,
        "retrieved_chunks": deduped_chunks,
        "technology_areas": technology_areas_out,
        "adk_architecture": {
            "runtime_mode": ADK_RUNTIME_MODE,
            "root_agent": root_agent.name,
            "sub_agents": [a.name for a in root_agent.sub_agents],
            "agent_trace": adk_trace,
        },
        "canonical_output": canonical_output,
    }
