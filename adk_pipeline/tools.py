"""
Deterministic Python Tools for the Client Patent Analysis Pipeline (Google ADK).
All database queries, company name resolution, staged retrieval, date formatting,
estimated patent-life calculations, and baseline investigation relevance scoring
are executed deterministically in Python.

Agents are strictly prohibited from constructing arbitrary BigQuery SQL queries.
"""

from datetime import date, datetime
import re
from typing import Dict, Any, List, Optional, Tuple

from adk_pipeline.schema_inspector import inspect_bigquery_publications_schema
from adk_pipeline.dataset_mirror import PATENTS_PUBLIC_DATA_MIRROR


# Reference date for deterministic patent life calculation
DEFAULT_REFERENCE_DATE = "2026-09-25"


def format_bq_date(date_int: Optional[int]) -> Optional[str]:
    """
    Deterministically converts BigQuery integer date YYYYMMDD (e.g., 20180412)
    into ISO 8601 string 'YYYY-MM-DD'. Returns None if date_int is 0 or invalid.
    Never fabricates missing dates.
    """
    if not date_int or date_int <= 0:
        return None
    s = str(date_int).strip()
    if len(s) != 8 or not s.isdigit():
        return None
    try:
        dt = date(int(s[0:4]), int(s[4:6]), int(s[6:8]))
        return dt.isoformat()
    except ValueError:
        return None


def derive_publication_status(grant_date_int: int, kind_code: str, country_code: str, remaining_years: Optional[float]) -> Dict[str, str]:
    """
    Deterministically derives available patent status from `patents-public-data.patents.publications`
    source facts (`grant_date`, `kind_code`, `country_code`, and statutory 20-year window).
    """
    kind = (kind_code or "").upper()
    if grant_date_int and grant_date_int > 0:
        if remaining_years is not None and remaining_years <= 0.0:
            return {
                "status": f"Granted Patent ({country_code} {kind}) — Estimated Statutory Term Expired",
                "fact_basis": f"Source fact: grant_date={format_bq_date(grant_date_int)}, kind_code={kind}. Deterministic calculation indicates 20-year statutory window from filing_date has elapsed."
            }
        return {
            "status": f"Granted Patent ({country_code} {kind})",
            "fact_basis": f"Source fact: grant_date={format_bq_date(grant_date_int)} (> 0) and kind_code={kind} in Google Patents Public Dataset."
        }
    else:
        if kind.startswith("A"):
            return {
                "status": f"Published Application / Pre-Grant Publication ({country_code} {kind}, No Grant Date Recorded)",
                "fact_basis": f"Source fact: grant_date=0 and kind_code={kind} in Google Patents Public Dataset."
            }
        return {
            "status": "Status Unconfirmed in Publication Record (grant_date=0)",
            "fact_basis": "Source fact: grant_date=0 in Google Patents Public Dataset."
        }


def extract_english_text(localized_list: List[Dict[str, Any]]) -> Optional[str]:
    """
    Extracts English text from a BigQuery REPEATED RECORD field (`title_localized`,
    `abstract_localized`, `claims_localized`, `description_localized`).
    Returns None if empty or not available.
    """
    if not localized_list:
        return None
    for item in localized_list:
        if item.get("language") == "en" and item.get("text"):
            return item["text"].strip()
    # Fallback to first non-empty entry if language tag wasn't 'en'
    for item in localized_list:
        if item.get("text"):
            return item["text"].strip()
    return None


def extract_independent_claims_deterministic(claims_text: Optional[str]) -> List[Dict[str, Any]]:
    """
    Deterministically parses verbatim independent claims from raw `claims_localized` text.
    A claim is identified as independent if it does not contain a dependency reference
    such as 'of claim X', 'according to claim X', or 'as claimed in claim X'.
    Never invents or modifies claim language.
    """
    if not claims_text or not claims_text.strip():
        return []

    # Split claims on numbered claim boundaries (e.g., "1. ", "\n2. ")
    pattern = re.compile(r"(?:^|\n)\s*(\d+)\.\s+", re.MULTILINE)
    matches = list(pattern.finditer(claims_text))
    if not matches:
        return [
            {
                "claim_number": "1",
                "text": claims_text.strip(),
                "is_independent": True,
                "source_fact": True
            }
        ]

    independent_claims: List[Dict[str, Any]] = []
    dep_regex = re.compile(r"\b(?:of|according to|as claimed in|as recited in|any preceding)\s+claim\b", re.IGNORECASE)

    for idx, match in enumerate(matches):
        claim_num = match.group(1)
        start_pos = match.end()
        end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(claims_text)
        body = claims_text[start_pos:end_pos].strip()
        full_claim = f"{claim_num}. {body}"
        is_dependent = bool(dep_regex.search(body))
        if not is_dependent:
            independent_claims.append({
                "claim_number": claim_num,
                "text": full_claim,
                "is_independent": True,
                "source_fact": True
            })

    return independent_claims


# ============================================================================
# STAGE 1 TOOL: RESOLVE CLIENT COMPANY (ASSIGNEE HARMONIZED RESOLUTION)
# ============================================================================

def resolve_client_company_tool(client_company: str) -> Dict[str, Any]:
    """
    Stage 1 of Staged Retrieval:
    Resolves `client_company` against `assignee_harmonized.name` and `assignee` in
    `patents-public-data.patents.publications`.
    Detects:
    - Empty / invalid input
    - Client company not found
    - Ambiguous company name (multiple distinct corporate assignees match)
    - Unambiguous single resolved corporate assignee
    """
    query_raw = (client_company or "").strip()
    if not query_raw:
        return {
            "status": "INVALID_INPUT",
            "error": "client_company is required and cannot be empty.",
            "resolved_assignee": None,
            "candidates": []
        }

    # Simulated BigQuery error trigger for testing BigQuery error handling
    if query_raw.upper() in ("TRIGGER_BQ_ERROR", "SIMULATE_BIGQUERY_ERROR"):
        return {
            "status": "BIGQUERY_ERROR",
            "error": "BigQuery job execution failed: Quota exceeded or table access error on patents-public-data.patents.publications.",
            "resolved_assignee": None,
            "candidates": []
        }

    # Parameterized Stage 1 BigQuery SQL (read-only template)
    stage1_sql = """
SELECT
  ah.name AS harmonized_assignee_name,
  ah.country_code AS country_code,
  COUNT(DISTINCT publication_number) AS publication_count
FROM `patents-public-data.patents.publications`,
  UNNEST(assignee_harmonized) AS ah
WHERE UPPER(ah.name) LIKE CONCAT('%', UPPER(@client_company), '%')
GROUP BY harmonized_assignee_name, country_code
ORDER BY publication_count DESC
LIMIT 20;
""".strip()

    # Aggregate distinct harmonized assignees from dataset
    assignee_stats: Dict[str, Dict[str, Any]] = {}
    for row in PATENTS_PUBLIC_DATA_MIRROR:
        raw_names = row.get("assignee", [])
        for ah in row.get("assignee_harmonized", []):
            h_name = ah.get("name", "")
            if not h_name:
                continue
            if h_name not in assignee_stats:
                assignee_stats[h_name] = {
                    "harmonized_name": h_name,
                    "country_code": ah.get("country_code", ""),
                    "publication_count": 0,
                    "raw_aliases": set()
                }
            assignee_stats[h_name]["publication_count"] += 1
            for r_name in raw_names:
                assignee_stats[h_name]["raw_aliases"].add(r_name)

    q_norm = re.sub(r"[^A-Z0-9\s]", "", query_raw.upper()).strip()
    corporate_suffixes = {"INC", "CORP", "CORPORATION", "INCORPORATED", "LTD", "LLC", "PLC", "AB", "CO"}
    q_tokens = [t for t in q_norm.split() if t not in corporate_suffixes]
    q_core = " ".join(q_tokens) if q_tokens else q_norm

    exact_matches: List[Dict[str, Any]] = []
    partial_matches: List[Dict[str, Any]] = []

    for h_name, info in assignee_stats.items():
        h_norm = re.sub(r"[^A-Z0-9\s]", "", h_name.upper()).strip()
        h_tokens = [t for t in h_norm.split() if t not in corporate_suffixes]
        h_core = " ".join(h_tokens)

        alias_norms = [re.sub(r"[^A-Z0-9\s]", "", a.upper()).strip() for a in info["raw_aliases"]]

        candidate_entry = {
            "harmonized_name": h_name,
            "country_code": info["country_code"],
            "publication_count": info["publication_count"],
            "raw_aliases": sorted(list(info["raw_aliases"]))
        }

        # Exact match on full harmonized name, raw alias, or exact core name
        if q_norm == h_norm or q_norm in alias_norms or (q_core == h_core and len(q_tokens) >= 1):
            exact_matches.append(candidate_entry)
        elif q_core and (q_core in h_norm or any(q_core in an for an in alias_norms)):
            partial_matches.append(candidate_entry)

    # If exact match found (and only 1 exact match), resolve immediately
    if len(exact_matches) == 1:
        resolved = exact_matches[0]
        return {
            "status": "RESOLVED",
            "query": query_raw,
            "resolved_assignee": resolved["harmonized_name"],
            "country_code": resolved["country_code"],
            "publication_count": resolved["publication_count"],
            "raw_aliases": resolved["raw_aliases"],
            "candidates": [resolved],
            "stage1_sql": stage1_sql
        }

    all_matches = exact_matches if len(exact_matches) > 1 else partial_matches

    if len(all_matches) == 1:
        resolved = all_matches[0]
        return {
            "status": "RESOLVED",
            "query": query_raw,
            "resolved_assignee": resolved["harmonized_name"],
            "country_code": resolved["country_code"],
            "publication_count": resolved["publication_count"],
            "raw_aliases": resolved["raw_aliases"],
            "candidates": [resolved],
            "stage1_sql": stage1_sql
        }

    if len(all_matches) > 1:
        # Multiple distinct corporate entities matched -> return AMBIGUOUS_COMPANY
        return {
            "status": "AMBIGUOUS_COMPANY",
            "query": query_raw,
            "resolved_assignee": None,
            "message": (
                f"Ambiguous company name '{query_raw}' matched {len(all_matches)} distinct harmonized "
                "assignee entities in `patents-public-data.patents.publications`. Please specify the exact "
                "corporate assignee entity to avoid conflating unrelated patent portfolios."
            ),
            "candidates": sorted(all_matches, key=lambda x: x["publication_count"], reverse=True),
            "stage1_sql": stage1_sql
        }

    # Not found
    available_assignees = sorted(
        [
            {
                "harmonized_name": k,
                "country_code": v["country_code"],
                "publication_count": v["publication_count"]
            }
            for k, v in assignee_stats.items()
        ],
        key=lambda x: x["harmonized_name"]
    )
    return {
        "status": "COMPANY_NOT_FOUND",
        "query": query_raw,
        "resolved_assignee": None,
        "message": (
            f"No patent publications found in `patents-public-data.patents.publications` matching assignee '{query_raw}'."
        ),
        "available_assignees_in_dataset": available_assignees,
        "stage1_sql": stage1_sql
    }


# ============================================================================
# STAGE 2 TOOL: RETRIEVE CANDIDATE METADATA (PORTFOLIO SCREENING)
# ============================================================================

# Mapping of common technology niche terms to relevant CPC subclasses and technical keywords
NICHE_SYNONYM_MAP: Dict[str, List[str]] = {
    "video streaming": ["streaming", "adaptive", "bitrate", "manifest", "hls", "dash", "cmaf", "segment", "playback", "video", "encoding", "transcoding", "cdn", "cache", "h04n21", "h04n19", "h04l65"],
    "adaptive streaming": ["adaptive", "bitrate", "abr", "manifest", "hls", "dash", "cmaf", "segment", "buffer", "h04n21/8456", "h04n21/2343", "h04n21/262"],
    "video encoding": ["encoding", "encoder", "codec", "quantization", "gop", "motion", "hdr", "reshaping", "convex hull", "transcoding", "multiplexing", "h04n19"],
    "content delivery": ["content delivery", "cdn", "edge", "cache", "prefetch", "anycast", "bgp", "origin", "coalescing", "pacing", "h04l67", "h04n21/222"],
    "playback optimization": ["playback", "buffer", "latency", "synchronization", "splice", "audio", "spatial", "clock", "trick-mode", "h04n21/43", "h04n21/44"],
    "cloud gaming": ["interactive", "slice", "nack", "frame streaming", "low-latency", "cloud", "h04n19/174", "h04n21/478"],
    "image sensor": ["cmos", "sensor", "pixel", "semiconductor", "substrate", "h04n25", "h01l27"]
}


def compute_niche_match_signals(
    title: str,
    abstract: str,
    cpc_codes: List[str],
    technology_area: Optional[str]
) -> Tuple[bool, float, List[str]]:
    """
    Deterministically evaluates whether a patent publication matches the optional `technology_area`
    filter and returns (matched, match_ratio_0_to_1, matched_terms).
    """
    if not technology_area or not technology_area.strip() or technology_area.strip().lower() in ("optional", "all", "any", "none"):
        return True, 1.0, ["Unfiltered portfolio query (all technology areas included)"]

    niche_raw = technology_area.strip().lower()
    haystack = f"{title} {abstract} {' '.join(cpc_codes)}".lower()

    # Build expanded terms from exact words + known domain synonyms if applicable
    raw_words = [w for w in re.split(r"[^a-z0-9/]+", niche_raw) if len(w) >= 2]
    expanded_terms = list(dict.fromkeys(raw_words))
    for key, syns in NICHE_SYNONYM_MAP.items():
        if key in niche_raw or any(w in key.split() for w in raw_words if len(w) >= 4):
            for s in syns:
                if s not in expanded_terms:
                    expanded_terms.append(s)

    matched_terms: List[str] = []
    direct_hits = 0
    for w in raw_words:
        if w in haystack:
            direct_hits += 1
            matched_terms.append(w)

    synonym_hits = 0
    for term in expanded_terms:
        if term not in raw_words and term in haystack:
            synonym_hits += 1
            matched_terms.append(term)

    if direct_hits == 0 and synonym_hits == 0:
        return False, 0.0, []

    # Score between 0.25 and 1.0 based on direct + domain synonym hits
    score = min(1.0, (direct_hits * 0.45) + (synonym_hits * 0.15))
    return True, round(score, 2), matched_terms[:8]


def retrieve_candidate_metadata_tool(
    resolved_assignee: str,
    technology_area: Optional[str] = None,
    max_candidates: int = 8
) -> Dict[str, Any]:
    """
    Stage 2 of Staged Retrieval:
    Screens lightweight metadata (`publication_number`, `title_localized`, `abstract_localized`,
    `cpc`, `filing_date`, `priority_date`, `grant_date`, `kind_code`) for the resolved assignee
    without loading full specification/claim bodies for the entire portfolio into LLM context.
    """
    stage2_sql = """
SELECT
  p.publication_number,
  p.application_number,
  p.country_code,
  p.kind_code,
  p.filing_date,
  p.priority_date,
  p.grant_date,
  (SELECT t.text FROM UNNEST(p.title_localized) AS t WHERE t.language = 'en' LIMIT 1) AS title_en,
  (SELECT a.text FROM UNNEST(p.abstract_localized) AS a WHERE a.language = 'en' LIMIT 1) AS abstract_en,
  ARRAY(SELECT DISTINCT c.code FROM UNNEST(p.cpc) AS c) AS cpc_codes,
  ARRAY_LENGTH(p.claims_localized) > 0 AS has_claims
FROM `patents-public-data.patents.publications` AS p,
  UNNEST(p.assignee_harmonized) AS ah
WHERE ah.name = @resolved_assignee
  AND (
    @technology_area IS NULL
    OR EXISTS (
      SELECT 1 FROM UNNEST(p.title_localized) AS t
      WHERE t.language = 'en' AND LOWER(t.text) LIKE CONCAT('%', LOWER(@technology_area), '%')
    )
    OR EXISTS (
      SELECT 1 FROM UNNEST(p.abstract_localized) AS a
      WHERE a.language = 'en' AND LOWER(a.text) LIKE CONCAT('%', LOWER(@technology_area), '%')
    )
  )
ORDER BY p.grant_date DESC, p.filing_date DESC
LIMIT @max_candidates;
""".strip()

    portfolio_rows = [
        row for row in PATENTS_PUBLIC_DATA_MIRROR
        if any(ah.get("name") == resolved_assignee for ah in row.get("assignee_harmonized", []))
    ]

    total_portfolio_count = len(portfolio_rows)
    candidates: List[Dict[str, Any]] = []
    filtered_out_count = 0

    for row in portfolio_rows:
        title = extract_english_text(row.get("title_localized", [])) or "Untitled Patent Publication"
        abstract = extract_english_text(row.get("abstract_localized", [])) or ""
        cpc_codes = [c.get("code") for c in row.get("cpc", []) if c.get("code")]

        matched, niche_score, matched_terms = compute_niche_match_signals(
            title=title,
            abstract=abstract,
            cpc_codes=cpc_codes,
            technology_area=technology_area
        )

        if not matched:
            filtered_out_count += 1
            continue

        has_claims = bool(extract_english_text(row.get("claims_localized", [])))
        candidates.append({
            "publication_number": row["publication_number"],
            "application_number": row.get("application_number"),
            "country_code": row.get("country_code", "US"),
            "kind_code": row.get("kind_code", ""),
            "family_id": row.get("family_id"),
            "title": title,
            "abstract": abstract,
            "cpc_codes": cpc_codes,
            "cpc_details": row.get("cpc", []),
            "priority_date_raw": row.get("priority_date", 0),
            "filing_date_raw": row.get("filing_date", 0),
            "grant_date_raw": row.get("grant_date", 0),
            "priority_date": format_bq_date(row.get("priority_date", 0)),
            "filing_date": format_bq_date(row.get("filing_date", 0)),
            "grant_date": format_bq_date(row.get("grant_date", 0)),
            "assignees": row.get("assignee", []),
            "assignee_harmonized": [ah.get("name") for ah in row.get("assignee_harmonized", [])],
            "inventors": [iv.get("name") for iv in row.get("inventor_harmonized", [])],
            "has_claims": has_claims,
            "niche_match_score": niche_score,
            "niche_matched_terms": matched_terms
        })

    # Sort deterministically by niche_match_score DESC, has_claims DESC, grant_date_raw DESC
    candidates.sort(
        key=lambda c: (c["niche_match_score"], 1 if c["has_claims"] else 0, c["grant_date_raw"]),
        reverse=True
    )
    selected_candidates = candidates[:max_candidates]

    if not selected_candidates:
        return {
            "status": "NO_PATENTS_FOUND",
            "resolved_assignee": resolved_assignee,
            "technology_area": technology_area,
            "total_portfolio_count": total_portfolio_count,
            "filtered_out_count": filtered_out_count,
            "candidates": [],
            "message": (
                f"No patents found for '{resolved_assignee}' matching technology area '{technology_area}' "
                f"(screened {total_portfolio_count} publications in portfolio)."
            ),
            "stage2_sql": stage2_sql
        }

    return {
        "status": "CANDIDATES_RETRIEVED",
        "resolved_assignee": resolved_assignee,
        "technology_area": technology_area,
        "total_portfolio_count": total_portfolio_count,
        "filtered_out_count": filtered_out_count,
        "selected_candidate_count": len(selected_candidates),
        "candidates": selected_candidates,
        "stage2_sql": stage2_sql
    }


# ============================================================================
# STAGE 3 TOOL: TARGETED CLAIM & DESCRIPTION RETRIEVAL
# ============================================================================

def fetch_staged_patent_claims_tool(publication_numbers: List[str]) -> Dict[str, Any]:
    """
    Stage 3 of Staged Retrieval:
    Fetches full `claims_localized` and `description_localized` only for the shortlisted
    candidate `publication_numbers` from Stage 2.
    Deterministically extracts verbatim independent claims and flags missing claims.
    """
    stage3_sql = """
SELECT
  p.publication_number,
  (SELECT c.text FROM UNNEST(p.claims_localized) AS c WHERE c.language = 'en' LIMIT 1) AS claims_en,
  (SELECT d.text FROM UNNEST(p.description_localized) AS d WHERE d.language = 'en' LIMIT 1) AS description_en
FROM `patents-public-data.patents.publications` AS p
WHERE p.publication_number IN UNNEST(@publication_numbers);
""".strip()

    pub_set = set(publication_numbers or [])
    records_by_pub: Dict[str, Dict[str, Any]] = {}

    for row in PATENTS_PUBLIC_DATA_MIRROR:
        pub_num = row["publication_number"]
        if pub_num not in pub_set:
            continue
        claims_text = extract_english_text(row.get("claims_localized", []))
        desc_text = extract_english_text(row.get("description_localized", []))
        independent_claims = extract_independent_claims_deterministic(claims_text)

        records_by_pub[pub_num] = {
            "publication_number": pub_num,
            "claims_available": bool(claims_text),
            "raw_claims_text": claims_text,
            "description_excerpt": desc_text,
            "independent_claims": independent_claims,
            "missing_claims_warning": (
                None if claims_text else
                "Source publication record in `patents-public-data.patents.publications` has empty `claims_localized`. Claims are not fabricated."
            )
        }

    return {
        "status": "CLAIMS_FETCHED",
        "requested_count": len(publication_numbers),
        "fetched_count": len(records_by_pub),
        "records": records_by_pub,
        "stage3_sql": stage3_sql
    }


# ============================================================================
# STEP 5 TOOL: DETERMINISTIC PATENT LIFE CALCULATION
# ============================================================================

def calculate_patent_life_tool(
    filing_date_int: int,
    priority_date_int: int,
    grant_date_int: int,
    kind_code: str = "B2",
    country_code: str = "US",
    reference_date_str: str = DEFAULT_REFERENCE_DATE
) -> Dict[str, Any]:
    """
    Step 5 — Deterministic Patent Life Calculator.
    Calculates an ESTIMATED remaining patent term in years where sufficient dates are available.
    Standard baseline: 20 years from earliest effective application `filing_date` (35 U.S.C. § 154(a)(2)).
    Never fabricates missing dates and always attaches the mandatory legal caveat.
    """
    caveat = "This is an estimate and not a legal determination of enforceability or expiration."
    filing_iso = format_bq_date(filing_date_int)
    priority_iso = format_bq_date(priority_date_int)
    grant_iso = format_bq_date(grant_date_int)

    if not filing_iso:
        return {
            "estimated_remaining_term_years": None,
            "estimated_expiration_year": None,
            "calculation_basis": (
                "Insufficient date metadata in source record: `filing_date` is missing (0). "
                + (f"Earliest recorded `priority_date` is {priority_iso}, but statutory 20-year term requires an effective application filing date." if priority_iso else "Both `filing_date` and `priority_date` are missing.")
            ),
            "caveat": caveat
        }

    filing_dt = date.fromisoformat(filing_iso)
    ref_dt = date.fromisoformat(reference_date_str)

    # Standard 20-year statutory term from filing date
    try:
        estimated_exp_dt = date(filing_dt.year + 20, filing_dt.month, filing_dt.day)
    except ValueError:
        # Handle Feb 29 leap year filing dates
        estimated_exp_dt = date(filing_dt.year + 20, 2, 28)

    delta_days = (estimated_exp_dt - ref_dt).days
    remaining_years = max(0.0, round(delta_days / 365.25, 1))

    grant_note = (
        f"Granted on {grant_iso} ({country_code} {kind_code})."
        if grant_iso else
        f"Published application ({country_code} {kind_code}) with no recorded grant_date (grant_date=0); term estimate assumes hypothetical grant."
    )

    if remaining_years <= 0.0:
        basis = (
            f"20-year statutory baseline from filing_date ({filing_iso}) reached nominal expiration around "
            f"{estimated_exp_dt.isoformat()} prior to reference date ({reference_date_str}). {grant_note} "
            "Excludes Patent Term Adjustment (PTA), Patent Term Extension (PTE), or terminal disclaimers."
        )
    else:
        basis = (
            f"Calculated as 20-year statutory baseline from filing_date ({filing_iso}) -> nominal baseline date "
            f"{estimated_exp_dt.isoformat()} relative to reference date ({reference_date_str}). "
            f"Priority date: {priority_iso or 'N/A'}. {grant_note} "
            "Excludes USPTO Patent Term Adjustment (PTA), Patent Term Extension (PTE), terminal disclaimers, and maintenance fee status."
        )

    return {
        "estimated_remaining_term_years": remaining_years,
        "estimated_expiration_date_nominal": estimated_exp_dt.isoformat(),
        "calculation_basis": basis,
        "caveat": caveat
    }


# ============================================================================
# STEP 6 TOOL: DETERMINISTIC + EXPLAINABLE PATENT INVESTIGATION RELEVANCE
# ============================================================================

def compute_investigation_relevance_tool(
    candidate_meta: Dict[str, Any],
    claim_record: Dict[str, Any],
    patent_life: Dict[str, Any],
    ai_analysis: Optional[Dict[str, Any]] = None,
    technology_area: Optional[str] = None
) -> Dict[str, Any]:
    """
    Step 6 — Deterministic & Explainable Preliminary Patent Investigation Relevance.
    Evaluates:
    1. Relevance to requested technology niche (0-30 pts)
    2. Technical richness (0-20 pts)
    3. Claim information availability (0-20 pts)
    4. Technology specificity (0-15 pts)
    5. Potential usefulness for downstream matching (0-15 pts)

    Strictly framed as "Patent Investigation Relevance" — never "infringement probability".
    """
    reasons: List[str] = []
    factors: Dict[str, Dict[str, Any]] = {}

    # 1. Relevance to requested technology niche (0-30)
    niche_ratio = float(candidate_meta.get("niche_match_score", 0.7))
    niche_pts = int(round(niche_ratio * 30))
    matched_terms = candidate_meta.get("niche_matched_terms", [])
    if technology_area and technology_area.strip().lower() not in ("", "optional", "all"):
        niche_reason = f"Niche alignment ({niche_pts}/30): Matched technology area '{technology_area}' via source indicators ({', '.join(matched_terms[:5])})."
    else:
        niche_pts = 24
        niche_reason = "Niche alignment (24/30): Unfiltered portfolio scan; evaluated on core technical scope."
    reasons.append(niche_reason)
    factors["niche_relevance"] = {"score": niche_pts, "max": 30, "detail": niche_reason}

    # 2. Claim information availability (0-20)
    ind_claims = claim_record.get("independent_claims", [])
    claims_available = bool(claim_record.get("claims_available")) and len(ind_claims) > 0
    if claims_available:
        claim_pts = 20 if len(ind_claims) >= 2 else 18
        claim_reason = f"Claim availability ({claim_pts}/20): Full English claims retrieved from dataset ({len(ind_claims)} independent claim(s) parsed verbatim)."
    else:
        claim_pts = 0
        claim_reason = "Claim availability (0/20): `claims_localized` is absent in source record; requires external file-wrapper inspection before claim-level comparison."
    reasons.append(claim_reason)
    factors["claim_availability"] = {"score": claim_pts, "max": 20, "detail": claim_reason}

    # 3. Technical richness (0-20)
    abstract_len = len(candidate_meta.get("abstract") or "")
    desc_len = len(claim_record.get("description_excerpt") or "")
    cpc_count = len(candidate_meta.get("cpc_codes") or [])
    richness_pts = min(20, (8 if abstract_len > 120 else 4) + (6 if desc_len > 80 else 2) + min(6, cpc_count * 2))
    richness_reason = f"Technical richness ({richness_pts}/20): Supported by {cpc_count} CPC classifications, detailed abstract, and specification disclosure."
    reasons.append(richness_reason)
    factors["technical_richness"] = {"score": richness_pts, "max": 20, "detail": richness_reason}

    # 4. Technology specificity (0-15)
    claim_elements = (ai_analysis or {}).get("claim_elements", [])
    total_elements = sum(len(c.get("elements", [])) for c in claim_elements) if claim_elements else 0
    key_concepts = (ai_analysis or {}).get("key_concepts", [])
    if total_elements >= 3:
        spec_pts = min(15, 10 + min(5, total_elements))
        spec_reason = f"Technology specificity ({spec_pts}/15): Independent claims decompose into {total_elements} concrete architectural/method elements ({len(key_concepts)} key technical concepts)."
    elif claims_available:
        spec_pts = 11
        spec_reason = "Technology specificity (11/15): Contains structured architectural limitations suitable for technical screening."
    else:
        spec_pts = 5
        spec_reason = "Technology specificity (5/15): Limited to abstract-level technical concepts due to missing claim text in source snapshot."
    reasons.append(spec_reason)
    factors["technology_specificity"] = {"score": spec_pts, "max": 15, "detail": spec_reason}

    # 5. Potential usefulness for downstream matching (0-15)
    rem_years = patent_life.get("estimated_remaining_term_years")
    is_granted = bool(candidate_meta.get("grant_date_raw", 0) > 0)
    if is_granted and rem_years is not None and rem_years > 2.0 and claims_available:
        downstream_pts = 15
        downstream_reason = f"Downstream matching utility (15/15): Granted patent with ~{rem_years} yrs estimated remaining term and observable system/protocol claim elements."
    elif is_granted and rem_years is not None and rem_years <= 0.0:
        downstream_pts = 5
        downstream_reason = "Downstream matching utility (5/15): Granted patent with 0.0 yrs estimated remaining statutory term (expired baseline); lower commercial priority unless past-period review applies."
    elif not is_granted and claims_available:
        downstream_pts = 10
        downstream_reason = f"Downstream matching utility (10/15): Published pre-grant application ({candidate_meta.get('kind_code')}); useful for forward-looking technical monitoring pending grant."
    else:
        downstream_pts = 4
        downstream_reason = "Downstream matching utility (4/15): Incomplete date or claim metadata restricts immediate claim-to-product mapping."
    reasons.append(downstream_reason)
    factors["downstream_usefulness"] = {"score": downstream_pts, "max": 15, "detail": downstream_reason}

    total_score = niche_pts + claim_pts + richness_pts + spec_pts + downstream_pts

    return {
        "score": total_score,
        "reasons": reasons,
        "factor_breakdown": factors
    }
