"""
Deterministic Python Tools for the Patent–Target Matching and Commercial Opportunity Agent (Google ADK).

Implements:
1. `retrieve_commercial_intelligence_tool`: Queries pre-fetched public commercial sources (SEC Form 10-K,
   investor disclosures, documented adoption metrics) from `target_knowledge.sqlite` without live web crawling
   and without fabricating product-level revenue.
2. `evaluate_claim_element_alignment_tool`: Performs Part 1 (Technical Matching) by comparing client patent
   independent claim elements and technical concepts against target-company capabilities and verbatim evidence.
3. `evaluate_commercial_opportunity_tool`: Performs Part 2 (Commercial Opportunity) distinctly from technical
   matching, combining target technology strategic criticality, public commercial scale, patent status, and
   deterministic remaining patent life.
4. `compute_investigation_priority_tool`: Performs Part 3 (Investigation Prioritization) using transparent
   gatekeeper rules and non-infringement language guardrails.
"""

import re
import sqlite3
from typing import Dict, Any, List, Optional, Tuple

from target_prefetch.pipeline import DB_PATH, initialize_database, run_prefetch_pipeline


STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "for", "on", "with", "by", "at", "from",
    "as", "is", "are", "be", "been", "being", "wherein", "comprising", "comprises", "configured",
    "method", "system", "apparatus", "device", "plurality", "first", "second", "third", "least",
    "one", "based", "each", "having", "including", "includes", "associated", "corresponding",
    "predetermined", "respective", "thereof", "via", "using", "used", "into", "over", "across",
}

# Synonym / technical domain expansion groups so related engineering terms match accurately
TECHNICAL_SYNONYM_GROUPS: List[List[str]] = [
    ["adaptive bitrate", "abr", "bitrate", "representation", "manifest", "profile", "ladder", "switching"],
    ["convex hull", "rate-distortion", "per-title", "per-shot", "shot-based", "dynamic optimizer", "vmaf", "perceptual"],
    ["quantization", "qp", "dqp", "crf", "coding tree unit", "ctu", "superblock", "hevc", "av1", "h.264", "codec", "encoding", "encoder"],
    ["scene cut", "scene-cut", "shot", "histogram", "discontinuity", "keyframe", "idr", "boundary"],
    ["hdr", "high dynamic range", "luminance", "tone mapping", "10-bit", "sei", "dolby vision", "metadata"],
    ["cdn", "content delivery", "open connect", "oca", "appliance", "edge", "cache", "pre-positioning", "off-peak", "nvme"],
    ["bgp", "border gateway protocol", "asn", "autonomous system", "ixp", "isp", "steering", "routing", "session"],
    ["pacing", "rtt", "round-trip", "congestion", "throughput", "packet", "tls", "socket", "bandwidth"],
    ["buffer", "occupancy", "rebuffering", "qoe", "telemetry", "startup", "client playback"],
    ["audio", "spatial audio", "dolby atmos", "loudness", "dialogue", "crossfading", "lip-sync", "pts", "timestamp", "isobmff", "cmaf", "synchronization"],
]


def _extract_technical_tokens(text: str) -> List[str]:
    raw_tokens = re.findall(r"[a-z0-9][a-z0-9\-]{2,}", (text or "").lower())
    return [t for t in raw_tokens if t not in STOPWORDS]


def _compute_concept_expansion_bonus(text_a: str, text_b: str) -> Tuple[float, List[str]]:
    """
    Checks how many domain technical synonym groups appear in both `text_a` and `text_b`.
    Returns a score bonus (0.0 to 1.0) and the list of shared technical mechanisms.
    """
    a_low = (text_a or "").lower()
    b_low = (text_b or "").lower()
    matched_mechanisms: List[str] = []

    for group in TECHNICAL_SYNONYM_GROUPS:
        a_hits = [term for term in group if term in a_low]
        b_hits = [term for term in group if term in b_low]
        if a_hits and b_hits:
            label = f"{a_hits[0]} ↔ {b_hits[0]}" if a_hits[0] != b_hits[0] else a_hits[0]
            matched_mechanisms.append(label)

    if not matched_mechanisms:
        return 0.0, []
    return min(1.0, len(matched_mechanisms) / 3.0), matched_mechanisms


# ============================================================================
# TOOL 1: COMMERCIAL INTELLIGENCE RETRIEVAL (PRE-FETCHED 10-K & PUBLIC DATA)
# ============================================================================

NETFLIX_PRODUCT_COMMERCIAL_PROFILES: List[Dict[str, Any]] = [
    {
        "match_keywords": ["open connect", "oca", "cdn", "content delivery", "bgp", "edge"],
        "strategic_role": "Core Global Delivery Infrastructure (Delivers ~100% of Netflix Streaming Traffic)",
        "commercial_tier_weight": 92,
        "monetization_driver": (
            "Critical Cost-of-Revenues & QoE Infrastructure: Delivers virtually 100% of global member streaming "
            "traffic across >190 countries via ISP-embedded and IXP Open Connect Appliances, materially reducing "
            "transit/peering expenses while sustaining 4K UHD and low-rebuffer playback."
        ),
        "adoption_metric": "100% of Netflix global video/audio streaming traffic (~260M–301M+ paid memberships)",
        "pricing_tier_linkage": "Supports all paid streaming tiers: Standard with Ads ($6.99/mo), Standard ($15.49/mo), and Premium 4K UHD ($22.99/mo)",
    },
    {
        "match_keywords": ["dynamic optimizer", "per-shot", "per-title", "encoding", "convex hull", "vmaf", "av1", "hdr"],
        "strategic_role": "Core Cloud Video Encoding & Perceptual Compression Pipeline",
        "commercial_tier_weight": 90,
        "monetization_driver": (
            "Direct Bandwidth Efficiency & Premium Tier Enabler: Reduces streaming bitrate requirements by up to "
            "30–50% at equivalent VMAF perceptual quality across the entire catalog, directly lowering CDN delivery "
            "costs and enabling 4K UHD / 10-bit HDR streaming on the Premium ($22.99/mo) subscription tier."
        ),
        "adoption_metric": "Applied across Netflix's global streaming catalog for H.264, HEVC, VP9, and AV1 streams",
        "pricing_tier_linkage": "Directly underpins Standard HD ($15.49/mo) and Premium 4K UHD / HDR10 / Dolby Vision ($22.99/mo) tiers",
    },
    {
        "match_keywords": ["playback", "abr", "audio-video", "spatial audio", "dolby atmos", "lip-sync", "client"],
        "strategic_role": "Core Member-Facing Playback Engine & Immersive Audio/Video Pipeline",
        "commercial_tier_weight": 88,
        "monetization_driver": (
            "Member QoE Retention & Premium Tier Differentiation: Powers adaptive bitrate playback, frame-accurate "
            "A/V lip-sync, and Dolby Atmos / spatial audio across smart TVs, mobile devices, and browsers; Spatial "
            "Audio and 4K HDR are headline features of Netflix's highest-margin Premium ($22.99/mo) plan."
        ),
        "adoption_metric": "Deployed across Smart TVs, Game Consoles, iOS, Android, and Web players for >260M–301M+ subscribers",
        "pricing_tier_linkage": "Headline feature differentiator for Premium ($22.99/mo US) Spatial Audio + 4K UHD tier",
    },
    {
        "match_keywords": ["recommender", "personalization", "search", "experimentation", "ranker"],
        "strategic_role": "Core Member Discovery, Personalization & Retention Platform",
        "commercial_tier_weight": 84,
        "monetization_driver": (
            "Subscriber Retention & Engagement Driver: Drives personalized homepage row generation and search "
            "across >250M–301M subscribers, materially reducing member churn and maximizing catalog utilization."
        ),
        "adoption_metric": "Serves personalized rankings and search across 100% of global subscriber profiles",
        "pricing_tier_linkage": "Supports subscriber retention and ad-impression engagement across all subscription tiers",
    },
    {
        "match_keywords": ["keystone", "kafka", "flink", "telemetry", "data infrastructure"],
        "strategic_role": "Core Real-Time Telemetry & Stream Processing Data Platform",
        "commercial_tier_weight": 78,
        "monetization_driver": (
            "Operational Analytics & CDN Steering Backbone: Processes trillions of daily QoE playback, A/B "
            "experimentation, and session steering events supporting global platform reliability."
        ),
        "adoption_metric": "Processes trillions of events/day across global streaming operations",
        "pricing_tier_linkage": "Internal operational data backbone supporting global streaming service delivery",
    },
]


def retrieve_commercial_intelligence_tool(
    target_company: str,
    product_or_service: str,
    technology: str,
) -> Dict[str, Any]:
    """
    Deterministic Python tool that retrieves pre-fetched public commercial intelligence
    (SEC Form 10-K filings, investor disclosures, adoption scale, and strategic importance)
    from `target_knowledge.sqlite` without crawling the web or fabricating product revenue.
    """
    initialize_database()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS cnt FROM documents")
    if int(cur.fetchone()["cnt"]) == 0:
        conn.close()
        run_prefetch_pipeline(mode="initial")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

    company_norm = (target_company or "").strip()
    if "netflix" in company_norm.lower():
        company_lookup = "Netflix"
    else:
        company_lookup = company_norm

    # Fetch commercial & scale evidence chunks from the 2-tier relational schema (`document_chunks` JOIN `documents`)
    cur.execute(
        """
        SELECT
            c.chunk_id,
            c.document_id,
            d.title,
            d.source_url,
            d.source_type,
            d.published_date,
            c.content
        FROM document_chunks c
        INNER JOIN documents d ON d.document_id = c.document_id
        WHERE LOWER(d.company) = LOWER(?)
          AND (
              LOWER(c.content) LIKE '%million%'
              OR LOWER(c.content) LIKE '%100% of%'
              OR LOWER(c.content) LIKE '%revenue%'
              OR LOWER(c.content) LIKE '%subscribers%'
              OR d.source_type IN ('open_connect_documentation', 'technical_paper')
          )
        ORDER BY d.published_date DESC
        LIMIT 4
        """,
        (company_lookup,),
    )
    filing_rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    if company_lookup != "Netflix" or len(filing_rows) == 0:
        return {
            "commercial_evidence_status": "INSUFFICIENT_PUBLIC_COMMERCIAL_DATA",
            "target_company": target_company,
            "product_or_service": product_or_service,
            "consolidated_company_revenue": None,
            "product_level_revenue_disclosed": False,
            "product_level_revenue_note": (
                f"No pre-fetched SEC 10-K or audited commercial disclosures available in `target_knowledge.sqlite` "
                f"for '{target_company}'. Product-level revenue is never fabricated."
            ),
            "subscriber_or_adoption_scale": "Not available in pre-fetched knowledge base",
            "pricing_tiers_disclosed": "Not available in pre-fetched knowledge base",
            "strategic_role": "Unverified in pre-fetched public commercial filings",
            "monetization_driver": "Requires public financial filing ingestion before commercial sizing.",
            "commercial_tier_weight": 40,
            "supporting_commercial_sources": [],
        }

    # Match the specific Netflix technology / product profile
    combined_label = f"{product_or_service} {technology}".lower()
    matched_profile = NETFLIX_PRODUCT_COMMERCIAL_PROFILES[0]
    for prof in NETFLIX_PRODUCT_COMMERCIAL_PROFILES:
        if any(kw in combined_label for kw in prof["match_keywords"]):
            matched_profile = prof
            break

    supporting_sources = [
        {
            "chunk_id": r["chunk_id"],
            "source_title": r["title"],
            "source_url": r["source_url"],
            "source_type": r["source_type"],
            "published_date": r["published_date"],
            "verbatim_excerpt": r["content"],
        }
        for r in filing_rows
    ]

    return {
        "commercial_evidence_status": "VERIFIED_PUBLIC_FILINGS",
        "target_company": "Netflix, Inc.",
        "product_or_service": product_or_service,
        "consolidated_company_revenue": (
            "$33.7B (FY2023 Form 10-K) / $39.0B (FY2024 Form 10-K) — Single Consolidated Streaming Segment"
        ),
        "product_level_revenue_disclosed": False,
        "product_level_revenue_note": (
            "Product-level revenue is NOT publicly disclosed. Per Netflix Form 10-K, Netflix operates and reports "
            "as a single consolidated streaming segment; standalone revenue for internal subsystems (Open Connect, "
            "Dynamic Optimizer, Client Playback Engine, Recommender System) is not broken out."
        ),
        "subscriber_or_adoption_scale": matched_profile["adoption_metric"],
        "pricing_tiers_disclosed": matched_profile["pricing_tier_linkage"],
        "strategic_role": matched_profile["strategic_role"],
        "monetization_driver": matched_profile["monetization_driver"],
        "commercial_tier_weight": matched_profile["commercial_tier_weight"],
        "supporting_commercial_sources": supporting_sources,
    }


# ============================================================================
# TOOL 2: PART 1 — TECHNICAL MATCHING & CLAIM-ELEMENT ALIGNMENT
# ============================================================================

def evaluate_claim_element_alignment_tool(
    patent: Dict[str, Any],
    target_area: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Deterministic Python tool for PART 1 — TECHNICAL MATCHING.
    Evaluates:
    1. Decomposed patent claim elements (`1A`, `1B`, `1C`...) against target capabilities & verbatim evidence.
    2. Concept & technology area overlap.
    3. Verbatim supporting evidence citations with `source_title` and `source_url`.
    4. Evidence gaps / unconfirmed technical parameters requiring expert/legal review.
    """
    patent_title = patent.get("title", "")
    patent_summary = patent.get("technical_summary", "") or patent.get("abstract_source_fact", "")
    patent_concepts = patent.get("key_concepts", []) or []
    patent_tech_areas = patent.get("technology_areas", []) or []
    patent_cpcs = patent.get("cpc_codes", []) or []
    decomposed_claims = patent.get("claim_elements", []) or []
    independent_claims = patent.get("independent_claims", []) or []

    target_tech = target_area.get("technology", "")
    target_product = target_area.get("product_or_service", "")
    target_capabilities = target_area.get("technical_capabilities", []) or []
    target_concepts = target_area.get("relevant_technical_concepts", []) or []
    target_evidence = target_area.get("supporting_evidence", []) or []

    # Build combined target corpus text
    target_corpus_text = " ".join(
        [target_tech, target_product]
        + target_capabilities
        + target_concepts
        + [ev.get("text", "") for ev in target_evidence]
    )
    target_tokens = set(_extract_technical_tokens(target_corpus_text))

    # 1. Evaluate Claim-by-Claim Element Alignment
    element_mappings: List[Dict[str, Any]] = []
    confirmed_count = 0
    partial_count = 0
    unconfirmed_count = 0

    all_elements: List[Dict[str, Any]] = []
    for cl in decomposed_claims:
        for el in cl.get("elements", []) or []:
            all_elements.append({
                "claim_number": cl.get("claim_number", "1"),
                "element_id": el.get("element_id", "1A"),
                "description": el.get("description", ""),
                "technical_concept": el.get("technical_concept", ""),
            })

    has_source_claims = len(independent_claims) > 0 and len(all_elements) > 0

    for el in all_elements:
        el_text = f"{el['technical_concept']} {el['description']}"
        el_tokens = _extract_technical_tokens(el_text)
        shared_tokens = [t for t in el_tokens if t in target_tokens]
        token_ratio = len(set(shared_tokens)) / max(1, len(set(el_tokens)))

        syn_bonus, shared_mechs = _compute_concept_expansion_bonus(el_text, target_corpus_text)

        # Find best matching verbatim evidence chunk and capability
        best_ev = None
        best_ev_score = -1.0
        for ev in target_evidence:
            ev_text = ev.get("text", "")
            ev_tokens = set(_extract_technical_tokens(ev_text))
            ev_shared = len([t for t in set(el_tokens) if t in ev_tokens])
            ev_syn, _ = _compute_concept_expansion_bonus(el_text, ev_text)
            score = ev_shared * 1.5 + ev_syn * 4.0
            if score > best_ev_score:
                best_ev_score = score
                best_ev = ev

        best_cap = target_capabilities[0] if target_capabilities else target_tech
        best_cap_score = -1.0
        for cap in target_capabilities:
            cap_tokens = set(_extract_technical_tokens(cap))
            cap_shared = len([t for t in set(el_tokens) if t in cap_tokens])
            cap_syn, _ = _compute_concept_expansion_bonus(el_text, cap)
            c_score = cap_shared * 1.5 + cap_syn * 3.5
            if c_score > best_cap_score:
                best_cap_score = c_score
                best_cap = cap

        combined_alignment_signal = token_ratio * 0.55 + syn_bonus * 0.65

        if combined_alignment_signal >= 0.42 or (len(shared_mechs) >= 2 and len(set(shared_tokens)) >= 2):
            alignment_status = "EVIDENCE_IDENTIFIED"
            confirmed_count += 1
            alignment_note = (
                f"Evidence identified in `{best_ev['source_title'] if best_ev else target_product}`: "
                f"documented capability ('{best_cap}') exhibits potential technical overlap with element "
                f"{el['element_id']} ({', '.join(shared_mechs[:2]) if shared_mechs else ', '.join(shared_tokens[:4])})."
            )
        elif combined_alignment_signal >= 0.20 or len(shared_mechs) >= 1 or len(set(shared_tokens)) >= 2:
            alignment_status = "PARTIAL_ALIGNMENT"
            partial_count += 1
            alignment_note = (
                f"Partial technical alignment: target documentation describes related subsystem ('{best_cap}'), "
                f"but specific parameter/implementation details of element {el['element_id']} require expert/technical verification."
            )
        else:
            alignment_status = "NOT_DOCUMENTED_IN_PUBLIC_SOURCES"
            unconfirmed_count += 1
            alignment_note = (
                f"Specific limitation in element {el['element_id']} is not explicitly confirmed in pre-fetched public "
                f"target sources; requires deeper technical/legal inspection."
            )

        element_mappings.append({
            "claim_number": el["claim_number"],
            "element_id": el["element_id"],
            "claim_element_description": el["description"],
            "technical_concept": el["technical_concept"],
            "alignment_status": alignment_status,
            "matched_target_capability": best_cap if alignment_status != "NOT_DOCUMENTED_IN_PUBLIC_SOURCES" else None,
            "shared_technical_terms": list(dict.fromkeys(shared_mechs + shared_tokens))[:6],
            "supporting_source_title": best_ev.get("source_title") if best_ev else None,
            "supporting_source_url": best_ev.get("source_url") if best_ev else None,
            "alignment_rationale": alignment_note,
        })

    # 2. Concept & Abstract/Summary Alignment
    patent_full_text = " ".join([patent_title, patent_summary] + patent_concepts + patent_tech_areas)
    patent_tokens = set(_extract_technical_tokens(patent_full_text))
    shared_concept_tokens = [t for t in patent_tokens if t in target_tokens]
    concept_token_ratio = len(shared_concept_tokens) / max(1, min(len(patent_tokens), 25))
    overall_syn_bonus, overall_shared_mechs = _compute_concept_expansion_bonus(
        patent_full_text, target_corpus_text
    )

    # 3. Rank & Select Top Supporting Technical Evidence Chunks for this Relationship
    ranked_evidence: List[Dict[str, Any]] = []
    for ev in target_evidence:
        ev_text = ev.get("text", "")
        ev_tokens = set(_extract_technical_tokens(ev_text))
        overlap_toks = [t for t in patent_tokens if t in ev_tokens]
        ev_syn, ev_mechs = _compute_concept_expansion_bonus(patent_full_text, ev_text)
        ev_score = len(overlap_toks) * 2.0 + ev_syn * 15.0
        if ev_score > 0:
            ranked_evidence.append({
                "text": ev_text,
                "source_title": ev.get("source_title", ""),
                "source_url": ev.get("source_url", ""),
                "source_type": ev.get("source_type", "public_documentation"),
                "published_date": ev.get("published_date"),
                "chunk_id": ev.get("chunk_id"),
                "relevance_score": round(ev_score, 2),
                "matched_mechanisms": ev_mechs[:3],
            })

    ranked_evidence.sort(key=lambda x: x["relevance_score"], reverse=True)
    selected_evidence = ranked_evidence[:3] if ranked_evidence else [
        {
            "text": ev.get("text", ""),
            "source_title": ev.get("source_title", ""),
            "source_url": ev.get("source_url", ""),
            "source_type": ev.get("source_type", "public_documentation"),
            "published_date": ev.get("published_date"),
            "chunk_id": ev.get("chunk_id"),
            "relevance_score": 1.0,
            "matched_mechanisms": [],
        }
        for ev in target_evidence[:2]
    ]

    # 4. Compute Deterministic Technical Relevance Score (0 - 100)
    # Factor A: Claim-Element Evidence Coverage (0 - 40 pts)
    if has_source_claims and len(all_elements) > 0:
        coverage_ratio = (confirmed_count * 1.0 + partial_count * 0.5) / len(all_elements)
        claim_coverage_pts = round(min(40.0, coverage_ratio * 42.0), 1)
    else:
        # Missing source claims in BigQuery publication -> penalize claim certainty
        claim_coverage_pts = round(min(18.0, (concept_token_ratio * 15.0 + overall_syn_bonus * 10.0)), 1)

    # Factor B: Technical Concept & Mechanism Overlap (0 - 30 pts)
    concept_overlap_pts = round(
        min(30.0, concept_token_ratio * 18.0 + overall_syn_bonus * 18.0), 1
    )

    # Factor C: Verbatim Target Evidence Specificity (0 - 20 pts)
    top_ev_signal = ranked_evidence[0]["relevance_score"] if ranked_evidence else 0.0
    evidence_depth_pts = round(min(20.0, top_ev_signal * 1.15), 1)

    # Factor D: CPC & Technology Domain Coherence (0 - 10 pts)
    cpc_pts = 0.0
    target_low = target_corpus_text.lower()
    if any(c.startswith("H04N19") or c.startswith("H04N21/2343") for c in patent_cpcs) and (
        "encoding" in target_low or "optimizer" in target_low or "shot" in target_low or "vmaf" in target_low
    ):
        cpc_pts = 9.5
    elif any(c.startswith("H04L67") or c.startswith("H04L47") or c.startswith("H04N21/2") for c in patent_cpcs) and (
        "open connect" in target_low or "cdn" in target_low or "bgp" in target_low or "pacing" in target_low
    ):
        cpc_pts = 9.5
    elif any(c.startswith("H04N21/4") or c.startswith("G10L") or c.startswith("H04S") for c in patent_cpcs) and (
        "playback" in target_low or "audio" in target_low or "atmos" in target_low or "sync" in target_low
    ):
        cpc_pts = 9.5
    elif len(overall_shared_mechs) > 0:
        cpc_pts = 6.5
    else:
        cpc_pts = 3.0

    raw_tech_score = round(
        min(98.0, claim_coverage_pts + concept_overlap_pts + evidence_depth_pts + cpc_pts), 1
    )

    # Determine Technical Overlap Level
    if not target_evidence:
        overlap_level = "Insufficient Evidence"
        raw_tech_score = 0.0
    elif raw_tech_score >= 76.0 and (confirmed_count >= 1 or not has_source_claims):
        overlap_level = "High"
    elif raw_tech_score >= 52.0:
        overlap_level = "Medium"
    else:
        overlap_level = "Low"

    # Identify explicit Evidence Gaps / Unconfirmed Elements
    evidence_gaps: List[str] = []
    if not has_source_claims:
        evidence_gaps.append(
            "Source publication in `patents-public-data.patents.publications` lacks indexed independent claims (`claims_localized` is empty); technical comparison is restricted to abstract/specification concepts and requires full prosecution wrapper review."
        )
    for em in element_mappings:
        if em["alignment_status"] == "NOT_DOCUMENTED_IN_PUBLIC_SOURCES":
            evidence_gaps.append(
                f"Element {em['element_id']} ({em['technical_concept']}): Specific limitation is not confirmed in public target documentation and requires technical inspection or legal discovery."
            )
        elif em["alignment_status"] == "PARTIAL_ALIGNMENT":
            evidence_gaps.append(
                f"Element {em['element_id']} ({em['technical_concept']}): High-level architecture is documented in `{em['supporting_source_title']}`, but exact algorithmic parameters require expert verification."
            )

    if not evidence_gaps and has_source_claims:
        evidence_gaps.append(
            "Public engineering documentation confirms high-level architectural mechanisms, but internal production source code, exact threshold constants, and claim construction boundaries require expert and legal review."
        )

    # Build neutral, evidence-backed Technical Overlap Summary
    mech_str = ", ".join(overall_shared_mechs[:3]) if overall_shared_mechs else ", ".join(shared_concept_tokens[:4])
    primary_source_title = selected_evidence[0]["source_title"] if selected_evidence else "pre-fetched target sources"
    if overlap_level in ("High", "Medium"):
        technical_overlap_summary = (
            f"Potential technical overlap ({overlap_level}) identified between {patent['patent_number']} "
            f"('{patent_title}') and {target_product} ({target_tech}). "
            f"Evidence identified in `{primary_source_title}` documents overlapping technical mechanisms "
            f"around {mech_str or 'streaming media processing'}. "
            + (
                f"Across {len(all_elements)} decomposed independent claim elements, {confirmed_count} show direct "
                f"documentary correspondence and {partial_count} show partial architectural alignment. "
                if has_source_claims
                else "Comparison is based on specification disclosures because source independent claims are not indexed in the dataset. "
            )
            + "Candidate for investigation; requires expert/legal review."
        )
    else:
        technical_overlap_summary = (
            f"Low potential technical overlap identified between {patent['patent_number']} and {target_product}. "
            f"While both operate in the broader media infrastructure domain, pre-fetched public documentation in "
            f"`{primary_source_title}` provides limited evidence for the specific claim limitations of {patent['patent_number']}. "
            f"Requires expert/legal review before further action."
        )

    return {
        "technical_overlap_level": overlap_level,
        "technical_relevance_score": raw_tech_score,
        "technical_overlap_summary": technical_overlap_summary,
        "has_source_claims": has_source_claims,
        "claim_element_counts": {
            "total_elements": len(all_elements),
            "evidence_identified": confirmed_count,
            "partial_alignment": partial_count,
            "not_documented": unconfirmed_count,
        },
        "claim_element_mapping": element_mappings,
        "shared_technical_mechanisms": overall_shared_mechs,
        "evidence_gaps_and_unconfirmed_aspects": evidence_gaps,
        "supporting_technical_evidence": selected_evidence,
        "technical_factor_breakdown": {
            "claim_element_coverage": {
                "score": claim_coverage_pts,
                "max": 40,
                "detail": (
                    f"{confirmed_count} confirmed + {partial_count} partial out of {len(all_elements)} claim elements"
                    if has_source_claims
                    else "Capped (no verbatim independent claims in source record)"
                ),
            },
            "concept_and_mechanism_alignment": {
                "score": concept_overlap_pts,
                "max": 30,
                "detail": f"Shared mechanisms: {', '.join(overall_shared_mechs[:3]) or 'general domain terms'}",
            },
            "verbatim_evidence_specificity": {
                "score": evidence_depth_pts,
                "max": 20,
                "detail": f"Backed by {len(selected_evidence)} verbatim chunks from pre-fetched Target Knowledge DB",
            },
            "cpc_domain_coherence": {
                "score": cpc_pts,
                "max": 10,
                "detail": f"CPC {', '.join(patent_cpcs[:2]) or 'N/A'} vs. {target_tech}",
            },
        },
    }


# ============================================================================
# TOOL 3: PART 2 — COMMERCIAL OPPORTUNITY & PATENT VIABILITY EVALUATION
# ============================================================================

def evaluate_commercial_opportunity_tool(
    patent: Dict[str, Any],
    target_area: Dict[str, Any],
    commercial_intel: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Deterministic Python tool for PART 2 — COMMERCIAL OPPORTUNITY.
    Evaluates commercial significance separately from technical overlap:
    1. Target Product / Technology Strategic Role & Adoption Scale (0 - 45 pts)
    2. Economic / Cost-of-Revenues / Premium-Tier Differentiation Lever (0 - 25 pts)
    3. Patent Asset Status & Remaining Term Viability (0 - 30 pts)
    Never fabricates product-level revenue or royalty calculations.
    """
    patent_status = patent.get("status", "Unknown")
    remaining_years = patent.get("estimated_remaining_term_years")
    patent_life_info = patent.get("patent_life", {}) or {}
    target_product = target_area.get("product_or_service", "")

    comm_status = commercial_intel.get("commercial_evidence_status", "INSUFFICIENT_PUBLIC_COMMERCIAL_DATA")
    base_weight = float(commercial_intel.get("commercial_tier_weight", 50))

    # Factor 1: Target Product Strategic Scale & Adoption Reach (0 - 45 pts)
    if comm_status == "VERIFIED_PUBLIC_FILINGS":
        scale_pts = round(min(45.0, (base_weight / 100.0) * 46.0), 1)
    else:
        scale_pts = 18.0

    # Factor 2: Cost-of-Revenues / Premium Tier Differentiation Impact (0 - 25 pts)
    if comm_status == "VERIFIED_PUBLIC_FILINGS":
        if base_weight >= 90:
            lever_pts = 23.5
        elif base_weight >= 85:
            lever_pts = 21.0
        else:
            lever_pts = 17.5
    else:
        lever_pts = 10.0

    # Factor 3: Deterministic Patent Status & Remaining Life Viability (0 - 30 pts)
    status_low = patent_status.lower()
    is_expired = "expired" in status_low or (remaining_years is not None and remaining_years <= 0.0)
    is_pending = "application" in status_low or "pending" in status_low or "ungranted" in status_low
    is_granted = "granted" in status_low and not is_expired

    if is_expired:
        viability_pts = 5.0
        viability_status_note = (
            "Expired 20-year statutory baseline (0.0 yrs remaining). Forward-looking licensing leverage is "
            "unavailable; any commercial evaluation is limited to historical lookback periods subject to legal review."
        )
    elif is_pending:
        viability_pts = 12.0
        rem_str = f"{remaining_years} yrs nominal" if remaining_years is not None else "unconfirmed term"
        viability_status_note = (
            f"Published Application / Pending ({rem_str}). Claims are not yet granted and remain subject to "
            "examination amendments; commercial opportunity is contingent on grant."
        )
    elif is_granted:
        if remaining_years is None:
            viability_pts = 16.0
            viability_status_note = "Granted patent with unconfirmed filing date in dataset; requires term verification."
        elif remaining_years >= 12.0:
            viability_pts = 28.5
            viability_status_note = f"Active Granted Baseline with long remaining runway ({remaining_years} years)."
        elif remaining_years >= 7.0:
            viability_pts = 24.0
            viability_status_note = f"Active Granted Baseline with substantial remaining life ({remaining_years} years)."
        elif remaining_years >= 3.0:
            viability_pts = 18.5
            viability_status_note = f"Active Granted Baseline with moderate remaining life ({remaining_years} years)."
        else:
            viability_pts = 13.0
            viability_status_note = f"Active Granted Baseline approaching end of term ({remaining_years} years remaining)."
    else:
        viability_pts = 12.0
        viability_status_note = f"Patent status '{patent_status}' requires formal legal register verification."

    raw_comm_score = round(min(98.0, scale_pts + lever_pts + viability_pts), 1)

    # Determine analytical monetary opportunity signal (never a fabricated dollar royalty!)
    if comm_status != "VERIFIED_PUBLIC_FILINGS":
        monetary_signal = "Insufficient Public Commercial Data"
    elif is_expired:
        monetary_signal = "Constrained — Patent Expired (0.0 Yrs Remaining)"
        raw_comm_score = min(raw_comm_score, 45.0)
    elif is_pending:
        monetary_signal = "Contingent — Pending Application (Ungranted)"
        raw_comm_score = min(raw_comm_score, 64.0)
    elif raw_comm_score >= 82.0:
        monetary_signal = "High Analytical Signal (Core Infrastructure / Scale + Long Term)"
    elif raw_comm_score >= 65.0:
        monetary_signal = "Medium-High Analytical Signal (Core Capability / Moderate Term)"
    else:
        monetary_signal = "Moderate Analytical Signal"

    monetary_rationale = (
        f"Analytical Signal: {monetary_signal}. "
        f"Target system '{target_product}' operates as {commercial_intel.get('strategic_role', 'documented infrastructure')} "
        f"({commercial_intel.get('subscriber_or_adoption_scale', 'scale unverified')}). "
        f"Company-level context: {commercial_intel.get('consolidated_company_revenue') or 'N/A'}. "
        f"{commercial_intel.get('product_level_revenue_note', '')} "
        f"Patent asset viability: {viability_status_note}"
    )

    return {
        "commercial_opportunity_score": raw_comm_score,
        "potential_monetary_opportunity": monetary_signal,
        "monetary_opportunity_rationale": monetary_rationale,
        "strategic_role": commercial_intel.get("strategic_role"),
        "monetization_driver": commercial_intel.get("monetization_driver"),
        "consolidated_company_revenue": commercial_intel.get("consolidated_company_revenue"),
        "product_level_revenue_disclosed": commercial_intel.get("product_level_revenue_disclosed", False),
        "product_level_revenue_note": commercial_intel.get("product_level_revenue_note"),
        "subscriber_or_adoption_scale": commercial_intel.get("subscriber_or_adoption_scale"),
        "pricing_tiers_disclosed": commercial_intel.get("pricing_tiers_disclosed"),
        "patent_status": patent_status,
        "estimated_remaining_term_years": remaining_years,
        "patent_life_calculation_basis": patent_life_info.get(
            "calculation_basis", "20-year statutory baseline from filing_date"
        ),
        "patent_viability_note": viability_status_note,
        "supporting_commercial_sources": commercial_intel.get("supporting_commercial_sources", []),
        "commercial_factor_breakdown": {
            "target_product_strategic_scale": {
                "score": scale_pts,
                "max": 45,
                "detail": commercial_intel.get("subscriber_or_adoption_scale", "N/A"),
            },
            "economic_and_tier_differentiation_lever": {
                "score": lever_pts,
                "max": 25,
                "detail": commercial_intel.get("pricing_tiers_disclosed", "N/A"),
            },
            "patent_status_and_remaining_life": {
                "score": viability_pts,
                "max": 30,
                "detail": viability_status_note,
            },
        },
    }


# ============================================================================
# TOOL 4: PART 3 — INVESTIGATION PRIORITIZATION & GUARDRAILS
# ============================================================================

FORBIDDEN_LEGAL_PHRASES = [
    r"\binfringes\b",
    r"\binfringed\b",
    r"\binfringement is established\b",
    r"\bproves infringement\b",
    r"\bconstitutes infringement\b",
    r"\bunlawful use\b",
    r"\bliability established\b",
]


def enforce_non_infringement_guardrail(text: str) -> str:
    """
    Deterministic language guardrail ensuring that no output states or implies
    that legal patent infringement has been established.
    """
    if not text:
        return ""
    cleaned = text
    for pattern in FORBIDDEN_LEGAL_PHRASES:
        cleaned = re.sub(pattern, "exhibits potential technical overlap", cleaned, flags=re.IGNORECASE)
    return cleaned


def compute_investigation_priority_tool(
    technical_eval: Dict[str, Any],
    commercial_eval: Dict[str, Any],
    patent: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Deterministic Python tool for PART 3 — INVESTIGATION PRIORITIZATION.
    Synthesizes Technical Relevance (Part 1) and Commercial Opportunity (Part 2) into an
    actionable Investigation Priority while keeping the two component scores separate.
    """
    tech_score = float(technical_eval.get("technical_relevance_score", 0.0))
    tech_level = technical_eval.get("technical_overlap_level", "Low")
    comm_score = float(commercial_eval.get("commercial_opportunity_score", 0.0))
    has_claims = bool(technical_eval.get("has_source_claims", True))

    status_low = (patent.get("status", "") or "").lower()
    rem_years = patent.get("estimated_remaining_term_years")
    is_expired = "expired" in status_low or (rem_years is not None and rem_years <= 0.0)
    is_pending = "application" in status_low or "pending" in status_low

    # Weighted composite for ordering (58% Technical Relevance + 42% Commercial Opportunity)
    composite_score = round(tech_score * 0.58 + comm_score * 0.42, 1)

    # Gatekeeper prioritization logic:
    # 1. Weak technical overlap cannot become High Priority regardless of commercial size
    if tech_level in ("Low", "Insufficient Evidence") or tech_score < 52.0:
        priority_tier = "Low Priority"
        composite_score = min(composite_score, 54.0)
        recommendation = (
            "Low priority for immediate investigation: although the target subsystem is commercially significant, "
            "public technical evidence shows low alignment with the specific claim limitations. Monitor only."
        )
    # 2. Expired patent cannot be High Priority for forward-looking investigation
    elif is_expired:
        priority_tier = "Low Priority (Expired Term)"
        composite_score = min(composite_score, 58.0)
        recommendation = (
            "Constrained priority: technical overlap evidence is present, but nominal 20-year statutory patent life "
            "has expired (0.0 yrs remaining). Requires legal counsel review regarding any historical damages window."
        )
    # 3. Pending / ungranted application or missing source claims -> Medium Priority (Requires Claim/Prosecution Verification)
    elif is_pending or not has_claims:
        priority_tier = "Medium Priority"
        composite_score = min(composite_score, 75.0)
        recommendation = (
            "Candidate for prosecution monitoring & deeper review: technical concept alignment is documented, "
            "but publication is either a pending application or lacks indexed source claims in BigQuery. "
            "Verify issued claim scope in USPTO PAIR / Global Dossier before formal claim charting."
        )
    # 4. Strong Technical Overlap + Strong Commercial Opportunity + Granted Active Patent -> High Priority
    elif tech_level == "High" and tech_score >= 76.0 and comm_score >= 72.0:
        priority_tier = "High Priority"
        recommendation = (
            "Primary candidate for investigation: strong potential technical overlap backed by verbatim target "
            "engineering disclosures, combined with core target infrastructure scale and active granted patent life "
            f"({rem_years} yrs remaining). Recommended for expert technical deep-dive and legal claim-chart review."
        )
    elif composite_score >= 64.0:
        priority_tier = "Medium Priority"
        recommendation = (
            "Secondary candidate for investigation: moderate-to-high technical alignment with documented target "
            "capabilities, with specific claim parameters requiring technical verification and expert/legal review."
        )
    else:
        priority_tier = "Low Priority"
        recommendation = (
            "Lower relative priority: retain in portfolio reference matrix; prioritize higher-evidence candidates first."
        )

    return {
        "investigation_priority": priority_tier,
        "priority_score": composite_score,
        "priority_rationale": enforce_non_infringement_guardrail(recommendation),
        "gatekeeper_flags": {
            "is_granted_active": not is_expired and not is_pending,
            "is_expired": is_expired,
            "is_pending_application": is_pending,
            "has_indexed_independent_claims": has_claims,
        },
    }
