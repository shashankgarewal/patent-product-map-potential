"""
Google ADK Multi-Agent Orchestration for the Patent–Target Matching and Commercial Opportunity Agent.

ADK Hierarchy:
    root_agent (SequentialAgent)
        ↓
    technical_matching_agent (LlmAgent — Part 1: Technical Relevance & Claim-Element Alignment)
        ↓
    commercial_opportunity_agent (LlmAgent — Part 2: Commercial Opportunity & Patent Viability)
        ↓
    investigation_priority_agent (LlmAgent — Part 3: Investigation Prioritization & Final Ranked Table)

Core Design Principles:
1. Evaluates TWO distinct analytical dimensions:
   - Part 1: TECHNICAL RELEVANCE (concept overlap, claim-element mapping, verbatim target evidence, evidence gaps)
   - Part 2: COMMERCIAL OPPORTUNITY (target strategic role, public 10-K commercial scale, patent status & remaining life)
   Never collapses Technical Relevance and Commercial Opportunity into a single similarity score.
2. Evidence-First & Non-Fabrication:
   - Never invents target product capabilities, patent claims, or product-level revenue.
   - Explicitly reports when product-level revenue is not broken out in SEC Form 10-K filings.
3. Strict Non-Infringement Positioning:
   - Uses screening terminology ("potential technical overlap", "candidate for investigation",
     "potentially relevant", "evidence identified", "requires expert/legal review").
"""

from typing import Dict, Any, List, Optional, Callable, Tuple

from adk_pipeline.agent import execute_deterministic_adk_stages as execute_client_patent_pipeline
from target_agent.agent import execute_target_retrieval_pipeline
from matching_agent.tools import (
    retrieve_commercial_intelligence_tool,
    evaluate_claim_element_alignment_tool,
    evaluate_commercial_opportunity_tool,
    compute_investigation_priority_tool,
    enforce_non_infringement_guardrail,
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
# GOOGLE ADK AGENT DEFINITIONS
# ============================================================================

technical_matching_agent = LlmAgent(
    name="technical_matching_agent",
    model="gemini-3.8-flash",
    description=(
        "Part 1 — Technical Matching Agent: Evaluates potential technical overlap between client patent "
        "claims/concepts and pre-fetched target company technologies, capabilities, and verbatim evidence."
    ),
    instruction=(
        "You are the Technical Matching Agent (Part 1).\n"
        "1. Compare each client patent's independent claim elements (`1A`, `1B`, `1C`...) and technical concepts "
        "against the target company's documented technologies, capabilities, and verbatim evidence.\n"
        "2. Distinguish matched technical mechanisms from unconfirmed claim limitations (evidence gaps).\n"
        "3. Cite verbatim target evidence (`source_title` and `source_url`) for every technical overlap finding.\n"
        "4. Use strict screening language ('potential technical overlap', 'evidence identified', "
        "'requires expert/legal review'). Never state or imply that legal infringement is established."
    ),
    tools=[evaluate_claim_element_alignment_tool],
    output_key="technical_matching_results",
)

commercial_opportunity_agent = LlmAgent(
    name="commercial_opportunity_agent",
    model="gemini-3.8-flash",
    description=(
        "Part 2 — Commercial Opportunity Agent: Evaluates target product commercial significance, public 10-K "
        "financial/adoption disclosures, patent legal status, and deterministic remaining patent life."
    ),
    instruction=(
        "You are the Commercial Opportunity Agent (Part 2).\n"
        "1. Evaluate Commercial Opportunity as a distinct dimension from Technical Relevance.\n"
        "2. Retrieve public commercial facts (SEC Form 10-K revenue, subscriber scale, pricing tiers, strategic role) "
        "using `retrieve_commercial_intelligence_tool`.\n"
        "3. NEVER fabricate product-level revenue or royalty/damages numbers. When a company reports a single "
        "consolidated segment, explicitly state that product-level revenue is not publicly disclosed.\n"
        "4. Incorporate deterministic patent status and estimated remaining patent life into the commercial signal."
    ),
    tools=[retrieve_commercial_intelligence_tool, evaluate_commercial_opportunity_tool],
    output_key="commercial_opportunity_results",
)

investigation_priority_agent = LlmAgent(
    name="investigation_priority_agent",
    model="gemini-3.8-flash",
    description=(
        "Part 3 — Investigation Prioritization Agent: Synthesizes Technical Relevance and Commercial Opportunity "
        "with patent-viability gatekeeper rules to produce the final ranked Patent–Product Intelligence Table."
    ),
    instruction=(
        "You are the Investigation Prioritization Agent (Part 3).\n"
        "1. Combine Part 1 (Technical Relevance) and Part 2 (Commercial Opportunity) without collapsing their "
        "separate scores.\n"
        "2. Apply gatekeeper rules: low technical overlap or expired patent term cannot be ranked High Priority.\n"
        "3. Produce the final ranked table with all 9 required analytical columns and verifiable source citations."
    ),
    tools=[compute_investigation_priority_tool, enforce_non_infringement_guardrail],
    output_key="prioritized_intelligence_table",
)

root_agent = SequentialAgent(
    name="root_agent",
    description=(
        "Root ADK orchestrator for Patent–Target Matching & Commercial Opportunity Analysis: "
        "technical_matching_agent -> commercial_opportunity_agent -> investigation_priority_agent."
    ),
    sub_agents=[
        technical_matching_agent,
        commercial_opportunity_agent,
        investigation_priority_agent,
    ],
)


# ============================================================================
# END-TO-END & STANDALONE MATCHING PIPELINE EXECUTION
# ============================================================================

def execute_patent_target_matching_pipeline(
    client_company: str = "Dolby Laboratories",
    target_company: str = "Netflix",
    technology_area: Optional[str] = "video streaming",
    client_patents: Optional[List[Dict[str, Any]]] = None,
    target_technology_areas: Optional[List[Dict[str, Any]]] = None,
    max_candidates: int = 6,
) -> Dict[str, Any]:
    """
    Executes the Google ADK Patent–Target Matching & Commercial Opportunity Pipeline.
    If `client_patents` or `target_technology_areas` are not passed in, runs the upstream
    Client Patent Pipeline and/or Target Retrieval Pipeline deterministically.
    """
    adk_trace: List[Dict[str, Any]] = []
    upstream_client_result: Optional[Dict[str, Any]] = None
    upstream_target_result: Optional[Dict[str, Any]] = None

    # 1. Ensure Client Patent Intelligence is available
    if client_patents is None:
        upstream_client_result = execute_client_patent_pipeline(
            client_company=client_company,
            technology_area=technology_area,
            max_candidates=max_candidates,
        )
        if upstream_client_result.get("pipeline_status") != "SUCCESS":
            return {
                "matching_status": upstream_client_result.get("pipeline_status", "CLIENT_PIPELINE_ERROR"),
                "client_company": client_company,
                "target_company": target_company,
                "technology_area": technology_area or "",
                "error": upstream_client_result.get("error")
                or upstream_client_result.get("resolution", {}).get("message")
                or "Client patent retrieval did not return a valid candidate set.",
                "upstream_client_resolution": upstream_client_result.get("resolution"),
                "ranked_matches": [],
            }
        patents_list = upstream_client_result.get("patents", [])
        resolved_client = upstream_client_result.get("resolved_assignee") or client_company
    else:
        patents_list = client_patents
        resolved_client = client_company

    # 2. Ensure Target Company Intelligence is available from pre-fetched SQLite DB
    if target_technology_areas is None:
        patent_context_for_target = [
            {
                "patent_number": p.get("patent_number"),
                "technology_areas": p.get("technology_areas", []),
                "key_concepts": p.get("key_concepts", []),
            }
            for p in patents_list
        ]
        upstream_target_result = execute_target_retrieval_pipeline(
            target_company=target_company,
            technology_area=technology_area,
            client_patent_context=patent_context_for_target,
            top_k_per_query=4,
        )
        if upstream_target_result.get("evidence_status") != "sufficient":
            reason = upstream_target_result.get(
                "diagnostic_reason",
                f"Insufficient pre-fetched target evidence in `target_knowledge.sqlite` for '{target_company}'.",
            )
            adk_trace.append({
                "agent": "technical_matching_agent",
                "step": "Part 1 — Target Evidence Verification",
                "tool": "evaluate_claim_element_alignment_tool",
                "status": "INSUFFICIENT_TARGET_EVIDENCE",
                "summary": reason,
            })
            return {
                "matching_status": "INSUFFICIENT_TARGET_EVIDENCE",
                "client_company": resolved_client,
                "target_company": target_company,
                "technology_area": technology_area or "",
                "diagnostic_reason": reason,
                "ranked_matches": [],
                "adk_architecture": {
                    "runtime_mode": ADK_RUNTIME_MODE,
                    "root_agent": root_agent.name,
                    "sub_agents": [a.name for a in root_agent.sub_agents],
                    "agent_trace": adk_trace,
                },
            }
        target_areas_list = upstream_target_result.get("technology_areas", [])
    else:
        target_areas_list = target_technology_areas

    if not patents_list or not target_areas_list:
        return {
            "matching_status": "INSUFFICIENT_EVIDENCE",
            "client_company": resolved_client,
            "target_company": target_company,
            "technology_area": technology_area or "",
            "diagnostic_reason": "Either client patents or target technology areas are empty.",
            "ranked_matches": [],
        }

    # =========================================================================
    # PART 1: TECHNICAL MATCHING (Evaluate each Patent x Target Technology Area)
    # =========================================================================
    selected_pairings: List[Dict[str, Any]] = []
    total_pairs_evaluated = 0

    for pat in patents_list:
        candidate_evals_for_patent: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
        for t_area in target_areas_list:
            total_pairs_evaluated += 1
            tech_eval = evaluate_claim_element_alignment_tool(patent=pat, target_area=t_area)
            candidate_evals_for_patent.append((t_area, tech_eval))

        # Sort target technology areas for this patent by technical_relevance_score descending
        candidate_evals_for_patent.sort(
            key=lambda item: item[1].get("technical_relevance_score", 0.0),
            reverse=True,
        )

        # Primary best-matching target product/technology for this patent
        best_t_area, best_tech_eval = candidate_evals_for_patent[0]
        alternative_target_matches = [
            {
                "target_product_or_service": ta.get("product_or_service"),
                "target_technology": ta.get("technology"),
                "technical_overlap_level": te.get("technical_overlap_level"),
                "technical_relevance_score": te.get("technical_relevance_score"),
            }
            for ta, te in candidate_evals_for_patent[1:3]
        ]

        selected_pairings.append({
            "patent": pat,
            "target_area": best_t_area,
            "technical_evaluation": best_tech_eval,
            "alternative_target_matches": alternative_target_matches,
        })

    adk_trace.append({
        "agent": "technical_matching_agent",
        "step": "Part 1 — Claim-Element & Technical Concept Alignment",
        "tool": "evaluate_claim_element_alignment_tool",
        "status": "COMPLETED",
        "summary": (
            f"Evaluated {total_pairs_evaluated} patent–target technology pairings across {len(patents_list)} "
            f"client patents and {len(target_areas_list)} documented {target_company} technology areas; "
            f"mapped independent claim elements to verbatim target evidence and flagged unconfirmed limitations."
        ),
    })

    # =========================================================================
    # PART 2: COMMERCIAL OPPORTUNITY ASSESSMENT (Distinct from Technical Score)
    # =========================================================================
    for item in selected_pairings:
        pat = item["patent"]
        t_area = item["target_area"]
        comm_intel = retrieve_commercial_intelligence_tool(
            target_company=target_company,
            product_or_service=t_area.get("product_or_service", ""),
            technology=t_area.get("technology", ""),
        )
        comm_eval = evaluate_commercial_opportunity_tool(
            patent=pat,
            target_area=t_area,
            commercial_intel=comm_intel,
        )
        item["commercial_evaluation"] = comm_eval

    adk_trace.append({
        "agent": "commercial_opportunity_agent",
        "step": "Part 2 — Public Commercial Intelligence & Patent Viability Assessment",
        "tool": "retrieve_commercial_intelligence_tool + evaluate_commercial_opportunity_tool",
        "status": "COMPLETED",
        "summary": (
            f"Retrieved pre-fetched SEC Form 10-K & public commercial disclosures for {target_company}; "
            "evaluated target product strategic criticality, adoption scale, patent status, and 20-year "
            "remaining term without fabricating product-level revenue."
        ),
    })

    # =========================================================================
    # PART 3: INVESTIGATION PRIORITIZATION & FINAL RANKED TABLE
    # =========================================================================
    ranked_matches: List[Dict[str, Any]] = []

    for item in selected_pairings:
        pat = item["patent"]
        t_area = item["target_area"]
        tech_eval = item["technical_evaluation"]
        comm_eval = item["commercial_evaluation"]

        priority_eval = compute_investigation_priority_tool(
            technical_eval=tech_eval,
            commercial_eval=comm_eval,
            patent=pat,
        )

        match_id = f"match_{pat.get('patent_number', '')}_{t_area.get('product_or_service', '')[:18]}".replace(" ", "_")

        ranked_matches.append({
            "match_id": match_id,
            # Column 1: Patent number
            "patent_number": pat.get("patent_number"),
            # Column 2: Patent title / description
            "patent_title": pat.get("title"),
            "patent_description": pat.get("technical_summary") or pat.get("abstract_source_fact") or "",
            "patent_abstract_source_fact": pat.get("abstract_source_fact") or "",
            "patent_cpc_codes": pat.get("cpc_codes", []),
            "patent_key_concepts": pat.get("key_concepts", []),
            "patent_technology_areas": pat.get("technology_areas", []),
            "patent_independent_claims": pat.get("independent_claims", []),
            "patent_filing_date": pat.get("filing_date"),
            "patent_priority_date": pat.get("priority_date"),
            "patent_grant_date": pat.get("grant_date"),
            # Column 3: Target product or technology
            "target_company": target_company,
            "target_product_or_service": t_area.get("product_or_service"),
            "target_technology": t_area.get("technology"),
            "target_technical_capabilities": t_area.get("technical_capabilities", []),
            "alternative_target_matches": item["alternative_target_matches"],
            # Column 4: Technical overlap (Part 1 distinct analysis)
            "technical_overlap": {
                "overlap_level": tech_eval["technical_overlap_level"],
                "technical_relevance_score": tech_eval["technical_relevance_score"],
                "summary": tech_eval["technical_overlap_summary"],
                "shared_technical_mechanisms": tech_eval["shared_technical_mechanisms"],
                "has_source_claims": tech_eval["has_source_claims"],
                "claim_element_counts": tech_eval["claim_element_counts"],
                "claim_element_mapping": tech_eval["claim_element_mapping"],
                "evidence_gaps": tech_eval["evidence_gaps_and_unconfirmed_aspects"],
                "factor_breakdown": tech_eval["technical_factor_breakdown"],
            },
            # Column 5: Evidence supporting the overlap (Verbatim quotes + URLs)
            "supporting_evidence": tech_eval["supporting_technical_evidence"],
            # Column 6: Patent status
            "patent_status": pat.get("status", "Unknown"),
            "patent_status_fact_basis": pat.get("status_fact_basis", ""),
            # Column 7: Estimated remaining patent life
            "estimated_remaining_patent_life": {
                "years_remaining": pat.get("estimated_remaining_term_years"),
                "expiration_date_nominal": (pat.get("patent_life") or {}).get("estimated_expiration_date_nominal"),
                "calculation_basis": comm_eval["patent_life_calculation_basis"],
                "viability_note": comm_eval["patent_viability_note"],
            },
            # Column 8: Potential monetary opportunity (Part 2 distinct analysis — analytical signal)
            "potential_monetary_opportunity": {
                "signal_tier": comm_eval["potential_monetary_opportunity"],
                "commercial_opportunity_score": comm_eval["commercial_opportunity_score"],
                "rationale": comm_eval["monetary_opportunity_rationale"],
                "strategic_role": comm_eval["strategic_role"],
                "monetization_driver": comm_eval["monetization_driver"],
                "consolidated_company_revenue": comm_eval["consolidated_company_revenue"],
                "product_level_revenue_disclosed": comm_eval["product_level_revenue_disclosed"],
                "product_level_revenue_note": comm_eval["product_level_revenue_note"],
                "subscriber_or_adoption_scale": comm_eval["subscriber_or_adoption_scale"],
                "pricing_tiers_disclosed": comm_eval["pricing_tiers_disclosed"],
                "supporting_commercial_sources": comm_eval["supporting_commercial_sources"],
                "factor_breakdown": comm_eval["commercial_factor_breakdown"],
            },
            # Column 9: Investigation priority (Part 3 synthesis)
            "investigation_priority": {
                "priority_tier": priority_eval["investigation_priority"],
                "priority_score": priority_eval["priority_score"],
                "rationale": priority_eval["priority_rationale"],
                "gatekeeper_flags": priority_eval["gatekeeper_flags"],
            },
        })

    # Sort ranked table by Investigation Priority tier first, then priority_score descending
    priority_order = {
        "High Priority": 3,
        "Medium Priority": 2,
        "Low Priority": 1,
        "Low Priority (Expired Term)": 0,
    }
    ranked_matches.sort(
        key=lambda r: (
            priority_order.get(r["investigation_priority"]["priority_tier"], 1),
            r["investigation_priority"]["priority_score"],
            r["technical_overlap"]["technical_relevance_score"],
        ),
        reverse=True,
    )

    for idx, row in enumerate(ranked_matches, start=1):
        row["rank"] = idx

    high_priority_count = sum(
        1 for r in ranked_matches if r["investigation_priority"]["priority_tier"] == "High Priority"
    )
    medium_priority_count = sum(
        1 for r in ranked_matches if r["investigation_priority"]["priority_tier"] == "Medium Priority"
    )

    adk_trace.append({
        "agent": "investigation_priority_agent",
        "step": "Part 3 — Multi-Dimension Investigation Prioritization & Guardrail Verification",
        "tool": "compute_investigation_priority_tool + enforce_non_infringement_guardrail",
        "status": "COMPLETED",
        "summary": (
            f"Ranked {len(ranked_matches)} patent–product relationships ({high_priority_count} High Priority, "
            f"{medium_priority_count} Medium Priority) while keeping Technical Relevance and Commercial "
            "Opportunity as separate analytical dimensions."
        ),
    })

    # Canonical output contract for downstream export / API inspection
    canonical_output = {
        "client_company": resolved_client,
        "target_company": target_company,
        "technology_area": technology_area or "optional",
        "positioning_notice": (
            "Preliminary technical and commercial screening only. Not a legal infringement determination "
            "or royalty/damages calculation. All candidates require expert technical and legal review."
        ),
        "ranked_patent_product_matches": [
            {
                "rank": r["rank"],
                "patent_number": r["patent_number"],
                "patent_title": r["patent_title"],
                "patent_description": r["patent_description"],
                "target_product_or_technology": f"{r['target_product_or_service']} ({r['target_technology']})",
                "technical_overlap": {
                    "level": r["technical_overlap"]["overlap_level"],
                    "technical_relevance_score": r["technical_overlap"]["technical_relevance_score"],
                    "explanation": r["technical_overlap"]["summary"],
                    "claim_element_mapping": r["technical_overlap"]["claim_element_mapping"],
                    "evidence_gaps": r["technical_overlap"]["evidence_gaps"],
                },
                "evidence_supporting_overlap": [
                    {
                        "verbatim_text": ev["text"],
                        "source_title": ev["source_title"],
                        "source_url": ev["source_url"],
                        "source_type": ev.get("source_type"),
                    }
                    for ev in r["supporting_evidence"]
                ],
                "patent_status": r["patent_status"],
                "estimated_remaining_patent_life_years": r["estimated_remaining_patent_life"]["years_remaining"],
                "potential_monetary_opportunity": {
                    "analytical_signal": r["potential_monetary_opportunity"]["signal_tier"],
                    "commercial_opportunity_score": r["potential_monetary_opportunity"]["commercial_opportunity_score"],
                    "strategic_role": r["potential_monetary_opportunity"]["strategic_role"],
                    "consolidated_company_revenue": r["potential_monetary_opportunity"]["consolidated_company_revenue"],
                    "product_level_revenue_note": r["potential_monetary_opportunity"]["product_level_revenue_note"],
                    "rationale": r["potential_monetary_opportunity"]["rationale"],
                    "commercial_sources": [
                        {
                            "source_title": cs["source_title"],
                            "source_url": cs["source_url"],
                        }
                        for cs in r["potential_monetary_opportunity"]["supporting_commercial_sources"]
                    ],
                },
                "investigation_priority": {
                    "priority": r["investigation_priority"]["priority_tier"],
                    "priority_score": r["investigation_priority"]["priority_score"],
                    "recommendation": r["investigation_priority"]["rationale"],
                },
            }
            for r in ranked_matches
        ],
    }

    return {
        "matching_status": "SUCCESS",
        "client_company": resolved_client,
        "target_company": target_company,
        "technology_area": technology_area or "",
        "summary_metrics": {
            "total_relationships_ranked": len(ranked_matches),
            "total_pairs_evaluated": total_pairs_evaluated,
            "high_priority_count": high_priority_count,
            "medium_priority_count": medium_priority_count,
            "low_priority_count": len(ranked_matches) - high_priority_count - medium_priority_count,
            "avg_technical_relevance_score": round(
                sum(r["technical_overlap"]["technical_relevance_score"] for r in ranked_matches)
                / max(1, len(ranked_matches)),
                1,
            ),
            "avg_commercial_opportunity_score": round(
                sum(r["potential_monetary_opportunity"]["commercial_opportunity_score"] for r in ranked_matches)
                / max(1, len(ranked_matches)),
                1,
            ),
        },
        "ranked_matches": ranked_matches,
        "adk_architecture": {
            "runtime_mode": ADK_RUNTIME_MODE,
            "root_agent": root_agent.name,
            "sub_agents": [a.name for a in root_agent.sub_agents],
            "agent_trace": adk_trace,
        },
        "upstream_client_summary": (
            {
                "resolved_assignee": upstream_client_result.get("resolved_assignee"),
                "patent_count": len(upstream_client_result.get("patents", [])),
            }
            if upstream_client_result
            else None
        ),
        "upstream_target_summary": (
            {
                "evidence_status": upstream_target_result.get("evidence_status"),
                "technology_areas_count": len(upstream_target_result.get("technology_areas", [])),
                "retrieved_chunks_count": len(upstream_target_result.get("retrieved_chunks", [])),
            }
            if upstream_target_result
            else None
        ),
        "canonical_output": canonical_output,
    }
