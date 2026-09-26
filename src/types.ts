export interface ClaimElement {
  element_id: string;
  description: string;
  technical_concept: string;
}

export interface DecomposedClaim {
  claim_number: string;
  elements: ClaimElement[];
}

export interface PatentLifeEstimate {
  estimated_remaining_term_years: number | null;
  estimated_expiration_date_nominal?: string | null;
  calculation_basis: string;
  caveat: string;
}

export interface RelevanceFactor {
  score: number;
  max: number;
  detail: string;
}

export interface InvestigationRelevance {
  score: number;
  reasons: string[];
  factor_breakdown?: Record<string, RelevanceFactor>;
}

export interface PatentRecord {
  patent_number: string;
  application_number?: string;
  family_id?: string;
  title: string;
  abstract_source_fact?: string;
  description_excerpt_source_fact?: string;
  technical_summary: string;
  technology_areas: string[];
  key_concepts: string[];
  independent_claims: string[];
  claim_elements: DecomposedClaim[];
  missing_claims_warning?: string | null;
  priority_date: string | null;
  filing_date: string | null;
  grant_date: string | null;
  status: string;
  status_fact_basis?: string;
  estimated_remaining_term_years: number | null;
  patent_life?: PatentLifeEstimate;
  cpc_codes: string[];
  assignees?: string[];
  assignee_harmonized?: string[];
  inventors?: string[];
  investigation_relevance: InvestigationRelevance;
  source: string;
}

export interface TechnologyCluster {
  cluster_name: string;
  parent_domain: string;
  sub_area: string;
  patent_count: number;
  patents: {
    patent_number: string;
    title: string;
    relevance_score: number;
  }[];
}

export interface AgentTraceStep {
  agent: string;
  step: string;
  tool: string;
  status: string;
  summary: string;
}

export interface SchemaField {
  name: string;
  type: string;
  mode: string;
  mapped_concept: string;
  description: string;
  subfields?: { name: string; type: string; mode: string }[];
}

export interface PipelineResponse {
  pipeline_status:
    | "SUCCESS"
    | "AMBIGUOUS_COMPANY"
    | "COMPANY_NOT_FOUND"
    | "NO_PATENTS_FOUND"
    | "BIGQUERY_ERROR"
    | "INVALID_INPUT"
    | "PIPELINE_ERROR";
  client_company: string;
  resolved_assignee?: string;
  technology_area: string;
  error?: string;
  resolution?: {
    status: string;
    query?: string;
    resolved_assignee?: string | null;
    country_code?: string;
    publication_count?: number;
    raw_aliases?: string[];
    message?: string;
    error?: string;
    candidates?: {
      harmonized_name: string;
      country_code: string;
      publication_count: number;
      raw_aliases: string[];
    }[];
    available_assignees_in_dataset?: {
      harmonized_name: string;
      country_code: string;
      publication_count: number;
    }[];
    stage1_sql?: string;
  };
  staged_retrieval_metrics?: {
    stage1_harmonized_assignee: string;
    stage2_total_portfolio_records: number;
    stage2_filtered_out_records: number;
    stage2_shortlisted_candidates: number;
    stage3_full_claims_fetched: number;
    stage1_sql?: string;
    stage2_sql?: string;
    stage3_sql?: string;
  };
  schema_inspection?: {
    dataset: string;
    connection: {
      table_id: string;
      live_bigquery_reachable: boolean;
      execution_mode: string;
      diagnostic: string;
    };
    schema_fields: SchemaField[];
    status_derivation_note: string;
  };
  adk_architecture?: {
    runtime_mode: string;
    root_agent: string;
    sub_agents: string[];
    agent_trace: AgentTraceStep[];
  };
  technology_clusters?: TechnologyCluster[];
  patents: PatentRecord[];
  canonical_output?: {
    client_company: string;
    technology_area: string;
    patents: any[];
  };
}

export interface TargetKnowledgeChunk {
  document_id: string;
  company: string;
  title: string;
  source_url: string;
  source_type: string;
  published_date: string | null;
  author: string | null;
  content: string;
  technology_area: string | null;
  chunk_id: string;
  embedding: number[];
  candidate_tags?: string[];
  chunk_index?: number;
  content_hash?: string;
  fetch_method?: string;
  mcp_tool_used?: string;
  ingested_at?: string;
  similarity_score?: number;
}

export interface TargetKnowledgeDocument {
  document_id: string;
  company: string;
  title: string;
  source_url: string;
  source_type: string;
  published_date: string | null;
  author: string | null;
  content: string;
  full_content?: string;
  content_hash: string;
  fetch_method?: string;
  mcp_tool_used?: string;
  technology_area: string | null;
  candidate_tags: string[];
  chunk_count: number;
  ingested_at: string;
  updated_at: string;
}

export interface FailedDocumentLog {
  id: number;
  company: string;
  source_url: string;
  title: string;
  error_code: string;
  error_message: string;
  logged_at: string;
}

export interface IngestionRunRecord {
  run_id: string;
  mode: string;
  started_at: string;
  completed_at: string;
  total_sources_processed: number;
  inserted_documents: number;
  updated_documents: number;
  inserted_chunks: number;
  skipped_duplicates: number;
  failed_documents_count: number;
  run_log: {
    document_id?: string;
    source_url: string;
    title: string;
    source_type?: string;
    fetch_method?: string;
    mcp_tool_used?: string;
    status: string;
    detail?: string;
    chunks_created?: number;
    technology_area?: string | null;
    candidate_tags?: string[];
  }[];
}

export interface TargetKnowledgeResponse {
  status: string;
  company: string;
  database_path: string;
  alloydb_config?: {
    engine: string;
    vector_extension: string;
    instance_uri: string;
    database_name: string;
    connection_uri_display: string;
    connection_mode: string;
    ddl_preview: string;
  };
  medium_mcp_config?: {
    server_id: string;
    server_name: string;
    registry_url: string;
    protocol_version: string;
    handled_domains: string[];
    direct_url_scraping_disabled: boolean;
    articles_ingested_via_mcp: number;
    tools: {
      name: string;
      description: string;
    }[];
  };
  configured_sources: {
    source_id: string;
    name: string;
    url_prefix: string;
    source_type: string;
    ingestion_protocol?: string;
    approval_status: string;
  }[];
  approved_technology_taxonomy: string[];
  summary_metrics: {
    total_documents_stored: number;
    medium_mcp_documents_stored?: number;
    direct_extractor_documents_stored?: number;
    total_chunks_stored: number;
    filtered_chunks_returned: number;
    failed_documents_logged: number;
    total_ingestion_runs: number;
    tag_distribution: Record<string, number>;
  };
  documents: TargetKnowledgeDocument[];
  chunks: TargetKnowledgeChunk[];
  failed_documents: FailedDocumentLog[];
  ingestion_runs: IngestionRunRecord[];
}

export interface TargetSupportingEvidence {
  text: string;
  source_title: string;
  source_url: string;
  source_type?: string;
  published_date?: string;
  chunk_id?: string;
  matched_queries?: string[];
}

export interface TargetTechnologyArea {
  technology: string;
  product_or_service: string;
  technical_capabilities: string[];
  relevant_technical_concepts?: string[];
  supporting_evidence: TargetSupportingEvidence[];
}

export interface TargetAgentResponse {
  evidence_status: "sufficient" | "insufficient";
  target_company?: string;
  technology_area?: string;
  diagnostic_reason?: string;
  error?: string;
  multi_query_log?: {
    query: string;
    rationale: string;
    returned_count: number;
    top_chunk_ids: string[];
  }[];
  retrieved_chunks?: any[];
  technology_areas?: TargetTechnologyArea[];
  adk_architecture?: {
    runtime_mode: string;
    root_agent: string;
    sub_agents: string[];
    agent_trace: AgentTraceStep[];
  };
  canonical_output?: {
    target_company?: string;
    technology_areas?: {
      technology: string;
      product_or_service: string;
      technical_capabilities: string[];
      supporting_evidence: {
        text: string;
        source_title: string;
        source_url: string;
      }[];
    }[];
    evidence_status?: "insufficient";
  };
}

export interface ClaimElementAlignment {
  claim_number: string;
  element_id: string;
  claim_element_description: string;
  technical_concept: string;
  alignment_status:
    | "EVIDENCE_IDENTIFIED"
    | "PARTIAL_ALIGNMENT"
    | "NOT_DOCUMENTED_IN_PUBLIC_SOURCES";
  matched_target_capability: string | null;
  shared_technical_terms: string[];
  supporting_source_title: string | null;
  supporting_source_url: string | null;
  alignment_rationale: string;
}

export interface RankedPatentProductMatch {
  rank: number;
  match_id: string;
  patent_number: string;
  patent_title: string;
  patent_description: string;
  patent_abstract_source_fact?: string;
  patent_cpc_codes: string[];
  patent_key_concepts: string[];
  patent_technology_areas: string[];
  patent_independent_claims: string[];
  patent_filing_date: string | null;
  patent_priority_date: string | null;
  patent_grant_date: string | null;
  target_company: string;
  target_product_or_service: string;
  target_technology: string;
  target_technical_capabilities: string[];
  alternative_target_matches?: {
    target_product_or_service: string;
    target_technology: string;
    technical_overlap_level: string;
    technical_relevance_score: number;
  }[];
  technical_overlap: {
    overlap_level: "High" | "Medium" | "Low" | "Insufficient Evidence";
    technical_relevance_score: number;
    summary: string;
    shared_technical_mechanisms: string[];
    has_source_claims: boolean;
    claim_element_counts: {
      total_elements: number;
      evidence_identified: number;
      partial_alignment: number;
      not_documented: number;
    };
    claim_element_mapping: ClaimElementAlignment[];
    evidence_gaps: string[];
    factor_breakdown: Record<string, RelevanceFactor>;
  };
  supporting_evidence: {
    text: string;
    source_title: string;
    source_url: string;
    source_type: string;
    published_date?: string;
    chunk_id?: string;
    relevance_score: number;
    matched_mechanisms: string[];
  }[];
  patent_status: string;
  patent_status_fact_basis?: string;
  estimated_remaining_patent_life: {
    years_remaining: number | null;
    expiration_date_nominal?: string | null;
    calculation_basis: string;
    viability_note: string;
  };
  potential_monetary_opportunity: {
    signal_tier: string;
    commercial_opportunity_score: number;
    rationale: string;
    strategic_role: string;
    monetization_driver: string;
    consolidated_company_revenue: string | null;
    product_level_revenue_disclosed: boolean;
    product_level_revenue_note: string;
    subscriber_or_adoption_scale: string;
    pricing_tiers_disclosed: string;
    supporting_commercial_sources: {
      chunk_id: string;
      source_title: string;
      source_url: string;
      source_type: string;
      published_date: string;
      verbatim_excerpt: string;
    }[];
    factor_breakdown: Record<string, RelevanceFactor>;
  };
  investigation_priority: {
    priority_tier: string;
    priority_score: number;
    rationale: string;
    gatekeeper_flags: {
      is_granted_active: boolean;
      is_expired: boolean;
      is_pending_application: boolean;
      has_indexed_independent_claims: boolean;
    };
  };
}

export interface MatchingAgentResponse {
  matching_status: string;
  client_company: string;
  target_company: string;
  technology_area: string;
  diagnostic_reason?: string;
  error?: string;
  summary_metrics?: {
    total_relationships_ranked: number;
    total_pairs_evaluated: number;
    high_priority_count: number;
    medium_priority_count: number;
    low_priority_count: number;
    avg_technical_relevance_score: number;
    avg_commercial_opportunity_score: number;
  };
  ranked_matches: RankedPatentProductMatch[];
  adk_architecture?: {
    runtime_mode: string;
    root_agent: string;
    sub_agents: string[];
    agent_trace: AgentTraceStep[];
  };
  canonical_output?: any;
}



