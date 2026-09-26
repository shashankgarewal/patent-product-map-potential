import React, { useState, useEffect } from "react";
import {
  Database,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Copy,
  Check,
  Play,
  PlusCircle,
  ShieldAlert,
  Layers,
  FileText,
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
            <div className="flex items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1.5 font-mono font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                OFFLINE TARGET KNOWLEDGE PREFETCH PIPELINE
              </span>
              <span className="text-slate-400">·</span>
              <span className="font-mono text-slate-500">
                DB: {data?.database_path || "target_prefetch/target_knowledge.sqlite"}
              </span>
            </div>

            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              Pre-Fetched Target Knowledge Database: Netflix
            </h2>

            <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
              Offline ingestion script and SQLite vector/chunk store completely decoupled from the runtime Target Retrieval Agent.
              The runtime application never crawls the web or Medium/blog sources; all target-company documents are pre-fetched from{" "}
              <strong className="text-slate-900">explicitly configured public Netflix sources</strong>, cleaned, tagged, chunked, embedded, and deduplicated via SHA-256 content hashes.
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
              <span>Run Incremental Ingestion</span>
            </button>

            <button
              type="button"
              onClick={() => triggerPrefetch("initial")}
              disabled={ingesting}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-[#0B0F19] rounded-lg hover:bg-slate-800 disabled:opacity-50 transition-colors cursor-pointer"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Re-Run Initial Prefetch</span>
            </button>
          </div>
        </div>

        {/* Pipeline Stage Flow Strip */}
        <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center gap-2 text-[11px] font-mono text-slate-600">
          <span className="px-2 py-1 bg-slate-100 rounded text-slate-800 font-semibold">
            1. Approved Source Allowlist
          </span>
          <span>→</span>
          <span className="px-2 py-1 bg-slate-100 rounded text-slate-800 font-semibold">
            2. Fetch & Clean HTML
          </span>
          <span>→</span>
          <span className="px-2 py-1 bg-slate-100 rounded text-slate-800 font-semibold">
            3. SHA-256 Duplicate Check
          </span>
          <span>→</span>
          <span className="px-2 py-1 bg-slate-100 rounded text-slate-800 font-semibold">
            4. Metadata & Tech Tags
          </span>
          <span>→</span>
          <span className="px-2 py-1 bg-slate-100 rounded text-slate-800 font-semibold">
            5. Semantic Chunking & 32-d Embedding
          </span>
          <span>→</span>
          <span className="px-2 py-1 bg-emerald-50 text-emerald-800 rounded font-semibold">
            6. SQLite Knowledge Store
          </span>
        </div>
      </section>

      {/* 4 KPI Cards */}
      {data && (
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
            <div className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              INGESTED SOURCE DOCUMENTS
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono tabular-nums text-slate-900">
                {data.summary_metrics.total_documents_stored}
              </span>
              <span className="text-xs text-slate-500">canonical docs</span>
            </div>
            <div className="text-[11px] text-slate-500">
              Across {data.configured_sources.length} explicitly approved Netflix domains
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
            <div className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              INDEXED & EMBEDDED CHUNKS
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono tabular-nums text-blue-600">
                {data.summary_metrics.total_chunks_stored}
              </span>
              <span className="text-xs text-blue-700 font-medium">searchable chunks</span>
            </div>
            <div className="text-[11px] text-slate-500">
              Each chunk stores 32-d vector embedding & provenance
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
            <div className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              SKIPPED DUPLICATES (LATEST RUN)
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono tabular-nums text-emerald-700">
                {data.ingestion_runs?.[0]?.skipped_duplicates ?? 0}
              </span>
              <span className="text-xs text-slate-500">deduplicated</span>
            </div>
            <div className="text-[11px] text-slate-500">
              Via deterministic document_id & SHA-256 content_hash
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1.5 shadow-2xs">
            <div className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">
              FAILED / REJECTED SOURCES LOGGED
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-mono tabular-nums text-amber-700">
                {data.summary_metrics.failed_documents_logged}
              </span>
              <span className="text-xs text-amber-800 font-medium">logged failures</span>
            </div>
            <div className="text-[11px] text-slate-500">
              Unapproved web domains & empty docs quarantined
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
            Child `document_chunks` ({data?.chunks.length ?? 0})
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
            Parent `documents` ({data?.documents.length ?? 0})
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
            Approved Sources & Tag Taxonomy
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
                      placeholder="Search pre-fetched Netflix chunks (e.g., Open Connect, BGP, convex hull, VMAF)..."
                      className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:bg-white"
                    />
                  </div>
                  <button
                    type="submit"
                    className="px-3 py-1.5 bg-[#0B0F19] text-white text-xs font-semibold rounded-md hover:bg-slate-800"
                  >
                    Search DB
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
                  <option value="technology_blog">technology_blog</option>
                  <option value="open_connect_documentation">open_connect_documentation</option>
                  <option value="technical_paper">technical_paper</option>
                  <option value="engineering_documentation">engineering_documentation</option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-[#080C14] text-white font-mono text-[10px] uppercase">
                    <th className="py-3 px-4">CHUNK ID & DOCUMENT ID</th>
                    <th className="py-3 px-4">TITLE & CLEANED CONTENT</th>
                    <th className="py-3 px-4">SOURCE TYPE & DATE</th>
                    <th className="py-3 px-4">TECH AREA & TAGS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {data.chunks.map((chunk) => {
                    const isSelected = selectedChunk?.chunk_id === chunk.chunk_id;
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
                          <div className="text-[11px] text-slate-500 mt-0.5">
                            {chunk.document_id}
                          </div>
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
                    STORED CHUNK RECORD & PROVENANCE
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
                    <span className="text-slate-400">source_type:</span>{" "}
                    <span className="text-slate-900 font-semibold">{selectedChunk.source_type}</span>
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
                    <span className="text-slate-400">embedding dims:</span>{" "}
                    <span className="text-slate-900 font-semibold">
                      {selectedChunk.embedding.length} floats
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
                  Stored Database Record Schema:
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
                Parent Table: `documents` (Full Untruncated Article Bodies & SHA-256 Hashes)
              </h3>
              <p className="text-xs text-slate-500">
                Preserves full cleaned article prose, headings, and code blocks in{" "}
                <span className="font-mono">documents.full_content</span> while child{" "}
                <span className="font-mono">document_chunks</span> reference{" "}
                <span className="font-mono">documents(document_id)</span>.
              </p>
            </div>
          </div>
          <div className="divide-y divide-slate-200">
            {data.documents.map((doc) => (
              <div key={doc.document_id} className="p-4 space-y-2.5 hover:bg-slate-50/60">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="font-mono font-bold text-blue-700">{doc.document_id}</span>
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
                      · SHA-256 <span className="font-mono">{doc.content_hash.slice(0, 16)}...</span>
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
                <pre className="p-3 bg-slate-950 text-slate-100 rounded-lg font-mono text-[11px] whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                  {(doc as any).full_content || doc.content}
                </pre>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* =====================================================================
          SUB-TAB 2: CONFIGURED NETFLIX SOURCES & TECHNOLOGY TAXONOMY
         ===================================================================== */}
      {subTab === "sources" && data && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-7 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
            <div className="p-4 border-b border-slate-200">
              <h3 className="text-sm font-bold text-slate-900">
                Explicitly Configured Public Netflix Sources Allowlist
              </h3>
              <p className="text-xs text-slate-500">
                Only documents matching these configured public source prefixes are permitted into the knowledge base.
              </p>
            </div>
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-[#080C14] text-white font-mono text-[10px]">
                  <th className="py-2.5 px-4">SOURCE NAME</th>
                  <th className="py-2.5 px-4">URL PREFIX</th>
                  <th className="py-2.5 px-4">SOURCE TYPE</th>
                  <th className="py-2.5 px-4">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {data.configured_sources.map((src) => (
                  <tr key={src.source_id} className="hover:bg-slate-50">
                    <td className="py-3 px-4 font-semibold text-slate-900">{src.name}</td>
                    <td className="py-3 px-4 font-mono text-blue-700">{src.url_prefix}</td>
                    <td className="py-3 px-4 font-mono text-slate-600">{src.source_type}</td>
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
              Candidate Technology Tag Taxonomy & Chunk Coverage
            </h3>
            <p className="text-xs text-slate-500">
              Candidate metadata tags extracted during prefetch; can later be refined by the Target Analysis Agent.
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
                    <span className="font-mono font-bold text-slate-900">{count} chunks</span>
                  </div>
                );
              })}
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
                Failed & Rejected Document Log (`failed_documents` table)
              </h3>
              <p className="text-xs text-slate-500">
                Records unapproved arbitrary web URLs, empty/corrupt documents, or fetch errors without polluting the knowledge base.
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
                    Latest Prefetch Run Trace ({data.ingestion_runs[0].run_id})
                  </h3>
                  <p className="text-xs text-slate-500">
                    Mode: <span className="font-mono font-semibold">{data.ingestion_runs[0].mode}</span> ·
                    Inserted Docs: {data.ingestion_runs[0].inserted_documents} · Skipped Duplicates:{" "}
                    {data.ingestion_runs[0].skipped_duplicates} · Failed:{" "}
                    {data.ingestion_runs[0].failed_documents_count}
                  </p>
                </div>
              </div>
              <div className="divide-y divide-slate-200 text-xs">
                {data.ingestion_runs[0].run_log.map((item, idx) => (
                  <div key={idx} className="p-3.5 flex items-center justify-between gap-4">
                    <div className="space-y-0.5 min-w-0">
                      <div className="font-semibold text-slate-900 truncate">{item.title}</div>
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
                          : item.status === "SKIPPED_DUPLICATE"
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
