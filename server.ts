import express from "express";
import { createServer as createViteServer } from "vite";
import { execFile } from "child_process";
import { promisify } from "util";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";
import { GoogleGenAI, Type } from "@google/genai";

dotenv.config();

// Ensure Local Medium MCP Server environment variables are configured
process.env.MEDIUM_MCP_SERVER_URL =
  process.env.MEDIUM_MCP_SERVER_URL || "http://127.0.0.1:3000/api/mcp/medium";
process.env.MEDIUM_MCP_SERVER_CMD =
  process.env.MEDIUM_MCP_SERVER_CMD || "python3 -m target_prefetch.medium_mcp_server --stdio";

const execFileAsync = promisify(execFile);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function runPythonMediumMcpRpc(rpcPayload: any): Promise<any> {
  const { stdout } = await execFileAsync(
    "python3",
    ["-m", "target_prefetch.medium_mcp_server", "--rpc", JSON.stringify(rpcPayload)],
    {
      cwd: __dirname,
      timeout: 15000,
      maxBuffer: 10 * 1024 * 1024,
      env: { ...process.env },
    }
  );
  return JSON.parse(stdout.trim());
}

// Initialize server-side Gemini client with mandatory User-Agent header
function getGenAIClient(): GoogleGenAI | null {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey || apiKey === "MY_GEMINI_API_KEY") {
    return null;
  }
  return new GoogleGenAI({
    apiKey,
    httpOptions: {
      headers: {
        "User-Agent": "aistudio-build",
      },
    },
  });
}

async function runPythonAdkCli(args: string[]): Promise<any> {
  const { stdout } = await execFileAsync("python3", ["-m", "adk_pipeline.cli", ...args], {
    cwd: __dirname,
    timeout: 60000,
    maxBuffer: 50 * 1024 * 1024,
  });
  return JSON.parse(stdout.trim());
}

async function runPythonTargetPrefetchCli(args: string[]): Promise<any> {
  const { stdout } = await execFileAsync("python3", ["-m", "target_prefetch.cli", ...args], {
    cwd: __dirname,
    timeout: 60000,
    maxBuffer: 50 * 1024 * 1024,
  });
  return JSON.parse(stdout.trim());
}

async function runPythonTargetAgentCli(args: string[]): Promise<any> {
  const { stdout } = await execFileAsync("python3", ["-m", "target_agent.cli", ...args], {
    cwd: __dirname,
    timeout: 60000,
    maxBuffer: 50 * 1024 * 1024,
  });
  return JSON.parse(stdout.trim());
}

async function runPythonMatchingAgentCli(args: string[]): Promise<any> {
  const { stdout } = await execFileAsync("python3", ["-m", "matching_agent.cli", ...args], {
    cwd: __dirname,
    timeout: 60000,
    maxBuffer: 50 * 1024 * 1024,
  });
  return JSON.parse(stdout.trim());
}

async function enrichWithMatchingAndCommercialAgent(matchingResult: any): Promise<any> {
  const ai = getGenAIClient();
  if (
    !ai ||
    matchingResult.matching_status !== "SUCCESS" ||
    !Array.isArray(matchingResult.ranked_matches) ||
    matchingResult.ranked_matches.length === 0
  ) {
    return matchingResult;
  }

  const compactMatches = matchingResult.ranked_matches.slice(0, 10).map((m: any) => ({
    patent_number: m.patent_number,
    patent_title: m.patent_title,
    patent_description: m.patent_description,
    patent_status: m.patent_status,
    estimated_remaining_years: m.estimated_remaining_patent_life?.years_remaining,
    target_product_or_service: m.target_product_or_service,
    target_technology: m.target_technology,
    technical_overlap_level: m.technical_overlap?.overlap_level,
    technical_relevance_score: m.technical_overlap?.technical_relevance_score,
    shared_technical_mechanisms: m.technical_overlap?.shared_technical_mechanisms || [],
    claim_element_counts: m.technical_overlap?.claim_element_counts,
    supporting_evidence_excerpts: (m.supporting_evidence || []).map((ev: any) => ({
      source_title: ev.source_title,
      source_url: ev.source_url,
      verbatim_text: ev.text,
    })),
    commercial_signal_tier: m.potential_monetary_opportunity?.signal_tier,
    commercial_opportunity_score: m.potential_monetary_opportunity?.commercial_opportunity_score,
    strategic_role: m.potential_monetary_opportunity?.strategic_role,
    consolidated_company_revenue: m.potential_monetary_opportunity?.consolidated_company_revenue,
    product_level_revenue_note: m.potential_monetary_opportunity?.product_level_revenue_note,
    subscriber_or_adoption_scale: m.potential_monetary_opportunity?.subscriber_or_adoption_scale,
    investigation_priority_tier: m.investigation_priority?.priority_tier,
  }));

  const systemInstruction = `You are the Google ADK Patent–Target Matching and Commercial Opportunity Agent (technical_matching_agent + commercial_opportunity_agent + investigation_priority_agent).
Your objective is to answer: "Which patent–target technology relationships appear important enough to deserve deeper technical, legal, and commercial investigation?"

CRITICAL RULES:
1. Keep TECHNICAL RELEVANCE (Part 1) and COMMERCIAL OPPORTUNITY (Part 2) strictly distinct.
2. NEVER state or imply that legal patent infringement has been established. Always use screening terminology such as: "potential technical overlap", "candidate for investigation", "potentially relevant", "evidence identified", and "requires expert/legal review".
3. NEVER fabricate target product capabilities, patent facts, or product-level revenue. When product-level revenue is not broken out in SEC Form 10-K filings (e.g. Netflix single consolidated streaming segment), explicitly note that product-level revenue is not publicly disclosed.
4. Cite exact source titles from 'supporting_evidence_excerpts' when explaining technical overlap.`;

  const prompt = `Client Company: ${matchingResult.client_company}
Target Company: ${matchingResult.target_company}
Technology Area: ${matchingResult.technology_area || "General"}

Synthesize concise, evidence-grounded Part 1 (technical_overlap_explanation), Part 2 (monetary_opportunity_rationale), and Part 3 (investigation_recommendation) narratives for each candidate relationship below:
${JSON.stringify(compactMatches, null, 2)}`;

  try {
    const response = await ai.models.generateContent({
      model: "gemini-3.8-flash",
      contents: prompt,
      config: {
        systemInstruction,
        temperature: 0.1,
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            enriched_relationships: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  patent_number: { type: Type.STRING },
                  technical_overlap_explanation: { type: Type.STRING },
                  monetary_opportunity_rationale: { type: Type.STRING },
                  investigation_recommendation: { type: Type.STRING },
                },
                required: [
                  "patent_number",
                  "technical_overlap_explanation",
                  "monetary_opportunity_rationale",
                  "investigation_recommendation",
                ],
              },
            },
          },
          required: ["enriched_relationships"],
        },
      },
    });

    const rawText = response.text;
    if (rawText) {
      const parsed = JSON.parse(rawText.trim());
      const byPub: Record<string, any> = {};
      for (const item of parsed.enriched_relationships || []) {
        if (item?.patent_number) {
          byPub[item.patent_number] = item;
        }
      }

      const sanitizeLegal = (txt: string) =>
        txt.replace(
          /\b(infringes|infringed|infringement is established|proves infringement|constitutes infringement)\b/gi,
          "exhibits potential technical overlap"
        );

      for (const row of matchingResult.ranked_matches) {
        const aiRow = byPub[row.patent_number];
        if (!aiRow) continue;
        if (aiRow.technical_overlap_explanation) {
          row.technical_overlap.summary = sanitizeLegal(aiRow.technical_overlap_explanation);
        }
        if (aiRow.monetary_opportunity_rationale) {
          row.potential_monetary_opportunity.rationale = sanitizeLegal(
            aiRow.monetary_opportunity_rationale
          );
        }
        if (aiRow.investigation_recommendation) {
          row.investigation_priority.rationale = sanitizeLegal(aiRow.investigation_recommendation);
        }
      }

      if (matchingResult.canonical_output?.ranked_patent_product_matches) {
        for (const cRow of matchingResult.canonical_output.ranked_patent_product_matches) {
          const aiRow = byPub[cRow.patent_number];
          if (!aiRow) continue;
          if (aiRow.technical_overlap_explanation) {
            cRow.technical_overlap.explanation = sanitizeLegal(aiRow.technical_overlap_explanation);
          }
          if (aiRow.monetary_opportunity_rationale) {
            cRow.potential_monetary_opportunity.rationale = sanitizeLegal(
              aiRow.monetary_opportunity_rationale
            );
          }
          if (aiRow.investigation_recommendation) {
            cRow.investigation_priority.recommendation = sanitizeLegal(
              aiRow.investigation_recommendation
            );
          }
        }
      }

      if (matchingResult.adk_architecture?.agent_trace) {
        for (const step of matchingResult.adk_architecture.agent_trace) {
          if (step.agent === "technical_matching_agent" || step.agent === "commercial_opportunity_agent") {
            step.status = "COMPLETED_VIA_GEMINI";
          }
        }
      }
    }
  } catch (_err) {
    // Keep deterministic evidence-backed explanations if LLM call fails
  }

  return matchingResult;
}

async function enrichWithTargetAnalysisAgent(
  targetResult: any,
  clientPatentContext: any[]
): Promise<any> {
  const ai = getGenAIClient();
  if (
    !ai ||
    targetResult.evidence_status !== "sufficient" ||
    !Array.isArray(targetResult.retrieved_chunks) ||
    targetResult.retrieved_chunks.length === 0
  ) {
    return targetResult;
  }

  const chunkContext = targetResult.retrieved_chunks.map((c: any) => ({
    chunk_id: c.chunk_id,
    source_title: c.title,
    source_url: c.source_url,
    source_type: c.source_type,
    published_date: c.published_date,
    content_verbatim: c.content,
    matched_queries: c.matched_queries || [],
  }));

  const systemInstruction = `You are the target_analysis_agent in a Google ADK Target Retrieval & Analysis Pipeline.
You answer: "What publicly documented technologies/capabilities of this target company are relevant to the client's patent technology?"
You NEVER answer: "Does the target company infringe the patent?"

CRITICAL RULES:
1. Reason ONLY over the provided 'retrieved_chunks' from the pre-fetched Target Company Knowledge Database.
2. Do not infer a product capability merely because a patent and target company share similar terminology. Require explicit supporting evidence from 'retrieved_chunks'.
3. Every 'supporting_evidence' entry MUST cite an exact 'chunk_id' from 'retrieved_chunks' so its verbatim text, source_title, and source_url are preserved without alteration.
4. Never state or imply legal infringement conclusions.`;

  const prompt = `Target Company: ${targetResult.target_company}
Requested Technology Area: ${targetResult.technology_area || "General"}
Client Patent Context:
${JSON.stringify(clientPatentContext || [], null, 2)}

Retrieved Evidence Chunks from Pre-Fetched Target Knowledge Database:
${JSON.stringify(chunkContext, null, 2)}

Group the relevant evidence into documented target technology areas, specific products/services (where supported by the evidence), concrete technical capabilities, and cite the supporting chunk_ids.`;

  try {
    const response = await ai.models.generateContent({
      model: "gemini-3.8-flash",
      contents: prompt,
      config: {
        systemInstruction,
        temperature: 0.1,
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            technology_areas: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  technology: { type: Type.STRING },
                  product_or_service: { type: Type.STRING },
                  technical_capabilities: {
                    type: Type.ARRAY,
                    items: { type: Type.STRING },
                  },
                  relevant_technical_concepts: {
                    type: Type.ARRAY,
                    items: { type: Type.STRING },
                  },
                  supporting_chunk_ids: {
                    type: Type.ARRAY,
                    items: { type: Type.STRING },
                  },
                },
                required: [
                  "technology",
                  "product_or_service",
                  "technical_capabilities",
                  "relevant_technical_concepts",
                  "supporting_chunk_ids",
                ],
              },
            },
          },
          required: ["technology_areas"],
        },
      },
    });

    const rawText = response.text;
    if (rawText) {
      const parsed = JSON.parse(rawText.trim());
      const chunkById: Record<string, any> = {};
      for (const ch of targetResult.retrieved_chunks) {
        chunkById[ch.chunk_id] = ch;
      }

      const enrichedAreas: any[] = [];
      for (const area of parsed.technology_areas || []) {
        const validEvidence: any[] = [];
        for (const cid of area.supporting_chunk_ids || []) {
          const ch = chunkById[cid];
          if (ch) {
            validEvidence.push({
              text: ch.content,
              source_title: ch.title,
              source_url: ch.source_url,
              source_type: ch.source_type,
              published_date: ch.published_date,
              chunk_id: ch.chunk_id,
              matched_queries: ch.matched_queries || [],
            });
          }
        }
        if (validEvidence.length > 0) {
          enrichedAreas.push({
            technology: area.technology,
            product_or_service: area.product_or_service,
            technical_capabilities: area.technical_capabilities || [],
            relevant_technical_concepts: area.relevant_technical_concepts || [],
            supporting_evidence: validEvidence,
          });
        }
      }

      if (enrichedAreas.length > 0) {
        targetResult.technology_areas = enrichedAreas;
        targetResult.canonical_output = {
          target_company: targetResult.target_company,
          technology_areas: enrichedAreas.map((ta) => ({
            technology: ta.technology,
            product_or_service: ta.product_or_service,
            technical_capabilities: ta.technical_capabilities,
            supporting_evidence: ta.supporting_evidence.map((ev: any) => ({
              text: ev.text,
              source_title: ev.source_title,
              source_url: ev.source_url,
            })),
          })),
        };
        if (targetResult.adk_architecture?.agent_trace) {
          for (const step of targetResult.adk_architecture.agent_trace) {
            if (step.agent === "target_analysis_agent") {
              step.status = "COMPLETED_VIA_GEMINI";
              step.summary = `Gemini (gemini-3.8-flash) synthesized ${enrichedAreas.length} evidence-backed target technology areas strictly from retrieved knowledge base chunks.`;
            }
          }
        }
      }
    }
  } catch (_err) {
    // Keep deterministic synthesis fallback if LLM call fails or hits rate limit
  }

  return targetResult;
}

async function enrichWithPatentAnalysisAgent(
  pipelineData: any,
  technologyArea?: string
): Promise<any> {
  const ai = getGenAIClient();
  if (!ai || !Array.isArray(pipelineData.patents) || pipelineData.patents.length === 0) {
    return pipelineData;
  }

  // Construct compact, evidence-only input for patent_analysis_agent (top 10 when max_candidates is 50-100 to prevent quota/token exhaustion)
  const candidatePrompts = pipelineData.patents.slice(0, 10).map((p: any) => ({
    patent_number: p.patent_number,
    title: p.title,
    abstract_source_fact: p.abstract_source_fact,
    description_excerpt_source_fact: p.description_excerpt_source_fact || "",
    cpc_codes: p.cpc_codes,
    independent_claims_verbatim: p.independent_claims || [],
    has_source_claims: Array.isArray(p.independent_claims) && p.independent_claims.length > 0,
  }));

  const systemInstruction = `You are the patent_analysis_agent in a Google ADK Client Patent Analysis Pipeline for the Patent–Product Intelligence Engine.
Your task is to analyze retrieved patent candidates from the Google Patents Public Dataset.

CRITICAL RULES:
1. Distinguish SOURCE FACT from AI INTERPRETATION. Do not alter patent numbers, titles, dates, CPC codes, or verbatim claim text.
2. Never invent patent facts, missing claims, or missing dates. If 'has_source_claims' is false or 'independent_claims_verbatim' is empty, you MUST return an empty array [] for 'claim_elements'.
3. For each patent with independent claims, decompose each independent claim into meaningful technical elements ('element_id' like '1A', '1B', '1C'; 'description' closely tracking the technical limitation; and 'technical_concept' naming the core engineering mechanism).
4. Group each patent into appropriate hierarchical technology areas (e.g., "Video Streaming > Adaptive Streaming", "Video Streaming > Content Delivery", "Video Streaming > Video Encoding", "Video Streaming > Playback Optimization"). Do not force a classification where evidence is insufficient.
5. Never state or imply legal infringement conclusions. Use neutral technical screening language ("potential technical overlap", "candidate for investigation", "requires expert/legal review").`;

  const prompt = `Requested Client Company: ${pipelineData.client_company} (Resolved Harmonized Assignee: ${pipelineData.resolved_assignee})
Requested Technology Niche: ${technologyArea || "All / Unfiltered"}

Analyze the following retrieved patent candidates and return structured technical intelligence for each patent:
${JSON.stringify(candidatePrompts, null, 2)}`;

  try {
    const response = await ai.models.generateContent({
      model: "gemini-3.8-flash",
      contents: prompt,
      config: {
        systemInstruction,
        temperature: 0.1,
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            analyzed_patents: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  patent_number: { type: Type.STRING },
                  technical_summary: {
                    type: Type.STRING,
                    description: "Concise 2-3 sentence technical summary grounded strictly in source abstract and description.",
                  },
                  technology_areas: {
                    type: Type.ARRAY,
                    items: { type: Type.STRING },
                    description: "Hierarchical technology cluster labels (e.g., 'Video Streaming > Adaptive Streaming').",
                  },
                  key_concepts: {
                    type: Type.ARRAY,
                    items: { type: Type.STRING },
                    description: "3 to 5 specific technical concepts disclosed in the patent.",
                  },
                  claim_elements: {
                    type: Type.ARRAY,
                    items: {
                      type: Type.OBJECT,
                      properties: {
                        claim_number: { type: Type.STRING },
                        elements: {
                          type: Type.ARRAY,
                          items: {
                            type: Type.OBJECT,
                            properties: {
                              element_id: { type: Type.STRING },
                              description: { type: Type.STRING },
                              technical_concept: { type: Type.STRING },
                            },
                            required: ["element_id", "description", "technical_concept"],
                          },
                        },
                      },
                      required: ["claim_number", "elements"],
                    },
                  },
                  relevance_rationale: {
                    type: Type.STRING,
                    description: "1-sentence technical explanation of why this candidate is relevant (or less relevant) to the requested technology niche for downstream investigation.",
                  },
                },
                required: [
                  "patent_number",
                  "technical_summary",
                  "technology_areas",
                  "key_concepts",
                  "claim_elements",
                  "relevance_rationale",
                ],
              },
            },
          },
          required: ["analyzed_patents"],
        },
      },
    });

    const rawText = response.text;
    if (rawText) {
      const parsed = JSON.parse(rawText.trim());
      const byPub: Record<string, any> = {};
      for (const item of parsed.analyzed_patents || []) {
        if (item && item.patent_number) {
          byPub[item.patent_number] = item;
        }
      }

      // Merge AI interpretations into deterministic patent records while protecting source facts
      for (const pat of pipelineData.patents) {
        const aiItem = byPub[pat.patent_number];
        if (!aiItem) continue;

        if (aiItem.technical_summary) {
          pat.technical_summary = aiItem.technical_summary;
        }
        if (Array.isArray(aiItem.technology_areas) && aiItem.technology_areas.length > 0) {
          pat.technology_areas = aiItem.technology_areas;
        }
        if (Array.isArray(aiItem.key_concepts) && aiItem.key_concepts.length > 0) {
          pat.key_concepts = aiItem.key_concepts;
        }

        // Enforce non-fabrication: only accept claim_elements if source independent_claims exist
        const hasSourceClaims = Array.isArray(pat.independent_claims) && pat.independent_claims.length > 0;
        if (hasSourceClaims && Array.isArray(aiItem.claim_elements) && aiItem.claim_elements.length > 0) {
          pat.claim_elements = aiItem.claim_elements;
        } else if (!hasSourceClaims) {
          pat.claim_elements = [];
        }

        if (aiItem.relevance_rationale && pat.investigation_relevance?.reasons) {
          pat.investigation_relevance.reasons = [
            `AI Technical Screening Note: ${aiItem.relevance_rationale}`,
            ...pat.investigation_relevance.reasons,
          ];
        }
      }

      // Rebuild technology_clusters from enriched technology_areas
      const clustersMap: Record<string, any[]> = {};
      for (const pat of pipelineData.patents) {
        for (const area of pat.technology_areas || ["Unclassified"]) {
          if (!clustersMap[area]) clustersMap[area] = [];
          clustersMap[area].push({
            patent_number: pat.patent_number,
            title: pat.title,
            relevance_score: pat.investigation_relevance?.score ?? 0,
          });
        }
      }
      pipelineData.technology_clusters = Object.entries(clustersMap).map(([area, items]) => ({
        cluster_name: area,
        parent_domain: area.includes(" > ") ? area.split(" > ")[0] : area,
        sub_area: area.includes(" > ") ? area.split(" > ").slice(1).join(" > ") : area,
        patent_count: items.length,
        patents: items,
      }));

      // Update agent trace to reflect completed Gemini LLM execution
      if (pipelineData.adk_architecture?.agent_trace) {
        for (const step of pipelineData.adk_architecture.agent_trace) {
          if (step.agent === "patent_analysis_agent") {
            step.status = "COMPLETED_VIA_GEMINI";
            step.summary = `Gemini (gemini-3.8-flash) analyzed ${pipelineData.patents.length} candidates, decomposed verbatim independent claims into technical elements, and clustered technologies.`;
          }
        }
      }
    }
  } catch (err: any) {
    // Preserve deterministic baseline analysis if Gemini API call encounters an error
    if (pipelineData.adk_architecture?.agent_trace) {
      for (const step of pipelineData.adk_architecture.agent_trace) {
        if (step.agent === "patent_analysis_agent") {
          step.status = "COMPLETED_DETERMINISTIC_FALLBACK";
          step.summary = `Used deterministic clause decomposition (${err?.message || "LLM unavailable"}).`;
        }
      }
    }
  }

  return pipelineData;
}

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json({ limit: "25mb" }));

  // 1. Inspect Google Patents Public Dataset Schema (`patents-public-data.patents.publications`)
  app.get("/api/schema", async (req, res) => {
    try {
      const liveCheck = req.query.live === "true";
      const args = ["--action", "inspect_schema"];
      if (liveCheck) args.push("--live_check");
      const schemaData = await runPythonAdkCli(args);
      res.json(schemaData);
    } catch (error: any) {
      res.status(500).json({
        error: "Failed to inspect BigQuery schema via Python tool.",
        details: error?.message || String(error),
      });
    }
  });

  // 2. Inspect & Query Pre-Fetched Target Knowledge Database (Offline SQLite Store)
  app.get("/api/target-knowledge", async (req, res) => {
    try {
      const company = String(req.query.company || "Netflix");
      const query = String(req.query.query || "");
      const tag = String(req.query.tag || "");
      const sourceType = String(req.query.source_type || "");
      const data = await runPythonTargetPrefetchCli([
        "--action",
        "status",
        "--company",
        company,
        "--query",
        query,
        "--tag",
        tag,
        "--source_type",
        sourceType,
      ]);
      res.json(data);
    } catch (error: any) {
      res.status(500).json({
        status: "ERROR",
        error: error?.message || "Failed to query Target Knowledge Database.",
      });
    }
  });

  // 3. Trigger Offline Target Knowledge Prefetch Script (Initial / Incremental / Custom Doc Test)
  app.post("/api/target-knowledge/prefetch", async (req, res) => {
    try {
      const { mode = "incremental", custom_document = null } = req.body || {};
      if (custom_document) {
        const data = await runPythonTargetPrefetchCli([
          "--action",
          "ingest_custom",
          "--custom_doc_json",
          JSON.stringify(custom_document),
        ]);
        res.json(data);
        return;
      }
      const data = await runPythonTargetPrefetchCli([
        "--action",
        "run_prefetch",
        "--mode",
        mode === "initial" ? "initial" : "incremental",
      ]);
      res.json(data);
    } catch (error: any) {
      res.status(500).json({
        status: "ERROR",
        error: error?.message || "Failed to execute Offline Target Prefetch Pipeline.",
      });
    }
  });

  // 4. Execute Target Retrieval & Analysis Agent Pipeline (root_agent -> target_retrieval_agent -> target_analysis_agent)
  app.post("/api/analyze-target-company", async (req, res) => {
    try {
      const {
        target_company = "Netflix",
        technology_area = "video streaming",
        client_patent_context = [],
        top_k = 4,
        use_llm = true,
      } = req.body || {};

      const payload = {
        target_company: String(target_company),
        technology_area: String(technology_area || ""),
        client_patent_context: Array.isArray(client_patent_context) ? client_patent_context : [],
        top_k: Number(top_k) || 4,
      };

      let targetResult = await runPythonTargetAgentCli([
        "--action",
        "run_agent",
        "--payload_json",
        JSON.stringify(payload),
      ]);

      if (targetResult.evidence_status === "sufficient" && use_llm) {
        targetResult = await enrichWithTargetAnalysisAgent(
          targetResult,
          payload.client_patent_context
        );
      }

      res.json(targetResult);
    } catch (error: any) {
      res.status(500).json({
        evidence_status: "insufficient",
        error: error?.message || "Failed to execute Target Retrieval Agent.",
      });
    }
  });

  // 5. Direct Deterministic Tool Endpoint: `search_target_knowledge(target_company, query, technology_area, top_k)`
  app.post("/api/target-retrieval-tool", async (req, res) => {
    try {
      const {
        target_company = "Netflix",
        query = "",
        technology_area = "",
        top_k = 5,
      } = req.body || {};

      const toolResult = await runPythonTargetAgentCli([
        "--action",
        "search_tool",
        "--target_company",
        String(target_company),
        "--query",
        String(query),
        "--technology_area",
        String(technology_area || ""),
        "--top_k",
        String(Number(top_k) || 5),
      ]);
      res.json(toolResult);
    } catch (error: any) {
      res.status(500).json({
        status: "ERROR",
        error: error?.message || "Failed to execute search_target_knowledge tool.",
      });
    }
  });

  // Local Medium MCP Server (medium-2) — JSON-RPC 2.0 HTTP Transport (MEDIUM_MCP_SERVER_URL)
  app.get("/api/mcp/medium", async (_req, res) => {
    try {
      const [initResp, toolsResp] = await Promise.all([
        runPythonMediumMcpRpc({
          jsonrpc: "2.0",
          id: "mcp_init_discovery",
          method: "initialize",
          params: { protocolVersion: "2024-11-05" },
        }),
        runPythonMediumMcpRpc({
          jsonrpc: "2.0",
          id: "mcp_tools_discovery",
          method: "tools/list",
          params: {},
        }),
      ]);
      res.json({
        status: "ONLINE",
        env: {
          MEDIUM_MCP_SERVER_URL: process.env.MEDIUM_MCP_SERVER_URL,
          MEDIUM_MCP_SERVER_CMD: process.env.MEDIUM_MCP_SERVER_CMD,
        },
        initialize: initResp,
        tools_list: toolsResp,
      });
    } catch (error: any) {
      res.status(500).json({
        status: "ERROR",
        error: error?.message || "Failed to query local Medium MCP Server.",
      });
    }
  });

  app.post("/api/mcp/medium", async (req, res) => {
    try {
      const rpcRequest = req.body && Object.keys(req.body).length > 0
        ? req.body
        : {
            jsonrpc: "2.0",
            id: 1,
            method: "tools/list",
            params: {},
          };
      const rpcResponse = await runPythonMediumMcpRpc(rpcRequest);
      res.json(rpcResponse);
    } catch (error: any) {
      res.status(500).json({
        jsonrpc: "2.0",
        id: req.body?.id ?? null,
        error: {
          code: -32603,
          message: error?.message || "Internal Medium MCP JSON-RPC error",
        },
      });
    }
  });

  // 6. Execute Patent–Target Matching & Commercial Opportunity Agent Pipeline (Google ADK)
  app.post("/api/analyze-patent-target-matching", async (req, res) => {
    try {
      const {
        client_company = "Apple",
        target_company = "Netflix",
        technology_area = "video streaming",
        client_patents = null,
        target_technology_areas = null,
        max_candidates = 6,
        use_llm = true,
      } = req.body || {};

      const payload: Record<string, any> = {
        client_company: String(client_company),
        target_company: String(target_company),
        technology_area: String(technology_area || ""),
        max_candidates: Number(max_candidates) || 6,
      };
      if (Array.isArray(client_patents) && client_patents.length > 0) {
        payload.client_patents = client_patents;
      }
      if (Array.isArray(target_technology_areas) && target_technology_areas.length > 0) {
        payload.target_technology_areas = target_technology_areas;
      }

      let matchingResult = await runPythonMatchingAgentCli([
        "--action",
        "run_matching",
        "--payload_json",
        JSON.stringify(payload),
      ]);

      if (matchingResult.matching_status === "SUCCESS" && use_llm) {
        matchingResult = await enrichWithMatchingAndCommercialAgent(matchingResult);
      }

      res.json(matchingResult);
    } catch (error: any) {
      res.status(500).json({
        matching_status: "PIPELINE_ERROR",
        error: error?.message || "Failed to execute Patent–Target Matching & Commercial Agent.",
      });
    }
  });

  // 2. Execute Unified Client Patent & Target Matching Analysis Pipeline
  app.post("/api/analyze-client-patents", async (req, res) => {
    try {
      const {
        client_company = "",
        target_company = "Netflix",
        technology_area = "",
        max_candidates = 6,
        use_llm = true,
      } = req.body || {};

      const cleanTargetCompany =
        String(target_company || "Netflix")
          .replace(/,\s*Inc\.?$/i, "")
          .trim() || "Netflix";

      const args = [
        "--action",
        "run_pipeline",
        "--client_company",
        String(client_company),
        "--technology_area",
        String(technology_area || ""),
        "--max_candidates",
        String(Number(max_candidates) || 6),
      ];

      let pipelineResult = await runPythonAdkCli(args);
      let matchingResult: any = null;

      if (pipelineResult.pipeline_status === "SUCCESS") {
        // Run deterministic Patent-Target Matching immediately using the retrieved client patents
        try {
          const rawPatents = pipelineResult.patents || [];
          const matchingPayload: Record<string, any> = {
            client_company:
              pipelineResult.resolved_assignee ||
              pipelineResult.client_company ||
              String(client_company),
            target_company: cleanTargetCompany,
            technology_area: String(technology_area || ""),
            max_candidates: Number(max_candidates) || 6,
          };
          if (rawPatents.length > 0 && rawPatents.length <= 12) {
            matchingPayload.client_patents = rawPatents;
          }
          matchingResult = await runPythonMatchingAgentCli([
            "--action",
            "run_matching",
            "--payload_json",
            JSON.stringify(matchingPayload),
          ]);
        } catch (mErr: any) {
          matchingResult = {
            matching_status: "PIPELINE_ERROR",
            client_company: pipelineResult.client_company,
            target_company: cleanTargetCompany,
            technology_area: String(technology_area || ""),
            error: mErr?.message || "Failed to execute Patent–Target Matching Pipeline.",
            ranked_matches: [],
          };
        }

        if (use_llm) {
          const [enrichedClient, enrichedMatching] = await Promise.all([
            enrichWithPatentAnalysisAgent(
              pipelineResult,
              technology_area ? String(technology_area) : undefined
            ),
            matchingResult && matchingResult.matching_status === "SUCCESS"
              ? enrichWithMatchingAndCommercialAgent(matchingResult)
              : Promise.resolve(matchingResult),
          ]);
          pipelineResult = enrichedClient;
          matchingResult = enrichedMatching;
        }

        // Sync enriched patent fields into matchingResult.ranked_matches and append matching ADK trace
        if (matchingResult && Array.isArray(matchingResult.ranked_matches)) {
          const patByNum: Record<string, any> = {};
          for (const p of pipelineResult.patents || []) {
            patByNum[p.patent_number] = p;
          }
          for (const m of matchingResult.ranked_matches) {
            const srcPat = patByNum[m.patent_number];
            if (srcPat) {
              m.patent_description = srcPat.technical_summary || m.patent_description;
              m.patent_technology_areas = srcPat.technology_areas || m.patent_technology_areas;
              m.patent_key_concepts = srcPat.key_concepts || m.patent_key_concepts;
            }
          }
        }

        if (
          pipelineResult.adk_architecture?.agent_trace &&
          matchingResult?.adk_architecture?.agent_trace
        ) {
          pipelineResult.adk_architecture.sub_agents = [
            ...(pipelineResult.adk_architecture.sub_agents || []),
            ...(matchingResult.adk_architecture.sub_agents || []),
          ];
          pipelineResult.adk_architecture.agent_trace = [
            ...pipelineResult.adk_architecture.agent_trace,
            ...matchingResult.adk_architecture.agent_trace,
          ];
        }
      }

      // Build the strict canonical output contract alongside the full pipeline telemetry
      const canonicalOutput = {
        client_company: pipelineResult.client_company,
        target_company: cleanTargetCompany,
        technology_area: pipelineResult.technology_area || "optional",
        patents: (pipelineResult.patents || []).map((p: any) => ({
          patent_number: p.patent_number,
          title: p.title,
          technical_summary: p.technical_summary,
          technology_areas: p.technology_areas,
          key_concepts: p.key_concepts,
          independent_claims: p.independent_claims,
          claim_elements: p.claim_elements,
          priority_date: p.priority_date,
          filing_date: p.filing_date,
          grant_date: p.grant_date,
          status: p.status,
          estimated_remaining_term_years: p.estimated_remaining_term_years,
          cpc_codes: p.cpc_codes,
          investigation_relevance: {
            score: p.investigation_relevance?.score ?? 0,
            reasons: p.investigation_relevance?.reasons ?? [],
          },
          source: "Google Patents Public Dataset",
        })),
        ranked_patent_product_matches:
          matchingResult?.canonical_output?.ranked_patent_product_matches || [],
      };

      res.json({
        ...pipelineResult,
        target_company: cleanTargetCompany,
        matching_analysis: matchingResult,
        canonical_output: canonicalOutput,
      });
    } catch (error: any) {
      res.status(500).json({
        pipeline_status: "PIPELINE_ERROR",
        error: error?.message || "Unexpected error in Client Patent Analysis Pipeline.",
      });
    }
  });

  // Mount Vite middleware in development or static dist in production
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(__dirname, "dist");
    app.use(express.static(distPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Patent–Product Intelligence Engine server listening on http://0.0.0.0:${PORT}`);
  });
}

startServer();
