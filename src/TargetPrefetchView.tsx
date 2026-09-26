import React, { useState, useEffect } from "react";
import {
  Database,
  RefreshCw,
  Search,
  ExternalLink,
  Copy,
  Check,
  Play,
  ShieldAlert,
  Server,
} from "lucide-react";
import { TargetKnowledgeResponse, TargetKnowledgeChunk } from "./types";

export default function TargetPrefetchView() {
  const [data, setData] = useState<TargetKnowledgeResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [ingesting, setIngesting] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedTag, setSelectedTag] = useState<string>("");
  const [selectedSourceType, setSelectedSourceType] = useState<string>("");
  const [selectedChunk, setSelectedChunk] = useState<TargetKnowledgeChunk | null>(null);
  const [copiedChunk, setCopiedChunk] = useState<boolean>(false);
  const [subTab, setSubTab] = useState<"chunks" | "documents" | "sources" | "logs">("chunks");
  const [mcpRpcResult, setMcpRpcResult] = useState<any | null>(null);
  const [testingMcp, setTestingMcp] = useState<boolean>(false);

  const testLocalMcpServer = async () => {
    setTestingMcp(true);
    try {
      const res = await fetch("/api/mcp/medium", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: "ui_test_1",
          method: "tools/call",
          params: {
            name: "medium_list_publication_articles",
            arguments: {
              publication: "netflixtechblog",
              limit: 5,
            },
          },
        }),
      });
      const json = await res.json();
      setMcpRpcResult(json);
    } finally {
      setTestingMcp(false);
    }
  };

  const fetchStatus = async (q = searchQuery, tag = selectedTag, st = selectedSourceType) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("company", "Netflix");
      if (q.trim()) params.set("query", q.trim());
      if (tag) params.set("tag", tag);
      if (st) params.set("source_type", st);

      const res = await fetch(`/api/target-knowledge?${params.toString()}`);
      const json: TargetKnowledgeResponse = await res.json();
      setData(json);
      if (json.chunks && json.chunks.length > 0) {
        setSelectedChunk(json.chunks[0]);
      } else {
        setSelectedChunk(null);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus("", "", "");
  }, []);

  const triggerPrefetch = async (mode: "initial" | "incremental", customDocument?: any) => {
    setIngesting(true);
    try {
      const res = await fetch("/api/target-knowledge/prefetch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode,
          custom_document: customDocument || null,
        }),
      });
      const json: TargetKnowledgeResponse = await res.json();
      setData(json);
      if (json.chunks && json.chunks.length > 0 && !selectedChunk) {
        setSelectedChunk(json.chunks[0]);
      }
    } finally {
      setIngesting(false);
    }
  };

  const handleCopySelectedChunkJson = () => {
    if (!selectedChunk) return;
    const canonicalChunk = {
      document_id: selectedChunk.document_id,
      company: selectedChunk.company,
      title: selectedChunk.title,
      source_url: selectedChunk.source_url,
      source_type: selectedChunk.source_type,
      published_date: selectedChunk.published_date,
      author: selectedChunk.author,
      content: selectedChunk.content,
      technology_area: selectedChunk.technology_area,
      chunk_id: selectedChunk.chunk_id,
      embedding: selectedChunk.embedding,
      fetch_method: selectedChunk.fetch_method,
      mcp_tool_used: selectedChunk.mcp_tool_used,
    };
    navigator.clipboard.writeText(JSON.stringify(canonicalChunk, null, 2));
    setCopiedChunk(true);
    setTimeout(() => setCopiedChunk(false), 2000);
  };

  return (
    <div className="space-y-5">
      {/* Header Banner */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-2xs">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1.5 font-mono font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                ALLOYDB + MEDIUM MCP SERVER PREFETCH PIPELINE
              </span>
              <span className="text-slate-400">·</span>
              <span className="inline-flex items-center gap-1 font-mono text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded font-semibold">
                <Server className="w-3 h-3" />
                MCP: {data?.medium_mcp_config?.registry_url || "https://mcpmarket.com/server/medium-2"}
              </span>
              <span className="text-slate-400">·</span>
              <span className="font-mono text-slate-500 truncate max-w-md">
                {data?.alloydb_config?.engine || "Google Cloud AlloyDB for PostgreSQL"} (pgvector + alloydb_scann)
              </span>
            </div>

            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              AlloyDB Pre-Fetched Target Knowledge Database: Netflix ({data?.summary_metrics.total_documents_stored ?? 10} Documents · Focus:{" "}
              {data?.prefetch_config?.prefetch_focus_area || "recommendation"})
            </h2>

            <p className="text-xs text-slate-600 max-w-4xl leading-relaxed">
              Offline ingestion pipeline backed by{" "}
              <strong className="text-slate-900">Google Cloud AlloyDB for PostgreSQL (`pgvector` + `alloydb_scann`)</strong> with{" "}
              <strong className="text-blue-700">`text-embedding-004` (`vector(768)`)</strong> embeddings and configurable{" "}
              <span className="font-mono font-semibold text-slate-900">
                PREFETCH_DOCUMENT_COUNT={data?.prefetch_config?.prefetch_document_count ?? 10}
              </span>{" "}
              (<span className="font-mono">{data?.prefetch_config?.chunk_size_words ?? 180}</span>-word chunks with{" "}
              <span className="font-mono">{data?.prefetch_config?.chunk_overlap_words ?? 35}</span>-word overlap).
              Medium articles on <span className="font-mono text-slate-800">https://netflixtechblog.medium.com/</span> and{" "}
              <span className="font-mono text-slate-800">https://netflixtechblog.com/</span> are retrieved exclusively via the{" "}
              <strong className="text-indigo-700">Medium MCP Server (`https://mcpmarket.com/server/medium-2`)</strong>.
            </p>
          </div>

          {/* Ingestion Execution Controls */}
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => triggerPrefetch("incremental")}
              disabled={ingesting}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-800 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50 transition-colors cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${ingesting ? "animate-spin" : ""}`} />
              <span>Run Incremental AlloyDB Ingestion</span>
            </button>

            <button
              type="button"
              onClick={() => triggerPrefetch("initial")}
              disabled={ingesting}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-[#0B0F19] rounded-lg hover:bg-slate-800 disabled:opacity-50 transition-colors cursor-pointer"
            >
              <Play className="w-3.5 h-3.5" />
              <span>
                Re-Run Configured ({data?.prefetch_config?.prefetch_document_count ?? 10}-Doc) AlloyDB Prefetch
              </span>
            </button>
          </div>
        </div>

        {/* Pipeline Stage Flow Strip */}
        <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center gap-2 text-[11px] font-mono text-slate-600">
          <span className="px-2 py-1 bg-slate-100 rounded text-slate-800 font-semibold">
            1. PREFETCH_DOCUMENT_COUNT={data?.prefetch_config?.prefetch_document_count ?? 10} (Recommendation)
          </span>
          <span>→</span>
          <span className="px-2 py-1 bg-indigo-50 text-indigo-800 rounded font-semibold">
            2. Medium MCP Server (`mcpmarket.com/server/medium-2`)
          </span>
          <span>→</span>
          <span className="px-2 py-1 bg-slate-100 rounded text-slate-800 font-semibold">
            3. Clean Body & Preserve Code Blocks
          </span>
          <span>→</span>
          <span className="px-2 py-1 bg-slate-100 rounded text-slate-800 font-semibold">
            4. {data?.prefetch_config?.chunk_size_words ?? 180}w / {data?.prefetch_config?.chunk_overlap_words ?? 35}w Overlap Chunking
          </span>
          <span>→</span>
          <span className="px-2 py-1 bg-blue-50 text-blue-800 rounded font-semibold">
            5. `text-embedding-004` (`vector(768)`)
          </span>
          <span>→</span>
          <span className="px-2 py-1 bg-emerald-50 text-emerald-800 rounded font-semibold">
            6. AlloyDB (`documents` + `document_chunks` ScaNN)
          </span>
        </div>
      </section>

      {/* 4 KPI Cards */}
      {data && (
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
            <div className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              ALLOYDB `documents` STORED
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono tabular-nums text-slate-900">
                {data.summary_metrics.total_documents_stored}
              </span>
              <span className="text-xs text-slate-500">canonical docs</span>
            </div>
            <div className="text-[11px] text-slate-500">
              {data.summary_metrics.medium_mcp_documents_stored ?? 35} via Medium MCP Server ·{" "}
              {data.summary_metrics.direct_extractor_documents_stored ?? 17} via Direct Docs
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
            <div className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              ALLOYDB SCANN `document_chunks`
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono tabular-nums text-blue-600">
                {data.summary_metrics.total_chunks_stored}
              </span>
              <span className="text-xs text-blue-700 font-medium">
                vector({data.prefetch_config?.embedding_dimensions ?? 768}) chunks
              </span>
            </div>
            <div className="text-[11px] text-slate-500">
              `{data.prefetch_config?.embedding_model || "text-embedding-004"}` · {data.prefetch_config?.chunk_size_words ?? 180}w/{data.prefetch_config?.chunk_overlap_words ?? 35}w overlap
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
            <div className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              MEDIUM MCP ARTICLES INGESTED
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono tabular-nums text-indigo-700">
                {data.summary_metrics.medium_mcp_documents_stored ?? 35}
              </span>
              <span className="text-xs text-indigo-700 font-medium">via MCP JSON-RPC</span>
            </div>
            <div className="text-[11px] text-slate-500">
              `netflixtechblog.medium.com` & `netflixtechblog.com`
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
            <div className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              QUARANTINE `failed_documents`
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono tabular-nums text-amber-700">
                {data.summary_metrics.failed_documents_logged}
              </span>
              <span className="text-xs text-amber-800 font-medium">logged failures</span>
            </div>
            <div className="text-[11px] text-slate-500">
              {data.ingestion_runs?.[0]?.skipped_duplicates ?? 1} SHA-256 duplicate skipped
            </div>
          </div>
        </section>
      )}

      {/* Sub-navigation & Interactive Verification Triggers */}
      <section className="bg-white border border-slate-200 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs">
          <button
            type="button"
            onClick={() => setSubTab("chunks")}
            className={`px-3 py-1.5 rounded-md font-semibold transition-colors ${
              subTab === "chunks"
                ? "bg-white text-slate-900 shadow-2xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            AlloyDB Child `document_chunks` ({data?.chunks.length ?? 0})
          </button>
          <button
            type="button"
            onClick={() => setSubTab("documents")}
            className={`px-3 py-1.5 rounded-md font-semibold transition-colors ${
              subTab === "documents"
                ? "bg-white text-slate-900 shadow-2xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            AlloyDB Parent `documents` ({data?.documents.length ?? 0})
          </button>
          <button
            type="button"
            onClick={() => setSubTab("sources")}
            className={`px-3 py-1.5 rounded-md font-semibold transition-colors ${
              subTab === "sources"
                ? "bg-white text-slate-900 shadow-2xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Medium MCP Server & AlloyDB Schema
          </button>
          <button
            type="button"
            onClick={() => setSubTab("logs")}
            className={`px-3 py-1.5 rounded-md font-semibold transition-colors ${
              subTab === "logs"
                ? "bg-white text-slate-900 shadow-2xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Quarantine `failed_documents` ({data?.failed_documents.length ?? 0})
          </button>
        </div>

        {/* 1-Click Ingestion Edge-Case Verification Buttons */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <button
            type="button"
            onClick={() => {
              triggerPrefetch("incremental", {
                company: "Netflix",
                title: "Per-Title Encode Optimization (Duplicate Test)",
                source_url: "https://netflixtechblog.com/per-title-encode-optimization-7e99442b62a2",
                source_type: "technology_blog",
                published_date: "2015-12-14",
                author: "Aaron Cockcroft, Jan De Cock, Anne Aaron",
                raw_html_or_text:
                  "<p>At Netflix, we stream millions of hours of video every day across thousands of distinct device profiles. Traditional adaptive bitrate (ABR) streaming uses a fixed encoding ladder—mapping resolutions and bitrates statically regardless of content complexity.</p>",
              });
              setSubTab("logs");
            }}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-md font-medium transition-colors cursor-pointer"
          >
            <Copy className="w-3.5 h-3.5 text-blue-600" />
            <span>Test Duplicate Ingestion</span>
          </button>

          <button
            type="button"
            onClick={() => {
              triggerPrefetch("incremental", {
                company: "Netflix",
                title: "Arbitrary Unapproved Web Scrape Attempt",
                source_url: "https://random-unapproved-forum.example.com/netflix-rumors",
                source_type: "arbitrary_web",
                published_date: "2025-05-01",
                author: "Anonymous",
                raw_html_or_text:
                  "<p>This URL is not in APPROVED_SOURCE_CONFIGS and must be rejected and logged.</p>",
              });
              setSubTab("logs");
            }}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200 rounded-md font-medium transition-colors cursor-pointer"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
            <span>Test Unapproved Source Rejection</span>
          </button>
        </div>
      </section>

      {/* =====================================================================
          SUB-TAB 1: STORED CHUNKS & EXACT REQUIRED JSON SCHEMA INSPECTOR
         ===================================================================== */}
      {subTab === "chunks" && data && (
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
          {/* Left 7 Cols: Search, Tag Filter & Stored Chunks Table */}
          <div className="xl:col-span-7 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
            <div className="p-4 border-b border-slate-200 space-y-3">
              <div className="flex flex-col sm:flex-row gap-2.5">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    fetchStatus(searchQuery, selectedTag, selectedSourceType);
                  }}
                  className="relative flex-1 flex gap-2"
                >
                  <div className="relative flex-1">
                    <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search AlloyDB ScaNN vector chunks (e.g., Open Connect, LL-HLS, CMAF, convex hull, VMAF)..."
                      className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:bg-white"
                    />
                  </div>
                  <button
                    type="submit"
                    className="px-3 py-1.5 bg-[#0B0F19] text-white text-xs font-semibold rounded-md hover:bg-slate-800"
                  >
                    Search AlloyDB
                  </button>
                </form>
              </div>

              <div className="flex flex-wrap items-center gap-2 text-xs">
                <select
                  value={selectedTag}
                  onChange={(e) => {
                    setSelectedTag(e.target.value);
                    fetchStatus(searchQuery, e.target.value, selectedSourceType);
                  }}
                  className="px-2.5 py-1 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700"
                >
                  <option value="">All Candidate Technology Tags</option>
                  {data.approved_technology_taxonomy.map((t) => (
                    <option key={t} value={t}>
                      {t} ({data.summary_metrics.tag_distribution[t] || 0})
                    </option>
                  ))}
                </select>

                <select
                  value={selectedSourceType}
                  onChange={(e) => {
                    setSelectedSourceType(e.target.value);
                    fetchStatus(searchQuery, selectedTag, e.target.value);
                  }}
                  className="px-2.5 py-1 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700"
                >
                  <option value="">All Approved Source Types</option>
                  <option value="technology_blog">technology_blog (Medium MCP)</option>
                  <option value="open_connect_documentation">open_connect_documentation</option>
                  <option value="technical_paper">technical_paper</option>
                  <option value="engineering_documentation">engineering_documentation</option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto max-h-[640px] overflow-y-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead className="sticky top-0 z-10">
                  <tr className="bg-[#080C14] text-white font-mono text-[10px] uppercase">
                    <th className="py-3 px-4">CHUNK ID & INGESTION CHANNEL</th>
                    <th className="py-3 px-4">TITLE & CLEANED CONTENT</th>
                    <th className="py-3 px-4">SOURCE TYPE & DATE</th>
                    <th className="py-3 px-4">TECH AREA & TAGS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {data.chunks.map((chunk) => {
                    const isSelected = selectedChunk?.chunk_id === chunk.chunk_id;
                    const isMcp = chunk.fetch_method === "MEDIUM_MCP_SERVER";
                    return (
                      <tr
                        key={chunk.chunk_id}
                        onClick={() => setSelectedChunk(chunk)}
                        className={`cursor-pointer transition-colors ${
                          isSelected ? "bg-blue-50/60" : "hover:bg-slate-50"
                        }`}
                      >
                        <td className="py-3.5 px-4 align-top font-mono">
                          <div className="font-bold text-blue-700">{chunk.chunk_id}</div>
                          <div className="text-[10px] text-slate-500 mt-0.5">
                            {chunk.document_id}
                          </div>
                          <span
                            className={`inline-block mt-1 px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                              isMcp
                                ? "bg-indigo-50 text-indigo-700"
                                : "bg-slate-100 text-slate-700"
                            }`}
                          >
                            {isMcp ? "MEDIUM_MCP_SERVER" : "DIRECT_EXTRACTOR"}
                          </span>
                        </td>

                        <td className="py-3.5 px-4 align-top max-w-xs">
                          <div className="font-semibold text-slate-900 leading-snug">
                            {chunk.title}
                          </div>
                          <p className="text-slate-600 line-clamp-2 mt-1 leading-relaxed">
                            {chunk.content}
                          </p>
                        </td>

                        <td className="py-3.5 px-4 align-top whitespace-nowrap">
                          <div className="font-mono text-[11px] font-semibold text-slate-800">
                            {chunk.source_type}
                          </div>
                          <div className="font-mono text-[11px] text-slate-500 mt-0.5">
                            {chunk.published_date || "N/A"}
                          </div>
                        </td>

                        <td className="py-3.5 px-4 align-top">
                          <div className="font-mono text-[11px] font-bold text-emerald-800">
                            {chunk.technology_area || "null"}
                          </div>
                          <div className="text-[11px] text-slate-500 mt-0.5">
                            {(chunk.candidate_tags || []).join(" · ")}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right 5 Cols: Selected Chunk Required Schema & Provenance Inspector */}
          {selectedChunk && (
            <div className="xl:col-span-5 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs divide-y divide-slate-200">
              <div className="p-4 bg-[#0B0F19] text-white flex items-center justify-between">
                <div>
                  <div className="text-[10px] font-mono text-sky-400 uppercase font-bold">
                    ALLOYDB STORED CHUNK RECORD & PROVENANCE
                  </div>
                  <div className="text-sm font-mono font-bold mt-0.5">{selectedChunk.chunk_id}</div>
                </div>
                <button
                  type="button"
                  onClick={handleCopySelectedChunkJson}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded text-xs font-mono transition-colors cursor-pointer"
                >
                  {copiedChunk ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Chunk JSON</span>
                    </>
                  )}
                </button>
              </div>

              <div className="p-4 space-y-2.5 text-xs">
                <div>
                  <span className="font-semibold text-slate-800">Title:</span>{" "}
                  <span className="text-slate-900 font-medium">{selectedChunk.title}</span>
                </div>
                <div className="truncate">
                  <span className="font-semibold text-slate-800">Source URL:</span>{" "}
                  <a
                    href={selectedChunk.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-mono text-blue-600 hover:underline"
                  >
                    {selectedChunk.source_url}
                  </a>
                </div>
                <div className="grid grid-cols-2 gap-2 font-mono text-[11px] bg-slate-50 p-2.5 rounded border border-slate-200">
                  <div>
                    <span className="text-slate-400">fetch_method:</span>{" "}
                    <span className="text-indigo-700 font-semibold">
                      {selectedChunk.fetch_method || "MEDIUM_MCP_SERVER"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400">published_date:</span>{" "}
                    <span className="text-slate-900 font-semibold">
                      {selectedChunk.published_date || "null"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400">technology_area:</span>{" "}
                    <span className="text-emerald-700 font-semibold">
                      {selectedChunk.technology_area || "null"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400">text-embedding-004:</span>{" "}
                    <span className="text-slate-900 font-semibold">
                      vector({selectedChunk.embedding.length}) (ScaNN)
                    </span>
                  </div>
                </div>
                <div>
                  <span className="font-semibold text-slate-800">Candidate Technology Tags:</span>{" "}
                  <span className="text-slate-600">
                    {(selectedChunk.candidate_tags || []).join(" · ")}
                  </span>
                </div>
              </div>

              {/* Exact Required Stored Record JSON Preview */}
              <div className="p-4 space-y-2">
                <div className="text-xs font-semibold text-slate-800">
                  AlloyDB Stored Record Schema:
                </div>
                <pre className="p-3.5 bg-slate-950 text-slate-100 rounded-lg font-mono text-[11px] overflow-x-auto max-h-[380px] leading-relaxed">
                  {JSON.stringify(
                    {
                      document_id: selectedChunk.document_id,
                      company: selectedChunk.company,
                      title: selectedChunk.title,
                      source_url: selectedChunk.source_url,
                      source_type: selectedChunk.source_type,
                      published_date: selectedChunk.published_date,
                      author: selectedChunk.author,
                      content: selectedChunk.content,
                      technology_area: selectedChunk.technology_area,
                      chunk_id: selectedChunk.chunk_id,
                      embedding: selectedChunk.embedding,
                      fetch_method: selectedChunk.fetch_method,
                      mcp_tool_used: selectedChunk.mcp_tool_used,
                    },
                    null,
                    2
                  )}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}

      {/* =====================================================================
          SUB-TAB 1.5: PARENT `documents` TABLE (FULL UNTRUNCATED ARTICLES & SHA-256)
         ===================================================================== */}
      {subTab === "documents" && data && (
        <section className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
          <div className="p-4 border-b border-slate-200 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                AlloyDB Parent Table: `documents` ({data.documents.length} Canonical Netflix Documents)
              </h3>
              <p className="text-xs text-slate-500">
                Preserves full cleaned article prose, headings, and code blocks in{" "}
                <span className="font-mono">documents.full_content</span> alongside{" "}
                <span className="font-mono">fetch_method</span> (`MEDIUM_MCP_SERVER` vs `DIRECT_DOCUMENT_EXTRACTOR`).
              </p>
            </div>
          </div>
          <div className="divide-y divide-slate-200 max-h-[700px] overflow-y-auto">
            {data.documents.map((doc) => {
              const isMcp = doc.fetch_method === "MEDIUM_MCP_SERVER";
              return (
                <div key={doc.document_id} className="p-4 space-y-2.5 hover:bg-slate-50/60">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-0.5">
                      <div className="flex flex-wrap items-center gap-2 text-xs">
                        <span className="font-mono font-bold text-blue-700">{doc.document_id}</span>
                        <span className="text-slate-300">·</span>
                        <span
                          className={`font-mono text-[11px] font-bold px-2 py-0.5 rounded ${
                            isMcp
                              ? "bg-indigo-50 text-indigo-700"
                              : "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {doc.fetch_method || "MEDIUM_MCP_SERVER"}
                        </span>
                        <span className="text-slate-300">·</span>
                        <span className="font-mono text-slate-600">{doc.source_type}</span>
                        <span className="text-slate-300">·</span>
                        <span className="font-mono text-slate-500">
                          {doc.published_date || "null"}
                        </span>
                        <span className="text-slate-300">·</span>
                        <span className="font-mono text-emerald-700 font-semibold">
                          {doc.chunk_count} child chunks
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-900">{doc.title}</h4>
                      <div className="text-[11px] text-slate-500">
                        Author: {doc.author || "null"} · Primary Tech Area:{" "}
                        <span className="font-mono font-semibold text-slate-800">
                          {doc.technology_area || "null"}
                        </span>{" "}
                        · Tool: <span className="font-mono text-indigo-700">{doc.mcp_tool_used}</span>{" "}
                        · SHA-256 <span className="font-mono">{doc.content_hash.slice(0, 12)}...</span>
                      </div>
                    </div>
                    <a
                      href={doc.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-xs font-mono text-blue-600 hover:underline shrink-0"
                    >
                      <span>{doc.source_url}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <pre className="p-3 bg-slate-950 text-slate-100 rounded-lg font-mono text-[11px] whitespace-pre-wrap leading-relaxed max-h-44 overflow-y-auto">
                    {doc.full_content || doc.content}
                  </pre>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* =====================================================================
          SUB-TAB 2: MEDIUM MCP SERVER & ALLOYDB SCANN SCHEMA
         ===================================================================== */}
      {subTab === "sources" && data && (
        <div className="space-y-5">
          {/* Medium MCP Server & AlloyDB Architecture Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            <div className="lg:col-span-6 bg-white border border-slate-200 rounded-xl p-5 space-y-3 shadow-2xs">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono font-bold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded">
                  MEDIUM MCP SERVER (JSON-RPC 2.0)
                </span>
                <span className="font-mono text-xs text-emerald-700 font-semibold">
                  {data.medium_mcp_config?.transport_status || data.medium_mcp_config?.protocol_version}
                </span>
              </div>
              <h3 className="text-base font-bold text-slate-900">
                {data.medium_mcp_config?.server_name || "medium-mcp-server (medium-2)"}
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Registry:{" "}
                <a
                  href={data.medium_mcp_config?.registry_url || "https://mcpmarket.com/server/medium-2"}
                  target="_blank"
                  rel="noreferrer"
                  className="font-mono text-blue-600 hover:underline"
                >
                  {data.medium_mcp_config?.registry_url || "https://mcpmarket.com/server/medium-2"}
                </a>
                . Instead of scraping Medium URLs directly, all articles under{" "}
                <span className="font-mono">https://netflixtechblog.medium.com/</span> and{" "}
                <span className="font-mono">https://netflixtechblog.com/</span> are retrieved via the local MCP server.
              </p>

              {/* Environment Variables Box */}
              <div className="p-3 bg-slate-950 text-slate-100 rounded-lg font-mono text-[11px] space-y-1.5">
                <div className="flex items-center justify-between text-[10px] text-slate-400 uppercase tracking-wider">
                  <span>Configured Environment Variables (.env)</span>
                  <button
                    type="button"
                    onClick={testLocalMcpServer}
                    disabled={testingMcp}
                    className="px-2 py-0.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-[10px] font-sans font-semibold cursor-pointer"
                  >
                    {testingMcp ? "Calling Local MCP..." : "Ping Local MCP Server (JSON-RPC)"}
                  </button>
                </div>
                <div className="truncate">
                  <span className="text-emerald-400">MEDIUM_MCP_SERVER_URL</span>=
                  <span className="text-amber-200">
                    "{data.medium_mcp_config?.server_url || "http://127.0.0.1:3000/api/mcp/medium"}"
                  </span>
                </div>
                <div className="truncate">
                  <span className="text-emerald-400">MEDIUM_MCP_SERVER_CMD</span>=
                  <span className="text-amber-200">
                    "{data.medium_mcp_config?.server_cmd || "python3 -m target_prefetch.medium_mcp_server --stdio"}"
                  </span>
                </div>
              </div>

              {mcpRpcResult && (
                <pre className="p-2.5 bg-slate-900 text-emerald-300 rounded-lg font-mono text-[10px] overflow-x-auto max-h-40 leading-relaxed">
                  {JSON.stringify(mcpRpcResult, null, 2)}
                </pre>
              )}

              <div className="space-y-2 pt-1">
                {data.medium_mcp_config?.tools.map((t) => (
                  <div
                    key={t.name}
                    className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                  >
                    <div className="font-mono font-bold text-indigo-700">{t.name}</div>
                    <div className="text-slate-600 mt-0.5">{t.description}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="lg:col-span-6 bg-white border border-slate-200 rounded-xl p-5 space-y-3 shadow-2xs">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono font-bold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded">
                  ALLOYDB FOR POSTGRESQL + SCANN VECTOR INDEX
                </span>
                <span className="font-mono text-xs text-slate-500">
                  {data.alloydb_config?.connection_mode}
                </span>
              </div>
              <h3 className="text-base font-bold text-slate-900">
                {data.alloydb_config?.engine || "Google Cloud AlloyDB for PostgreSQL"}
              </h3>
              <div className="text-xs font-mono text-slate-600 truncate">
                URI: {data.alloydb_config?.instance_uri}
              </div>
              <pre className="p-3 bg-slate-950 text-slate-100 rounded-lg font-mono text-[10px] overflow-x-auto max-h-56 leading-relaxed">
                {data.alloydb_config?.ddl_preview}
              </pre>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            <div className="lg:col-span-7 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
              <div className="p-4 border-b border-slate-200">
                <h3 className="text-sm font-bold text-slate-900">
                  Explicitly Configured Public Netflix Sources Allowlist
                </h3>
                <p className="text-xs text-slate-500">
                  Only documents matching these configured public source prefixes are permitted into AlloyDB.
                </p>
              </div>
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-[#080C14] text-white font-mono text-[10px]">
                    <th className="py-2.5 px-4">SOURCE NAME</th>
                    <th className="py-2.5 px-4">URL PREFIX</th>
                    <th className="py-2.5 px-4">INGESTION PROTOCOL</th>
                    <th className="py-2.5 px-4">STATUS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {data.configured_sources.map((src) => (
                    <tr key={src.source_id} className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-semibold text-slate-900">{src.name}</td>
                      <td className="py-3 px-4 font-mono text-blue-700">{src.url_prefix}</td>
                      <td className="py-3 px-4 font-mono text-[11px] text-indigo-700 font-semibold">
                        {src.ingestion_protocol || src.source_type}
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] font-bold text-emerald-700">
                        {src.approval_status}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-5 space-y-3 shadow-2xs">
              <h3 className="text-sm font-bold text-slate-900">
                Candidate Technology Tag Taxonomy & Document Coverage
              </h3>
              <p className="text-xs text-slate-500">
                Candidate metadata tags extracted during prefetch; refined by the Target Analysis Agent.
              </p>
              <div className="divide-y divide-slate-100 text-xs">
                {data.approved_technology_taxonomy.map((tag) => {
                  const count = data.summary_metrics.tag_distribution[tag] || 0;
                  return (
                    <div
                      key={tag}
                      onClick={() => {
                        setSelectedTag(tag);
                        setSubTab("chunks");
                        fetchStatus(searchQuery, tag, selectedSourceType);
                      }}
                      className="py-2 flex items-center justify-between cursor-pointer hover:text-blue-600"
                    >
                      <span className="font-mono font-medium text-slate-800">{tag}</span>
                      <span className="font-mono font-bold text-slate-900">{count} docs</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          SUB-TAB 3: DUPLICATE DETECTION & FAILED-DOCUMENT LOGS
         ===================================================================== */}
      {subTab === "logs" && data && (
        <div className="space-y-5">
          {/* Failed-Document Log Table */}
          <section className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
            <div className="p-4 border-b border-slate-200">
              <h3 className="text-sm font-bold text-slate-900">
                AlloyDB Quarantine Log (`failed_documents` table)
              </h3>
              <p className="text-xs text-slate-500">
                Records unapproved arbitrary web URLs, empty/corrupt documents, or fetch errors without polluting the AlloyDB knowledge base.
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-[#080C14] text-white font-mono text-[10px]">
                    <th className="py-2.5 px-4">LOGGED AT</th>
                    <th className="py-2.5 px-4">SOURCE URL</th>
                    <th className="py-2.5 px-4">TITLE</th>
                    <th className="py-2.5 px-4">ERROR CODE</th>
                    <th className="py-2.5 px-4">DIAGNOSTIC REASON</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {data.failed_documents.map((f) => (
                    <tr key={f.id} className="hover:bg-slate-50">
                      <td className="py-2.5 px-4 font-mono text-slate-500 whitespace-nowrap">
                        {f.logged_at}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-red-700">{f.source_url}</td>
                      <td className="py-2.5 px-4 font-medium text-slate-900">{f.title}</td>
                      <td className="py-2.5 px-4 font-mono font-bold text-amber-800">
                        {f.error_code}
                      </td>
                      <td className="py-2.5 px-4 text-slate-600">{f.error_message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Latest Ingestion Run Item-by-Item Trace */}
          {data.ingestion_runs?.[0] && (
            <section className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
              <div className="p-4 border-b border-slate-200 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    Latest AlloyDB Prefetch Run Trace ({data.ingestion_runs[0].run_id})
                  </h3>
                  <p className="text-xs text-slate-500">
                    Mode: <span className="font-mono font-semibold">{data.ingestion_runs[0].mode}</span> ·
                    Inserted Docs: {data.ingestion_runs[0].inserted_documents} · Inserted Chunks:{" "}
                    {data.ingestion_runs[0].inserted_chunks} · Skipped Duplicates:{" "}
                    {data.ingestion_runs[0].skipped_duplicates} · Failed:{" "}
                    {data.ingestion_runs[0].failed_documents_count}
                  </p>
                </div>
              </div>
              <div className="divide-y divide-slate-200 text-xs max-h-[500px] overflow-y-auto">
                {data.ingestion_runs[0].run_log.map((item, idx) => (
                  <div key={idx} className="p-3.5 flex items-center justify-between gap-4">
                    <div className="space-y-0.5 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-900 truncate">{item.title}</span>
                        {item.fetch_method && (
                          <span
                            className={`font-mono text-[10px] font-bold px-1.5 py-0.5 rounded ${
                              item.fetch_method === "MEDIUM_MCP_SERVER"
                                ? "bg-indigo-50 text-indigo-700"
                                : "bg-slate-100 text-slate-700"
                            }`}
                          >
                            {item.fetch_method}
                          </span>
                        )}
                      </div>
                      <div className="font-mono text-[11px] text-slate-500 truncate">
                        {item.source_url}
                      </div>
                      {item.detail && (
                        <div className="text-[11px] text-slate-600">{item.detail}</div>
                      )}
                    </div>
                    <span
                      className={`font-mono text-[11px] font-bold px-2.5 py-1 rounded shrink-0 ${
                        item.status === "INGESTED"
                          ? "bg-emerald-50 text-emerald-800"
                          : item.status.startsWith("SKIPPED")
                          ? "bg-blue-50 text-blue-800"
                          : "bg-red-50 text-red-800"
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
