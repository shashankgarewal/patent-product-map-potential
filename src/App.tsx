import React, { useState, useEffect, useMemo } from "react";
import {
  Search,
  Building2,
  Target,
  Network,
  Zap,
  ShieldCheck,
  Copy,
  Check,
  Download,
  FileSpreadsheet,
  FileCode2,
  AlertTriangle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Layers,
  Database,
  BarChart3,
  Archive,
  SlidersHorizontal,
  Clock,
  CheckCircle2,
  BookOpen,
  Scale,
  TrendingUp,
} from "lucide-react";
import { PipelineResponse, PatentRecord, RankedPatentProductMatch } from "./types";
import TargetPrefetchView from "./TargetPrefetchView";
import TargetAgentView from "./TargetAgentView";

type WorkspaceView =
  | "dossier"
  | "claims"
  | "clusters"
  | "target_agent"
  | "target_prefetch"
  | "schema"
  | "json";

export interface UnifiedCandidateMatchRow {
  patent: PatentRecord;
  match: RankedPatentProductMatch | null;
}

export default function App() {
  const [clientCompany, setClientCompany] = useState<string>("Apple");
  const [targetCompanyPreview, setTargetCompanyPreview] = useState<string>("Netflix, Inc.");
  const [technologyArea, setTechnologyArea] = useState<string>("content recommendation");
  const [maxCandidates, setMaxCandidates] = useState<number>(10);
  const [maxCandidatesInput, setMaxCandidatesInput] = useState<string>("10");
  const [inputMode, setInputMode] = useState<"form" | "json">("form");
  const [rawJsonInput, setRawJsonInput] = useState<string>(
    JSON.stringify(
      {
        client_company: "Apple",
        target_company: "Netflix",
        technology_area: "content recommendation",
        max_candidates: 10,
      },
      null,
      2
    )
  );
  const [jsonError, setJsonError] = useState<string | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [pipelineData, setPipelineData] = useState<PipelineResponse | null>(null);
  const [selectedPatentNumber, setSelectedPatentNumber] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<WorkspaceView>("dossier");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [clusterFilter, setClusterFilter] = useState<string>("ALL");
  const [priorityFilter, setPriorityFilter] = useState<string>("ALL");
  const [sortBy, setSortBy] = useState<
    "priority_desc" | "technical_desc" | "commercial_desc" | "relevance_desc" | "term_desc" | "filing_desc"
  >("priority_desc");
  const [copiedTable, setCopiedTable] = useState<boolean>(false);
  const [copiedJson, setCopiedJson] = useState<boolean>(false);
  const [completedTimestamp, setCompletedTimestamp] = useState<string>("07:24:12 UTC");

  const executePipeline = async (
    companyOverride?: string,
    techOverride?: string,
    maxCandidatesOverride?: number
  ) => {
    setJsonError(null);
    let companyToRun = companyOverride !== undefined ? companyOverride : clientCompany;
    let targetToRun = targetCompanyPreview.replace(/,\s*Inc\.?$/i, "").trim() || "Netflix";
    let techToRun = techOverride !== undefined ? techOverride : technologyArea;
    const parsedInputCount = parseInt(maxCandidatesInput, 10);
    let countToRun =
      maxCandidatesOverride !== undefined
        ? maxCandidatesOverride
        : !Number.isNaN(parsedInputCount)
        ? Math.max(1, Math.min(100, parsedInputCount))
        : maxCandidates;
    setMaxCandidates(countToRun);
    setMaxCandidatesInput(String(countToRun));

    if (companyOverride === undefined && inputMode === "json") {
      try {
        const parsed = JSON.parse(rawJsonInput);
        companyToRun = String(parsed.client_company || "").trim();
        if (parsed.target_company) {
          targetToRun = String(parsed.target_company).trim();
          setTargetCompanyPreview(targetToRun);
        }
        techToRun =
          parsed.technology_area && parsed.technology_area !== "optional"
            ? String(parsed.technology_area).trim()
            : "";
        if (parsed.max_candidates !== undefined) {
          countToRun = Math.max(1, Math.min(100, Number(parsed.max_candidates) || 10));
          setMaxCandidates(countToRun);
          setMaxCandidatesInput(String(countToRun));
        }
        setClientCompany(companyToRun);
        setTechnologyArea(techToRun);
      } catch (_err) {
        setJsonError(
          'Invalid JSON payload. Expected {"client_company": "...", "target_company": "...", "technology_area": "...", "max_candidates": 6}'
        );
        return;
      }
    } else {
      setRawJsonInput(
        JSON.stringify(
          {
            client_company: companyToRun,
            target_company: targetToRun,
            technology_area: techToRun || "optional",
            max_candidates: countToRun,
          },
          null,
          2
        )
      );
    }

    setLoading(true);
    setClusterFilter("ALL");
    setPriorityFilter("ALL");
    try {
      const res = await fetch("/api/analyze-client-patents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_company: companyToRun,
          target_company: targetToRun,
          technology_area: techToRun,
          max_candidates: countToRun,
          use_llm: true,
        }),
      });
      const data: PipelineResponse = await res.json();
      setPipelineData(data);
      const now = new Date();
      setCompletedTimestamp(
        `${String(now.getUTCHours()).padStart(2, "0")}:${String(now.getUTCMinutes()).padStart(
          2,
          "0"
        )}:${String(now.getUTCSeconds()).padStart(2, "0")} UTC`
      );
      const firstMatchPatent = data.matching_analysis?.ranked_matches?.[0]?.patent_number;
      if (firstMatchPatent) {
        setSelectedPatentNumber(firstMatchPatent);
      } else if (data.patents && data.patents.length > 0) {
        setSelectedPatentNumber(data.patents[0].patent_number);
      } else {
        setSelectedPatentNumber(null);
      }
    } catch (e: any) {
      setPipelineData({
        pipeline_status: "PIPELINE_ERROR",
        client_company: companyToRun,
        target_company: targetToRun,
        technology_area: techToRun,
        error: e?.message || "Failed to execute ADK Client Patent & Target Matching Pipeline.",
        patents: [],
      });
    } finally {
      setLoading(false);
    }
  };

  const matchByPatentNumber = useMemo(() => {
    const map: Record<string, RankedPatentProductMatch> = {};
    for (const m of pipelineData?.matching_analysis?.ranked_matches || []) {
      map[m.patent_number] = m;
    }
    return map;
  }, [pipelineData]);

  const unifiedRows: UnifiedCandidateMatchRow[] = useMemo(() => {
    if (!pipelineData?.patents) return [];
    let rows: UnifiedCandidateMatchRow[] = pipelineData.patents.map((p) => ({
      patent: p,
      match: matchByPatentNumber[p.patent_number] || null,
    }));

    if (clusterFilter !== "ALL") {
      rows = rows.filter((r) => (r.patent.technology_areas || []).includes(clusterFilter));
    }

    if (priorityFilter !== "ALL") {
      rows = rows.filter((r) => r.match?.investigation_priority?.priority_tier === priorityFilter);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      rows = rows.filter(({ patent: p, match: m }) => {
        const patHit =
          p.patent_number.toLowerCase().includes(q) ||
          p.title.toLowerCase().includes(q) ||
          p.technical_summary.toLowerCase().includes(q) ||
          (p.cpc_codes || []).some((c) => c.toLowerCase().includes(q)) ||
          (p.key_concepts || []).some((k) => k.toLowerCase().includes(q)) ||
          (p.independent_claims || []).some((cl) => cl.toLowerCase().includes(q));
        const matchHit =
          m &&
          (m.target_product_or_service.toLowerCase().includes(q) ||
            m.target_technology.toLowerCase().includes(q) ||
            m.technical_overlap.summary.toLowerCase().includes(q) ||
            m.potential_monetary_opportunity.rationale.toLowerCase().includes(q));
        return Boolean(patHit || matchHit);
      });
    }

    rows.sort((a, b) => {
      if (sortBy === "priority_desc") {
        const pA = a.match?.investigation_priority?.priority_score ?? a.patent.investigation_relevance?.score ?? 0;
        const pB = b.match?.investigation_priority?.priority_score ?? b.patent.investigation_relevance?.score ?? 0;
        return pB - pA;
      }
      if (sortBy === "technical_desc") {
        const tA = a.match?.technical_overlap?.technical_relevance_score ?? a.patent.investigation_relevance?.score ?? 0;
        const tB = b.match?.technical_overlap?.technical_relevance_score ?? b.patent.investigation_relevance?.score ?? 0;
        return tB - tA;
      }
      if (sortBy === "commercial_desc") {
        const cA = a.match?.potential_monetary_opportunity?.commercial_opportunity_score ?? 0;
        const cB = b.match?.potential_monetary_opportunity?.commercial_opportunity_score ?? 0;
        return cB - cA;
      }
      if (sortBy === "relevance_desc") {
        return (b.patent.investigation_relevance?.score ?? 0) - (a.patent.investigation_relevance?.score ?? 0);
      }
      if (sortBy === "term_desc") {
        return (b.patent.estimated_remaining_term_years ?? -1) - (a.patent.estimated_remaining_term_years ?? -1);
      }
      if (sortBy === "filing_desc") {
        return (b.patent.filing_date || "").localeCompare(a.patent.filing_date || "");
      }
      return 0;
    });

    return rows;
  }, [pipelineData, matchByPatentNumber, clusterFilter, priorityFilter, searchQuery, sortBy]);

  const filteredPatents = useMemo(() => unifiedRows.map((r) => r.patent), [unifiedRows]);

  const selectedRow: UnifiedCandidateMatchRow | null = useMemo(() => {
    if (!unifiedRows.length) return null;
    return (
      unifiedRows.find((r) => r.patent.patent_number === selectedPatentNumber) || unifiedRows[0]
    );
  }, [unifiedRows, selectedPatentNumber]);

  const selectedPatent: PatentRecord | null = selectedRow?.patent || null;
  const selectedMatch: RankedPatentProductMatch | null = selectedRow?.match || null;

  const averageRemainingTerm = useMemo(() => {
    if (!pipelineData?.patents?.length) return null;
    const validTerms = pipelineData.patents
      .map((p) => p.estimated_remaining_term_years)
      .filter((t): t is number => t !== null && t !== undefined);
    if (!validTerms.length) return null;
    const sum = validTerms.reduce((acc, v) => acc + v, 0);
    return (sum / validTerms.length).toFixed(1);
  }, [pipelineData]);

  const highPriorityCount = useMemo(() => {
    if (pipelineData?.matching_analysis?.summary_metrics?.high_priority_count !== undefined) {
      return pipelineData.matching_analysis.summary_metrics.high_priority_count;
    }
    if (!pipelineData?.patents) return 0;
    return pipelineData.patents.filter((p) => (p.investigation_relevance?.score ?? 0) >= 80).length;
  }, [pipelineData]);

  const handleCopyTable = () => {
    if (!unifiedRows.length) return;
    const headers = [
      "Rank",
      "Patent Number",
      "Title & Technical Summary",
      "Technology Cluster",
      "Target Product / Technology",
      "Technical Overlap (Part 1)",
      "Supporting Target Evidence",
      "Patent Status",
      "Est. Remaining Term (Yrs)",
      "Potential Monetary Opportunity (Part 2)",
      "Investigation Priority (Part 3)",
    ];
    const rows = unifiedRows.map(({ patent: p, match: m }, i) => [
      i + 1,
      p.patent_number,
      `${p.title} — ${p.technical_summary}`,
      (p.technology_areas || []).join("; "),
      m ? `${m.target_product_or_service} (${m.target_technology})` : "Target Evidence Pending",
      m
        ? `${m.technical_overlap.overlap_level} (${m.technical_overlap.technical_relevance_score}/100): ${m.technical_overlap.summary}`
        : `Portfolio Relevance ${p.investigation_relevance?.score ?? 0}/100`,
      m
        ? (m.supporting_evidence || [])
            .map((e) => `${e.source_title} (${e.source_url})`)
            .join(" | ")
        : p.source,
      p.status,
      p.estimated_remaining_term_years === null ? "N/A" : p.estimated_remaining_term_years,
      m
        ? `${m.potential_monetary_opportunity.signal_tier} (${m.potential_monetary_opportunity.commercial_opportunity_score}/100)`
        : "N/A",
      m
        ? `${m.investigation_priority.priority_tier} (${m.investigation_priority.priority_score}/100)`
        : `${p.investigation_relevance?.score ?? 0}/100`,
    ]);
    const tsv = [headers.join("\t"), ...rows.map((r) => r.join("\t"))].join("\n");
    navigator.clipboard.writeText(tsv);
    setCopiedTable(true);
    setTimeout(() => setCopiedTable(false), 2000);
  };

  const handleExportCsv = () => {
    if (!unifiedRows.length) return;
    const escapeCsv = (val: any) => `"${String(val ?? "").replace(/"/g, '""')}"`;
    const headers = [
      "Rank",
      "Patent Number",
      "Title",
      "Technical Summary",
      "Technology Areas",
      "Key Concepts",
      "Target Product or Service",
      "Target Technology",
      "Technical Overlap Level",
      "Part 1 Technical Score",
      "Technical Overlap Summary",
      "Supporting Target Evidence",
      "Priority Date",
      "Filing Date",
      "Grant Date",
      "Patent Status",
      "Est Remaining Term Years",
      "Part 2 Commercial Opportunity Signal",
      "Part 2 Commercial Score",
      "Part 3 Investigation Priority Tier",
      "Part 3 Investigation Priority Score",
      "CPC Codes",
      "Portfolio Relevance Score",
    ];
    const rows = unifiedRows.map(({ patent: p, match: m }, idx) => [
      idx + 1,
      p.patent_number,
      p.title,
      p.technical_summary,
      (p.technology_areas || []).join(" | "),
      (p.key_concepts || []).join(" | "),
      m?.target_product_or_service || "",
      m?.target_technology || "",
      m?.technical_overlap?.overlap_level || "",
      m?.technical_overlap?.technical_relevance_score ?? "",
      m?.technical_overlap?.summary || "",
      (m?.supporting_evidence || [])
        .map((e) => `${e.source_title} [${e.source_url}]: ${e.text}`)
        .join(" || "),
      p.priority_date || "",
      p.filing_date || "",
      p.grant_date || "",
      p.status,
      p.estimated_remaining_term_years ?? "",
      m?.potential_monetary_opportunity?.signal_tier || "",
      m?.potential_monetary_opportunity?.commercial_opportunity_score ?? "",
      m?.investigation_priority?.priority_tier || "",
      m?.investigation_priority?.priority_score ?? "",
      (p.cpc_codes || []).join(" | "),
      p.investigation_relevance?.score ?? 0,
    ]);
    const csvContent = [
      headers.map(escapeCsv).join(","),
      ...rows.map((r) => r.map(escapeCsv).join(",")),
    ].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `patent_product_intelligence_${(pipelineData?.client_company || "client")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")}_vs_${(pipelineData?.target_company || "target")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportJson = () => {
    if (!pipelineData?.canonical_output) return;
    const blob = new Blob([JSON.stringify(pipelineData.canonical_output, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `client_patent_pipeline_${(pipelineData.client_company || "output")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleCopyJson = () => {
    if (!pipelineData?.canonical_output) return;
    navigator.clipboard.writeText(JSON.stringify(pipelineData.canonical_output, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-[#F4F6FA] text-[#0F172A] font-sans">
      {/* =====================================================================
          LEFT SIDEBAR — DOSSIER INITIATION PANEL (Matches Reference Image 1)
         ===================================================================== */}
      <aside className="w-full lg:w-[370px] xl:w-[390px] shrink-0 bg-white border-r border-slate-200 flex flex-col justify-between">
        <div>
          {/* Top Brand Header inside Sidebar */}
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold tracking-wider text-slate-600 uppercase">
                  PATENT–PRODUCT INTELLIGENCE
                </span>
                <span className="text-[10px] font-mono font-semibold text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded">
                  CORP-IP
                </span>
              </div>
              <div className="text-base font-bold text-slate-900 mt-0.5">New Analysis</div>
            </div>

            {/* Dark P-Search Brand Mark */}
            <div className="w-9 h-9 rounded-xl bg-[#0B0F19] flex items-center justify-center text-white shadow-xs shrink-0">
              <span className="font-mono font-bold text-base tracking-tighter text-white">P</span>
              <span className="w-2 h-2 rounded-full bg-sky-400 -ml-0.5 mt-2"></span>
            </div>
          </div>

          <div className="p-6 space-y-5">
            {/* Dossier Initiation Title Block */}
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs font-bold tracking-wide text-blue-600 uppercase">
                <Search className="w-3.5 h-3.5" />
                <span>DOSSIER INITIATION</span>
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                Patent–Product Intelligence
              </h1>
              <p className="text-xs text-slate-600 leading-relaxed">
                Identify patent–product relationships that deserve deeper investigation.
              </p>
            </div>

            {/* ANALYSIS PARAMETERS CARD */}
            <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-4 shadow-2xs">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold tracking-wider text-slate-700 uppercase">
                  ANALYSIS PARAMETERS
                </span>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setInputMode(inputMode === "form" ? "json" : "form")}
                    className="text-[10px] font-mono font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 px-2 py-0.5 rounded transition-colors"
                  >
                    {inputMode === "form" ? "USPTO / EPO / WIPO · JSON" : "Form View"}
                  </button>
                </div>
              </div>

              {inputMode === "form" ? (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    executePipeline();
                  }}
                  className="space-y-4"
                >
                  {/* Field 1: Client / Patent Owner */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <label htmlFor="client-owner" className="font-semibold text-slate-800">
                        Client / Patent Owner
                      </label>
                      <span className="text-[11px] text-red-600 font-medium">*Required</span>
                    </div>
                    <div className="relative">
                      <Building2 className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        id="client-owner"
                        type="text"
                        value={clientCompany}
                        onChange={(e) => setClientCompany(e.target.value)}
                        placeholder="e.g. Company name"
                        className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-slate-900 text-slate-900"
                      />
                    </div>
                    <p className="text-[11px] text-slate-500 leading-normal">
                      The company whose patent portfolio will be analyzed via Google Patents Public Dataset.
                    </p>
                  </div>

                  {/* Field 2: Target Company (Active for Target Retrieval Agent) */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <label htmlFor="target-company" className="font-semibold text-slate-800">
                        Target Company
                      </label>
                      <button
                        type="button"
                        onClick={() => setActiveView("target_agent")}
                        className="text-[11px] text-indigo-700 font-semibold hover:underline"
                      >
                        Open Target Agent →
                      </button>
                    </div>
                    <div className="relative">
                      <Target className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        id="target-company"
                        type="text"
                        value={targetCompanyPreview}
                        onChange={(e) => setTargetCompanyPreview(e.target.value)}
                        placeholder="e.g. Netflix"
                        className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-slate-200 rounded-lg text-slate-900 focus:outline-none focus:border-slate-900"
                      />
                    </div>
                    <p className="text-[11px] text-slate-500 leading-normal">
                      Queried exclusively from the pre-fetched Target Knowledge Database (zero web crawling).
                    </p>
                  </div>

                  {/* Field 3: Technology Area / Niche (Optional) */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <label htmlFor="tech-niche" className="font-semibold text-slate-800">
                        Technology Area / Niche (Optional)
                      </label>
                      <span className="text-[11px] text-slate-500">Optional</span>
                    </div>
                    <div className="relative">
                      <Network className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        id="tech-niche"
                        type="text"
                        value={technologyArea}
                        onChange={(e) => setTechnologyArea(e.target.value)}
                        placeholder="e.g. content recommendation, video streaming, video encoding"
                        className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-slate-900 text-slate-900"
                      />
                    </div>
                    <p className="text-[11px] text-slate-500 leading-normal">
                      Optionally narrow the analysis to a specific technology area (e.g.{" "}
                      <span className="font-mono text-slate-700">content recommendation</span>).
                    </p>
                  </div>

                  {/* Field 4: Number of Patents in Result */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <label htmlFor="max-candidates" className="font-semibold text-slate-800">
                        Number of Patents in Result
                      </label>
                      <span className="text-[11px] font-mono text-blue-700 font-semibold">
                        max_candidates: {maxCandidates} (1–100)
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="relative w-24 shrink-0">
                        <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                        <input
                          id="max-candidates"
                          type="number"
                          min={1}
                          max={100}
                          value={maxCandidatesInput}
                          onChange={(e) => {
                            const raw = e.target.value;
                            setMaxCandidatesInput(raw);
                            const val = parseInt(raw, 10);
                            if (!Number.isNaN(val)) {
                              const clamped = Math.max(1, Math.min(100, val));
                              setMaxCandidates(clamped);
                            }
                          }}
                          onBlur={() => {
                            const val = parseInt(maxCandidatesInput, 10);
                            const clamped = Number.isNaN(val) ? 10 : Math.max(1, Math.min(100, val));
                            setMaxCandidates(clamped);
                            setMaxCandidatesInput(String(clamped));
                          }}
                          className="w-full pl-8 pr-2 py-1.5 text-xs font-mono font-semibold bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-slate-900 text-slate-900"
                        />
                      </div>
                      <div className="flex items-center gap-1 flex-1">
                        {[6, 15, 25, 50, 100].map((num) => (
                          <button
                            key={num}
                            type="button"
                            onClick={() => {
                              setMaxCandidates(num);
                              setMaxCandidatesInput(String(num));
                            }}
                            className={`flex-1 py-1.5 rounded-lg text-[11px] font-mono font-semibold border transition-colors cursor-pointer ${
                              maxCandidates === num
                                ? "bg-slate-900 text-white border-slate-900"
                                : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                            }`}
                          >
                            {num}
                          </button>
                        ))}
                      </div>
                    </div>
                    <p className="text-[11px] text-slate-500 leading-normal">
                      Supports 1 to 100 patents. If the local mirror has fewer matches, BigQuery Vector Search (<span className="font-mono">text-embedding-004</span>) dynamically fetches &amp; embeds additional patents.
                    </p>
                  </div>

                  {/* BASELINE INGESTION RULES Box */}
                  <div className="bg-[#EFF6FF]/80 border border-blue-100 rounded-xl p-3.5 space-y-2">
                    <div className="flex items-center gap-1.5 text-[11px] font-bold tracking-wider text-slate-800 uppercase">
                      <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
                      <span>PIPELINE INGESTION & ADK RULES</span>
                    </div>
                    <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[11px] text-slate-700">
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-600 shrink-0"></span>
                        <span>3-Stage BigQuery Fetch</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-600 shrink-0"></span>
                        <span>Verbatim Claim Parsing</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-600 shrink-0"></span>
                        <span>Source vs AI Separation</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-600 shrink-0"></span>
                        <span>20-Yr Term Estimation</span>
                      </div>
                    </div>
                  </div>

                  {/* Primary Dark Action Button */}
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 px-4 bg-[#080C14] hover:bg-slate-800 disabled:opacity-50 text-white font-semibold text-xs rounded-xl shadow-xs flex items-center justify-center gap-2 transition-colors cursor-pointer"
                  >
                    <Search className="w-4 h-4" />
                    <span>
                      {loading
                        ? "Executing Google ADK Pipeline..."
                        : "Analyze Client Patent Portfolio"}
                    </span>
                  </button>
                </form>
              ) : (
                <div className="space-y-3">
                  <div className="text-[11px] text-slate-600">
                    Input JSON Contract (<span className="font-mono">client_company</span> +{" "}
                    <span className="font-mono">technology_area</span>):
                  </div>
                  <textarea
                    value={rawJsonInput}
                    onChange={(e) => setRawJsonInput(e.target.value)}
                    rows={6}
                    className="w-full font-mono text-xs p-3 bg-slate-950 text-slate-100 rounded-lg border border-slate-800 focus:outline-none"
                  />
                  {jsonError && <p className="text-xs text-red-600 font-medium">{jsonError}</p>}
                  <button
                    type="button"
                    onClick={() => executePipeline()}
                    disabled={loading}
                    className="w-full py-2.5 px-4 bg-[#080C14] hover:bg-slate-800 text-white font-semibold text-xs rounded-xl transition-colors"
                  >
                    {loading ? "Executing..." : "Run JSON Input via ADK"}
                  </button>
                </div>
              )}
            </div>

            {/* Non-Infringement Screening Notice */}
            <div className="flex items-start gap-2.5 text-[11px] text-slate-500 leading-relaxed px-1">
              <ShieldCheck className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
              <p>
                Uses publicly available patent records from{" "}
                <span className="font-mono text-slate-700">patents-public-data.patents.publications</span>.
                Results are intended for preliminary screening and investigation prioritization,{" "}
                <strong className="font-semibold text-slate-700">
                  not a legal infringement determination
                </strong>
                .
              </p>
            </div>
          </div>
        </div>

        {/* Bottom 3-Icon Navigation Bar inside Sidebar (Matches Reference Image 1) */}
        <div className="border-t border-slate-200 bg-white px-4 py-2.5 grid grid-cols-3 gap-1 text-center">
          <button
            type="button"
            onClick={() => setActiveView("dossier")}
            className={`flex flex-col items-center gap-1 py-1 rounded-lg text-[11px] font-medium transition-colors ${
              activeView === "dossier"
                ? "text-blue-600 font-semibold"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Dossier Matrix</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveView("target_prefetch")}
            className={`flex flex-col items-center gap-1 py-1 rounded-lg text-[11px] font-medium transition-colors ${
              activeView === "target_prefetch"
                ? "text-blue-600 font-semibold"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            <Database className="w-4 h-4" />
            <span>Target Prefetch DB</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveView("schema")}
            className={`flex flex-col items-center gap-1 py-1 rounded-lg text-[11px] font-medium transition-colors ${
              activeView === "schema" || activeView === "json"
                ? "text-blue-600 font-semibold"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            <Archive className="w-4 h-4" />
            <span>ADK & JSON</span>
          </button>
        </div>
      </aside>

      {/* =====================================================================
          RIGHT MAIN WORKSPACE — EXECUTIVE DOSSIER & ADK INSPECTOR (Matches Image 2)
         ===================================================================== */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Utility Header Bar */}
        <header className="bg-white border-b border-slate-200 px-6 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1 min-w-[260px]">
            <div className="inline-flex items-center gap-1.5 text-[11px] font-mono font-semibold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-md shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
              <span>BIGQUERY PATENTS + OFFLINE TARGET DB</span>
            </div>

            <div className="relative flex-1 max-w-md">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search patent claims, CPC classes, technical concepts..."
                className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:bg-white focus:border-slate-400"
              />
            </div>
          </div>

          {/* Right Navigation Tabs */}
          <div className="flex items-center gap-2 text-xs">
            <div className="hidden xl:flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
              <button
                type="button"
                onClick={() => setActiveView("dossier")}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  activeView === "dossier"
                    ? "bg-blue-700 text-white shadow-2xs"
                    : "text-slate-700 hover:text-slate-900"
                }`}
              >
                Candidate Matrix &amp; Target Matching
              </button>
              <button
                type="button"
                onClick={() => setActiveView("claims")}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  activeView === "claims"
                    ? "bg-white text-slate-900 shadow-2xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Claim Elements
              </button>
              <button
                type="button"
                onClick={() => setActiveView("clusters")}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  activeView === "clusters"
                    ? "bg-white text-slate-900 shadow-2xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Tech Clusters
              </button>
              <button
                type="button"
                onClick={() => setActiveView("target_agent")}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  activeView === "target_agent"
                    ? "bg-indigo-700 text-white shadow-2xs"
                    : "text-indigo-800 hover:bg-indigo-50"
                }`}
              >
                Target Retrieval Agent (ADK)
              </button>
              <button
                type="button"
                onClick={() => setActiveView("target_prefetch")}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  activeView === "target_prefetch"
                    ? "bg-emerald-700 text-white shadow-2xs"
                    : "text-emerald-800 hover:bg-emerald-50"
                }`}
              >
                Target Prefetch DB
              </button>
              <button
                type="button"
                onClick={() => setActiveView("schema")}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  activeView === "schema"
                    ? "bg-white text-slate-900 shadow-2xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                ADK &amp; Schema
              </button>
              <button
                type="button"
                onClick={() => setActiveView("json")}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  activeView === "json"
                    ? "bg-white text-slate-900 shadow-2xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Output JSON
              </button>
            </div>
          </div>
        </header>

        {/* Main Scrollable Content */}
        <main className="p-6 space-y-5 max-w-[1320px] w-full mx-auto">
          {activeView === "target_prefetch" ? (
            <TargetPrefetchView />
          ) : activeView === "target_agent" ? (
            <TargetAgentView
              targetCompanyDefault={
                targetCompanyPreview.includes("Netflix") ? "Netflix" : targetCompanyPreview
              }
              technologyAreaDefault={technologyArea}
              clientPatents={pipelineData?.patents || []}
            />
          ) : !pipelineData ? (
            <div className="space-y-5">
              {/* =================================================================
                  DEFAULT LANDING STATE: TECHNICAL SPECIFICATION & WORKFLOW BLUEPRINT
                  (Displayed before user presses "Analyze Client Patent Portfolio")
                 ================================================================= */}
              <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-5 shadow-2xs">
                <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <span className="inline-flex items-center gap-1.5 font-mono font-semibold text-slate-800 bg-slate-100 border border-slate-200 px-2.5 py-0.5 rounded">
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            loading ? "bg-blue-600 animate-ping" : "bg-amber-500"
                          }`}
                        ></span>
                        {loading
                          ? "EXECUTING ADK PIPELINE..."
                          : "STANDBY · AWAITING PORTFOLIO ANALYSIS"}
                      </span>
                      <span className="text-slate-400">·</span>
                      <span className="font-mono text-blue-700 bg-blue-50 px-2 py-0.5 rounded font-semibold">
                        SPEC-PPI-2026 · SYSTEM ARCHITECTURE & WORKFLOW SPECIFICATION
                      </span>
                    </div>

                    <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                      Patent–Product Intelligence Engine: Technical Workflow Specification
                    </h2>

                    <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
                      No portfolio analysis has been executed yet. Configure the{" "}
                      <strong className="font-semibold text-slate-900">Client / Patent Owner</strong>,{" "}
                      <strong className="font-semibold text-slate-900">Target Company</strong>, and optional{" "}
                      <strong className="font-semibold text-slate-900">Technology Area / Niche</strong> in the left
                      initiation panel and press{" "}
                      <span className="font-mono font-semibold text-slate-900 bg-slate-100 px-1.5 py-0.5 rounded">
                        Analyze Client Patent Portfolio
                      </span>{" "}
                      to execute the staged Google ADK pipeline and generate the analysis dossier.
                    </p>
                  </div>

                  <div className="shrink-0">
                    <button
                      type="button"
                      onClick={() => executePipeline()}
                      disabled={loading}
                      className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#080C14] hover:bg-slate-800 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-xs transition-colors cursor-pointer"
                    >
                      <Search className="w-3.5 h-3.5" />
                      <span>
                        {loading
                          ? "Executing ADK Pipeline..."
                          : `Analyze ${clientCompany || "Client"} Patent Portfolio`}
                      </span>
                    </button>
                  </div>
                </div>

                {/* 4 Architectural Invariants Strip */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-3 border-t border-slate-100">
                  <div className="border border-slate-200/90 rounded-lg p-3 bg-slate-50/50 space-y-1">
                    <div className="text-[10px] font-mono font-bold tracking-wider text-blue-700 uppercase">
                      INVARIANT 01 · STAGED RETRIEVAL
                    </div>
                    <div className="text-xs font-bold text-slate-900">
                      BigQuery 3-Stage Funnel
                    </div>
                    <p className="text-[11px] text-slate-600 leading-normal">
                      Never dumps entire portfolios into LLM context; resolves assignee, filters CPC/metadata, then fetches claims for top candidates.
                    </p>
                  </div>

                  <div className="border border-slate-200/90 rounded-lg p-3 bg-slate-50/50 space-y-1">
                    <div className="text-[10px] font-mono font-bold tracking-wider text-emerald-700 uppercase">
                      INVARIANT 02 · OFFLINE TARGET DB
                    </div>
                    <div className="text-xs font-bold text-slate-900">
                      AlloyDB ScaNN + Medium MCP
                    </div>
                    <p className="text-[11px] text-slate-600 leading-normal">
                      Pre-fetches configurable <span className="font-mono">PREFETCH_DOCUMENT_COUNT=10</span> Netflix Recommendation docs into AlloyDB with <span className="font-mono">text-embedding-004</span> (<span className="font-mono">vector(768)</span>) &amp; 180w/35w chunks; dynamically fetches &amp; embeds on cache miss.
                    </p>
                  </div>

                  <div className="border border-slate-200/90 rounded-lg p-3 bg-slate-50/50 space-y-1">
                    <div className="text-[10px] font-mono font-bold tracking-wider text-indigo-700 uppercase">
                      INVARIANT 03 · DUAL EVALUATION
                    </div>
                    <div className="text-xs font-bold text-slate-900">
                      Technical ≠ Commercial Score
                    </div>
                    <p className="text-[11px] text-slate-600 leading-normal">
                      Evaluates Claim-Element Technical Overlap and Public 10-K Commercial Opportunity as orthogonal dimensions.
                    </p>
                  </div>

                  <div className="border border-slate-200/90 rounded-lg p-3 bg-slate-50/50 space-y-1">
                    <div className="text-[10px] font-mono font-bold tracking-wider text-amber-800 uppercase">
                      INVARIANT 04 · LEGAL POSITIONING
                    </div>
                    <div className="text-xs font-bold text-slate-900">
                      Non-Infringement Guardrail
                    </div>
                    <p className="text-[11px] text-slate-600 leading-normal">
                      Preliminary technical screening only. Enforces strict evidence provenance and flags unconfirmed claim elements.
                    </p>
                  </div>
                </div>
              </section>

              {/* =================================================================
                  END-TO-END 3-PIPELINE ARCHITECTURAL WORKFLOW SPECIFICATION
                 ================================================================= */}
              <section className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                {/* PIPELINE 1: CLIENT PATENT PIPELINE */}
                <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs flex flex-col justify-between">
                  <div className="p-5 space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[11px] font-bold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded">
                        PIPELINE 01 · CLIENT PATENT INTELLIGENCE
                      </span>
                      <span className="font-mono text-[11px] text-slate-400">adk_pipeline/</span>
                    </div>

                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        Google Patents BigQuery & ADK Claim Analysis
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5 font-mono">
                        Source: patents-public-data.patents.publications
                      </p>
                    </div>

                    <div className="space-y-2.5 text-xs">
                      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-1">
                        <div className="font-mono font-bold text-slate-900">
                          Stage 1 · Assignee Disambiguation
                        </div>
                        <p className="text-[11px] text-slate-600 leading-relaxed">
                          Resolves <span className="font-mono">client_company</span> against{" "}
                          <span className="font-mono">assignee_harmonized.name</span> and raw aliases. Halts with candidate selector if multiple distinct corporate entities match.
                        </p>
                      </div>

                      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-1">
                        <div className="font-mono font-bold text-slate-900">
                          Stage 2 · Metadata & CPC Subgroup Filter
                        </div>
                        <p className="text-[11px] text-slate-600 leading-relaxed">
                          Screens active utility grants (<span className="font-mono">B2/B1</span>) and applications (<span className="font-mono">A1</span>) across title, abstract, and CPC classifications (<span className="font-mono">H04N21/</span>, <span className="font-mono">H04N19/</span>, <span className="font-mono">H04L65/</span>).
                        </p>
                      </div>

                      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-1">
                        <div className="font-mono font-bold text-slate-900">
                          Stage 3 · Claim Element Decomposition
                        </div>
                        <p className="text-[11px] text-slate-600 leading-relaxed">
                          Extracts verbatim independent claims, decomposes limitations into atomic elements (<span className="font-mono">1A, 1B, 1C, 1D</span>), separates <strong>Source Facts</strong> from <strong>AI Interpretation</strong>, and computes 20-year remaining term from <span className="font-mono">filing_date</span>.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="px-5 py-3 bg-slate-50 border-t border-slate-200 font-mono text-[11px] text-slate-600 flex items-center justify-between">
                    <span>ADK: root → retrieval → analysis → ranking</span>
                    <span className="text-blue-700 font-bold">STEP 1</span>
                  </div>
                </div>

                {/* PIPELINE 2: OFFLINE TARGET KNOWLEDGE & RETRIEVAL PIPELINE */}
                <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs flex flex-col justify-between">
                  <div className="p-5 space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[11px] font-bold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded">
                        PIPELINE 02 · TARGET KNOWLEDGE & ADK RETRIEVAL
                      </span>
                      <span className="font-mono text-[11px] text-slate-400">target_prefetch/</span>
                    </div>

                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        AlloyDB ScaNN Store & Medium MCP Server
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5 font-mono">
                        MCP: https://mcpmarket.com/server/medium-2
                      </p>
                    </div>

                    <div className="space-y-2.5 text-xs">
                      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-1">
                        <div className="font-mono font-bold text-slate-900">
                          1. Medium MCP Server (JSON-RPC 2.0)
                        </div>
                        <p className="text-[11px] text-slate-600 leading-relaxed">
                          Fetches <span className="font-mono">netflixtechblog.medium.com</span> and{" "}
                          <span className="font-mono">netflixtechblog.com</span> articles via MCP tools (<span className="font-mono">medium_get_article_content</span>) instead of raw URL scraping, preserving headings and <span className="font-mono">&lt;pre&gt;&lt;code&gt;</span> blocks.
                        </p>
                      </div>

                      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-1">
                        <div className="font-mono font-bold text-slate-900">
                          2. AlloyDB 2-Tier Parent-Child Schema
                        </div>
                        <p className="text-[11px] text-slate-600 leading-relaxed">
                          Stores <span className="font-mono">PREFETCH_DOCUMENT_COUNT=10</span> recommendation articles in <span className="font-mono">documents</span> and 180w/35w overlapping chunks in <span className="font-mono">document_chunks</span> with <span className="font-mono">text-embedding-004</span> (<span className="font-mono">vector(768)</span>) ScaNN embeddings.
                        </p>
                      </div>

                      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-1">
                        <div className="font-mono font-bold text-slate-900">
                          3. Dynamic Vector Search &amp; On-Demand Embedding
                        </div>
                        <p className="text-[11px] text-slate-600 leading-relaxed">
                          When mirror patents or prefetched AlloyDB docs have no match, dynamically queries BigQuery <span className="font-mono">VECTOR_SEARCH</span> and fetches/embeds Netflix docs with <span className="font-mono">text-embedding-004</span>.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="px-5 py-3 bg-slate-50 border-t border-slate-200 font-mono text-[11px] text-slate-600 flex items-center justify-between">
                    <span>ADK: root → target_retrieval → target_analysis</span>
                    <span className="text-emerald-700 font-bold">STEP 2</span>
                  </div>
                </div>

                {/* PIPELINE 3: PATENT-TARGET MATCHING & COMMERCIAL AGENT */}
                <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs flex flex-col justify-between">
                  <div className="p-5 space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[11px] font-bold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded">
                        PIPELINE 03 · MATCHING & COMMERCIAL AGENT
                      </span>
                      <span className="font-mono text-[11px] text-slate-400">matching_agent/</span>
                    </div>

                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        Evidence Alignment & Opportunity Prioritization
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5 font-mono">
                        Dual-Axis Technical + Commercial Screening
                      </p>
                    </div>

                    <div className="space-y-2.5 text-xs">
                      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-1">
                        <div className="font-mono font-bold text-slate-900">
                          Part 1 · Claim-Element Technical Alignment
                        </div>
                        <p className="text-[11px] text-slate-600 leading-relaxed">
                          Maps each independent claim element (<span className="font-mono">1A–1D</span>) against documented target capabilities and verbatim quotes, explicitly surfacing unconfirmed limitations (evidence gaps).
                        </p>
                      </div>

                      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-1">
                        <div className="font-mono font-bold text-slate-900">
                          Part 2 · Public Commercial Opportunity Signal
                        </div>
                        <p className="text-[11px] text-slate-600 leading-relaxed">
                          Combines SEC Form 10-K consolidated scale ($33.7B–$39.0B revenue, 260M–301M+ subscribers), subscription tier linkage, patent status, and remaining term without fabricating product revenue.
                        </p>
                      </div>

                      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-1">
                        <div className="font-mono font-bold text-slate-900">
                          Part 3 · Gatekeeper Investigation Priority
                        </div>
                        <p className="text-[11px] text-slate-600 leading-relaxed">
                          Produces the 9-column Ranked Patent–Product Intelligence Table with deterministic caps when technical overlap is low or a patent is expired.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="px-5 py-3 bg-slate-50 border-t border-slate-200 font-mono text-[11px] text-slate-600 flex items-center justify-between">
                    <span>ADK: technical → commercial → priority</span>
                    <span className="text-indigo-700 font-bold">STEP 3</span>
                  </div>
                </div>
              </section>

              {/* =================================================================
                  GOOGLE ADK MULTI-AGENT & DETERMINISTIC TOOL SPECIFICATION MATRIX
                 ================================================================= */}
              <section className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
                <div className="p-5 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">
                      Google ADK Multi-Agent & Deterministic Python Tool Specification
                    </h3>
                    <p className="text-xs text-slate-500">
                      Strict separation between deterministic Python data/math operations and Gemini LLM technical reasoning.
                    </p>
                  </div>
                  <span className="font-mono text-[11px] text-slate-600 bg-slate-100 px-2.5 py-1 rounded">
                    Orchestrator: Google ADK SequentialAgent
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-[#080C14] text-white font-mono text-[10px] uppercase">
                        <th className="py-3 px-4">PIPELINE STAGE & ADK AGENT</th>
                        <th className="py-3 px-4">DETERMINISTIC PYTHON TOOL(S)</th>
                        <th className="py-3 px-4">EXECUTION RESPONSIBILITY BOUNDARY</th>
                        <th className="py-3 px-4">OUTPUT ARTIFACT</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      <tr className="hover:bg-slate-50">
                        <td className="py-3 px-4 font-mono font-bold text-blue-700">
                          01. patent_retrieval_agent
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-800">
                          inspect_patents_schema_tool<br />
                          resolve_client_company_tool<br />
                          retrieve_staged_patents_tool
                        </td>
                        <td className="py-3 px-4 text-slate-600">
                          <strong>Deterministic Python:</strong> Queries <span className="font-mono">patents-public-data.patents.publications</span>, resolves harmonized assignees, filters by CPC/technology niche, and retrieves top candidate claims.
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-700">
                          Shortlisted BigQuery Patent Records
                        </td>
                      </tr>
                      <tr className="hover:bg-slate-50">
                        <td className="py-3 px-4 font-mono font-bold text-blue-700">
                          02. patent_analysis_agent
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-800">
                          analyze_patent_candidates_tool<br />
                          estimate_remaining_patent_life
                        </td>
                        <td className="py-3 px-4 text-slate-600">
                          <strong>Hybrid ADK + Python:</strong> Decomposes independent claims into atomic elements (<span className="font-mono">1A..1D</span>), extracts technical concepts, and deterministically computes 20-year remaining term from <span className="font-mono">filing_date</span>.
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-700">
                          Decomposed Claims & Source vs. AI Facts
                        </td>
                      </tr>
                      <tr className="hover:bg-slate-50">
                        <td className="py-3 px-4 font-mono font-bold text-blue-700">
                          03. patent_ranking_agent
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-800">
                          cluster_and_rank_patents_tool
                        </td>
                        <td className="py-3 px-4 text-slate-600">
                          <strong>Deterministic Python:</strong> Assigns hierarchical technology clusters (<span className="font-mono">Parent &gt; Sub-area</span>) and calculates the 100-point transparent relevance breakdown.
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-700">
                          Ranked Client Patent Dossier JSON
                        </td>
                      </tr>
                      <tr className="hover:bg-slate-50">
                        <td className="py-3 px-4 font-mono font-bold text-emerald-700">
                          04. target_retrieval_agent
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-800">
                          search_target_knowledge<br />
                          fetch_article_via_medium_mcp
                        </td>
                        <td className="py-3 px-4 text-slate-600">
                          <strong>Deterministic Python + AlloyDB:</strong> Queries pre-fetched AlloyDB <span className="font-mono">document_chunks</span> (<span className="font-mono">vector(32)</span> ScaNN + keyword + tag filters) populated via Medium MCP Server.
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-700">
                          Target Capabilities & Verbatim Quotes
                        </td>
                      </tr>
                      <tr className="hover:bg-slate-50">
                        <td className="py-3 px-4 font-mono font-bold text-indigo-700">
                          05. matching &amp; priority agents
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-800">
                          evaluate_claim_element_alignment_tool<br />
                          retrieve_commercial_intelligence_tool<br />
                          compute_investigation_priority_tool
                        </td>
                        <td className="py-3 px-4 text-slate-600">
                          <strong>Hybrid ADK + Python Gatekeeper:</strong> Aligns claim elements against target evidence, evaluates SEC 10-K commercial scale separately, and enforces non-infringement guardrails.
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-700">
                          9-Column Ranked Intelligence Table
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          ) : (
            <>
          {/* =================================================================
              EXECUTIVE DOSSIER HEADER CARD (Unified Portfolio + Target Matching)
             ================================================================= */}
          <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-5 shadow-2xs">
            <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2.5 text-xs">
                  <span className="inline-flex items-center gap-1.5 font-mono font-semibold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
                    PATENT–PRODUCT INTELLIGENCE DOSSIER #ADK-2026
                  </span>
                  <span className="text-slate-400">·</span>
                  <span className="font-mono text-slate-500">Completed {completedTimestamp}</span>
                </div>

                <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                  {pipelineData?.client_company || clientCompany} ↔{" "}
                  {pipelineData?.target_company ||
                    targetCompanyPreview.replace(/,\s*Inc\.?$/i, "").trim() ||
                    "Netflix"}
                  {pipelineData?.technology_area ? ` · ${pipelineData.technology_area}` : ""}
                </h2>

                <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
                  {pipelineData?.pipeline_status === "SUCCESS" ? (
                    <>
                      Unified Google ADK Candidate Matrix &amp; Patent–Target Matching analysis complete.{" "}
                      <strong className="font-semibold text-slate-900">
                        {pipelineData.patents.length} candidate patent publications
                      </strong>{" "}
                      retrieved from{" "}
                      <span className="font-mono">patents-public-data.patents.publications</span>{" "}
                      (out of{" "}
                      <strong className="font-semibold text-slate-900">
                        {pipelineData.staged_retrieval_metrics?.stage2_total_portfolio_records ??
                          pipelineData.patents.length}{" "}
                        screened utility filings
                      </strong>
                      ) and aligned against{" "}
                      <strong className="font-semibold text-slate-900">
                        {pipelineData?.target_company || "Netflix"}
                      </strong>{" "}
                      pre-fetched AlloyDB target capabilities and SEC Form 10-K disclosures.
                    </>
                  ) : (
                    <>
                      Deterministic Stage 1 / Stage 2 check halted pipeline execution with status{" "}
                      <span className="font-mono font-semibold text-amber-700">
                        {pipelineData?.pipeline_status || "PENDING"}
                      </span>
                      .
                    </>
                  )}
                </p>
              </div>

              {/* Action Buttons (Copy Table, Export CSV, Export Canonical JSON) */}
              <div className="flex flex-wrap items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={handleCopyTable}
                  disabled={!unifiedRows.length}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 transition-colors cursor-pointer"
                >
                  {copiedTable ? (
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                  ) : (
                    <Copy className="w-3.5 h-3.5 text-slate-500" />
                  )}
                  <span>{copiedTable ? "Copied Table" : "Copy Table"}</span>
                </button>

                <button
                  type="button"
                  onClick={handleExportCsv}
                  disabled={!unifiedRows.length}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 transition-colors cursor-pointer"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5 text-slate-500" />
                  <span>Export CSV</span>
                </button>

                <button
                  type="button"
                  onClick={handleExportJson}
                  disabled={!pipelineData?.canonical_output}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-[#0B0F19] rounded-lg hover:bg-slate-800 disabled:opacity-40 transition-colors cursor-pointer"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Export Canonical JSON</span>
                </button>
              </div>
            </div>

            {/* 4-Column Metadata Strip */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2 border-t border-slate-100">
              <div className="border border-slate-200/90 rounded-lg p-3 flex items-center gap-3 bg-slate-50/40">
                <Building2 className="w-4 h-4 text-blue-600 shrink-0" />
                <div className="min-w-0">
                  <div className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                    CLIENT ↔ TARGET ENTITIES
                  </div>
                  <div className="text-xs font-semibold text-slate-900 truncate font-mono">
                    {pipelineData?.resolved_assignee || pipelineData?.client_company || "Unresolved"} ↔{" "}
                    {pipelineData?.target_company || "Netflix"}
                  </div>
                </div>
              </div>

              <div className="border border-slate-200/90 rounded-lg p-3 flex items-center gap-3 bg-slate-50/40">
                <Network className="w-4 h-4 text-blue-600 shrink-0" />
                <div className="min-w-0">
                  <div className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                    TECHNICAL SECTOR / NICHE
                  </div>
                  <div className="text-xs font-semibold text-slate-900 truncate">
                    {pipelineData?.technology_area || "All Portfolio Technologies"}
                  </div>
                </div>
              </div>

              <div className="border border-slate-200/90 rounded-lg p-3 flex items-center gap-3 bg-slate-50/40">
                <Layers className="w-4 h-4 text-blue-600 shrink-0" />
                <div className="min-w-0">
                  <div className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                    ADK AGENT HIERARCHY
                  </div>
                  <div className="text-xs font-semibold text-slate-900 truncate font-mono">
                    retrieval → analysis → matching → priority
                  </div>
                </div>
              </div>

              <div className="border border-slate-200/90 rounded-lg p-3 flex items-center gap-3 bg-slate-50/40">
                <Database className="w-4 h-4 text-blue-600 shrink-0" />
                <div className="min-w-0">
                  <div className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                    EMBEDDING &amp; VECTOR ENGINE
                  </div>
                  <div className="text-xs font-semibold text-slate-900 truncate font-mono">
                    text-embedding-004 (768-d) · {pipelineData?.patents?.length || 0} Patents
                    {pipelineData?.staged_retrieval_metrics?.dynamic_bigquery_vector_search?.triggered
                      ? ` (+${pipelineData.staged_retrieval_metrics.dynamic_bigquery_vector_search.fetched_count} BQ Vector)`
                      : ""}
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* =================================================================
              ERROR / AMBIGUOUS COMPANY DISAMBIGUATION BANNER
             ================================================================= */}
          {!loading && pipelineData && pipelineData.pipeline_status !== "SUCCESS" && (
            <section className="bg-white border-2 border-amber-300 rounded-xl p-6 space-y-5">
              <div className="flex items-start gap-3.5">
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <div className="text-xs font-mono font-semibold text-amber-800">
                    DETERMINISTIC GUARDRAIL · {pipelineData.pipeline_status}
                  </div>
                  <h3 className="text-base font-bold text-slate-900">
                    {pipelineData.pipeline_status === "AMBIGUOUS_COMPANY" &&
                      `Ambiguous Company Name Resolution: "${pipelineData.client_company}"`}
                    {pipelineData.pipeline_status === "COMPANY_NOT_FOUND" &&
                      `Client Company Not Found in Dataset: "${pipelineData.client_company}"`}
                    {pipelineData.pipeline_status === "NO_PATENTS_FOUND" &&
                      `Zero Patents Matched Technology Area Filter: "${pipelineData.technology_area}"`}
                    {pipelineData.pipeline_status === "BIGQUERY_ERROR" &&
                      "BigQuery Retrieval Error"}
                    {(pipelineData.pipeline_status === "INVALID_INPUT" ||
                      pipelineData.pipeline_status === "PIPELINE_ERROR") &&
                      "Pipeline Execution Error"}
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {pipelineData.resolution?.message ||
                      pipelineData.resolution?.error ||
                      pipelineData.error ||
                      (pipelineData as any).stage2_retrieval?.message}
                  </p>
                </div>
              </div>

              {pipelineData.pipeline_status === "AMBIGUOUS_COMPANY" &&
                pipelineData.resolution?.candidates && (
                  <div className="space-y-3 pt-3 border-t border-slate-200">
                    <div className="text-xs font-semibold text-slate-800">
                      Candidate Harmonized Assignees Identified in{" "}
                      <span className="font-mono">patents-public-data.patents.publications</span>:
                    </div>
                    <div className="overflow-x-auto border border-slate-200 rounded-lg">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="bg-[#0B0F19] text-white font-mono text-[11px]">
                            <th className="py-2.5 px-4">HARMONIZED ASSIGNEE (assignee_harmonized.name)</th>
                            <th className="py-2.5 px-4">COUNTRY</th>
                            <th className="py-2.5 px-4">RAW ASSIGNEE ALIASES</th>
                            <th className="py-2.5 px-4 text-right">PUBLICATIONS</th>
                            <th className="py-2.5 px-4 text-right">SELECT ENTITY</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200">
                          {pipelineData.resolution.candidates.map((cand) => (
                            <tr key={cand.harmonized_name} className="hover:bg-slate-50">
                              <td className="py-3 px-4 font-mono font-bold text-blue-700">
                                {cand.harmonized_name}
                              </td>
                              <td className="py-3 px-4 font-mono text-slate-600">
                                {cand.country_code}
                              </td>
                              <td className="py-3 px-4 text-slate-600">
                                {(cand.raw_aliases || []).join(" · ")}
                              </td>
                              <td className="py-3 px-4 text-right font-mono font-semibold tabular-nums">
                                {cand.publication_count}
                              </td>
                              <td className="py-3 px-4 text-right">
                                <button
                                  type="button"
                                  onClick={() => {
                                    setClientCompany(cand.harmonized_name);
                                    executePipeline(cand.harmonized_name, technologyArea);
                                  }}
                                  className="px-3 py-1.5 bg-[#0B0F19] hover:bg-slate-800 text-white font-semibold rounded-md text-xs transition-colors cursor-pointer"
                                >
                                  Analyze Entity
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

              {pipelineData.pipeline_status === "COMPANY_NOT_FOUND" &&
                pipelineData.resolution?.available_assignees_in_dataset && (
                  <div className="space-y-2.5 pt-3 border-t border-slate-200">
                    <div className="text-xs font-semibold text-slate-800">
                      Select an available corporate assignee in the dataset:
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {pipelineData.resolution.available_assignees_in_dataset.map((item) => (
                        <button
                          key={item.harmonized_name}
                          type="button"
                          onClick={() => {
                            setClientCompany(item.harmonized_name);
                            executePipeline(item.harmonized_name, technologyArea);
                          }}
                          className="px-3 py-1.5 text-xs font-mono bg-slate-100 hover:bg-slate-200 text-slate-900 rounded-md transition-colors cursor-pointer"
                        >
                          {item.harmonized_name} ({item.publication_count} pubs)
                        </button>
                      ))}
                    </div>
                  </div>
                )}

              {pipelineData.pipeline_status === "NO_PATENTS_FOUND" && (
                <div className="pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setTechnologyArea("");
                      executePipeline(clientCompany, "");
                    }}
                    className="px-4 py-2 text-xs font-semibold text-white bg-[#0B0F19] rounded-lg hover:bg-slate-800 transition-colors"
                  >
                    Clear Technology Niche Filter & Analyze All Portfolio Filings
                  </button>
                </div>
              )}
            </section>
          )}

          {/* =================================================================
              4 KPI SUMMARY CARDS (Unified Portfolio + Part 1 Technical + Part 2 Commercial)
             ================================================================= */}
          {!loading && pipelineData && pipelineData.pipeline_status === "SUCCESS" && (
            <>
              <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* KPI 1: High-Priority Candidates */}
                <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
                  <div className="flex items-center justify-between text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                    <span>HIGH-PRIORITY CANDIDATES</span>
                    <ShieldCheck className="w-3.5 h-3.5 text-red-600" />
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold font-mono tabular-nums text-red-600">
                      {highPriorityCount}
                    </span>
                    <span className="text-xs text-slate-600">
                      of {pipelineData.patents.length} returned ({Math.max(pipelineData.patents.length, pipelineData.staged_retrieval_metrics?.stage2_total_portfolio_records ?? pipelineData.patents.length)} portfolio filings screened)
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Active granted + strong technical evidence + core target scale
                  </div>
                </div>

                {/* KPI 2: Part 1 Avg Technical Score */}
                <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
                  <div className="flex items-center justify-between text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                    <span>PART 1 · AVG TECHNICAL SCORE</span>
                    <Layers className="w-3.5 h-3.5 text-blue-600" />
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold font-mono tabular-nums text-blue-700">
                      {pipelineData.matching_analysis?.summary_metrics?.avg_technical_relevance_score ?? 0}
                    </span>
                    <span className="text-xs text-slate-500">/ 100 (Part 1 Separate)</span>
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Claim-element coverage + verbatim AlloyDB target evidence
                  </div>
                </div>

                {/* KPI 3: Part 2 Avg Commercial Score */}
                <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
                  <div className="flex items-center justify-between text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                    <span>PART 2 · AVG COMMERCIAL SCORE</span>
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold font-mono tabular-nums text-emerald-700">
                      {pipelineData.matching_analysis?.summary_metrics?.avg_commercial_opportunity_score ?? 0}
                    </span>
                    <span className="text-xs text-slate-500">/ 100 (Part 2 Separate)</span>
                  </div>
                  <div className="text-[11px] text-slate-500">
                    SEC 10-K infrastructure criticality + ~{averageRemainingTerm ?? "N/A"} yr avg patent life
                  </div>
                </div>

                {/* KPI 4: Revenue Non-Fabrication & Clusters */}
                <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
                  <div className="flex items-center justify-between text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                    <span>COMMERCIAL &amp; CLUSTER BASIS</span>
                    <Scale className="w-3.5 h-3.5 text-slate-600" />
                  </div>
                  <div className="text-sm font-bold text-slate-900 font-mono">
                    SEC Form 10-K · {pipelineData.technology_clusters?.length ?? 0} Clusters
                  </div>
                  <div className="text-[11px] text-slate-500 leading-snug">
                    Consolidated $33.7B–$39.0B reported; subsystem revenue explicitly marked undisclosed
                  </div>
                </div>
              </section>

              {/* ===============================================================
                  VIEW 1: UNIFIED CANDIDATE MATRIX & PATENT–TARGET MATCHING TABLE + ANALYSIS
                 =============================================================== */}
              {activeView === "dossier" && (
                <div className="space-y-5">
                  {/* Unified Candidate Matrix & 9-Column Patent-Target Matching Table Card */}
                  <section className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
                    {/* Table Control Header */}
                    <div className="px-5 py-4 border-b border-slate-200 flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2.5">
                          <h3 className="text-sm font-bold text-slate-900">
                            Unified Candidate Patent Matrix &amp; Patent–Target Matching Table
                          </h3>
                          <span className="text-[11px] font-mono font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                            {unifiedRows.length} Ranked Patent–Product Candidates
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500">
                          Combines BigQuery Patent Source Facts, Claim Decomposition &amp; Technology Clusters with Target Product Discovery, Part 1 Technical Overlap, Part 2 Monetary Opportunity &amp; Part 3 Investigation Priority.
                        </p>
                      </div>

                      <div className="flex flex-wrap items-center gap-2.5 text-xs">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] font-bold text-slate-400 uppercase">
                            CLUSTER:
                          </span>
                          <select
                            value={clusterFilter}
                            onChange={(e) => setClusterFilter(e.target.value)}
                            className="bg-white border border-slate-200 rounded-md px-2 py-1 text-xs font-medium text-slate-800 focus:outline-none"
                          >
                            <option value="ALL">All Clusters ({pipelineData.patents.length})</option>
                            {(pipelineData.technology_clusters || []).map((c) => (
                              <option key={c.cluster_name} value={c.cluster_name}>
                                {c.sub_area} ({c.patent_count})
                              </option>
                            ))}
                          </select>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] font-bold text-slate-400 uppercase">
                            PRIORITY:
                          </span>
                          <select
                            value={priorityFilter}
                            onChange={(e) => setPriorityFilter(e.target.value)}
                            className="bg-white border border-slate-200 rounded-md px-2 py-1 text-xs font-medium text-slate-800 focus:outline-none"
                          >
                            <option value="ALL">All Priorities</option>
                            <option value="High Priority">High Priority</option>
                            <option value="Medium Priority">Medium Priority</option>
                            <option value="Low Priority">Low Priority</option>
                            <option value="Low Priority (Expired Term)">
                              Low Priority (Expired Term)
                            </option>
                          </select>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] font-bold text-slate-400 uppercase">
                            SORT BY:
                          </span>
                          <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value as any)}
                            className="bg-white border border-slate-200 rounded-md px-2 py-1 text-xs font-semibold text-slate-900 focus:outline-none"
                          >
                            <option value="priority_desc">
                              Investigation Priority (High → Low)
                            </option>
                            <option value="technical_desc">
                              Part 1 Technical Overlap (High → Low)
                            </option>
                            <option value="commercial_desc">
                              Part 2 Commercial Opportunity (High → Low)
                            </option>
                            <option value="relevance_desc">
                              Portfolio Relevance (High → Low)
                            </option>
                            <option value="term_desc">
                              Estimated Remaining Term (High → Low)
                            </option>
                            <option value="filing_desc">Filing Date (Newest → Oldest)</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* Unified 9-Column Dark-Header Matrix Table */}
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="bg-[#080C14] text-white text-[10px] font-mono font-bold tracking-wider uppercase">
                            <th className="py-3.5 px-3.5 w-36">1. PATENT NO. &amp; DATES</th>
                            <th className="py-3.5 px-3.5 w-64">
                              2. PATENT TITLE, CLUSTER &amp; CLAIMS
                            </th>
                            <th className="py-3.5 px-3.5 w-48">3. TARGET PRODUCT / TECHNOLOGY</th>
                            <th className="py-3.5 px-3.5 w-60">4. TECHNICAL OVERLAP (PART 1)</th>
                            <th className="py-3.5 px-3.5 w-60">5. EVIDENCE SUPPORTING OVERLAP</th>
                            <th className="py-3.5 px-3.5 w-32">6. PATENT STATUS</th>
                            <th className="py-3.5 px-3.5 w-28">7. EST. LIFE</th>
                            <th className="py-3.5 px-3.5 w-52">
                              8. POTENTIAL MONETARY OPPORTUNITY (PART 2)
                            </th>
                            <th className="py-3.5 px-3.5 w-44">9. INVESTIGATION PRIORITY</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200 text-xs">
                          {unifiedRows.map(({ patent: pat, match: row }, idx) => {
                            const isSelected = selectedPatent?.patent_number === pat.patent_number;
                            const portfolioScore = pat.investigation_relevance?.score ?? 0;
                            const totalElements = (pat.claim_elements || []).reduce(
                              (acc, cg) => acc + (cg.elements?.length || 0),
                              0
                            );
                            const overlapLevel = row?.technical_overlap?.overlap_level || "Medium";
                            const techScore =
                              row?.technical_overlap?.technical_relevance_score ?? portfolioScore;
                            const priorityTier =
                              row?.investigation_priority?.priority_tier ||
                              (portfolioScore >= 80
                                ? "High Priority"
                                : portfolioScore >= 60
                                ? "Medium Priority"
                                : "Low Priority");
                            const priorityScore =
                              row?.investigation_priority?.priority_score ?? portfolioScore;
                            const yearsRem =
                              row?.estimated_remaining_patent_life?.years_remaining ??
                              pat.estimated_remaining_term_years;

                            return (
                              <tr
                                key={pat.patent_number}
                                onClick={() => setSelectedPatentNumber(pat.patent_number)}
                                className={`cursor-pointer transition-colors align-top ${
                                  isSelected
                                    ? "bg-blue-50/60 border-l-4 border-l-blue-600"
                                    : "hover:bg-slate-50/90"
                                }`}
                              >
                                {/* 1. Patent Number, Rank & Dates */}
                                <td className="py-4 px-3.5 font-mono">
                                  <div className="flex items-center gap-1.5">
                                    <span
                                      className={`inline-flex items-center justify-center w-5 h-5 rounded font-mono font-bold text-[10px] ${
                                        idx === 0
                                          ? "bg-red-50 text-red-700 border border-red-200"
                                          : "bg-slate-100 text-slate-700 border border-slate-200"
                                      }`}
                                    >
                                      #{idx + 1}
                                    </span>
                                    <span className="font-bold text-blue-700 text-xs">
                                      {pat.patent_number}
                                    </span>
                                  </div>
                                  <div className="text-[10px] text-slate-500 mt-1.5 tabular-nums">
                                    {pat.grant_date
                                      ? `Granted: ${pat.grant_date}`
                                      : "Application (Ungranted)"}
                                  </div>
                                  <div className="text-[10px] text-slate-400 tabular-nums">
                                    Filed: {pat.filing_date || "Missing"}
                                  </div>
                                  <div className="text-[10px] text-slate-500 mt-1">
                                    CPC: {(pat.cpc_codes || []).slice(0, 2).join(" · ") || "N/A"}
                                  </div>
                                </td>

                                {/* 2. Patent Title, Summary, Technology Cluster & Claims */}
                                <td className="py-4 px-3.5 space-y-1.5">
                                  <div className="font-bold text-slate-900 leading-snug">
                                    {pat.title}
                                  </div>
                                  <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed">
                                    {pat.technical_summary}
                                  </p>
                                  <div className="text-[11px] font-semibold text-slate-800 pt-0.5">
                                    {(pat.technology_areas || [])
                                      .map((a) => (a.includes(" > ") ? a.split(" > ")[1] : a))
                                      .join(" & ")}
                                  </div>
                                  <div className="text-[10px] text-slate-500">
                                    {(pat.key_concepts || []).slice(0, 3).join(" · ")}
                                  </div>
                                  <div className="pt-1 flex flex-wrap items-center gap-1.5 text-[10px] font-mono">
                                    {totalElements > 0 ? (
                                      <span className="text-emerald-800 font-semibold">
                                        ● {totalElements} Claim Elements (Verbatim)
                                      </span>
                                    ) : (
                                      <span className="text-amber-800">
                                        ○ Missing Claims in Snapshot
                                      </span>
                                    )}
                                  </div>
                                </td>

                                {/* 3. Target Product or Technology */}
                                <td className="py-4 px-3.5">
                                  {row ? (
                                    <>
                                      <div className="font-bold text-slate-900 leading-snug">
                                        {row.target_product_or_service}
                                      </div>
                                      <div className="text-[11px] font-medium text-indigo-700 mt-1">
                                        {row.target_technology}
                                      </div>
                                      <div className="text-[10px] text-slate-500 mt-1 font-mono">
                                        Target: {row.target_company}
                                      </div>
                                    </>
                                  ) : (
                                    <div className="text-[11px] text-slate-500">
                                      No target product match in pre-fetched DB
                                    </div>
                                  )}
                                </td>

                                {/* 4. Technical Overlap (Part 1) */}
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
                                      {techScore}/100
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
                                      style={{ width: `${Math.min(100, techScore)}%` }}
                                    />
                                  </div>
                                  <p className="text-[11px] text-slate-600 line-clamp-3 leading-relaxed">
                                    {row?.technical_overlap?.summary || pat.technical_summary}
                                  </p>
                                  {row && (
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
                                          Missing source claims (concept match)
                                        </span>
                                      )}
                                    </div>
                                  )}
                                </td>

                                {/* 5. Evidence Supporting Overlap */}
                                <td className="py-4 px-3.5">
                                  <div className="space-y-2">
                                    {(row?.supporting_evidence || []).slice(0, 2).map((ev, i) => (
                                      <div
                                        key={i}
                                        className="text-[11px] bg-slate-50 border border-slate-200/80 rounded p-2 space-y-1"
                                      >
                                        <div className="font-semibold text-slate-800 line-clamp-1">
                                          {ev.source_title}
                                        </div>
                                        <p className="text-[10px] text-slate-600 line-clamp-2 italic">
                                          &ldquo;{ev.text}&rdquo;
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
                                    {(!row?.supporting_evidence ||
                                      row.supporting_evidence.length === 0) && (
                                      <div className="text-[11px] text-slate-400">
                                        Source: {pat.source}
                                      </div>
                                    )}
                                  </div>
                                </td>

                                {/* 6. Patent Status */}
                                <td className="py-4 px-3.5">
                                  <div
                                    className={`text-[11px] font-semibold leading-snug ${
                                      pat.status.toLowerCase().includes("expired")
                                        ? "text-red-700"
                                        : pat.status.toLowerCase().includes("application")
                                        ? "text-amber-700"
                                        : "text-emerald-700"
                                    }`}
                                  >
                                    {pat.status}
                                  </div>
                                </td>

                                {/* 7. Estimated Remaining Patent Life */}
                                <td className="py-4 px-3.5 font-mono tabular-nums">
                                  {yearsRem === null || yearsRem === undefined ? (
                                    <div>
                                      <div className="font-bold text-amber-700">Unknown</div>
                                      <div className="text-[10px] text-slate-400">No filing_date</div>
                                    </div>
                                  ) : yearsRem <= 0 ? (
                                    <div>
                                      <div className="font-bold text-red-600">0.0 yrs</div>
                                      <div className="text-[10px] text-slate-400">20-yr elapsed</div>
                                    </div>
                                  ) : (
                                    <div>
                                      <div className="text-sm font-bold text-slate-900">
                                        ~{Number(yearsRem).toFixed(1)} yrs
                                      </div>
                                      <div className="text-[10px] text-slate-500 mt-0.5">
                                        Exp:{" "}
                                        {pat.patent_life?.estimated_expiration_date_nominal?.slice(
                                          0,
                                          7
                                        ) || "20-yr term"}
                                      </div>
                                    </div>
                                  )}
                                </td>

                                {/* 8. Potential Monetary Opportunity (Part 2) */}
                                <td className="py-4 px-3.5">
                                  {row ? (
                                    <>
                                      <div className="flex items-center justify-between gap-2 mb-1">
                                        <span className="text-[11px] font-bold text-emerald-800 line-clamp-1">
                                          {row.potential_monetary_opportunity.signal_tier
                                            .split("(")[0]
                                            .trim()}
                                        </span>
                                        <span className="font-mono font-bold text-xs tabular-nums text-emerald-700 shrink-0">
                                          {
                                            row.potential_monetary_opportunity
                                              .commercial_opportunity_score
                                          }
                                          /100
                                        </span>
                                      </div>
                                      <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden mb-1.5">
                                        <div
                                          className="h-full bg-emerald-600"
                                          style={{
                                            width: `${Math.min(
                                              100,
                                              row.potential_monetary_opportunity
                                                .commercial_opportunity_score
                                            )}%`,
                                          }}
                                        />
                                      </div>
                                      <div className="text-[10px] text-slate-600 leading-snug line-clamp-2">
                                        {row.potential_monetary_opportunity.strategic_role}
                                      </div>
                                      <div className="text-[10px] font-mono text-slate-500 mt-1">
                                        10-K: $33.7B–$39.0B (Subsystem rev. undisclosed)
                                      </div>
                                    </>
                                  ) : (
                                    <div className="text-[11px] text-slate-400">N/A</div>
                                  )}
                                </td>

                                {/* 9. Investigation Priority (Part 3 + Portfolio Relevance) */}
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
                                    Priority: {priorityScore}/100
                                  </div>
                                  <div className="font-mono text-[10px] text-slate-500 tabular-nums">
                                    Portfolio Relevance: {portfolioScore}/100
                                  </div>
                                  {row?.investigation_priority?.rationale && (
                                    <p className="text-[10px] text-slate-600 mt-1 line-clamp-2 leading-relaxed">
                                      {row.investigation_priority.rationale}
                                    </p>
                                  )}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>

                    {/* Bottom Matrix Status Strip */}
                    <div className="px-5 py-3 bg-slate-50 border-t border-slate-200 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-600">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                        <span>
                          {highPriorityCount} High-Priority Patent–Product Relationships Ranked
                        </span>
                        <span className="text-slate-300">·</span>
                        <span>
                          Sources: Google Patents Public Dataset + Pre-Fetched AlloyDB Target Store
                        </span>
                      </div>
                      <div className="font-mono text-[11px] text-slate-500">
                        Click any row above to inspect unified Claim Alignment, Target Evidence, 10-K Commercial Signal &amp; Source Facts below
                      </div>
                    </div>
                  </section>

                  {/* =============================================================
                      UNIFIED SELECTED CANDIDATE & PATENT–TARGET MATCHING ANALYSIS
                     ============================================================= */}
                  {selectedPatent && (
                    <section className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
                      <div className="px-6 py-4 bg-[#0B0F19] text-white flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                        <div className="flex flex-wrap items-center gap-2.5">
                          <span className="font-mono text-xs font-bold text-sky-400">
                            UNIFIED CANDIDATE &amp; TARGET MATCHING ANALYSIS
                          </span>
                          <span className="text-slate-500">·</span>
                          <span className="font-mono text-sm font-bold">
                            {selectedPatent.patent_number}
                          </span>
                          {selectedMatch && (
                            <>
                              <span className="text-sky-400 font-mono text-xs">↔</span>
                              <span className="font-semibold text-xs text-emerald-300">
                                {selectedMatch.target_product_or_service}
                              </span>
                            </>
                          )}
                          <span className="text-slate-500">·</span>
                          <span className="text-xs text-slate-300 truncate max-w-xl">
                            {selectedPatent.title}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-[11px] font-mono text-slate-300 shrink-0">
                          {selectedMatch && (
                            <>
                              <span>
                                Part 1 Tech:{" "}
                                <strong className="text-sky-300">
                                  {selectedMatch.technical_overlap.technical_relevance_score}/100
                                </strong>
                              </span>
                              <span>·</span>
                              <span>
                                Part 2 Comm:{" "}
                                <strong className="text-emerald-300">
                                  {
                                    selectedMatch.potential_monetary_opportunity
                                      .commercial_opportunity_score
                                  }
                                  /100
                                </strong>
                              </span>
                              <span>·</span>
                            </>
                          )}
                          <span>
                            Priority:{" "}
                            <strong className="text-white">
                              {selectedMatch?.investigation_priority?.priority_tier ||
                                `${selectedPatent.investigation_relevance?.score ?? 0}/100`}
                            </strong>
                          </span>
                        </div>
                      </div>

                      <div className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
                        {/* =========================================================
                            LEFT 7 COLS: PART 1 TECHNICAL MATCHING & CLAIM DECOMPOSITION
                           ========================================================= */}
                        <div className="lg:col-span-7 space-y-5">
                          {/* Part 1 Technical Overlap & Factor Breakdown */}
                          {selectedMatch && (
                            <div className="border border-slate-200 rounded-lg p-4 space-y-4">
                              <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-3">
                                <div>
                                  <div className="text-[11px] font-mono font-bold text-blue-700 uppercase">
                                    PART 1 — TECHNICAL MATCHING ANALYSIS (technical_matching_agent)
                                  </div>
                                  <h4 className="text-base font-bold text-slate-900 mt-0.5">
                                    {selectedPatent.patent_number} ↔{" "}
                                    {selectedMatch.target_product_or_service}
                                  </h4>
                                  <div className="text-xs text-indigo-700 font-medium">
                                    Target Technology: {selectedMatch.target_technology}
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
                                    {selectedMatch.technical_overlap.overlap_level} Overlap
                                  </div>
                                </div>
                              </div>

                              <div className="bg-blue-50/50 border border-blue-200/80 rounded-lg p-3.5 space-y-1.5">
                                <div className="text-[11px] font-mono font-bold text-blue-900 uppercase">
                                  Evidence-Backed Technical Overlap Explanation (Screening Assessment)
                                </div>
                                <p className="text-xs text-slate-800 leading-relaxed">
                                  {selectedMatch.technical_overlap.summary}
                                </p>
                                {selectedMatch.technical_overlap.shared_technical_mechanisms.length >
                                  0 && (
                                  <div className="text-[11px] font-mono text-blue-800 pt-1">
                                    Shared Mechanisms:{" "}
                                    {selectedMatch.technical_overlap.shared_technical_mechanisms.join(
                                      " · "
                                    )}
                                  </div>
                                )}
                              </div>

                              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                                {Object.entries(
                                  selectedMatch.technical_overlap.factor_breakdown || {}
                                ).map(([key, fac]) => (
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
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Unified Step 3 Claim Element Decomposition & Target Capability Mapping */}
                          <div className="border border-slate-200 rounded-lg p-4 space-y-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                                  Step 3 &amp; Part 1 · Independent Claim Element Decomposition ↔ Target Capability Mapping
                                </span>
                                <p className="text-[11px] text-slate-500">
                                  Decomposed patent claim limitations aligned against documented target-company capabilities (no legal infringement conclusions).
                                </p>
                              </div>
                              {selectedMatch && (
                                <span className="text-[11px] font-mono text-slate-600 shrink-0">
                                  {
                                    selectedMatch.technical_overlap.claim_element_counts
                                      .evidence_identified
                                  }{" "}
                                  Confirmed ·{" "}
                                  {
                                    selectedMatch.technical_overlap.claim_element_counts
                                      .partial_alignment
                                  }{" "}
                                  Partial ·{" "}
                                  {
                                    selectedMatch.technical_overlap.claim_element_counts
                                      .not_documented
                                  }{" "}
                                  Unconfirmed
                                </span>
                              )}
                            </div>

                            {selectedPatent.missing_claims_warning ? (
                              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900">
                                <strong>Missing Claims Handled Without Fabrication:</strong>{" "}
                                {selectedPatent.missing_claims_warning}
                              </div>
                            ) : selectedMatch &&
                              selectedMatch.technical_overlap.claim_element_mapping.length > 0 ? (
                              <div className="border border-slate-200 rounded-lg overflow-hidden">
                                <table className="w-full text-left border-collapse text-xs">
                                  <thead>
                                    <tr className="bg-slate-100 text-slate-700 font-mono text-[10px] uppercase">
                                      <th className="py-2 px-3 w-16">ELEM</th>
                                      <th className="py-2 px-3">
                                        DECOMPOSED CLAIM LIMITATION (SOURCE + AI)
                                      </th>
                                      <th className="py-2 px-3 w-44">TARGET EVIDENCE STATUS</th>
                                      <th className="py-2 px-3">
                                        DOCUMENTED TARGET CAPABILITY &amp; SOURCE
                                      </th>
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-slate-200">
                                    {selectedMatch.technical_overlap.claim_element_mapping.map(
                                      (em) => (
                                        <tr key={em.element_id} className="align-top hover:bg-slate-50">
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
                                            <p className="leading-relaxed">
                                              {em.alignment_rationale}
                                            </p>
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
                                      )
                                    )}
                                  </tbody>
                                </table>
                              </div>
                            ) : (
                              (selectedPatent.claim_elements || []).map((claimGroup) => (
                                <div key={claimGroup.claim_number} className="space-y-2">
                                  <div className="text-xs font-mono font-bold text-slate-800">
                                    Independent Claim {claimGroup.claim_number} — Decomposed Technical Elements
                                  </div>
                                  <div className="border border-slate-200 rounded-lg overflow-hidden">
                                    <table className="w-full text-left border-collapse text-xs">
                                      <thead>
                                        <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-mono text-[11px]">
                                          <th className="py-2 px-3 w-20">ID</th>
                                          <th className="py-2 px-3 w-48">TECHNICAL CONCEPT</th>
                                          <th className="py-2 px-3">ELEMENT DESCRIPTION</th>
                                        </tr>
                                      </thead>
                                      <tbody className="divide-y divide-slate-200">
                                        {claimGroup.elements.map((el) => (
                                          <tr key={el.element_id} className="hover:bg-slate-50">
                                            <td className="py-2.5 px-3 align-top font-mono font-bold text-blue-700">
                                              {el.element_id}
                                            </td>
                                            <td className="py-2.5 px-3 align-top font-semibold text-slate-900">
                                              {el.technical_concept}
                                            </td>
                                            <td className="py-2.5 px-3 align-top text-slate-600 leading-relaxed">
                                              {el.description}
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              ))
                            )}

                            {/* Verbatim Independent Claim Source Fact */}
                            {(selectedPatent.independent_claims || []).length > 0 && (
                              <div className="space-y-2 pt-2">
                                <div className="flex items-center justify-between text-xs">
                                  <span className="font-semibold text-slate-800">
                                    Verbatim Independent Claim Text (claims_localized)
                                  </span>
                                  <span className="font-mono text-[10px] text-slate-500">
                                    SOURCE FACT
                                  </span>
                                </div>
                                {(selectedPatent.independent_claims || []).map((clText, i) => (
                                  <pre
                                    key={i}
                                    className="text-xs font-mono text-slate-700 whitespace-pre-wrap leading-relaxed bg-slate-50 p-3.5 rounded-lg border border-slate-200"
                                  >
                                    {clText}
                                  </pre>
                                ))}
                              </div>
                            )}
                          </div>

                          {/* Verbatim Supporting Target Evidence Chunks & Evidence Gaps */}
                          {selectedMatch && (
                            <div className="border border-slate-200 rounded-lg p-4 space-y-4">
                              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                                Verbatim Supporting Target Evidence (Pre-Fetched AlloyDB Target Store)
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
                                      &ldquo;{ev.text}&rdquo;
                                    </p>
                                    <a
                                      href={ev.source_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center gap-1 font-mono text-[11px] text-blue-600 hover:underline"
                                    >
                                      <span>{ev.source_url}</span>
                                      <ExternalLink className="w-3 h-3" />
                                    </a>
                                  </div>
                                ))}
                              </div>

                              <div className="border border-amber-200 bg-amber-50/40 rounded-lg p-3.5 space-y-1.5">
                                <div className="text-[11px] font-mono font-bold text-amber-900 uppercase">
                                  Evidence Gaps &amp; Unconfirmed Parameters (Requires Expert / Legal Review)
                                </div>
                                <ul className="list-disc list-inside space-y-1 text-xs text-slate-700 leading-relaxed">
                                  {selectedMatch.technical_overlap.evidence_gaps.map((gap, i) => (
                                    <li key={i}>{gap}</li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* =========================================================
                            RIGHT 5 COLS: PART 2 COMMERCIAL + PART 3 PRIORITY + SOURCE FACTS
                           ========================================================= */}
                        <div className="lg:col-span-5 space-y-5">
                          {/* Part 2: Commercial Opportunity & SEC Form 10-K Evidence */}
                          {selectedMatch && (
                            <div className="border border-slate-200 rounded-lg p-4 space-y-4">
                              <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-3">
                                <div>
                                  <div className="text-[11px] font-mono font-bold text-emerald-700 uppercase">
                                    PART 2 — COMMERCIAL OPPORTUNITY (commercial_opportunity_agent)
                                  </div>
                                  <h4 className="text-sm font-bold text-slate-900 mt-0.5">
                                    Commercial Significance &amp; Patent Viability
                                  </h4>
                                </div>
                                <div className="text-right shrink-0">
                                  <div className="text-[10px] font-mono uppercase text-slate-400">
                                    PART 2 SCORE
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

                              <div className="bg-emerald-50/60 border border-emerald-200 rounded-lg p-3.5 space-y-1.5">
                                <div className="text-xs font-bold text-emerald-950">
                                  Signal: {selectedMatch.potential_monetary_opportunity.signal_tier}
                                </div>
                                <p className="text-xs text-slate-800 leading-relaxed">
                                  {selectedMatch.potential_monetary_opportunity.rationale}
                                </p>
                              </div>

                              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
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

                              <div className="border border-slate-200 rounded-lg divide-y divide-slate-200 text-xs">
                                <div className="p-2.5 flex flex-col gap-0.5">
                                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                                    CONSOLIDATED COMPANY REVENUE (SEC FORM 10-K)
                                  </span>
                                  <span className="font-semibold text-slate-900">
                                    {selectedMatch.potential_monetary_opportunity
                                      .consolidated_company_revenue || "Not publicly disclosed"}
                                  </span>
                                </div>
                                <div className="p-2.5 flex flex-col gap-0.5 bg-amber-50/40">
                                  <span className="text-[10px] font-mono font-bold text-amber-800 uppercase">
                                    PRODUCT-LEVEL REVENUE GUARDRAIL (NON-FABRICATION)
                                  </span>
                                  <span className="text-slate-800 leading-relaxed">
                                    {
                                      selectedMatch.potential_monetary_opportunity
                                        .product_level_revenue_note
                                    }
                                  </span>
                                </div>
                                <div className="p-2.5 flex flex-col gap-0.5">
                                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                                    STRATEGIC ROLE &amp; ADOPTION SCALE
                                  </span>
                                  <span className="font-semibold text-slate-900">
                                    {selectedMatch.potential_monetary_opportunity.strategic_role}
                                  </span>
                                  <span className="text-slate-600 text-[11px]">
                                    {
                                      selectedMatch.potential_monetary_opportunity
                                        .subscriber_or_adoption_scale
                                    }
                                  </span>
                                </div>
                                <div className="p-2.5 flex flex-col gap-0.5">
                                  <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                                    SUBSCRIPTION PRICING TIER LINKAGE
                                  </span>
                                  <span className="text-slate-800">
                                    {
                                      selectedMatch.potential_monetary_opportunity
                                        .pricing_tiers_disclosed
                                    }
                                  </span>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Part 3: Investigation Prioritization */}
                          {selectedMatch && (
                            <div className="border border-slate-200 rounded-lg p-4 space-y-2.5">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                                  Part 3 · {selectedMatch.investigation_priority.priority_tier} (
                                  {selectedMatch.investigation_priority.priority_score}/100)
                                </span>
                                <span className="text-[10px] font-mono font-semibold text-indigo-800 bg-indigo-50 px-2 py-0.5 rounded">
                                  GATEKEEPER VERIFIED
                                </span>
                              </div>
                              <p className="text-xs text-slate-700 leading-relaxed">
                                {selectedMatch.investigation_priority.rationale}
                              </p>
                            </div>
                          )}

                          {/* Box 1: Verbatim BigQuery Source Facts */}
                          <div className="border border-slate-200 rounded-lg p-4 space-y-3">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                                Patent Source Facts (BigQuery Dataset)
                              </span>
                              <span className="text-[10px] font-mono font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                                SOURCE FACT
                              </span>
                            </div>

                            <div className="grid grid-cols-3 gap-2 text-xs font-mono bg-slate-50 p-2.5 rounded border border-slate-200/70">
                              <div>
                                <div className="text-[10px] text-slate-400">PRIORITY DATE</div>
                                <div className="font-semibold text-slate-900">
                                  {selectedPatent.priority_date || "Missing"}
                                </div>
                              </div>
                              <div>
                                <div className="text-[10px] text-slate-400">FILING DATE</div>
                                <div className="font-semibold text-slate-900">
                                  {selectedPatent.filing_date || "Missing"}
                                </div>
                              </div>
                              <div>
                                <div className="text-[10px] text-slate-400">GRANT DATE</div>
                                <div className="font-semibold text-slate-900">
                                  {selectedPatent.grant_date || "Ungranted"}
                                </div>
                              </div>
                            </div>

                            <div className="text-xs space-y-1 text-slate-600">
                              <div>
                                <strong className="text-slate-800">Harmonized Assignee:</strong>{" "}
                                <span className="font-mono">
                                  {(selectedPatent.assignee_harmonized || []).join(", ")}
                                </span>
                              </div>
                              <div>
                                <strong className="text-slate-800">Inventors:</strong>{" "}
                                {(selectedPatent.inventors || []).join(", ") || "N/A"}
                              </div>
                              <div>
                                <strong className="text-slate-800">CPC Codes:</strong>{" "}
                                <span className="font-mono">
                                  {(selectedPatent.cpc_codes || []).join(", ")}
                                </span>
                              </div>
                              <div>
                                <strong className="text-slate-800">Status Basis:</strong>{" "}
                                {selectedPatent.status}
                              </div>
                            </div>

                            {selectedPatent.abstract_source_fact && (
                              <div className="pt-2 border-t border-slate-100 space-y-1">
                                <div className="text-[11px] font-semibold text-slate-700">
                                  Verbatim Abstract (abstract_localized):
                                </div>
                                <p className="text-xs text-slate-600 leading-relaxed">
                                  {selectedPatent.abstract_source_fact}
                                </p>
                              </div>
                            )}
                          </div>

                          {/* Box 2: Step 5 — Estimated Patent Life & Step 6 Portfolio Relevance */}
                          <div className="border border-slate-200 rounded-lg p-4 space-y-2.5">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                                Step 5 &amp; 6 · Patent Term &amp; Portfolio Relevance (
                                {selectedPatent.investigation_relevance?.score}/100)
                              </span>
                              <span className="text-[10px] font-mono font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded">
                                DETERMINISTIC PYTHON
                              </span>
                            </div>
                            <div className="text-xs text-slate-700">
                              <strong>Estimated Remaining Term:</strong>{" "}
                              <span className="font-mono font-bold text-slate-900">
                                {selectedPatent.estimated_remaining_term_years === null
                                  ? "null (Insufficient Dates)"
                                  : `${selectedPatent.estimated_remaining_term_years} years`}
                              </span>
                            </div>
                            {selectedPatent.patent_life && (
                              <>
                                <p className="text-xs text-slate-600 leading-relaxed">
                                  {selectedPatent.patent_life.calculation_basis}
                                </p>
                                <p className="text-[11px] text-amber-800 bg-amber-50/80 border border-amber-200/80 p-2 rounded font-medium">
                                  {selectedPatent.patent_life.caveat}
                                </p>
                              </>
                            )}
                            <ul className="space-y-1 text-xs text-slate-600 list-disc pl-4 pt-1">
                              {(selectedPatent.investigation_relevance?.reasons || []).map(
                                (reason, idx) => (
                                  <li key={idx} className="leading-relaxed">
                                    {reason}
                                  </li>
                                )
                              )}
                            </ul>
                          </div>
                        </div>
                      </div>
                    </section>
                  )}
                </div>
              )}

              {/* ===============================================================
                  VIEW 2: ALL CLAIM ELEMENT DECOMPOSITIONS (STEP 3)
                 =============================================================== */}
              {activeView === "claims" && (
                <section className="bg-white border border-slate-200 rounded-xl divide-y divide-slate-200 shadow-2xs">
                  <div className="p-5 flex items-center justify-between">
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        Step 3 · Portfolio-Wide Claim Element Decomposition
                      </h3>
                      <p className="text-xs text-slate-500">
                        All shortlisted candidate patents decomposed into structured technical elements ready for target-company comparison.
                      </p>
                    </div>
                  </div>

                  {pipelineData.patents.map((pat) => (
                    <div key={pat.patent_number} className="p-5 space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-mono font-bold text-blue-700 text-sm mr-2">
                            {pat.patent_number}
                          </span>
                          <span className="font-semibold text-sm text-slate-900">{pat.title}</span>
                        </div>
                        <span className="font-mono text-xs text-slate-500">
                          Relevance: {pat.investigation_relevance?.score}/100
                        </span>
                      </div>

                      {pat.missing_claims_warning ? (
                        <div className="p-3 bg-amber-50 border border-amber-200 rounded text-xs text-amber-900">
                          {pat.missing_claims_warning}
                        </div>
                      ) : (
                        <div className="border border-slate-200 rounded-lg overflow-hidden">
                          <table className="w-full text-left border-collapse text-xs">
                            <thead>
                              <tr className="bg-[#080C14] text-white font-mono text-[10px]">
                                <th className="py-2 px-3 w-24">CLAIM / ID</th>
                                <th className="py-2 px-3 w-56">TECHNICAL CONCEPT (AI)</th>
                                <th className="py-2 px-3">DECOMPOSED LIMITATION DESCRIPTION</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-200">
                              {(pat.claim_elements || []).flatMap((cg) =>
                                cg.elements.map((el) => (
                                  <tr key={`${cg.claim_number}-${el.element_id}`}>
                                    <td className="py-2.5 px-3 font-mono font-bold text-blue-700">
                                      Claim {cg.claim_number} · {el.element_id}
                                    </td>
                                    <td className="py-2.5 px-3 font-semibold text-slate-900">
                                      {el.technical_concept}
                                    </td>
                                    <td className="py-2.5 px-3 text-slate-600">{el.description}</td>
                                  </tr>
                                ))
                              )}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  ))}
                </section>
              )}

              {/* ===============================================================
                  VIEW 3: TECHNOLOGY CLUSTERING (STEP 4)
                 =============================================================== */}
              {activeView === "clusters" && (
                <section className="bg-white border border-slate-200 rounded-xl divide-y divide-slate-200 shadow-2xs">
                  <div className="p-5">
                    <h3 className="text-base font-bold text-slate-900">
                      Step 4 · Hierarchical Technology Clustering
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Candidate patents grouped into technical domains without forcing unsupported classifications.
                    </p>
                  </div>

                  <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
                    {(pipelineData.technology_clusters || []).map((cluster) => (
                      <div
                        key={cluster.cluster_name}
                        className="border border-slate-200 rounded-xl p-4 space-y-3"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-[11px] font-bold text-blue-600 uppercase">
                              {cluster.parent_domain}
                            </div>
                            <div className="text-sm font-bold text-slate-900">
                              {cluster.sub_area} ({cluster.patent_count})
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              setClusterFilter(cluster.cluster_name);
                              setActiveView("dossier");
                            }}
                            className="px-2.5 py-1 text-xs font-medium bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-md transition-colors"
                          >
                            Filter Matrix
                          </button>
                        </div>

                        <div className="divide-y divide-slate-100 text-xs">
                          {cluster.patents.map((p) => (
                            <div
                              key={p.patent_number}
                              onClick={() => {
                                setSelectedPatentNumber(p.patent_number);
                                setActiveView("dossier");
                              }}
                              className="py-2 flex items-center justify-between gap-2 cursor-pointer hover:text-blue-700"
                            >
                              <div className="truncate">
                                <span className="font-mono font-bold mr-2">{p.patent_number}</span>
                                <span className="text-slate-600">{p.title}</span>
                              </div>
                              <span className="font-mono font-semibold text-slate-900 shrink-0">
                                {p.relevance_score}/100
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* ===============================================================
                  VIEW 4: GOOGLE ADK TRACE & BIGQUERY SCHEMA INSPECTION (STEP 1)
                 =============================================================== */}
              {activeView === "schema" && (
                <div className="space-y-5">
                  <section className="bg-white border border-slate-200 rounded-xl divide-y divide-slate-200 shadow-2xs">
                    <div className="p-5">
                      <h3 className="text-base font-bold text-slate-900">
                        Google ADK Orchestration Trace (root_agent → retrieval → analysis → ranking)
                      </h3>
                      <p className="text-xs text-slate-500">
                        All BigQuery operations and patent life calculations are isolated inside deterministic Python tools.
                      </p>
                    </div>
                    <div className="divide-y divide-slate-200">
                      {(pipelineData.adk_architecture?.agent_trace || []).map((step, i) => (
                        <div key={i} className="p-4 flex items-center justify-between gap-4 text-xs">
                          <div className="space-y-1">
                            <div className="font-mono">
                              <span className="font-bold text-blue-700">{step.agent}</span>
                              <span className="mx-2 text-slate-400">→</span>
                              <span className="font-semibold text-slate-900">{step.step}</span>
                              <span className="mx-2 text-slate-400">·</span>
                              <span className="text-slate-500">Tool: {step.tool}</span>
                            </div>
                            <div className="text-slate-600">{step.summary}</div>
                          </div>
                          <span className="font-mono text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded shrink-0">
                            {step.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </section>

                  {pipelineData.schema_inspection && (
                    <section className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
                      <div className="p-5 border-b border-slate-200 space-y-1">
                        <h3 className="text-base font-bold text-slate-900">
                          Step 1 · Inspected BigQuery Schema:{" "}
                          <span className="font-mono text-blue-700">
                            {pipelineData.schema_inspection.dataset}
                          </span>
                        </h3>
                        <p className="text-xs text-slate-600">
                          {pipelineData.schema_inspection.status_derivation_note}
                        </p>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse text-xs">
                          <thead>
                            <tr className="bg-[#080C14] text-white font-mono text-[10px]">
                              <th className="py-2.5 px-4">COLUMN NAME</th>
                              <th className="py-2.5 px-4">BIGQUERY TYPE</th>
                              <th className="py-2.5 px-4">SUBFIELDS</th>
                              <th className="py-2.5 px-4">MAPPED CONCEPT</th>
                              <th className="py-2.5 px-4">DESCRIPTION</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-200">
                            {pipelineData.schema_inspection.schema_fields.map((f) => (
                              <tr key={f.name} className="hover:bg-slate-50">
                                <td className="py-2.5 px-4 font-mono font-bold text-slate-900">
                                  {f.name}
                                </td>
                                <td className="py-2.5 px-4 font-mono text-slate-600">
                                  {f.type} ({f.mode})
                                </td>
                                <td className="py-2.5 px-4 font-mono text-[11px] text-slate-500">
                                  {f.subfields
                                    ? f.subfields.map((s) => `${s.name}: ${s.type}`).join(", ")
                                    : "—"}
                                </td>
                                <td className="py-2.5 px-4 font-semibold text-slate-800">
                                  {f.mapped_concept}
                                </td>
                                <td className="py-2.5 px-4 text-slate-600">{f.description}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </section>
                  )}
                </div>
              )}

              {/* ===============================================================
                  VIEW 5: CANONICAL OUTPUT JSON (EXACT REQUIRED SCHEMA)
                 =============================================================== */}
              {activeView === "json" && (
                <section className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
                  <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">
                        Canonical Client Patent Analysis Output JSON
                      </h3>
                      <p className="text-xs text-slate-500">
                        Matches the exact output JSON schema required for the Client Patent Analysis Pipeline.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={handleCopyJson}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-800 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                    >
                      {copiedJson ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                          <span>Copied JSON</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy JSON</span>
                        </>
                      )}
                    </button>
                  </div>
                  <pre className="p-5 text-xs font-mono bg-[#080C14] text-slate-100 overflow-x-auto max-h-[680px] leading-relaxed">
                    {JSON.stringify(pipelineData.canonical_output, null, 2)}
                  </pre>
                </section>
              )}
            </>
          )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
