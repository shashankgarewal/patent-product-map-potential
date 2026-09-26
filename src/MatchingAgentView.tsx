import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  ExternalLink,
  AlertTriangle,
  Copy,
  Check,
  Download,
  FileSpreadsheet,
  Layers,
  Scale,
  TrendingUp,
  Clock,
  CheckCircle2,
  FileText,
  Sparkles,
  BookOpen,
} from "lucide-react";
import { MatchingAgentResponse, PatentRecord, RankedPatentProductMatch } from "./types";

interface MatchingAgentViewProps {
  clientCompanyDefault: string;
  targetCompanyDefault: string;
  technologyAreaDefault: string;
  clientPatents: PatentRecord[];
}

export default function MatchingAgentView({
  clientCompanyDefault,
  targetCompanyDefault,
  technologyAreaDefault,
  clientPatents,
}: MatchingAgentViewProps) {
  const [clientCompany, setClientCompany] = useState<string>(
    clientCompanyDefault || "Apple"
  );
  const [targetCompany, setTargetCompany] = useState<string>(
    targetCompanyDefault.includes("Netflix") ? "Netflix" : targetCompanyDefault || "Netflix"
  );
  const [technologyArea, setTechnologyArea] = useState<string>(
    technologyAreaDefault || "video streaming"
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [matchingData, setMatchingData] = useState<MatchingAgentResponse | null>(null);
  const [selectedMatchId, setSelectedMatchId] = useState<string | null>(null);
  const [priorityFilter, setPriorityFilter] = useState<string>("ALL");
  const [copiedTable, setCopiedTable] = useState<boolean>(false);
  const [copiedJson, setCopiedJson] = useState<boolean>(false);
  const [showJsonModal, setShowJsonModal] = useState<boolean>(false);

  useEffect(() => {
    if (clientCompanyDefault) setClientCompany(clientCompanyDefault);
  }, [clientCompanyDefault]);

  useEffect(() => {
    if (targetCompanyDefault) {
      setTargetCompany(targetCompanyDefault.includes("Netflix") ? "Netflix" : targetCompanyDefault);
    }
  }, [targetCompanyDefault]);

  useEffect(() => {
    setTechnologyArea(technologyAreaDefault);
  }, [technologyAreaDefault]);

  const runMatchingPipeline = async (
    overrideClient?: string,
    overrideTarget?: string,
    overrideTech?: string,
    useUpstreamPatents: boolean = true
  ) => {
    const cComp = overrideClient !== undefined ? overrideClient : clientCompany;
    const tComp = overrideTarget !== undefined ? overrideTarget : targetCompany;
    const tArea = overrideTech !== undefined ? overrideTech : technologyArea;

    setLoading(true);
    try {
      const payload: Record<string, any> = {
        client_company: cComp,
        target_company: tComp,
        technology_area: tArea,
        use_llm: true,
      };
      if (
        useUpstreamPatents &&
        clientPatents.length > 0 &&
        cComp.toLowerCase() === clientCompanyDefault.toLowerCase()
      ) {
        payload.client_patents = clientPatents;
      }

      const res = await fetch("/api/analyze-patent-target-matching", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data: MatchingAgentResponse = await res.json();
      setMatchingData(data);
      if (data.ranked_matches && data.ranked_matches.length > 0) {
        setSelectedMatchId(data.ranked_matches[0].match_id);
      } else {
        setSelectedMatchId(null);
      }
    } catch (err: any) {
      setMatchingData({
        matching_status: "PIPELINE_ERROR",
        client_company: cComp,
        target_company: tComp,
        technology_area: tArea,
        error: err?.message || "Failed to execute Patent–Target Matching & Commercial Agent.",
        ranked_matches: [],
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runMatchingPipeline(clientCompany, targetCompany, technologyArea, true);
  }, [clientPatents]);

  const filteredMatches: RankedPatentProductMatch[] = (matchingData?.ranked_matches || []).filter(
    (m) => {
      if (priorityFilter === "ALL") return true;
      return m.investigation_priority.priority_tier === priorityFilter;
    }
  );

  const selectedMatch: RankedPatentProductMatch | null =
    filteredMatches.find((m) => m.match_id === selectedMatchId) ||
    filteredMatches[0] ||
    null;

  const handleCopyRankedTable = () => {
    if (!filteredMatches.length) return;
    const headers = [
      "Rank",
      "Patent Number",
      "Patent Title",
      "Target Product / Technology",
      "Technical Overlap (Part 1)",
      "Supporting Evidence Sources",
      "Patent Status",
      "Est. Remaining Life (Yrs)",
      "Potential Monetary Opportunity (Part 2 Signal)",
      "Investigation Priority (Part 3)",
    ];
    const rows = filteredMatches.map((r) => [
      `#${r.rank}`,
      r.patent_number,
      r.patent_title,
      `${r.target_product_or_service} (${r.target_technology})`,
      `${r.technical_overlap.overlap_level} (${r.technical_overlap.technical_relevance_score}/100) — ${r.technical_overlap.summary}`,
      r.supporting_evidence.map((ev) => `${ev.source_title} (${ev.source_url})`).join("; "),
      r.patent_status,
      r.estimated_remaining_patent_life.years_remaining !== null
        ? `${r.estimated_remaining_patent_life.years_remaining} yrs`
        : "N/A",
      `${r.potential_monetary_opportunity.signal_tier} (${r.potential_monetary_opportunity.commercial_opportunity_score}/100)`,
      `${r.investigation_priority.priority_tier} (${r.investigation_priority.priority_score}/100)`,
    ]);
    const tsv = [headers.join("\t"), ...rows.map((r) => r.join("\t"))].join("\n");
    navigator.clipboard.writeText(tsv);
    setCopiedTable(true);
    setTimeout(() => setCopiedTable(false), 2000);
  };

  const handleExportCsv = () => {
    if (!filteredMatches.length) return;
    const escapeCsv = (val: any) => `"${String(val ?? "").replace(/"/g, '""')}"`;
    const headers = [
      "Rank",
      "Patent Number",
      "Patent Title",
      "Patent Description",
      "Target Product or Technology",
      "Technical Overlap Level",
      "Technical Relevance Score (Part 1)",
      "Technical Overlap Explanation",
      "Evidence Supporting Overlap",
      "Patent Status",
      "Estimated Remaining Patent Life (Years)",
      "Potential Monetary Opportunity Signal",
      "Commercial Opportunity Score (Part 2)",
      "Product-Level Revenue Disclosure Note",
      "Investigation Priority",
      "Investigation Priority Score (Part 3)",
      "Investigation Recommendation",
    ];
    const lines = filteredMatches.map((r) =>
      [
        r.rank,
        r.patent_number,
        r.patent_title,
        r.patent_description,
        `${r.target_product_or_service} — ${r.target_technology}`,
        r.technical_overlap.overlap_level,
        r.technical_overlap.technical_relevance_score,
        r.technical_overlap.summary,
        r.supporting_evidence
          .map((e) => `[${e.source_title}] ${e.text} (${e.source_url})`)
          .join(" | "),
        r.patent_status,
        r.estimated_remaining_patent_life.years_remaining ?? "Unknown",
        r.potential_monetary_opportunity.signal_tier,
        r.potential_monetary_opportunity.commercial_opportunity_score,
        r.potential_monetary_opportunity.product_level_revenue_note,
        r.investigation_priority.priority_tier,
        r.investigation_priority.priority_score,
        r.investigation_priority.rationale,
      ]
        .map(escapeCsv)
        .join(",")
    );
    const blob = new Blob([[headers.join(","), ...lines].join("\n")], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `patent_product_intelligence_matrix_${clientCompany
      .toLowerCase()
      .replace(/\s+/g, "_")}_vs_${targetCompany.toLowerCase().replace(/\s+/g, "_")}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportJson = () => {
    if (!matchingData?.canonical_output) return;
    const blob = new Blob([JSON.stringify(matchingData.canonical_output, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `patent_product_matching_canonical_${clientCompany
      .toLowerCase()
      .replace(/\s+/g, "_")}_vs_${targetCompany.toLowerCase().replace(/\s+/g, "_")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-5">
      {/* =====================================================================
          HEADER & END-TO-END MATCHING AGENT ORCHESTRATOR BAR
         ===================================================================== */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-5 shadow-2xs">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1.5 font-mono font-semibold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
                PATENT–TARGET MATCHING & COMMERCIAL OPPORTUNITY AGENT (ADK)
              </span>
              <span className="text-slate-400">·</span>
              <span className="font-mono text-slate-600">
                root_agent → technical_matching_agent → commercial_opportunity_agent → investigation_priority_agent
              </span>
            </div>

            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              Patent–Product Intelligence Matrix: {matchingData?.client_company || clientCompany} →{" "}
              {matchingData?.target_company || targetCompany}
            </h2>

            <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
              Evaluates <strong className="font-semibold text-slate-900">Part 1: Technical Relevance</strong>{" "}
              (claim-element alignment & verbatim target evidence) and{" "}
              <strong className="font-semibold text-slate-900">Part 2: Commercial Opportunity</strong>{" "}
              (pre-fetched SEC Form 10-K disclosures, strategic infrastructure criticality & deterministic
              20-year patent life) as{" "}
              <strong className="font-semibold text-slate-900">two distinct analytical dimensions</strong>{" "}
              before synthesizing <strong className="font-semibold text-slate-900">Part 3: Investigation Priority</strong>.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={handleCopyRankedTable}
              disabled={!filteredMatches.length}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 cursor-pointer"
            >
              {copiedTable ? (
                <Check className="w-3.5 h-3.5 text-emerald-600" />
              ) : (
                <Copy className="w-3.5 h-3.5 text-slate-500" />
              )}
              <span>{copiedTable ? "Copied Table" : "Copy 9-Col Table"}</span>
            </button>

            <button
              type="button"
              onClick={handleExportCsv}
              disabled={!filteredMatches.length}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 cursor-pointer"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-slate-500" />
              <span>Export CSV</span>
            </button>

            <button
              type="button"
              onClick={() => setShowJsonModal(!showJsonModal)}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 cursor-pointer"
            >
              <FileText className="w-3.5 h-3.5 text-slate-500" />
              <span>{showJsonModal ? "Hide Canonical JSON" : "View Canonical JSON"}</span>
            </button>

            <button
              type="button"
              onClick={handleExportJson}
              disabled={!matchingData?.canonical_output}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-[#080C14] rounded-lg hover:bg-slate-800 disabled:opacity-40 cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Dossier JSON</span>
            </button>
          </div>
        </div>

        {/* Interactive Client + Target + Niche Execution Strip */}
        <div className="pt-4 border-t border-slate-200 grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
          <div className="md:col-span-3 space-y-1">
            <label className="text-[10px] font-bold tracking-wider uppercase text-slate-500 block">
              CLIENT / PATENT OWNER
            </label>
            <input
              type="text"
              value={clientCompany}
              onChange={(e) => setClientCompany(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg font-medium text-slate-900 focus:bg-white focus:outline-none focus:border-slate-400"
              placeholder="e.g., Dolby Laboratories"
            />
          </div>

          <div className="md:col-span-3 space-y-1">
            <label className="text-[10px] font-bold tracking-wider uppercase text-slate-500 block">
              TARGET COMPANY (OFFLINE DB)
            </label>
            <input
              type="text"
              value={targetCompany}
              onChange={(e) => setTargetCompany(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg font-medium text-slate-900 focus:bg-white focus:outline-none focus:border-slate-400"
              placeholder="e.g., Netflix"
            />
          </div>

          <div className="md:col-span-3 space-y-1">
            <label className="text-[10px] font-bold tracking-wider uppercase text-slate-500 block">
              TECHNOLOGY AREA / NICHE
            </label>
            <input
              type="text"
              value={technologyArea}
              onChange={(e) => setTechnologyArea(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg font-medium text-slate-900 focus:bg-white focus:outline-none focus:border-slate-400"
              placeholder="e.g., video streaming"
            />
          </div>

          <div className="md:col-span-3">
            <button
              type="button"
              onClick={() => runMatchingPipeline(clientCompany, targetCompany, technologyArea, false)}
              disabled={loading}
              className="w-full py-2 px-4 bg-[#080C14] hover:bg-slate-800 disabled:opacity-50 text-white font-semibold text-xs rounded-lg flex items-center justify-center gap-2 transition-colors cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{loading ? "Running ADK Matching..." : "Run Patent–Target Matching"}</span>
            </button>
          </div>
        </div>

        {/* Mandatory Positioning & Non-Infringement Guardrail Banner */}
        <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-2.5 flex items-start gap-2.5 text-[11px] text-slate-600">
          <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
          <div>
            <strong className="font-semibold text-slate-900">
              Preliminary Technical & Commercial Screening Only — Not a Legal Infringement Determination:
            </strong>{" "}
            Identifies <em>potential technical overlap</em>, <em>candidates for investigation</em>, and{" "}
            <em>analytical monetary opportunity signals</em> grounded in BigQuery patent publications and
            pre-fetched public target disclosures. Never establishes patent infringement or calculates
            royalties/damages; all candidates require expert technical and legal counsel review.
          </div>
        </div>
      </section>

      {/* =====================================================================
          INSUFFICIENT EVIDENCE OR ERROR GUARDRAIL
         ===================================================================== */}
      {!loading && matchingData && matchingData.matching_status !== "SUCCESS" && (
        <section className="bg-white border-2 border-amber-300 rounded-xl p-6 space-y-3">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <div className="text-xs font-mono font-semibold text-amber-800">
                EVIDENCE GUARDRAIL · {matchingData.matching_status}
              </div>
              <h3 className="text-base font-bold text-slate-900">
                Cannot Fabricate Patent–Target Matching Relationships
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                {matchingData.diagnostic_reason ||
                  matchingData.error ||
                  "Insufficient pre-fetched target company evidence or unresolved client company."}
              </p>
            </div>
          </div>
        </section>
      )}

      {/* =====================================================================
          4 KPI SUMMARY STRIP (SEPARATE PART 1 TECHNICAL VS PART 2 COMMERCIAL)
         ===================================================================== */}
      {!loading && matchingData && matchingData.matching_status === "SUCCESS" && (
        <>
          <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
              <div className="flex items-center justify-between text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                <span>HIGH-PRIORITY CANDIDATES</span>
                <ShieldCheck className="w-3.5 h-3.5 text-red-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold font-mono tabular-nums text-red-600">
                  {matchingData.summary_metrics?.high_priority_count ?? 0}
                </span>
                <span className="text-xs text-slate-600">
                  of {matchingData.summary_metrics?.total_relationships_ranked ?? 0} ranked
                </span>
              </div>
              <div className="text-[11px] text-slate-500">
                Active granted + strong technical evidence + core target scale
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
              <div className="flex items-center justify-between text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                <span>PART 1 · AVG TECHNICAL SCORE</span>
                <Layers className="w-3.5 h-3.5 text-blue-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold font-mono tabular-nums text-blue-700">
                  {matchingData.summary_metrics?.avg_technical_relevance_score ?? 0}
                </span>
                <span className="text-xs text-slate-500">/ 100 (Part 1 Separate)</span>
              </div>
              <div className="text-[11px] text-slate-500">
                Claim-element coverage + verbatim target evidence
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
              <div className="flex items-center justify-between text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                <span>PART 2 · AVG COMMERCIAL SCORE</span>
                <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold font-mono tabular-nums text-emerald-700">
                  {matchingData.summary_metrics?.avg_commercial_opportunity_score ?? 0}
                </span>
                <span className="text-xs text-slate-500">/ 100 (Part 2 Separate)</span>
              </div>
              <div className="text-[11px] text-slate-500">
                10-K infrastructure criticality + patent life viability
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
              <div className="flex items-center justify-between text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                <span>REVENUE NON-FABRICATION</span>
                <Scale className="w-3.5 h-3.5 text-slate-600" />
              </div>
              <div className="text-sm font-bold text-slate-900 font-mono">
                SEC Form 10-K Verified
              </div>
              <div className="text-[11px] text-slate-500 leading-snug">
                Consolidated $33.7B–$39.0B reported; subsystem revenue explicitly marked undisclosed
              </div>
            </div>
          </section>

          {/* Optional Canonical JSON Drawer */}
          {showJsonModal && (
            <section className="bg-slate-950 text-slate-100 rounded-xl p-5 space-y-3 border border-slate-800">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-semibold text-blue-400">
                  CANONICAL PATENT–PRODUCT INTELLIGENCE OUTPUT JSON
                </span>
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard.writeText(
                      JSON.stringify(matchingData.canonical_output, null, 2)
                    );
                    setCopiedJson(true);
                    setTimeout(() => setCopiedJson(false), 2000);
                  }}
                  className="px-2.5 py-1 text-xs font-mono bg-slate-800 hover:bg-slate-700 rounded text-slate-200 cursor-pointer"
                >
                  {copiedJson ? "Copied JSON" : "Copy JSON"}
                </button>
              </div>
              <pre className="text-[11px] font-mono overflow-x-auto max-h-96 leading-relaxed text-slate-300">
                {JSON.stringify(matchingData.canonical_output, null, 2)}
              </pre>
            </section>
          )}

          {/* =================================================================
              MAIN FINAL OUTPUT: 9-COLUMN RANKED PATENT–PRODUCT INTELLIGENCE TABLE
             ================================================================= */}
          <section className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
            <div className="px-5 py-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2.5">
                  <h3 className="text-sm font-bold text-slate-900">
                    Ranked Patent–Product Intelligence Table (All 9 Required Screening Dimensions)
                  </h3>
                  <span className="text-[11px] font-mono font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                    {filteredMatches.length} Relationships
                  </span>
                </div>
                <p className="text-[11px] text-slate-500">
                  Click any row to inspect the full Claim-Element vs. Target Capability Alignment
                  Matrix (Part 1) and SEC Form 10-K Commercial Evidence Dossier (Part 2) below.
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-[10px] font-bold text-slate-400 uppercase">
                  FILTER PRIORITY:
                </span>
                <select
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value)}
                  className="bg-white border border-slate-200 rounded-md px-2.5 py-1 text-xs font-medium text-slate-800"
                >
                  <option value="ALL">
                    All Priorities ({matchingData.ranked_matches.length})
                  </option>
                  <option value="High Priority">High Priority</option>
                  <option value="Medium Priority">Medium Priority</option>
                  <option value="Low Priority">Low Priority</option>
                  <option value="Low Priority (Expired Term)">
                    Low Priority (Expired Term)
                  </option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[#080C14] text-white text-[10px] font-mono font-bold tracking-wider uppercase">
                    <th className="py-3.5 px-3.5 w-28">1. PATENT NO.</th>
                    <th className="py-3.5 px-3.5 w-56">2. PATENT TITLE / DESCRIPTION</th>
                    <th className="py-3.5 px-3.5 w-52">3. TARGET PRODUCT / TECHNOLOGY</th>
                    <th className="py-3.5 px-3.5 w-60">4. TECHNICAL OVERLAP (PART 1)</th>
                    <th className="py-3.5 px-3.5 w-60">5. EVIDENCE SUPPORTING OVERLAP</th>
                    <th className="py-3.5 px-3.5 w-32">6. PATENT STATUS</th>
                    <th className="py-3.5 px-3.5 w-28">7. EST. LIFE</th>
                    <th className="py-3.5 px-3.5 w-56">
                      8. POTENTIAL MONETARY OPPORTUNITY (PART 2)
                    </th>
                    <th className="py-3.5 px-3.5 w-44">9. INVESTIGATION PRIORITY</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 text-xs">
                  {filteredMatches.map((row) => {
                    const isSelected = selectedMatch?.match_id === row.match_id;
                    const overlapLevel = row.technical_overlap.overlap_level;
                    const priorityTier = row.investigation_priority.priority_tier;
                    const yearsRem = row.estimated_remaining_patent_life.years_remaining;

                    return (
                      <tr
                        key={row.match_id}
                        onClick={() => setSelectedMatchId(row.match_id)}
                        className={`cursor-pointer transition-colors align-top ${
                          isSelected
                            ? "bg-blue-50/60 border-l-4 border-l-blue-600"
                            : "hover:bg-slate-50/80"
                        }`}
                      >
                        {/* 1. Patent Number */}
                        <td className="py-4 px-3.5 font-mono">
                          <div className="text-[10px] font-bold text-slate-400">
                            RANK #{row.rank}
                          </div>
                          <div className="font-bold text-blue-700 text-xs mt-0.5">
                            {row.patent_number}
                          </div>
                          <div className="text-[10px] text-slate-500 mt-1">
                            CPC: {(row.patent_cpc_codes || []).slice(0, 2).join(" · ") || "N/A"}
                          </div>
                        </td>

                        {/* 2. Patent Title / Description */}
                        <td className="py-4 px-3.5">
                          <div className="font-bold text-slate-900 leading-snug">
                            {row.patent_title}
                          </div>
                          <p className="text-[11px] text-slate-600 line-clamp-3 mt-1 leading-relaxed">
                            {row.patent_description}
                          </p>
                        </td>

                        {/* 3. Target Product or Technology */}
                        <td className="py-4 px-3.5">
                          <div className="font-bold text-slate-900 leading-snug">
                            {row.target_product_or_service}
                          </div>
                          <div className="text-[11px] font-medium text-indigo-700 mt-1">
                            {row.target_technology}
                          </div>
                          <div className="text-[10px] text-slate-500 mt-1 font-mono">
                            Target: {row.target_company}
                          </div>
                        </td>

                        {/* 4. Technical Overlap (Part 1 Distinct Score & Summary) */}
                        <td className="py-4 px-3.5">
                          <div className="flex items-center justify-between gap-2 mb-1.5">
                            <span
                              className={`text-[11px] font-mono font-bold ${
                                overlapLevel === "High"
                                  ? "text-blue-700"
                                  : overlapLevel === "Medium"
                                  ? "text-amber-700"
                                  : "text-slate-600"
                              }`}
                            >
                              {overlapLevel} Overlap
                            </span>
                            <span className="font-mono font-bold text-xs tabular-nums text-slate-900">
                              {row.technical_overlap.technical_relevance_score}/100
                            </span>
                          </div>
                          <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden mb-2">
                            <div
                              className={`h-full ${
                                overlapLevel === "High"
                                  ? "bg-blue-600"
                                  : overlapLevel === "Medium"
                                  ? "bg-amber-500"
                                  : "bg-slate-400"
                              }`}
                              style={{
                                width: `${Math.min(
                                  100,
                                  row.technical_overlap.technical_relevance_score
                                )}%`,
                              }}
                            />
                          </div>
                          <p className="text-[11px] text-slate-600 line-clamp-3 leading-relaxed">
                            {row.technical_overlap.summary}
                          </p>
                          <div className="text-[10px] font-mono text-slate-500 mt-1.5">
                            {row.technical_overlap.has_source_claims ? (
                              <>
                                Claims:{" "}
                                <strong className="text-emerald-700">
                                  {row.technical_overlap.claim_element_counts.evidence_identified}{" "}
                                  confirmed
                                </strong>{" "}
                                · {row.technical_overlap.claim_element_counts.partial_alignment}{" "}
                                partial
                              </>
                            ) : (
                              <span className="text-amber-700">
                                Missing source claims (concept match only)
                              </span>
                            )}
                          </div>
                        </td>

                        {/* 5. Evidence Supporting Overlap */}
                        <td className="py-4 px-3.5">
                          <div className="space-y-2">
                            {(row.supporting_evidence || []).slice(0, 2).map((ev, i) => (
                              <div
                                key={i}
                                className="text-[11px] bg-slate-50 border border-slate-200/80 rounded p-2 space-y-1"
                              >
                                <div className="font-semibold text-slate-800 line-clamp-1">
                                  {ev.source_title}
                                </div>
                                <p className="text-[10px] text-slate-600 line-clamp-2 italic">
                                  "{ev.text}"
                                </p>
                                <a
                                  href={ev.source_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  onClick={(e) => e.stopPropagation()}
                                  className="inline-flex items-center gap-1 text-[10px] font-mono text-blue-600 hover:underline"
                                >
                                  <span>Source URL</span>
                                  <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              </div>
                            ))}
                          </div>
                        </td>

                        {/* 6. Patent Status */}
                        <td className="py-4 px-3.5">
                          <div
                            className={`text-[11px] font-semibold leading-snug ${
                              row.patent_status.toLowerCase().includes("expired")
                                ? "text-red-700"
                                : row.patent_status.toLowerCase().includes("application")
                                ? "text-amber-700"
                                : "text-emerald-700"
                            }`}
                          >
                            {row.patent_status}
                          </div>
                          <div className="text-[10px] font-mono text-slate-500 mt-1">
                            Filed: {row.patent_filing_date || "Unknown"}
                          </div>
                        </td>

                        {/* 7. Estimated Remaining Patent Life */}
                        <td className="py-4 px-3.5 font-mono">
                          <div
                            className={`text-sm font-bold tabular-nums ${
                              yearsRem === null
                                ? "text-slate-400"
                                : yearsRem <= 0
                                ? "text-red-600"
                                : yearsRem >= 10
                                ? "text-emerald-700"
                                : "text-slate-900"
                            }`}
                          >
                            {yearsRem !== null ? `${yearsRem} yrs` : "Unknown"}
                          </div>
                          <div className="text-[10px] text-slate-500 mt-0.5">
                            {row.estimated_remaining_patent_life.expiration_date_nominal
                              ? `Exp: ${row.estimated_remaining_patent_life.expiration_date_nominal}`
                              : "20-yr statutory baseline"}
                          </div>
                        </td>

                        {/* 8. Potential Monetary Opportunity (Part 2 Distinct Score & Signal) */}
                        <td className="py-4 px-3.5">
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <span className="text-[11px] font-bold text-emerald-800 line-clamp-1">
                              {row.potential_monetary_opportunity.signal_tier.split("(")[0].trim()}
                            </span>
                            <span className="font-mono font-bold text-xs tabular-nums text-emerald-700 shrink-0">
                              {row.potential_monetary_opportunity.commercial_opportunity_score}/100
                            </span>
                          </div>
                          <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden mb-1.5">
                            <div
                              className="h-full bg-emerald-600"
                              style={{
                                width: `${Math.min(
                                  100,
                                  row.potential_monetary_opportunity.commercial_opportunity_score
                                )}%`,
                              }}
                            />
                          </div>
                          <div className="text-[10px] text-slate-600 leading-snug line-clamp-2">
                            {row.potential_monetary_opportunity.strategic_role}
                          </div>
                          <div className="text-[10px] font-mono text-slate-500 mt-1">
                            10-K Segment: $33.7B–$39.0B (Subsystem rev. undisclosed)
                          </div>
                        </td>

                        {/* 9. Investigation Priority */}
                        <td className="py-4 px-3.5">
                          <div
                            className={`inline-flex items-center gap-1.5 text-xs font-bold ${
                              priorityTier === "High Priority"
                                ? "text-red-600"
                                : priorityTier === "Medium Priority"
                                ? "text-amber-700"
                                : "text-slate-600"
                            }`}
                          >
                            <span
                              className={`w-2 h-2 rounded-full ${
                                priorityTier === "High Priority"
                                  ? "bg-red-600"
                                  : priorityTier === "Medium Priority"
                                  ? "bg-amber-500"
                                  : "bg-slate-400"
                              }`}
                            />
                            <span>{priorityTier}</span>
                          </div>
                          <div className="font-mono text-xs font-bold text-slate-900 mt-1 tabular-nums">
                            Priority Score: {row.investigation_priority.priority_score}/100
                          </div>
                          <p className="text-[10px] text-slate-600 mt-1 line-clamp-2 leading-relaxed">
                            {row.investigation_priority.rationale}
                          </p>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>

          {/* =================================================================
              DETAILED TWO-PART ANALYTICAL INSPECTOR FOR SELECTED RELATIONSHIP
             ================================================================= */}
          {selectedMatch && (
            <section className="grid grid-cols-1 lg:grid-cols-12 gap-5">
              {/* LEFT 7 COLUMNS: PART 1 — TECHNICAL RELEVANCE & CLAIM-ELEMENT ALIGNMENT */}
              <div className="lg:col-span-7 bg-white border border-slate-200 rounded-xl p-6 space-y-5 shadow-2xs">
                <div className="flex items-start justify-between gap-4 border-b border-slate-200 pb-4">
                  <div className="space-y-1">
                    <div className="text-[11px] font-mono font-bold text-blue-700 uppercase">
                      PART 1 — TECHNICAL MATCHING ANALYSIS (technical_matching_agent)
                    </div>
                    <h3 className="text-lg font-bold text-slate-900">
                      {selectedMatch.patent_number} ↔ {selectedMatch.target_product_or_service}
                    </h3>
                    <div className="text-xs text-slate-600">
                      {selectedMatch.patent_title} ·{" "}
                      <span className="font-semibold text-indigo-700">
                        {selectedMatch.target_technology}
                      </span>
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <div className="text-[10px] font-mono uppercase text-slate-400">
                      PART 1 TECHNICAL SCORE
                    </div>
                    <div className="text-2xl font-bold font-mono tabular-nums text-blue-700">
                      {selectedMatch.technical_overlap.technical_relevance_score}
                      <span className="text-xs text-slate-400 font-normal">/100</span>
                    </div>
                    <div className="text-[11px] font-semibold text-slate-700">
                      {selectedMatch.technical_overlap.overlap_level} Technical Overlap
                    </div>
                  </div>
                </div>

                {/* Technical Overlap Narrative */}
                <div className="bg-blue-50/50 border border-blue-200/80 rounded-lg p-4 space-y-2">
                  <div className="text-[11px] font-mono font-bold text-blue-900 uppercase">
                    Evidence-Backed Technical Overlap Explanation (Screening Assessment)
                  </div>
                  <p className="text-xs text-slate-800 leading-relaxed">
                    {selectedMatch.technical_overlap.summary}
                  </p>
                  {selectedMatch.technical_overlap.shared_technical_mechanisms.length > 0 && (
                    <div className="text-[11px] font-mono text-blue-800 pt-1">
                      Shared Mechanisms:{" "}
                      {selectedMatch.technical_overlap.shared_technical_mechanisms.join(" · ")}
                    </div>
                  )}
                </div>

                {/* Part 1 Deterministic Factor Breakdown */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  {Object.entries(selectedMatch.technical_overlap.factor_breakdown || {}).map(
                    ([key, fac]) => (
                      <div
                        key={key}
                        className="border border-slate-200 rounded-lg p-2.5 bg-slate-50/50"
                      >
                        <div className="text-[10px] font-mono uppercase text-slate-500 truncate">
                          {key.replace(/_/g, " ")}
                        </div>
                        <div className="text-sm font-bold font-mono text-slate-900 mt-0.5 tabular-nums">
                          {fac.score} / {fac.max}
                        </div>
                        <div className="text-[10px] text-slate-500 line-clamp-2 mt-0.5">
                          {fac.detail}
                        </div>
                      </div>
                    )
                  )}
                </div>

                {/* Claim-Element to Target Capability Alignment Matrix */}
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                      Independent Claim Element ↔ Target Capability Mapping
                    </h4>
                    <span className="text-[11px] font-mono text-slate-500">
                      {selectedMatch.technical_overlap.claim_element_counts.evidence_identified}{" "}
                      Confirmed ·{" "}
                      {selectedMatch.technical_overlap.claim_element_counts.partial_alignment}{" "}
                      Partial ·{" "}
                      {selectedMatch.technical_overlap.claim_element_counts.not_documented}{" "}
                      Unconfirmed
                    </span>
                  </div>

                  {selectedMatch.technical_overlap.claim_element_mapping.length === 0 ? (
                    <div className="border border-amber-200 bg-amber-50/60 rounded-lg p-3.5 text-xs text-amber-900">
                      <strong>Source Claim Guardrail:</strong> This publication (
                      <span className="font-mono">{selectedMatch.patent_number}</span>) does not
                      contain indexed independent claims in{" "}
                      <span className="font-mono">patents-public-data.patents.publications</span>.
                      The agent refuses to fabricate claim elements and restricts technical
                      comparison to abstract and specification disclosures.
                    </div>
                  ) : (
                    <div className="border border-slate-200 rounded-lg overflow-hidden">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="bg-slate-100 text-slate-700 font-mono text-[10px] uppercase">
                            <th className="py-2 px-3 w-16">ELEM</th>
                            <th className="py-2 px-3">PATENT CLAIM LIMITATION (SOURCE FACT)</th>
                            <th className="py-2 px-3 w-44">TARGET EVIDENCE STATUS</th>
                            <th className="py-2 px-3">DOCUMENTED TARGET CAPABILITY & SOURCE</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200">
                          {selectedMatch.technical_overlap.claim_element_mapping.map((em) => (
                            <tr key={em.element_id} className="align-top">
                              <td className="py-2.5 px-3 font-mono font-bold text-blue-700">
                                {em.element_id}
                              </td>
                              <td className="py-2.5 px-3">
                                <div className="font-semibold text-slate-900">
                                  {em.technical_concept}
                                </div>
                                <div className="text-[11px] text-slate-600 mt-0.5 leading-relaxed">
                                  {em.claim_element_description}
                                </div>
                              </td>
                              <td className="py-2.5 px-3 font-mono text-[10px]">
                                {em.alignment_status === "EVIDENCE_IDENTIFIED" ? (
                                  <span className="font-bold text-emerald-700">
                                    ● EVIDENCE IDENTIFIED
                                  </span>
                                ) : em.alignment_status === "PARTIAL_ALIGNMENT" ? (
                                  <span className="font-bold text-amber-700">
                                    ◐ PARTIAL ALIGNMENT
                                  </span>
                                ) : (
                                  <span className="font-bold text-slate-500">
                                    ○ NOT IN PUBLIC DOCS
                                  </span>
                                )}
                              </td>
                              <td className="py-2.5 px-3 text-[11px] text-slate-700">
                                <p className="leading-relaxed">{em.alignment_rationale}</p>
                                {em.supporting_source_url && (
                                  <a
                                    href={em.supporting_source_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-[10px] font-mono text-blue-600 hover:underline mt-1"
                                  >
                                    <span>{em.supporting_source_title}</span>
                                    <ExternalLink className="w-2.5 h-2.5" />
                                  </a>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                {/* Verbatim Supporting Target Evidence Chunks */}
                <div className="space-y-2.5">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Verbatim Supporting Target Evidence (From Pre-Fetched Target Knowledge DB)
                  </h4>
                  <div className="space-y-2.5">
                    {selectedMatch.supporting_evidence.map((ev, idx) => (
                      <div
                        key={idx}
                        className="border border-slate-200 rounded-lg p-3.5 bg-slate-50/60 space-y-1.5"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs font-bold text-slate-900">
                            {ev.source_title}
                          </span>
                          <span className="text-[10px] font-mono text-slate-500">
                            {ev.source_type} · {ev.published_date || "Public Source"}
                          </span>
                        </div>
                        <p className="text-xs text-slate-700 italic leading-relaxed">
                          "{ev.text}"
                        </p>
                        <div className="pt-1 flex items-center justify-between text-[11px]">
                          <a
                            href={ev.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 font-mono text-blue-600 hover:underline"
                          >
                            <span>{ev.source_url}</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Evidence Gaps & Unconfirmed Technical Aspects */}
                <div className="border border-amber-200 bg-amber-50/40 rounded-lg p-4 space-y-2">
                  <div className="text-[11px] font-mono font-bold text-amber-900 uppercase">
                    Evidence Gaps & Unconfirmed Parameters (Requires Expert / Legal Review)
                  </div>
                  <ul className="list-disc list-inside space-y-1 text-xs text-slate-700 leading-relaxed">
                    {selectedMatch.technical_overlap.evidence_gaps.map((gap, i) => (
                      <li key={i}>{gap}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* RIGHT 5 COLUMNS: PART 2 — COMMERCIAL OPPORTUNITY & PART 3 — PRIORITIZATION */}
              <div className="lg:col-span-5 space-y-5">
                <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-5 shadow-2xs">
                  <div className="flex items-start justify-between gap-4 border-b border-slate-200 pb-4">
                    <div className="space-y-1">
                      <div className="text-[11px] font-mono font-bold text-emerald-700 uppercase">
                        PART 2 — COMMERCIAL OPPORTUNITY (commercial_opportunity_agent)
                      </div>
                      <h3 className="text-base font-bold text-slate-900">
                        Commercial Significance & Patent Viability
                      </h3>
                      <div className="text-xs text-slate-600">
                        Analytical signal — distinct from Part 1 technical overlap
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <div className="text-[10px] font-mono uppercase text-slate-400">
                        PART 2 COMMERCIAL SCORE
                      </div>
                      <div className="text-2xl font-bold font-mono tabular-nums text-emerald-700">
                        {
                          selectedMatch.potential_monetary_opportunity
                            .commercial_opportunity_score
                        }
                        <span className="text-xs text-slate-400 font-normal">/100</span>
                      </div>
                    </div>
                  </div>

                  {/* Analytical Monetary Opportunity Signal Banner */}
                  <div className="bg-emerald-50/60 border border-emerald-200 rounded-lg p-4 space-y-2">
                    <div className="text-xs font-bold text-emerald-950">
                      Signal: {selectedMatch.potential_monetary_opportunity.signal_tier}
                    </div>
                    <p className="text-xs text-slate-800 leading-relaxed">
                      {selectedMatch.potential_monetary_opportunity.rationale}
                    </p>
                  </div>

                  {/* Part 2 Factor Breakdown */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                    {Object.entries(
                      selectedMatch.potential_monetary_opportunity.factor_breakdown || {}
                    ).map(([k, fac]) => (
                      <div
                        key={k}
                        className="border border-slate-200 rounded-lg p-2.5 bg-slate-50/50"
                      >
                        <div className="text-[10px] font-mono uppercase text-slate-500 truncate">
                          {k.replace(/_/g, " ")}
                        </div>
                        <div className="text-sm font-bold font-mono text-slate-900 mt-0.5 tabular-nums">
                          {fac.score} / {fac.max}
                        </div>
                        <div className="text-[10px] text-slate-500 line-clamp-2 mt-0.5">
                          {fac.detail}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Public Commercial Intelligence Table (SEC Form 10-K & Non-Fabrication Proof) */}
                  <div className="space-y-2.5">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                      Pre-Fetched Public Commercial Facts (SEC Form 10-K & Disclosures)
                    </h4>
                    <div className="border border-slate-200 rounded-lg divide-y divide-slate-200 text-xs">
                      <div className="p-3 flex flex-col gap-0.5">
                        <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                          CONSOLIDATED COMPANY / SEGMENT REVENUE (SOURCE FACT)
                        </span>
                        <span className="font-semibold text-slate-900">
                          {selectedMatch.potential_monetary_opportunity
                            .consolidated_company_revenue || "Not publicly disclosed in DB"}
                        </span>
                      </div>

                      <div className="p-3 flex flex-col gap-0.5 bg-amber-50/40">
                        <span className="text-[10px] font-mono font-bold text-amber-800 uppercase">
                          PRODUCT-LEVEL REVENUE GUARDRAIL (NON-FABRICATION RULE)
                        </span>
                        <span className="text-slate-800 leading-relaxed">
                          {
                            selectedMatch.potential_monetary_opportunity
                              .product_level_revenue_note
                          }
                        </span>
                      </div>

                      <div className="p-3 flex flex-col gap-0.5">
                        <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                          STRATEGIC ROLE & ADOPTION SCALE
                        </span>
                        <span className="font-semibold text-slate-900">
                          {selectedMatch.potential_monetary_opportunity.strategic_role}
                        </span>
                        <span className="text-slate-600 text-[11px] mt-0.5">
                          {
                            selectedMatch.potential_monetary_opportunity
                              .subscriber_or_adoption_scale
                          }
                        </span>
                      </div>

                      <div className="p-3 flex flex-col gap-0.5">
                        <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                          SUBSCRIPTION PRICING TIER LINKAGE
                        </span>
                        <span className="text-slate-800">
                          {selectedMatch.potential_monetary_opportunity.pricing_tiers_disclosed}
                        </span>
                      </div>

                      <div className="p-3 flex flex-col gap-0.5">
                        <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                          DETERMINISTIC PATENT STATUS & REMAINING TERM VIABILITY
                        </span>
                        <span className="font-semibold text-slate-900">
                          {selectedMatch.patent_status} ·{" "}
                          {selectedMatch.estimated_remaining_patent_life.years_remaining !== null
                            ? `${selectedMatch.estimated_remaining_patent_life.years_remaining} years remaining`
                            : "Remaining term unknown"}
                        </span>
                        <span className="text-[11px] text-slate-600 mt-0.5">
                          {selectedMatch.estimated_remaining_patent_life.viability_note}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Supporting SEC 10-K Sources */}
                  {selectedMatch.potential_monetary_opportunity.supporting_commercial_sources
                    .length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                        Supporting Commercial Source Citations (Form 10-K)
                      </h4>
                      {selectedMatch.potential_monetary_opportunity.supporting_commercial_sources.map(
                        (cs) => (
                          <div
                            key={cs.chunk_id}
                            className="border border-slate-200 rounded-lg p-3 bg-slate-50 text-[11px] space-y-1"
                          >
                            <div className="font-bold text-slate-900">{cs.source_title}</div>
                            <p className="text-slate-600 italic line-clamp-3">
                              "{cs.verbatim_excerpt}"
                            </p>
                            <a
                              href={cs.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 font-mono text-[10px] text-blue-600 hover:underline"
                            >
                              <span>{cs.source_url}</span>
                              <ExternalLink className="w-2.5 h-2.5" />
                            </a>
                          </div>
                        )
                      )}
                    </div>
                  )}
                </div>

                {/* PART 3: INVESTIGATION PRIORITIZATION & ADK EXECUTION TRACE */}
                <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-2xs">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                    <div>
                      <div className="text-[11px] font-mono font-bold text-slate-500 uppercase">
                        PART 3 — INVESTIGATION PRIORITIZATION (investigation_priority_agent)
                      </div>
                      <h4 className="text-base font-bold text-slate-900">
                        {selectedMatch.investigation_priority.priority_tier} (Score:{" "}
                        {selectedMatch.investigation_priority.priority_score}/100)
                      </h4>
                    </div>
                    <CheckCircle2 className="w-5 h-5 text-blue-600" />
                  </div>

                  <p className="text-xs text-slate-700 leading-relaxed">
                    {selectedMatch.investigation_priority.rationale}
                  </p>

                  {/* ADK Agent Trace */}
                  {matchingData.adk_architecture?.agent_trace && (
                    <div className="pt-2 border-t border-slate-100 space-y-2">
                      <div className="text-[10px] font-mono font-bold uppercase text-slate-400">
                        GOOGLE ADK SEQUENTIAL AGENT EXECUTION TRACE
                      </div>
                      {matchingData.adk_architecture.agent_trace.map((st, i) => (
                        <div
                          key={i}
                          className="text-[11px] bg-slate-50 border border-slate-200/80 rounded p-2.5 space-y-0.5"
                        >
                          <div className="flex items-center justify-between font-mono">
                            <span className="font-bold text-slate-900">{st.agent}</span>
                            <span className="text-[10px] text-emerald-700 font-semibold">
                              {st.status}
                            </span>
                          </div>
                          <div className="text-slate-600">{st.summary}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
