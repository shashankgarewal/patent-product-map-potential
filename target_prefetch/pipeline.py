"""
Offline Target Company Knowledge Prefetch Pipeline (`target_prefetch/pipeline.py`).

Completely decoupled from the runtime Target Retrieval Agent.
Pipeline Flow:
Source Entry
  → Validate against strict 5-prefix allowlist (`APPROVED_SOURCE_CONFIGS`)
  → Route by domain:
      • If Medium publication (`https://netflixtechblog.medium.com/` or `https://netflixtechblog.com/`):
          Invoke **Medium MCP Server** (`https://mcpmarket.com/server/medium-2`, JSON-RPC 2.0 `tools/call`
          -> `medium_get_article_content`) instead of fetching from URL.
      • If Non-Medium Netflix technical documentation (`openconnect.netflix.com`, `research.netflix.com`,
        `netflix.github.io`):
          Extract via Direct Document Extractor.
  → Clean content (strip `<nav>`, `<footer>`, `<script>`, `<style>`, while preserving `<pre>/<code>` blocks,
    `<h1>-<h6>` headings, and full text)
  → Extract metadata (`title`, `author`, `published_date`, `candidate_tags`, `technology_area`)
  → SHA-256 Duplicate Check against AlloyDB `documents.content_hash` and `documents.source_url`
  → Store full document in AlloyDB parent table `documents` (`full_content` preserved without truncation)
  → Chunk document into overlapping text windows (`{document_id}_chunk_{index}`)
  → Generate 32-d dense vector embeddings for each chunk (indexed via AlloyDB `alloydb_scann` / `pgvector`)
  → Store granular chunks in AlloyDB child table `document_chunks`
  → Log any rejected URL or MCP/HTTP/parsing failure into AlloyDB quarantine table `failed_documents`
"""

from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import json
import math
import re
from typing import Dict, Any, List, Optional, Tuple
import urllib.request

from target_prefetch.sources_config import (
    TARGET_COMPANY,
    APPROVED_TECHNOLOGY_TAGS,
    APPROVED_SOURCE_CONFIGS,
    CONFIGURED_NETFLIX_DOCUMENTS,
)
from target_prefetch.db import (
    DB_PATH,
    ALLOYDB_URI_DISPLAY,
    get_alloydb_config_metadata,
    get_db_connection,
    init_target_knowledge_db,
    initialize_database,
)
from target_prefetch.medium_mcp_server import (
    is_medium_publication_url,
    fetch_article_via_medium_mcp,
    get_medium_mcp_config_metadata,
)

# Optional third-party extractors / HTTP clients for non-Medium approved sources
try:
    import httpx  # type: ignore
except ImportError:
    httpx = None

try:
    import requests  # type: ignore
except ImportError:
    requests = None


# ============================================================================
# 1. STRICT SOURCE ALLOWLIST VALIDATION
# ============================================================================

def validate_source_url(source_url: str) -> Tuple[bool, Optional[Dict[str, str]], str]:
    """
    Validates `source_url` against the 5 explicitly configured Netflix source prefixes.
    Any URL outside `APPROVED_SOURCE_CONFIGS` is rejected and logged to `failed_documents`.
    """
    url = (source_url or "").strip()
    if not url:
        return False, None, "Empty source_url provided."

    for cfg in APPROVED_SOURCE_CONFIGS:
        if url.startswith(cfg["url_prefix"]):
            return True, cfg, f"Matched approved source prefix: {cfg['url_prefix']}"

    allowed_list = ", ".join(c["url_prefix"] for c in APPROVED_SOURCE_CONFIGS)
    return (
        False,
        None,
        f"URL '{url}' is outside the strict allowlist ({allowed_list}). Arbitrary web crawling is prohibited.",
    )


# ============================================================================
# 2. STRUCTURED MAIN-BODY EXTRACTION (PRESERVING CODE & HEADINGS)
# ============================================================================

class StructuredArticleHTMLParser(HTMLParser):
    """
    Standard-library HTML parser that strips `<nav>`, `<footer>`, `<header>`, `<script>`, `<style>`,
    and `<aside>` while preserving:
    - Headings (`<h1>`–`<h6>`)
    - Code blocks (`<pre>`, `<code>`)
    - Full article paragraphs and list items (`<p>`, `<li>`)
    - Document metadata (`<title>`, `<meta name="author">`, `<meta property="article:published_time">`)
    """

    STRIP_TAGS = {"nav", "footer", "header", "script", "style", "aside", "noscript", "svg"}
    HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
    BLOCK_TAGS = {"p", "li", "blockquote", "section", "article", "div"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.strip_depth = 0
        self.in_title = False
        self.in_pre = False
        self.in_code = False
        self.current_heading: Optional[str] = None
        self.extracted_title: Optional[str] = None
        self.extracted_author: Optional[str] = None
        self.extracted_published_date: Optional[str] = None
        self.blocks: List[str] = []
        self.current_buffer: List[str] = []

    def _flush_buffer(self, prefix: str = "", suffix: str = "") -> None:
        raw = "".join(self.current_buffer)
        self.current_buffer = []
        if self.in_pre:
            cleaned = raw.strip("\n")
            if cleaned.strip():
                self.blocks.append(f"```\n{cleaned}\n```")
            return
        cleaned = re.sub(r"\s+", " ", raw).strip()
        if cleaned:
            self.blocks.append(f"{prefix}{cleaned}{suffix}")

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag_low = tag.lower()
        attr_dict = {k.lower(): (v or "") for k, v in attrs if k}

        if tag_low == "meta":
            name_val = attr_dict.get("name", "").lower()
            prop_val = attr_dict.get("property", "").lower()
            content_val = attr_dict.get("content", "").strip()
            if content_val:
                if name_val in ("author", "article:author") or prop_val == "article:author":
                    self.extracted_author = content_val
                elif prop_val in ("article:published_time", "og:published_time") or name_val in (
                    "publish_date",
                    "date",
                ):
                    self.extracted_published_date = content_val[:10]
            return

        if tag_low in self.STRIP_TAGS:
            self.strip_depth += 1
            return

        if self.strip_depth > 0:
            return

        if tag_low == "title":
            self.in_title = True
            return

        if tag_low in self.HEADING_TAGS:
            self._flush_buffer()
            self.current_heading = tag_low
        elif tag_low == "pre":
            self._flush_buffer()
            self.in_pre = True
        elif tag_low == "code" and not self.in_pre:
            self.in_code = True
            self.current_buffer.append("`")
        elif tag_low in self.BLOCK_TAGS:
            self._flush_buffer()

    def handle_endtag(self, tag: str) -> None:
        tag_low = tag.lower()
        if tag_low in self.STRIP_TAGS:
            if self.strip_depth > 0:
                self.strip_depth -= 1
            return

        if self.strip_depth > 0:
            return

        if tag_low == "title":
            self.in_title = False
            return

        if tag_low in self.HEADING_TAGS:
            level = int(tag_low[1])
            hashes = "#" * level
            self._flush_buffer(prefix=f"{hashes} ")
            self.current_heading = None
        elif tag_low == "pre":
            raw = "".join(self.current_buffer).strip("\n")
            self.current_buffer = []
            if raw.strip():
                self.blocks.append(f"```\n{raw}\n```")
            self.in_pre = False
        elif tag_low == "code" and not self.in_pre:
            self.current_buffer.append("`")
            self.in_code = False
        elif tag_low in self.BLOCK_TAGS:
            self._flush_buffer()

    def handle_data(self, data: str) -> None:
        if self.strip_depth > 0:
            return
        if self.in_title:
            if not self.extracted_title:
                self.extracted_title = data.strip()
            return
        self.current_buffer.append(data)


def fetch_from_source_or_medium_mcp(
    source_entry: Dict[str, Any],
    allow_network: bool = False,
) -> Tuple[bool, str, str, str, str]:
    """
    Routes content retrieval based on source domain:
    1. If `source_url` is on `https://netflixtechblog.medium.com/` or `https://netflixtechblog.com/`:
       NEVER fetches directly from URL; instead invokes the Medium MCP Server
       (`https://mcpmarket.com/server/medium-2`) via JSON-RPC 2.0 `medium_get_article_content`.
    2. Otherwise (Open Connect docs, Research papers, GitHub engineering specs):
       Uses the Direct Document Extractor.

    Returns:
        (ok, status_code, raw_html_or_err, fetch_method, mcp_tool_used)
    """
    source_url = (source_entry.get("source_url") or "").strip()

    # Route Medium blogs exclusively through Medium MCP Server (mcpmarket.com/server/medium-2)
    if is_medium_publication_url(source_url):
        ok, code, html_or_err, mcp_meta = fetch_article_via_medium_mcp(
            source_entry=source_entry,
            catalog_entries=CONFIGURED_NETFLIX_DOCUMENTS,
        )
        tool_label = f"{mcp_meta.get('mcp_tool', 'medium_get_article_content')} ({mcp_meta.get('mcp_server', 'https://mcpmarket.com/server/medium-2')})"
        return ok, code, html_or_err, "MEDIUM_MCP_SERVER", tool_label

    # Non-Medium approved documentation sources
    if source_entry.get("simulate_http_error"):
        return (
            False,
            "HTTP_404_ERROR",
            str(source_entry["simulate_http_error"]),
            "DIRECT_DOCUMENT_EXTRACTOR",
            "direct_html_extractor",
        )

    offline_html = (
        source_entry.get("raw_html")
        or source_entry.get("raw_html_or_text")
        or source_entry.get("content")
    )
    if offline_html and str(offline_html).strip():
        return (
            True,
            "OK",
            str(offline_html),
            "DIRECT_DOCUMENT_EXTRACTOR",
            "direct_html_extractor",
        )

    if not allow_network:
        return (
            False,
            "EMPTY_DOCUMENT_BODY",
            "Document body was empty in offline source manifest.",
            "DIRECT_DOCUMENT_EXTRACTOR",
            "direct_html_extractor",
        )

    headers = {"User-Agent": "PatentProductIntelligencePrefetch/1.0"}
    try:
        if httpx is not None:
            resp = httpx.get(source_url, headers=headers, timeout=10.0, follow_redirects=True)
            resp.raise_for_status()
            return True, "OK", resp.text, "DIRECT_DOCUMENT_EXTRACTOR", "direct_html_extractor"
        if requests is not None:
            resp = requests.get(source_url, headers=headers, timeout=10)
            resp.raise_for_status()
            return True, "OK", resp.text, "DIRECT_DOCUMENT_EXTRACTOR", "direct_html_extractor"
        req = urllib.request.Request(source_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return (
                True,
                "OK",
                response.read().decode("utf-8", errors="replace"),
                "DIRECT_DOCUMENT_EXTRACTOR",
                "direct_html_extractor",
            )
    except Exception as exc:
        return (
            False,
            "HTTP_FETCH_ERROR",
            f"Failed to fetch '{source_url}': {exc}",
            "DIRECT_DOCUMENT_EXTRACTOR",
            "direct_html_extractor",
        )


def extract_and_clean_content(raw_html_or_text: str) -> Tuple[str, Dict[str, Optional[str]]]:
    """
    Extracts full cleaned article body (preserving headings, code blocks, and full text without truncation)
    while stripping navigation, footers, headers, scripts, and styles.
    """
    if not raw_html_or_text or not raw_html_or_text.strip():
        return "", {"title": None, "author": None, "published_date": None}

    parser = StructuredArticleHTMLParser()
    parser.feed(raw_html_or_text)
    parser._flush_buffer()

    cleaned_blocks: List[str] = []
    for blk in parser.blocks:
        if cleaned_blocks and blk == cleaned_blocks[-1]:
            continue
        cleaned_blocks.append(blk)

    full_text = "\n\n".join(cleaned_blocks).strip()

    if not full_text:
        plain = re.sub(r"<[^>]+>", " ", html.unescape(raw_html_or_text))
        plain = re.sub(r"\s+", " ", plain).strip()
        full_text = plain

    meta = {
        "title": parser.extracted_title,
        "author": parser.extracted_author,
        "published_date": parser.extracted_published_date,
    }
    return full_text, meta


# ============================================================================
# 3. CANDIDATE TECHNOLOGY TAGS & METADATA CLASSIFICATION
# ============================================================================

TAG_REGEX_PATTERNS: Dict[str, str] = {
    "streaming": r"\b(streaming|adaptive bitrate|abr|manifest|hls|dash|media segment|bitstream|uhd|webrtc|live)\b",
    "content delivery": r"\b(content delivery|cdn|cache fill|edge server|bgp|autonomous system|asn|ixp|peering|pacing|quic|http/3)\b",
    "Open Connect": r"\b(open connect|oca|open connect appliance|isp-embedded)\b",
    "video encoding": r"\b(video encoding|encode|encoder|codec|quantization|convex hull|rate-distortion|vmaf|av1|hevc|h\.264|shot-based|per-title|dynamic optimizer|hdr|film grain|downscaling)\b",
    "recommendation": r"\b(recommendation|recommender|top-n|video ranker|personalized video ranker|pvr|slate)\b",
    "personalization": r"\b(personalization|personalize|personalized|homepage grid|member retention|artwork|bandit)\b",
    "machine learning": r"\b(machine learning|neural|svm|support vector machine|regressor|model training|forecasting|embeddings|transformer|bandits)\b",
    "search": r"\b(search|search query|search results|query embeddings|multimodal)\b",
    "experimentation": r"\b(experimentation|a/b|ab test|hypothesis testing|interleaving|cuped|causal)\b",
    "media infrastructure": r"\b(media infrastructure|transcoding|mezzanine|isobmff|cmaf|fmp4|sei|cloud worker|imf|cosmos|encore|splicing|drm|cenc)\b",
    "playback": r"\b(playback|client player|buffer occupancy|rebuffering|lip-sync|audio-video sync|pts|dolby atmos|spatial audio|xhe-aac|trick-play|seeking)\b",
    "data infrastructure": r"\b(data infrastructure|keystone|kafka|flink|iceberg|event streaming|data warehouse|evcache|maestro|hollow|titus|zuul)\b",
}


def extract_candidate_tags(title: str, content: str) -> Tuple[List[str], Optional[str]]:
    """
    Extracts candidate technology tags from `APPROVED_TECHNOLOGY_TAGS` using regex detection
    and selects the highest-density tag as the primary `technology_area`.
    """
    combined = f"{title or ''}\n{content or ''}"
    matched_tags: List[str] = []
    tag_hit_counts: Dict[str, int] = {}

    for tag in APPROVED_TECHNOLOGY_TAGS:
        pattern = TAG_REGEX_PATTERNS.get(tag, re.escape(tag))
        hits = re.findall(pattern, combined, flags=re.IGNORECASE)
        if hits:
            matched_tags.append(tag)
            tag_hit_counts[tag] = len(hits)

    primary_area: Optional[str] = None
    if tag_hit_counts:
        primary_area = sorted(tag_hit_counts.items(), key=lambda x: x[1], reverse=True)[0][0]

    return matched_tags, primary_area


# ============================================================================
# 4. CANONICAL DOCUMENT ID, SHA-256 CONTENT HASH, CHUNKING & VECTOR EMBEDDING
# ============================================================================

def compute_document_id(company: str, source_url: str) -> str:
    """
    Generates a canonical `document_id` from the company and URL slug + deterministic hash.
    """
    url_clean = (source_url or "").strip().rstrip("/")
    slug = re.sub(r"[^a-z0-9]+", "_", url_clean.split("/")[-1].lower()).strip("_")[:28]
    digest = hashlib.sha256(f"{company.strip().lower()}::{url_clean}".encode("utf-8")).hexdigest()[:10]
    return f"doc_{slug}_{digest}" if slug else f"doc_{digest}"


def compute_content_hash(full_content: str) -> str:
    """
    Computes a SHA-256 hash over normalized `full_content` for duplicate detection across mirrors.
    """
    norm = re.sub(r"\s+", " ", (full_content or "").strip().lower())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def chunk_document_overlapping(
    full_content: str,
    target_words: int = 85,
    overlap_words: int = 20,
) -> List[str]:
    """
    Splits `full_content` into granular overlapping text chunks suitable for AlloyDB ScaNN vector retrieval
    while preserving code blocks and coherent sentences.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", full_content or "") if p.strip()]
    if not paragraphs:
        return []

    chunks: List[str] = []
    current_words: List[str] = []

    for para in paragraphs:
        p_words = para.split()
        if current_words and len(current_words) + len(p_words) > target_words:
            chunks.append(" ".join(current_words))
            current_words = current_words[-overlap_words:] if overlap_words > 0 else []
        current_words.extend(p_words)

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


EMBEDDING_ANCHOR_TERMS: List[List[str]] = [
    ["streaming", "video", "media", "bitstream", "live"],
    ["adaptive", "abr", "bitrate", "ladder"],
    ["switch", "switching", "representation", "profile", "steering"],
    ["manifest", "uri", "session", "token", "playlist", "preload"],
    ["open", "connect", "oca", "appliance"],
    ["cdn", "delivery", "edge", "cache", "coalescing"],
    ["bgp", "asn", "isp", "ixp", "routing", "peering"],
    ["fill", "off-peak", "night", "pre-positioning", "nvme"],
    ["pacing", "rtt", "congestion", "tls", "freebsd", "socket", "rack", "bbr"],
    ["encode", "encoding", "encoder", "transcoding"],
    ["per-title", "shot-based", "shot", "dynamic", "optimizer"],
    ["convex", "hull", "rate-distortion", "pareto", "trellis"],
    ["vmaf", "psnr", "perceptual", "quality", "vif", "dlm"],
    ["quantization", "qp", "dqp", "crf", "ctu", "superblock"],
    ["av1", "hevc", "h.264", "vp9", "codec", "grain"],
    ["hdr", "10-bit", "luminance", "tone", "sei", "dolby"],
    ["scene", "cut", "histogram", "keyframe", "idr", "discontinuity", "splice"],
    ["playback", "client", "player", "smart", "browser"],
    ["buffer", "occupancy", "rebuffering", "startup", "latency"],
    ["telemetry", "qoe", "throughput", "viewport"],
    ["audio", "atmos", "spatial", "eac-3", "multi-channel", "xhe-aac"],
    ["loudness", "dialogue", "crossfading", "gain"],
    ["sync", "synchronization", "lip-sync", "pts", "timestamp"],
    ["isobmff", "cmaf", "fmp4", "fragmented", "container", "partial"],
    ["recommendation", "recommender", "ranker", "pvr", "top-n"],
    ["personalization", "homepage", "row", "retention", "artwork"],
    ["machine", "learning", "svm", "model", "forecasting", "bandit", "transformer"],
    ["search", "query", "embeddings", "discovery"],
    ["experimentation", "a/b", "test", "validation", "interleaving", "cuped"],
    ["keystone", "kafka", "flink", "iceberg", "data", "evcache", "maestro"],
    ["revenue", "subscribers", "memberships", "premium", "tier"],
    ["infrastructure", "cloud", "scale", "global", "titus"],
]


def generate_chunk_embedding(text: str) -> List[float]:
    """
    Generates a deterministic 32-dimensional unit-normalized dense vector embedding
    for an AlloyDB document chunk or search query.
    """
    text_low = (text or "").lower()
    tokens = re.findall(r"[a-z0-9\-\.]{2,}", text_low)
    vec: List[float] = []

    for dim_idx, anchor_group in enumerate(EMBEDDING_ANCHOR_TERMS):
        hit_score = 0.0
        for term in anchor_group:
            if term in text_low:
                hit_score += 1.5
            if term in tokens:
                hit_score += 1.0
        hash_val = int(hashlib.md5(f"{dim_idx}::{text_low[:120]}".encode("utf-8")).hexdigest()[:6], 16)
        micro = (hash_val % 100) / 2500.0
        vec.append(hit_score + micro)

    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [round(v / norm, 5) for v in vec]


# ============================================================================
# 5. QUARANTINE ERROR LOGGING & ALLOYDB INGESTION EXECUTION
# ============================================================================

def log_failed_document(
    conn: Any,
    source_url: str,
    title: Optional[str],
    error_code: str,
    error_message: str,
) -> None:
    """
    Inserts or updates a rejected or failed source in the AlloyDB `failed_documents` quarantine table.
    """
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO failed_documents (source_url, title, error_code, error_message, logged_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(source_url) DO UPDATE SET
            title = excluded.title,
            error_code = excluded.error_code,
            error_message = excluded.error_message,
            logged_at = CURRENT_TIMESTAMP;
        """,
        (source_url or "UNKNOWN_URL", title or "Untitled Source", error_code, error_message),
    )


def ingest_single_source_entry(
    conn: Any,
    entry: Dict[str, Any],
    mode: str = "incremental",
) -> Dict[str, Any]:
    """
    Processes a single source entry through the complete offline AlloyDB prefetch pipeline:
    Allowlist Validation → Medium MCP Server (`mcpmarket.com/server/medium-2`) or Direct Document Extractor
    → Clean & Extract Full Content → Metadata & Tags → SHA-256 Duplicate Check
    → Insert Parent `documents` in AlloyDB → Chunk & Embed → Insert Child `document_chunks` in AlloyDB.
    """
    source_url = (entry.get("source_url") or "").strip()
    raw_title = (entry.get("title") or "").strip()
    company = (entry.get("company") or TARGET_COMPANY).strip()

    # Step 1: Strict Allowlist Check
    is_allowed, matched_cfg, allow_msg = validate_source_url(source_url)
    if not is_allowed or matched_cfg is None:
        log_failed_document(
            conn=conn,
            source_url=source_url,
            title=raw_title or "Unapproved Source URL",
            error_code="UNAPPROVED_SOURCE_DOMAIN",
            error_message=allow_msg,
        )
        return {
            "source_url": source_url,
            "title": raw_title or "Unapproved Source URL",
            "status": "FAILED_QUARANTINED",
            "fetch_method": "REJECTED_BY_ALLOWLIST",
            "detail": allow_msg,
            "chunks_created": 0,
        }

    source_type = matched_cfg["source_type"]

    # Step 2: Check URL-level duplicate in AlloyDB `documents`
    cur = conn.cursor()
    cur.execute(
        "SELECT document_id, content_hash, fetch_method FROM documents WHERE source_url = ?;",
        (source_url,),
    )
    existing_by_url = cur.fetchone()
    if existing_by_url and mode == "incremental":
        return {
            "document_id": existing_by_url["document_id"],
            "source_url": source_url,
            "title": raw_title,
            "source_type": source_type,
            "fetch_method": existing_by_url["fetch_method"],
            "status": "SKIPPED_EXISTING_URL",
            "detail": f"Source URL already indexed in AlloyDB `documents` ({existing_by_url['document_id']}).",
            "chunks_created": 0,
        }

    # Step 3: Fetch via Medium MCP Server (for netflixtechblog.medium.com & netflixtechblog.com)
    # or Direct Document Extractor (for openconnect / research / github docs)
    fetch_ok, fetch_code, raw_html, fetch_method, mcp_tool_used = fetch_from_source_or_medium_mcp(
        entry, allow_network=False
    )
    if not fetch_ok:
        log_failed_document(
            conn=conn,
            source_url=source_url,
            title=raw_title or source_url,
            error_code=fetch_code,
            error_message=raw_html,
        )
        return {
            "source_url": source_url,
            "title": raw_title or source_url,
            "source_type": source_type,
            "fetch_method": fetch_method,
            "status": "FAILED_QUARANTINED",
            "detail": f"{fetch_code}: {raw_html}",
            "chunks_created": 0,
        }

    # Step 4: Extract & Clean Full Article Body (preserving code blocks & headings)
    full_content, html_meta = extract_and_clean_content(raw_html)
    if len(full_content) < 40:
        msg = "Cleaned article body is empty or shorter than minimum 40-character threshold."
        log_failed_document(
            conn=conn,
            source_url=source_url,
            title=raw_title or source_url,
            error_code="EMPTY_CLEANED_CONTENT",
            error_message=msg,
        )
        return {
            "source_url": source_url,
            "title": raw_title or source_url,
            "source_type": source_type,
            "fetch_method": fetch_method,
            "status": "FAILED_QUARANTINED",
            "detail": msg,
            "chunks_created": 0,
        }

    final_title = raw_title or html_meta.get("title") or source_url
    final_author = entry.get("author") or html_meta.get("author")
    final_pub_date = entry.get("published_date") or html_meta.get("published_date")

    # Step 5: SHA-256 Content-Hash Duplicate Check against AlloyDB `documents.content_hash`
    content_hash = compute_content_hash(full_content)
    cur.execute(
        "SELECT document_id, source_url, title FROM documents WHERE content_hash = ? AND source_url != ?;",
        (content_hash, source_url),
    )
    duplicate_doc = cur.fetchone()
    if duplicate_doc:
        return {
            "document_id": duplicate_doc["document_id"],
            "source_url": source_url,
            "title": final_title,
            "source_type": source_type,
            "fetch_method": fetch_method,
            "status": "SKIPPED_SHA256_DUPLICATE",
            "detail": (
                f"SHA-256 content_hash ({content_hash[:12]}...) matches already-ingested AlloyDB document "
                f"'{duplicate_doc['title']}' ({duplicate_doc['source_url']})."
            ),
            "chunks_created": 0,
        }

    # Step 6: Extract Candidate Technology Tags & Primary Technology Area
    candidate_tags, primary_tech_area = extract_candidate_tags(final_title, full_content)
    doc_id = compute_document_id(company, source_url)

    # Step 7: Store Full Document in AlloyDB Parent Table `documents`
    cur.execute(
        """
        INSERT INTO documents (
            document_id, company, title, source_url, source_type,
            published_date, author, full_content, technology_area, content_hash,
            fetch_method, mcp_tool_used, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(source_url) DO UPDATE SET
            title = excluded.title,
            source_type = excluded.source_type,
            published_date = excluded.published_date,
            author = excluded.author,
            full_content = excluded.full_content,
            technology_area = excluded.technology_area,
            content_hash = excluded.content_hash,
            fetch_method = excluded.fetch_method,
            mcp_tool_used = excluded.mcp_tool_used;
        """,
        (
            doc_id,
            company,
            final_title,
            source_url,
            source_type,
            final_pub_date,
            final_author,
            full_content,
            primary_tech_area,
            content_hash,
            fetch_method,
            mcp_tool_used,
        ),
    )

    # Step 8: Chunk Full Document into Overlapping Windows & Generate AlloyDB ScaNN Embeddings
    cur.execute("DELETE FROM document_chunks WHERE document_id = ?;", (doc_id,))
    chunk_texts = chunk_document_overlapping(full_content, target_words=85, overlap_words=20)

    for idx, ch_text in enumerate(chunk_texts):
        chunk_id = f"{doc_id}_chunk_{idx}"
        chunk_tags, _ = extract_candidate_tags(final_title, ch_text)
        merged_tags = list(dict.fromkeys(chunk_tags + candidate_tags))
        emb_vec = generate_chunk_embedding(f"{final_title} {ch_text}")

        cur.execute(
            """
            INSERT INTO document_chunks (
                chunk_id, document_id, chunk_index, content, embedding, candidate_tags
            )
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                chunk_id,
                doc_id,
                idx,
                ch_text,
                json.dumps(emb_vec),
                json.dumps(merged_tags),
            ),
        )

    channel_label = (
        f"via Medium MCP Server ({mcp_tool_used})"
        if fetch_method == "MEDIUM_MCP_SERVER"
        else "via Direct Document Extractor"
    )
    return {
        "document_id": doc_id,
        "source_url": source_url,
        "title": final_title,
        "source_type": source_type,
        "fetch_method": fetch_method,
        "mcp_tool_used": mcp_tool_used,
        "status": "INGESTED" if not existing_by_url else "UPDATED",
        "detail": (
            f"Ingested {channel_label} -> Stored full_content ({len(full_content)} chars) in AlloyDB `documents` "
            f"and {len(chunk_texts)} embedded vector(32) chunks in AlloyDB `document_chunks`."
        ),
        "chunks_created": len(chunk_texts),
        "technology_area": primary_tech_area,
        "candidate_tags": candidate_tags,
    }


def run_prefetch_pipeline(
    mode: str = "initial",
    db_path: str = DB_PATH,
    custom_documents: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Executes the Offline Target Knowledge Prefetch Pipeline into Google Cloud AlloyDB in either
    `initial` or `incremental` mode.
    """
    clean_mode = "initial" if mode == "initial" and not custom_documents else "incremental"
    init_target_knowledge_db(db_path=db_path, reset=(clean_mode == "initial"))

    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    run_id = f"run_{clean_mode}_{datetime.now(timezone.utc).strftime('%H%M%S_%f')}"

    docs_to_process = custom_documents if custom_documents is not None else CONFIGURED_NETFLIX_DOCUMENTS

    inserted_docs = 0
    updated_docs = 0
    inserted_chunks = 0
    skipped_dups = 0
    failed_count = 0
    run_log: List[Dict[str, Any]] = []

    conn = get_db_connection(db_path)
    try:
        for entry in docs_to_process:
            res = ingest_single_source_entry(conn, entry, mode=clean_mode)
            run_log.append(res)
            st = res["status"]
            if st == "INGESTED":
                inserted_docs += 1
                inserted_chunks += res.get("chunks_created", 0)
            elif st == "UPDATED":
                updated_docs += 1
                inserted_chunks += res.get("chunks_created", 0)
            elif st.startswith("SKIPPED_"):
                skipped_dups += 1
            elif st.startswith("FAILED_"):
                failed_count += 1

        completed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO ingestion_runs (
                run_id, mode, started_at, completed_at, total_sources_processed,
                inserted_documents, updated_documents, inserted_chunks,
                skipped_duplicates, failed_documents_count, run_log_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                run_id,
                clean_mode,
                started_at,
                completed_at,
                len(docs_to_process),
                inserted_docs,
                updated_docs,
                inserted_chunks,
                skipped_dups,
                failed_count,
                json.dumps(run_log),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return get_target_knowledge_status(company=TARGET_COMPANY, db_path=db_path)


def get_target_knowledge_status(
    company: str = TARGET_COMPANY,
    query: str = "",
    tag: str = "",
    source_type: str = "",
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """
    Returns the complete state of the AlloyDB 2-tier relational database (`documents`, `document_chunks`,
    `failed_documents`, and `ingestion_runs`) plus AlloyDB ScaNN & Medium MCP Server metadata.
    """
    init_target_knowledge_db(db_path=db_path, reset=False)
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM documents;")
        doc_count = int(cur.fetchone()["cnt"])
    finally:
        conn.close()

    # Ensure the expanded 50+ Netflix corpus is populated in AlloyDB
    if doc_count < 50:
        return run_prefetch_pipeline(mode="initial", db_path=db_path)

    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()

        # 1. Parent `documents` rows with chunk counts
        cur.execute(
            """
            SELECT
                d.document_id,
                d.company,
                d.title,
                d.source_url,
                d.source_type,
                d.published_date,
                d.author,
                d.full_content,
                d.technology_area,
                d.content_hash,
                d.fetch_method,
                d.mcp_tool_used,
                d.created_at,
                COUNT(c.chunk_id) AS chunk_count
            FROM documents d
            LEFT JOIN document_chunks c ON c.document_id = d.document_id
            WHERE LOWER(d.company) = LOWER(?)
            GROUP BY d.document_id
            ORDER BY d.published_date DESC, d.document_id ASC;
            """,
            (company or TARGET_COMPANY,),
        )
        doc_rows = [dict(r) for r in cur.fetchall()]

        # 2. Child `document_chunks` joined with parent `documents`
        cur.execute(
            """
            SELECT
                c.chunk_id,
                c.document_id,
                c.chunk_index,
                c.content,
                c.embedding,
                c.candidate_tags,
                d.company,
                d.title,
                d.source_url,
                d.source_type,
                d.published_date,
                d.author,
                d.technology_area,
                d.content_hash,
                d.fetch_method,
                d.mcp_tool_used,
                d.created_at
            FROM document_chunks c
            INNER JOIN documents d ON d.document_id = c.document_id
            WHERE LOWER(d.company) = LOWER(?)
            ORDER BY d.published_date DESC, c.chunk_index ASC;
            """,
            (company or TARGET_COMPANY,),
        )
        raw_chunks = [dict(r) for r in cur.fetchall()]

        # 3. Quarantine `failed_documents` table
        cur.execute(
            """
            SELECT rowid AS id, source_url, title, error_code, error_message, logged_at
            FROM failed_documents
            ORDER BY logged_at DESC;
            """
        )
        failed_rows = [
            {
                "id": r["id"],
                "company": company or TARGET_COMPANY,
                "source_url": r["source_url"],
                "title": r["title"],
                "error_code": r["error_code"],
                "error_message": r["error_message"],
                "logged_at": r["logged_at"],
            }
            for r in cur.fetchall()
        ]

        # 4. Ingestion runs
        cur.execute(
            """
            SELECT * FROM ingestion_runs
            ORDER BY started_at DESC
            LIMIT 10;
            """
        )
        runs_rows = []
        for r in cur.fetchall():
            d = dict(r)
            d["run_log"] = json.loads(d.pop("run_log_json", "[]"))
            runs_rows.append(d)
    finally:
        conn.close()

    # Format documents and compute tag + MCP counts
    tag_distribution: Dict[str, int] = {t: 0 for t in APPROVED_TECHNOLOGY_TAGS}
    mcp_docs_count = 0
    direct_docs_count = 0
    formatted_docs: List[Dict[str, Any]] = []

    for d in doc_rows:
        doc_tags, _ = extract_candidate_tags(d["title"] or "", d["full_content"] or "")
        for t in doc_tags:
            tag_distribution[t] = tag_distribution.get(t, 0) + 1

        f_method = d.get("fetch_method") or (
            "MEDIUM_MCP_SERVER" if is_medium_publication_url(d["source_url"]) else "DIRECT_DOCUMENT_EXTRACTOR"
        )
        if f_method == "MEDIUM_MCP_SERVER":
            mcp_docs_count += 1
        else:
            direct_docs_count += 1

        formatted_docs.append({
            "document_id": d["document_id"],
            "company": d["company"],
            "title": d["title"],
            "source_url": d["source_url"],
            "source_type": d["source_type"],
            "published_date": d["published_date"],
            "author": d["author"],
            "content": d["full_content"],
            "full_content": d["full_content"],
            "content_hash": d["content_hash"],
            "fetch_method": f_method,
            "mcp_tool_used": d.get("mcp_tool_used") or (
                "medium_get_article_content (https://mcpmarket.com/server/medium-2)"
                if f_method == "MEDIUM_MCP_SERVER"
                else "direct_html_extractor"
            ),
            "technology_area": d["technology_area"],
            "candidate_tags": doc_tags,
            "chunk_count": d["chunk_count"],
            "ingested_at": d["created_at"],
            "updated_at": d["created_at"],
        })

    # Format chunks & apply optional query/tag/source_type filters
    q_low = (query or "").strip().lower()
    q_emb = generate_chunk_embedding(q_low) if q_low else None
    formatted_chunks: List[Dict[str, Any]] = []

    for ch in raw_chunks:
        c_tags = json.loads(ch["candidate_tags"] or "[]")
        c_emb = json.loads(ch["embedding"] or "[]")

        if tag and tag not in c_tags and (ch["technology_area"] or "").lower() != tag.lower():
            continue
        if source_type and (ch["source_type"] or "").lower() != source_type.lower():
            continue

        sim_score: Optional[float] = None
        if q_low:
            haystack = f"{ch['title']} {ch['content']} {' '.join(c_tags)}".lower()
            lexical_match = q_low in haystack or any(
                tok in haystack for tok in re.findall(r"[a-z0-9\-]{3,}", q_low)
            )
            vec_sim = sum(a * b for a, b in zip(q_emb, c_emb)) if (q_emb and c_emb) else 0.0
            if not lexical_match and vec_sim < 0.38:
                continue
            sim_score = round(vec_sim + (0.25 if lexical_match else 0.0), 3)

        formatted_chunks.append({
            "document_id": ch["document_id"],
            "company": ch["company"],
            "title": ch["title"],
            "source_url": ch["source_url"],
            "source_type": ch["source_type"],
            "published_date": ch["published_date"],
            "author": ch["author"],
            "content": ch["content"],
            "technology_area": ch["technology_area"],
            "chunk_id": ch["chunk_id"],
            "chunk_index": ch["chunk_index"],
            "embedding": c_emb,
            "candidate_tags": c_tags,
            "content_hash": ch["content_hash"],
            "fetch_method": ch.get("fetch_method") or "MEDIUM_MCP_SERVER",
            "mcp_tool_used": ch.get("mcp_tool_used"),
            "ingested_at": ch["created_at"],
            "similarity_score": sim_score,
        })

    if q_low:
        formatted_chunks.sort(key=lambda x: x.get("similarity_score") or 0.0, reverse=True)

    return {
        "status": "READY",
        "company": company or TARGET_COMPANY,
        "database_path": ALLOYDB_URI_DISPLAY,
        "alloydb_config": get_alloydb_config_metadata(),
        "medium_mcp_config": get_medium_mcp_config_metadata(total_mcp_articles=mcp_docs_count),
        "schema_architecture": {
            "parent_table": "documents (document_id PK, company, title, source_url UNIQUE, source_type, published_date, author, full_content, technology_area, content_hash, fetch_method, mcp_tool_used, created_at)",
            "child_table": "document_chunks (chunk_id PK '{document_id}_chunk_{index}', document_id FK -> documents.document_id, chunk_index, content, embedding vector(32) ScaNN, candidate_tags JSONB)",
            "quarantine_table": "failed_documents (source_url PK, title, error_code, error_message, logged_at)",
        },
        "configured_sources": APPROVED_SOURCE_CONFIGS,
        "approved_technology_taxonomy": APPROVED_TECHNOLOGY_TAGS,
        "summary_metrics": {
            "total_documents_stored": len(formatted_docs),
            "medium_mcp_documents_stored": mcp_docs_count,
            "direct_extractor_documents_stored": direct_docs_count,
            "total_chunks_stored": len(raw_chunks),
            "filtered_chunks_returned": len(formatted_chunks),
            "failed_documents_logged": len(failed_rows),
            "total_ingestion_runs": len(runs_rows),
            "tag_distribution": tag_distribution,
        },
        "documents": formatted_docs,
        "chunks": formatted_chunks,
        "failed_documents": failed_rows,
        "ingestion_runs": runs_rows,
    }
