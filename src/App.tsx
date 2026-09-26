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
} from "lucide-react";
import { PipelineResponse, PatentRecord } from "./types";
import TargetPrefetchView from "./TargetPrefetchView";
import TargetAgentView from "./TargetAgentView";
import MatchingAgentView from "./MatchingAgentView";

type WorkspaceView =
  | "dossier"
  | "matching"
  | "claims"
  | "clusters"
  | "target_agent"
  | "target_prefetch"
  | "schema"
  | "json";

export default function App() {
  const [clientCompany, setClientCompany] = useState<string>("Apple");
  const [targetCompanyPreview, setTargetCompanyPreview] = useState<string>("Netflix, Inc.");
  const [technologyArea, setTechnologyArea] = useState<string>("video streaming");
  const [inputMode, setInputMode] = useState<"form" | "json">("form");
  const [rawJsonInput, setRawJsonInput] = useState<string>(
    JSON.stringify(
      {
        client_company: "Apple",
        technology_area: "video streaming",
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
  const [sortBy, setSortBy] = useState<"relevance_desc" | "term_desc" | "filing_desc">("relevance_desc");
  const [copiedTable, setCopiedTable] = useState<boolean>(false);
  const [copiedJson, setCopiedJson] = useState<boolean>(false);
  const [completedTimestamp, setCompletedTimestamp] = useState<string>("07:24:12 UTC");

  const executePipeline = async (companyOverride?: string, techOverride?: string) => {
    setJsonError(null);
    let companyToRun = companyOverride !== undefined ? companyOverride : clientCompany;
    let techToRun = techOverride !== undefined ? techOverride : technologyArea;

    if (companyOverride === undefined && inputMode === "json") {
      try {
        const parsed = JSON.parse(rawJsonInput);
        companyToRun = String(parsed.client_company || "").trim();
        techToRun =
          parsed.technology_area && parsed.technology_area !== "optional"
            ? String(parsed.technology_area).trim()
            : "";
        setClientCompany(companyToRun);
        setTechnologyArea(techToRun);
      } catch (_err) {
        setJsonError('Invalid JSON payload. Expected {"client_company": "...", "technology_area": "..."}');
        return;
      }
    } else {
      setRawJsonInput(
        JSON.stringify(
          {
            client_company: companyToRun,
            technology_area: techToRun || "optional",
          },
          null,
          2
        )
      );
    }

    setLoading(true);
    setClusterFilter("ALL");
    try {
      const res = await fetch("/api/analyze-client-patents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_company: companyToRun,
          technology_area: techToRun,
          max_candidates: 6,
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
      if (data.patents && data.patents.length > 0) {
        setSelectedPatentNumber(data.patents[0].patent_number);
      } else {
        setSelectedPatentNumber(null);
      }
    } catch (e: any) {
      setPipelineData({
        pipeline_status: "PIPELINE_ERROR",
        client_company: companyToRun,
        technology_area: techToRun,
        error: e?.message || "Failed to execute ADK Client Patent Pipeline.",
        patents: [],
      });
    } finally {
      setLoading(false);
    }
  };

  const filteredPatents = useMemo(() => {
    if (!pipelineData?.patents) return [];
    let list = [...pipelineData.patents];

    if (clusterFilter !== "ALL") {
      list = list.filter((p) => (p.technology_areas || []).includes(clusterFilter));
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (p) =>
          p.patent_number.toLowerCase().includes(q) ||
          p.title.toLowerCase().includes(q) ||
          p.technical_summary.toLowerCase().includes(q) ||
          (p.cpc_codes || []).some((c) => c.toLowerCase().includes(q)) ||
          (p.key_concepts || []).some((k) => k.toLowerCase().includes(q)) ||
          (p.independent_claims || []).some((cl) => cl.toLowerCase().includes(q))
      );
    }

    list.sort((a, b) => {
      if (sortBy === "relevance_desc") {
        return (b.investigation_relevance?.score ?? 0) - (a.investigation_relevance?.score ?? 0);
      }
      if (sortBy === "term_desc") {
        return (b.estimated_remaining_term_years ?? -1) - (a.estimated_remaining_term_years ?? -1);
      }
      if (sortBy === "filing_desc") {
        return (b.filing_date || "").localeCompare(a.filing_date || "");
      }
      return 0;
    });

    return list;
  }, [pipelineData, clusterFilter, searchQuery, sortBy]);

  const selectedPatent: PatentRecord | null = useMemo(() => {
    if (!filteredPatents.length) return null;
    return (
      filteredPatents.find((p) => p.patent_number === selectedPatentNumber) ||
      filteredPatents[0]
    );
  }, [filteredPatents, selectedPatentNumber]);

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
    if (!pipelineData?.patents) return 0;
    return pipelineData.patents.filter((p) => (p.investigation_relevance?.score ?? 0) >= 80).length;
  }, [pipelineData]);

  const handleCopyTable = () => {
    if (!filteredPatents.length) return;
    const headers = [
      "Rank",
      "Patent Number",
      "Title",
      "Technology Areas",
      "Status",
      "Filing Date",
      "Grant Date",
      "Est. Remaining Term (Yrs)",
      "Investigation Relevance Score",
    ];
    const rows = filteredPatents.map((p, i) => [
      i + 1,
      p.patent_number,
      p.title,
      (p.technology_areas || []).join("; "),
      p.status,
      p.filing_date || "Missing",
      p.grant_date || "Ungranted",
      p.estimated_remaining_term_years === null ? "N/A" : p.estimated_remaining_term_years,
      `${p.investigation_relevance?.score ?? 0}/100`,
    ]);
    const tsv = [headers.join("\t"), ...rows.map((r) => r.join("\t"))].join("\n");
    navigator.clipboard.writeText(tsv);
    setCopiedTable(true);
    setTimeout(() => setCopiedTable(false), 2000);
  };

  const handleExportCsv = () => {
    if (!filteredPatents.length) return;
    const escapeCsv = (val: any) => `"${String(val ?? "").replace(/"/g, '""')}"`;
    const headers = [
      "Patent Number",
      "Title",
      "Technical Summary",
      "Technology Areas",
      "Key Concepts",
      "Priority Date",
      "Filing Date",
      "Grant Date",
      "Status",
      "Est Remaining Term Years",
      "CPC Codes",
      "Investigation Relevance Score",
      "Source",
    ];
    const rows = filteredPatents.map((p) => [
      p.patent_number,
      p.title,
      p.technical_summary,
      (p.technology_areas || []).join(" | "),
      (p.key_concepts || []).join(" | "),
      p.priority_date || "",
      p.filing_date || "",
      p.grant_date || "",
      p.status,
      p.estimated_remaining_term_years ?? "",
      (p.cpc_codes || []).join(" | "),
      p.investigation_relevance?.score ?? 0,
      p.source,
    ]);
    const csvContent = [
      headers.map(escapeCsv).join(","),
      ...rows.map((r) => r.map(escapeCsv).join(",")),
    ].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `client_patent_candidates_${(pipelineData?.client_company || "export")
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
                        placeholder="e.g. video streaming, adaptive streaming, video encoding"
                        className="w-full pl-9 pr-3 py-2 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-slate-900 text-slate-900"
                      />
                    </div>
                    <p className="text-[11px] text-slate-500 leading-normal">
                      Optionally narrow the analysis to a specific technology area. Leave blank to analyze the client company&apos;s broader patent portfolio.
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
                    ? "bg-white text-slate-900 shadow-2xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Candidate Matrix
              </button>
              <button
                type="button"
                onClick={() => setActiveView("matching")}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  activeView === "matching"
                    ? "bg-blue-700 text-white shadow-2xs"
                    : "text-blue-800 hover:bg-blue-50"
                }`}
              >
                Patent–Target Matching (ADK)
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
                ADK & Schema
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
          ) : activeView === "matching" ? (
            <MatchingAgentView
              clientCompanyDefault={pipelineData?.client_company || clientCompany}
              targetCompanyDefault={
                targetCompanyPreview.includes("Netflix") ? "Netflix" : targetCompanyPreview
              }
              technologyAreaDefault={technologyArea}
              clientPatents={pipelineData?.patents || []}
            />
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
                      Zero runtime web crawling. Pre-fetches 62 Netflix docs (45 via Medium MCP Server) into AlloyDB `vector(32)` tables.
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
                          Stores 62 full untruncated articles in <span className="font-mono">documents</span> (with SHA-256 <span className="font-mono">content_hash</span> deduplication) and 130 overlapping chunks in <span className="font-mono">document_chunks</span> with <span className="font-mono">vector(32)</span> ScaNN embeddings.
                        </p>
                      </div>

                      <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-1">
                        <div className="font-mono font-bold text-slate-900">
                          3. Runtime Target Retrieval Agent (ADK)
                        </div>
                        <p className="text-[11px] text-slate-600 leading-relaxed">
                          Expands client patent concepts into multi-query hybrid vector + keyword lookups against AlloyDB (<span className="font-mono">search_target_knowledge</span>) without browsing the internet.
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
              EXECUTIVE DOSSIER HEADER CARD (Matches Reference Image 2)
             ================================================================= */}
          <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-5 shadow-2xs">
            <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
              <div className="space-y-2">
                <div className="flex items-center gap-2.5 text-xs">
                  <span className="inline-flex items-center gap-1.5 font-mono font-semibold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
                    CLIENT PATENT DOSSIER #ADK-2026
                  </span>
                  <span className="text-slate-400">·</span>
                  <span className="font-mono text-slate-500">Completed {completedTimestamp}</span>
                </div>

                <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                  Client Patent Intelligence: {pipelineData?.client_company || clientCompany}
                  {pipelineData?.technology_area ? ` (${pipelineData.technology_area})` : ""}
                </h2>

                <p className="text-xs text-slate-600 max-w-2xl leading-relaxed">
                  {pipelineData?.pipeline_status === "SUCCESS" ? (
                    <>
                      Staged ADK analysis complete.{" "}
                      <strong className="font-semibold text-slate-900">
                        {pipelineData.patents.length} candidate patent publications
                      </strong>{" "}
                      retrieved and decomposed across{" "}
                      <strong className="font-semibold text-slate-900">
                        {pipelineData.staged_retrieval_metrics?.stage2_total_portfolio_records ??
                          pipelineData.patents.length}{" "}
                        screened portfolio utility filings
                      </strong>{" "}
                      in <span className="font-mono">patents-public-data.patents.publications</span>.
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
                  disabled={!filteredPatents.length}
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
                  disabled={!filteredPatents.length}
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

            {/* 4-Column Metadata Strip (Matches Reference Image 2) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2 border-t border-slate-100">
              <div className="border border-slate-200/90 rounded-lg p-3 flex items-center gap-3 bg-slate-50/40">
                <Building2 className="w-4 h-4 text-blue-600 shrink-0" />
                <div className="min-w-0">
                  <div className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                    CLIENT (HARMONIZED ASSIGNEE)
                  </div>
                  <div className="text-xs font-semibold text-slate-900 truncate font-mono">
                    {pipelineData?.resolved_assignee || pipelineData?.client_company || "Unresolved"}
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
                    root → retrieval → analysis → ranking
                  </div>
                </div>
              </div>

              <div className="border border-slate-200/90 rounded-lg p-3 flex items-center gap-3 bg-slate-50/40">
                <Database className="w-4 h-4 text-blue-600 shrink-0" />
                <div className="min-w-0">
                  <div className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                    VERIFICATION BASIS
                  </div>
                  <div className="text-xs font-semibold text-slate-900 truncate font-mono">
                    patents-public-data.patents
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
              4 KPI SUMMARY CARDS (Matches Reference Image 2)
             ================================================================= */}
          {!loading && pipelineData && pipelineData.pipeline_status === "SUCCESS" && (
            <>
              <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* KPI 1: Total Screened Portfolio Assets */}
                <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-2 shadow-2xs">
                  <div className="flex items-center justify-between text-[11px] font-bold tracking-wider text-slate-400 uppercase">
                    <span>STAGE 2 SCREENED ASSETS</span>
                    <Database className="w-3.5 h-3.5 text-slate-400" />
                  </div>
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-3xl font-bold font-mono tabular-nums text-slate-900">
                      {pipelineData.staged_retrieval_metrics?.stage2_total_portfolio_records ??
                        pipelineData.patents.length}
                    </span>
                    <span className="text-xs text-slate-500">publications</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[11px] text-slate-600">
                    <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                    <span>
                      Shortlisted {pipelineData.patents.length} for Stage 3 claim extraction
                    </span>
                  </div>
                </div>

                {/* KPI 2: High Priority Investigation Candidates */}
                <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-2 shadow-2xs">
                  <div className="flex items-center justify-between text-[11px] font-bold tracking-wider text-slate-400 uppercase">
                    <span>HIGH-RELEVANCE CANDIDATES</span>
                    <ShieldCheck className="w-3.5 h-3.5 text-red-600" />
                  </div>
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-3xl font-bold font-mono tabular-nums text-red-600">
                      {highPriorityCount}
                    </span>
                    <span className="text-xs text-red-700 font-medium">
                      candidates (score ≥ 80)
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Out of {pipelineData.patents.length} analyzed portfolio records
                  </div>
                </div>

                {/* KPI 3: Technology Clusters Identified */}
                <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-2 shadow-2xs">
                  <div className="flex items-center justify-between text-[11px] font-bold tracking-wider text-slate-400 uppercase">
                    <span>TECHNOLOGY CLUSTERS</span>
                    <Layers className="w-3.5 h-3.5 text-blue-600" />
                  </div>
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-3xl font-bold font-mono tabular-nums text-blue-600">
                      {pipelineData.technology_clusters?.length ?? 0}
                    </span>
                    <span className="text-xs text-blue-700 font-medium">technical sub-areas</span>
                  </div>
                  <div className="text-[11px] text-slate-500 truncate">
                    {(pipelineData.technology_clusters || [])
                      .map((c) => c.sub_area)
                      .join(" · ")}
                  </div>
                </div>

                {/* KPI 4: Avg. Estimated Remaining Term */}
                <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-2 shadow-2xs">
                  <div className="flex items-center justify-between text-[11px] font-bold tracking-wider text-slate-400 uppercase">
                    <span>AVG. EST. REMAINING LIFE</span>
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                  </div>
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-3xl font-bold font-mono tabular-nums text-slate-900">
                      {averageRemainingTerm !== null ? averageRemainingTerm : "N/A"}
                    </span>
                    <span className="text-xs text-slate-500">years</span>
                  </div>
                  <div className="text-[11px] text-slate-500">
                    20-yr statutory baseline (not legal opinion)
                  </div>
                </div>
              </section>

              {/* ===============================================================
                  VIEW 1: CANDIDATE PATENT INTELLIGENCE MATRIX + INSPECTOR
                 =============================================================== */}
              {activeView === "dossier" && (
                <div className="space-y-5">
                  {/* Main Matrix Table Card */}
                  <section className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
                    {/* Table Control Header */}
                    <div className="px-5 py-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="flex items-center gap-2.5">
                        <h3 className="text-sm font-bold text-slate-900">
                          Candidate Patent Intelligence Matrix
                        </h3>
                        <span className="text-[11px] font-mono font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                          {filteredPatents.length} Candidates Ranked
                        </span>
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-xs">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[11px] font-bold text-slate-400 uppercase">
                            CLUSTER:
                          </span>
                          <select
                            value={clusterFilter}
                            onChange={(e) => setClusterFilter(e.target.value)}
                            className="bg-white border border-slate-200 rounded-md px-2.5 py-1 text-xs font-medium text-slate-800 focus:outline-none"
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
                          <span className="text-[11px] font-bold text-slate-400 uppercase">
                            SORT BY:
                          </span>
                          <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value as any)}
                            className="bg-white border border-slate-200 rounded-md px-2.5 py-1 text-xs font-semibold text-slate-900 focus:outline-none"
                          >
                            <option value="relevance_desc">
                              Investigation Relevance (High → Low)
                            </option>
                            <option value="term_desc">
                              Estimated Remaining Term (High → Low)
                            </option>
                            <option value="filing_desc">Filing Date (Newest → Oldest)</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* Dark-Header Matrix Table (Matches Reference Image 2) */}
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="bg-[#080C14] text-white text-[10px] font-mono font-bold tracking-wider uppercase">
                            <th className="py-3.5 px-4 w-16">PRIORITY</th>
                            <th className="py-3.5 px-4 w-44">PATENT (SOURCE FACT)</th>
                            <th className="py-3.5 px-4">
                              TECHNICAL SUMMARY (AI) & INDEPENDENT CLAIMS (SOURCE FACT)
                            </th>
                            <th className="py-3.5 px-4 w-56">TECHNOLOGY CLUSTER & CONCEPTS</th>
                            <th className="py-3.5 px-4 w-36">CLAIM ELEMENTS</th>
                            <th className="py-3.5 px-4 w-36">EST. PATENT LIFE</th>
                            <th className="py-3.5 px-4 w-44">INVESTIGATION RELEVANCE</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200 text-xs">
                          {filteredPatents.map((pat, idx) => {
                            const isSelected = selectedPatent?.patent_number === pat.patent_number;
                            const score = pat.investigation_relevance?.score ?? 0;
                            const totalElements = (pat.claim_elements || []).reduce(
                              (acc, cg) => acc + (cg.elements?.length || 0),
                              0
                            );

                            return (
                              <tr
                                key={pat.patent_number}
                                onClick={() => setSelectedPatentNumber(pat.patent_number)}
                                className={`cursor-pointer transition-colors ${
                                  isSelected ? "bg-blue-50/50" : "hover:bg-slate-50/90"
                                }`}
                              >
                                {/* Column 1: Priority Rank Number */}
                                <td className="py-4 px-4 align-top">
                                  <span
                                    className={`inline-flex items-center justify-center w-7 h-7 rounded-md font-mono font-bold text-xs ${
                                      idx === 0
                                        ? "bg-red-50 text-red-700 border border-red-200"
                                        : "bg-slate-100 text-slate-700 border border-slate-200"
                                    }`}
                                  >
                                    {idx + 1}
                                  </span>
                                </td>

                                {/* Column 2: Patent Number, Dates & Title */}
                                <td className="py-4 px-4 align-top">
                                  <div className="flex items-center gap-1 font-mono font-bold text-blue-700">
                                    <span>{pat.patent_number}</span>
                                    <ExternalLink className="w-3 h-3 text-slate-400 shrink-0" />
                                  </div>
                                  <div className="text-[11px] text-slate-500 mt-1 font-mono tabular-nums">
                                    {pat.grant_date
                                      ? `Granted: ${pat.grant_date}`
                                      : "Application (Ungranted)"}
                                  </div>
                                  <div className="text-[11px] text-slate-400 font-mono tabular-nums">
                                    Filed: {pat.filing_date || "Missing (0)"}
                                  </div>
                                  <div className="font-semibold text-slate-900 mt-2 leading-snug">
                                    {pat.title}
                                  </div>
                                </td>

                                {/* Column 3: Technical Summary + Independent Claims */}
                                <td className="py-4 px-4 align-top max-w-md space-y-2">
                                  <p className="text-slate-600 leading-relaxed">
                                    {pat.technical_summary}
                                  </p>
                                  <div className="flex flex-wrap items-center gap-2 pt-1">
                                    {pat.independent_claims && pat.independent_claims.length > 0 ? (
                                      <span className="font-mono text-[11px] text-blue-800 bg-blue-50 border border-blue-200/60 px-2 py-0.5 rounded">
                                        Independent Claims:{" "}
                                        {pat.independent_claims.map((_, i) => i + 1).join(", ")} (Verbatim)
                                      </span>
                                    ) : (
                                      <span className="font-mono text-[11px] text-amber-800 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded">
                                        Missing Claims in Source Snapshot
                                      </span>
                                    )}
                                    <span className="font-mono text-[11px] text-slate-500">
                                      CPC: {(pat.cpc_codes || []).slice(0, 2).join(", ")}
                                    </span>
                                  </div>
                                </td>

                                {/* Column 4: Technology Cluster & Concepts */}
                                <td className="py-4 px-4 align-top space-y-1.5">
                                  <div className="font-semibold text-slate-900 leading-snug">
                                    {(pat.technology_areas || [])
                                      .map((a) => (a.includes(" > ") ? a.split(" > ")[1] : a))
                                      .join(" & ")}
                                  </div>
                                  <div className="text-[11px] text-slate-500 leading-normal">
                                    {(pat.key_concepts || []).slice(0, 3).join(" · ")}
                                  </div>
                                </td>

                                {/* Column 5: Claim Elements Decomposed */}
                                <td className="py-4 px-4 align-top">
                                  {totalElements > 0 ? (
                                    <div className="space-y-1">
                                      <span className="inline-flex items-center gap-1 font-mono text-[11px] font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded">
                                        ● {totalElements} Elements
                                      </span>
                                      <div className="text-[11px] text-slate-500">
                                        Click row to inspect clauses
                                      </div>
                                    </div>
                                  ) : (
                                    <div className="space-y-1">
                                      <span className="inline-flex items-center gap-1 font-mono text-[11px] font-semibold text-amber-800 bg-amber-50 px-2 py-0.5 rounded">
                                        ● 0 Elements
                                      </span>
                                      <div className="text-[11px] text-slate-400">
                                        No claim text in dataset
                                      </div>
                                    </div>
                                  )}
                                </td>

                                {/* Column 6: Estimated Patent Life */}
                                <td className="py-4 px-4 align-top font-mono tabular-nums">
                                  {pat.estimated_remaining_term_years === null ? (
                                    <div>
                                      <div className="font-bold text-amber-700">null (Missing)</div>
                                      <div className="text-[11px] text-slate-400 font-sans">
                                        No filing_date
                                      </div>
                                    </div>
                                  ) : pat.estimated_remaining_term_years <= 0 ? (
                                    <div>
                                      <div className="font-bold text-slate-400">0.0 years</div>
                                      <div className="text-[11px] text-slate-400 font-sans">
                                        20-yr baseline elapsed
                                      </div>
                                    </div>
                                  ) : (
                                    <div>
                                      <div className="font-bold text-slate-900">
                                        ~{pat.estimated_remaining_term_years.toFixed(1)} years
                                      </div>
                                      <div className="text-[11px] text-slate-400">
                                        Nominal:{" "}
                                        {pat.patent_life?.estimated_expiration_date_nominal?.slice(
                                          0,
                                          7
                                        ) || "20-yr term"}
                                      </div>
                                    </div>
                                  )}
                                </td>

                                {/* Column 7: Investigation Relevance */}
                                <td className="py-4 px-4 align-top">
                                  <div className="space-y-1">
                                    <span
                                      className={`inline-block font-mono text-[11px] font-bold px-2 py-0.5 rounded ${
                                        score >= 80
                                          ? "bg-blue-50 text-blue-700"
                                          : score >= 60
                                          ? "bg-amber-50 text-amber-800"
                                          : "bg-slate-100 text-slate-700"
                                      }`}
                                    >
                                      {score >= 80
                                        ? `High (${score}/100)`
                                        : score >= 60
                                        ? `Moderate (${score}/100)`
                                        : `Low (${score}/100)`}
                                    </span>
                                    <div className="text-[11px] text-slate-500 line-clamp-2">
                                      {pat.status}
                                    </div>
                                  </div>
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
                          {highPriorityCount} of {pipelineData.patents.length} Shortlisted Patents
                          Score ≥ 80 on Investigation Relevance
                        </span>
                        <span className="text-slate-300">·</span>
                        <span>Source: Google Patents Public Dataset</span>
                      </div>
                      <div className="font-mono text-[11px] text-slate-500">
                        Click any row above to inspect Source Facts vs. AI Interpretation below
                      </div>
                    </div>
                  </section>

                  {/* =============================================================
                      SELECTED PATENT DEEP-DIVE DRAWER (Step 2, 3, 5, 6 Breakdown)
                     ============================================================= */}
                  {selectedPatent && (
                    <section className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
                      <div className="px-6 py-4 bg-[#0B0F19] text-white flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-xs font-bold text-sky-400">
                            SELECTED CANDIDATE INSPECTOR
                          </span>
                          <span className="text-slate-500">·</span>
                          <span className="font-mono text-sm font-bold">
                            {selectedPatent.patent_number}
                          </span>
                          <span className="text-xs text-slate-300 truncate max-w-xl">
                            {selectedPatent.title}
                          </span>
                        </div>
                        <div className="text-[11px] font-mono text-slate-300 shrink-0">
                          Source Fact vs. AI Interpretation Verified
                        </div>
                      </div>

                      <div className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
                        {/* Left 5 Cols: Source Facts + Patent Life + Investigation Relevance */}
                        <div className="lg:col-span-5 space-y-5">
                          {/* Box 1: Verbatim Source Facts */}
                          <div className="border border-slate-200 rounded-lg p-4 space-y-3">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                                Source Facts (BigQuery Dataset)
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

                          {/* Box 2: Step 5 — Estimated Patent Life */}
                          <div className="border border-slate-200 rounded-lg p-4 space-y-2.5">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                                Step 5 · Estimated Patent Term
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
                          </div>

                          {/* Box 3: Step 6 — Explainable Investigation Relevance */}
                          <div className="border border-slate-200 rounded-lg p-4 space-y-2.5">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                                Step 6 · Investigation Relevance ({selectedPatent.investigation_relevance?.score}/100)
                              </span>
                              <span className="text-[10px] font-mono font-semibold text-blue-800 bg-blue-50 px-2 py-0.5 rounded">
                                EXPLAINABLE SCORING
                              </span>
                            </div>
                            <ul className="space-y-1.5 text-xs text-slate-600 list-disc pl-4">
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

                        {/* Right 7 Cols: Step 3 — Independent Claim & Decomposed Claim Elements */}
                        <div className="lg:col-span-7 space-y-5">
                          <div className="border border-slate-200 rounded-lg p-4 space-y-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                                  Step 3 · Claim Element Decomposition
                                </span>
                                <p className="text-[11px] text-slate-500">
                                  Structured technical representations for downstream target-company evidence comparison (no legal conclusions).
                                </p>
                              </div>
                              <span className="text-[10px] font-mono font-semibold text-indigo-800 bg-indigo-50 px-2 py-0.5 rounded">
                                AI INTERPRETATION + SOURCE CLAIMS
                              </span>
                            </div>

                            {selectedPatent.missing_claims_warning ? (
                              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900">
                                <strong>Missing Claims Handled Without Fabrication:</strong>{" "}
                                {selectedPatent.missing_claims_warning}
                              </div>
                            ) : (
                              <>
                                {/* Decomposed Elements Table */}
                                {(selectedPatent.claim_elements || []).map((claimGroup) => (
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
                                ))}

                                {/* Verbatim Independent Claim Source Fact */}
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
                              </>
                            )}
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
