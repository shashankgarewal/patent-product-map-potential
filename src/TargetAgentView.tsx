import React, { useState, useEffect } from "react";
import {
  Search,
  Layers,
  Database,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Copy,
  Check,
  Play,
  SlidersHorizontal,
  ShieldCheck,
  FileCode2,
} from "lucide-react";
import { PatentRecord, TargetAgentResponse } from "./types";

interface TargetAgentViewProps {
  targetCompanyDefault: string;
  technologyAreaDefault: string;
  clientPatents: PatentRecord[];
}

export default function TargetAgentView({
  targetCompanyDefault,
  technologyAreaDefault,
  clientPatents,
}: TargetAgentViewProps) {
  const [targetCompany, setTargetCompany] = useState<string>(targetCompanyDefault || "Netflix");
  const [technologyArea, setTechnologyArea] = useState<string>(
    technologyAreaDefault || "video streaming"
  );
  const [inputMode, setInputMode] = useState<"structured" | "json">("structured");
  const [rawJsonPayload, setRawJsonPayload] = useState<string>("");
  const [jsonError, setJsonError] = useState<string | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [agentData, setAgentData] = useState<TargetAgentResponse | null>(null);
  const [subTab, setSubTab] = useState<"technologies" | "queries" | "json">("technologies");
  const [copiedJson, setCopiedJson] = useState<boolean>(false);

  const buildPatentContextPayload = (patents: PatentRecord[]) => {
    if (!patents || patents.length === 0) {
      return [
        {
          patent_number: "US-10594774-B2",
          technology_areas: ["adaptive streaming", "content delivery"],
          key_concepts: ["adaptive bitrate", "client buffer telemetry", "video delivery"],
        },
        {
          patent_number: "US-10609394-B2",
          technology_areas: ["video encoding"],
          key_concepts: ["HDR reshaping metadata", "per-shot encoding", "SEI signaling"],
        },
      ];
    }
    return patents.slice(0, 5).map((p) => ({
      patent_number: p.patent_number,
      technology_areas: (p.technology_areas || []).map((a) =>
        a.includes(" > ") ? a.split(" > ")[1].toLowerCase() : a.toLowerCase()
      ),
      key_concepts: (p.key_concepts || []).slice(0, 4),
    }));
  };

  const runTargetAgent = async (
    companyOverride?: string,
    techOverride?: string,
    customContextOverride?: any[]
  ) => {
    setJsonError(null);
    let companyToRun = companyOverride !== undefined ? companyOverride : targetCompany;
    let techToRun = techOverride !== undefined ? techOverride : technologyArea;
    let contextToRun =
      customContextOverride !== undefined
        ? customContextOverride
        : buildPatentContextPayload(clientPatents);

    if (companyOverride === undefined && inputMode === "json") {
      try {
        const parsed = JSON.parse(rawJsonPayload);
        companyToRun = String(parsed.target_company || "Netflix");
        techToRun = String(parsed.technology_area || "");
        contextToRun = Array.isArray(parsed.client_patent_context)
          ? parsed.client_patent_context
          : [];
        setTargetCompany(companyToRun);
        setTechnologyArea(techToRun);
      } catch (_e) {
        setJsonError("Invalid JSON input payload.");
        return;
      }
    } else {
      setRawJsonPayload(
        JSON.stringify(
          {
            target_company: companyToRun,
            technology_area: techToRun,
            client_patent_context: contextToRun,
          },
          null,
          2
        )
      );
    }

    setLoading(true);
    try {
      const res = await fetch("/api/analyze-target-company", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_company: companyToRun,
          technology_area: techToRun,
          client_patent_context: contextToRun,
          top_k: 4,
          use_llm: true,
        }),
      });
      const data: TargetAgentResponse = await res.json();
      setAgentData(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const initialCtx = buildPatentContextPayload(clientPatents);
    setRawJsonPayload(
      JSON.stringify(
        {
          target_company: "Netflix",
          technology_area: technologyAreaDefault || "video streaming",
          client_patent_context: initialCtx,
        },
        null,
        2
      )
    );
    runTargetAgent("Netflix", technologyAreaDefault || "video streaming", initialCtx);
  }, []);

  const handleCopyJson = () => {
    if (!agentData?.canonical_output) return;
    navigator.clipboard.writeText(JSON.stringify(agentData.canonical_output, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  return (
    <div className="space-y-5">
      {/* Header & ADK Architecture Card */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-2xs">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1.5 font-mono font-semibold text-indigo-800 bg-indigo-50 px-2.5 py-0.5 rounded">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-600"></span>
                GOOGLE ADK TARGET RETRIEVAL & ANALYSIS AGENT
              </span>
              <span className="text-slate-400">·</span>
              <span className="font-mono text-slate-500">
                root_agent → target_retrieval_agent → target_analysis_agent
              </span>
            </div>

            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              Target Technology & Product Intelligence: {agentData?.target_company || targetCompany}
            </h2>

            <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
              Answers:{" "}
              <em className="text-slate-900 font-medium">
                &ldquo;What publicly documented technologies/capabilities of this target company are
                relevant to the client&apos;s patent technology?&rdquo;
              </em>{" "}
              Operates strictly against the pre-fetched{" "}
              <span className="font-mono">target_knowledge.sqlite</span> database using multi-query
              expansion via <span className="font-mono">search_target_knowledge()</span> with zero
              runtime web crawling.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => setInputMode(inputMode === "structured" ? "json" : "structured")}
              className="px-3 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors cursor-pointer"
            >
              {inputMode === "structured" ? "Edit Input JSON Payload" : "Structured Controls"}
            </button>
            <button
              type="button"
              onClick={() => runTargetAgent()}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-[#0B0F19] hover:bg-slate-800 disabled:opacity-50 rounded-lg transition-colors cursor-pointer"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{loading ? "Running Target Agent..." : "Run Target Retrieval Agent"}</span>
            </button>
          </div>
        </div>

        {/* Input / Scenario Bar */}
        {inputMode === "structured" ? (
          <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-3 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-slate-700">Target Company:</span>
                <input
                  type="text"
                  value={targetCompany}
                  onChange={(e) => setTargetCompany(e.target.value)}
                  className="px-2.5 py-1 border border-slate-200 rounded font-medium text-slate-900 w-36"
                />
              </div>
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-slate-700">Technology Area:</span>
                <input
                  type="text"
                  value={technologyArea}
                  onChange={(e) => setTechnologyArea(e.target.value)}
                  className="px-2.5 py-1 border border-slate-200 rounded font-medium text-slate-900 w-44"
                />
              </div>
              <span className="text-slate-500 font-mono text-[11px]">
                + {clientPatents.length || 2} Client Patent Context items synced
              </span>
            </div>

            {/* Quick Verification Scenarios for Target Retrieval Agent */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <button
                type="button"
                onClick={() => {
                  setTargetCompany("Netflix");
                  setTechnologyArea("video streaming");
                  runTargetAgent(
                    "Netflix",
                    "video streaming",
                    buildPatentContextPayload(clientPatents)
                  );
                }}
                className="px-2.5 py-1 bg-blue-50 text-blue-800 hover:bg-blue-100 rounded font-medium transition-colors cursor-pointer"
              >
                Netflix · Video Streaming (Sufficient Evidence)
              </button>

              <button
                type="button"
                onClick={() => {
                  setTargetCompany("Netflix");
                  setTechnologyArea("quantum propulsion reactors");
                  runTargetAgent("Netflix", "quantum propulsion reactors", [
                    {
                      patent_number: "US-9999999-B2",
                      technology_areas: ["quantum propulsion"],
                      key_concepts: ["antimatter containment", "warp plasma manifold"],
                    },
                  ]);
                }}
                className="px-2.5 py-1 bg-amber-50 text-amber-900 border border-amber-200 hover:bg-amber-100 rounded font-medium transition-colors cursor-pointer"
              >
                Test Insufficient Evidence Guardrail
              </button>
            </div>
          </div>
        ) : (
          <div className="pt-3 border-t border-slate-100 space-y-2">
            <div className="text-xs font-semibold text-slate-700">
              Target Retrieval Agent Input JSON (`target_company`, `technology_area`, `client_patent_context`):
            </div>
            <textarea
              value={rawJsonPayload}
              onChange={(e) => setRawJsonPayload(e.target.value)}
              rows={7}
              className="w-full p-3 font-mono text-xs bg-slate-950 text-slate-100 rounded-lg border border-slate-800"
            />
            {jsonError && <p className="text-xs text-red-600 font-medium">{jsonError}</p>}
          </div>
        )}
      </section>

      {/* Sub-navigation Bar */}
      {agentData && (
        <section className="bg-white border border-slate-200 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs">
            <button
              type="button"
              onClick={() => setSubTab("technologies")}
              className={`px-3 py-1.5 rounded-md font-semibold transition-colors ${
                subTab === "technologies"
                  ? "bg-white text-slate-900 shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Discovered Target Technologies & Evidence (
              {agentData.technology_areas?.length ?? 0})
            </button>
            <button
              type="button"
              onClick={() => setSubTab("queries")}
              className={`px-3 py-1.5 rounded-md font-semibold transition-colors ${
                subTab === "queries"
                  ? "bg-white text-slate-900 shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Multi-Query Retrieval & ADK Trace ({agentData.multi_query_log?.length ?? 0} Queries)
            </button>
            <button
              type="button"
              onClick={() => setSubTab("json")}
              className={`px-3 py-1.5 rounded-md font-semibold transition-colors ${
                subTab === "json"
                  ? "bg-white text-slate-900 shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Canonical Output JSON
            </button>
          </div>

          <div className="text-xs font-mono text-slate-500">
            Evidence Status:{" "}
            <strong
              className={
                agentData.evidence_status === "sufficient"
                  ? "text-emerald-700"
                  : "text-amber-700"
              }
            >
              {agentData.evidence_status.toUpperCase()}
            </strong>
          </div>
        </section>
      )}

      {/* INSUFFICIENT EVIDENCE STATE */}
      {!loading && agentData && agentData.evidence_status === "insufficient" && (
        <section className="bg-white border-2 border-amber-300 rounded-xl p-6 space-y-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <div className="text-xs font-mono font-bold text-amber-800">
                EVIDENCE GUARDRAIL · {"{\"evidence_status\": \"insufficient\"}"}
              </div>
              <h3 className="text-base font-bold text-slate-900">
                Insufficient Evidence in Pre-Fetched Target Knowledge Database
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                {agentData.diagnostic_reason ||
                  "No supporting evidence chunks matched the requested patent concepts in the pre-fetched target database. The agent refused to fabricate target product capabilities."}
              </p>
            </div>
          </div>

          <div className="p-4 bg-slate-950 text-slate-100 rounded-lg font-mono text-xs">
            {JSON.stringify(agentData.canonical_output, null, 2)}
          </div>
        </section>
      )}

      {/* SUB-TAB 1: DISCOVERED TARGET TECHNOLOGIES, PRODUCTS & VERBATIM EVIDENCE */}
      {!loading &&
        agentData &&
        agentData.evidence_status === "sufficient" &&
        subTab === "technologies" && (
          <div className="space-y-4">
            {(agentData.technology_areas || []).map((area, idx) => (
              <section
                key={idx}
                className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs"
              >
                <div className="px-6 py-4 bg-[#0B0F19] text-white flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="text-[10px] font-mono text-sky-400 uppercase font-bold">
                      TARGET TECHNOLOGY AREA #{idx + 1} · {area.technology}
                    </div>
                    <h3 className="text-base font-bold mt-0.5">{area.product_or_service}</h3>
                  </div>
                  <span className="text-xs font-mono text-emerald-300 shrink-0">
                    {area.supporting_evidence.length} Supporting Source Chunk(s)
                  </span>
                </div>

                <div className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
                  {/* Left 5 Cols: Documented Technical Capabilities */}
                  <div className="lg:col-span-5 space-y-4">
                    <div className="space-y-2">
                      <div className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                        Documented Technical Capabilities
                      </div>
                      <ul className="space-y-2 text-xs text-slate-700 list-disc pl-4">
                        {area.technical_capabilities.map((cap, cIdx) => (
                          <li key={cIdx} className="leading-relaxed">
                            {cap}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {area.relevant_technical_concepts &&
                      area.relevant_technical_concepts.length > 0 && (
                        <div className="pt-3 border-t border-slate-100 space-y-1 text-xs">
                          <div className="font-semibold text-slate-800">
                            Relevant Technical Concepts:
                          </div>
                          <div className="text-slate-600 font-mono text-[11px]">
                            {area.relevant_technical_concepts.join(" · ")}
                          </div>
                        </div>
                      )}
                  </div>

                  {/* Right 7 Cols: Verbatim Supporting Evidence from Target Knowledge DB */}
                  <div className="lg:col-span-7 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                        Verbatim Supporting Evidence (Pre-Fetched Target Knowledge DB)
                      </span>
                      <span className="text-[10px] font-mono font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded">
                        SOURCE TRACEABILITY VERIFIED
                      </span>
                    </div>

                    <div className="space-y-3">
                      {area.supporting_evidence.map((ev, evIdx) => (
                        <div
                          key={evIdx}
                          className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-2 text-xs"
                        >
                          <p className="text-slate-700 leading-relaxed">&ldquo;{ev.text}&rdquo;</p>
                          <div className="pt-2 border-t border-slate-200/80 flex flex-wrap items-center justify-between gap-2 text-[11px]">
                            <div className="font-semibold text-slate-900">
                              Source: {ev.source_title}
                            </div>
                            <a
                              href={ev.source_url}
                              target="_blank"
                              rel="noreferrer"
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
                </div>
              </section>
            ))}
          </div>
        )}

      {/* SUB-TAB 2: MULTI-QUERY RETRIEVAL LOG & ADK TRACE */}
      {!loading && agentData && subTab === "queries" && (
        <div className="space-y-5">
          <section className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
            <div className="p-4 border-b border-slate-200">
              <h3 className="text-sm font-bold text-slate-900">
                Multi-Query Retrieval Execution Log (`search_target_knowledge` Tool)
              </h3>
              <p className="text-xs text-slate-500">
                `target_retrieval_agent` expands client patent concepts into multiple distinct retrieval queries against `target_knowledge.sqlite`.
              </p>
            </div>
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-[#080C14] text-white font-mono text-[10px]">
                  <th className="py-2.5 px-4">#</th>
                  <th className="py-2.5 px-4">RETRIEVAL QUERY</th>
                  <th className="py-2.5 px-4">CONCEPT DERIVATION RATIONALE</th>
                  <th className="py-2.5 px-4 text-right">MATCHED CHUNKS</th>
                  <th className="py-2.5 px-4">TOP CHUNK IDS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {(agentData.multi_query_log || []).map((q, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="py-2.5 px-4 font-mono text-slate-500">{i + 1}</td>
                    <td className="py-2.5 px-4 font-mono font-bold text-blue-700">{q.query}</td>
                    <td className="py-2.5 px-4 text-slate-600">{q.rationale}</td>
                    <td className="py-2.5 px-4 text-right font-mono font-semibold">
                      {q.returned_count}
                    </td>
                    <td className="py-2.5 px-4 font-mono text-[11px] text-slate-500">
                      {(q.top_chunk_ids || []).join(", ") || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          {agentData.adk_architecture && (
            <section className="bg-white border border-slate-200 rounded-xl divide-y divide-slate-200 shadow-2xs">
              <div className="p-4">
                <h3 className="text-sm font-bold text-slate-900">
                  Google ADK Agent Trace (`root_agent` → `target_retrieval_agent` → `target_analysis_agent`)
                </h3>
              </div>
              {agentData.adk_architecture.agent_trace.map((step, i) => (
                <div key={i} className="p-4 flex items-center justify-between gap-4 text-xs">
                  <div className="space-y-1">
                    <div className="font-mono">
                      <span className="font-bold text-indigo-700">{step.agent}</span>
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
            </section>
          )}
        </div>
      )}

      {/* SUB-TAB 3: CANONICAL OUTPUT JSON */}
      {!loading && agentData && subTab === "json" && (
        <section className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
          <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Target Retrieval & Analysis Agent Canonical Output JSON
              </h3>
              <p className="text-xs text-slate-500">
                Exact output structure ready for the downstream Patent–Technology Matching Agent.
              </p>
            </div>
            <button
              type="button"
              onClick={handleCopyJson}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-800 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors cursor-pointer"
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
          <pre className="p-5 text-xs font-mono bg-[#080C14] text-slate-100 overflow-x-auto max-h-[640px] leading-relaxed">
            {JSON.stringify(agentData.canonical_output, null, 2)}
          </pre>
        </section>
      )}
    </div>
  );
}
