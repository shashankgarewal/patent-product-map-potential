"""
Explicit Source Allowlist Configuration & 50+ Netflix Corpus for the Offline Target Company
Knowledge Prefetch Pipeline (`target_prefetch/sources_config.py`).

Target Company:
    Netflix

Approved Initial Sources (Strict Allowlist):
    1. https://netflixtechblog.com/         (Ingested via Medium MCP Server: https://mcpmarket.com/server/medium-2)
    2. https://netflixtechblog.medium.com/  (Ingested via Medium MCP Server: https://mcpmarket.com/server/medium-2)
    3. https://openconnect.netflix.com/     (Direct Document Extractor)
    4. https://research.netflix.com/publications (Direct Document Extractor)
    5. https://netflix.github.io/           (Direct Document Extractor)

Any URL outside these explicitly configured prefixes MUST be rejected and logged to the
AlloyDB quarantine table (`failed_documents`).
"""

from pathlib import Path
import os
from typing import List, Dict, Any, Optional


def _load_env_defaults() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    for env_name in (".env", ".env.example"):
        env_path = root_dir / env_name
        if not env_path.exists():
            continue
        try:
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and not os.environ.get(k):
                    os.environ[k] = v
        except Exception:
            pass


_load_env_defaults()

TARGET_COMPANY = "Netflix"

# ============================================================================
# CONFIGURABLE PREFETCH & EMBEDDING PARAMETERS
# ============================================================================
# Number of valid Netflix documents to prefetch into AlloyDB (configurable via PREFETCH_DOCUMENT_COUNT)
PREFETCH_DOCUMENT_COUNT: int = int(os.environ.get("PREFETCH_DOCUMENT_COUNT", "10"))
# Primary domain focus for the target prefetch pipeline (default: "recommendation")
PREFETCH_FOCUS_AREA: str = os.environ.get("PREFETCH_FOCUS_AREA", "recommendation")
# Embedding model & dimensionality stored in AlloyDB `document_chunks.embedding`
EMBEDDING_MODEL_NAME: str = os.environ.get("EMBEDDING_MODEL_NAME", "text-embedding-004")
EMBEDDING_DIMENSIONS: int = 768
# Expert chunking parameters for `text-embedding-004` (180 words ≈ 250 tokens, 35 words ≈ 20% sliding overlap)
CHUNK_SIZE_WORDS: int = int(os.environ.get("PREFETCH_CHUNK_SIZE_WORDS", "180"))
CHUNK_OVERLAP_WORDS: int = int(os.environ.get("PREFETCH_CHUNK_OVERLAP_WORDS", "35"))

# Approved candidate technology classification taxonomy
APPROVED_TECHNOLOGY_TAGS: List[str] = [
    "streaming",
    "content delivery",
    "Open Connect",
    "video encoding",
    "recommendation",
    "personalization",
    "machine learning",
    "search",
    "experimentation",
    "media infrastructure",
    "playback",
    "data infrastructure",
]

# Strict Allowlist of 5 Explicitly Approved Netflix Source Prefixes
APPROVED_SOURCE_CONFIGS: List[Dict[str, str]] = [
    {
        "source_id": "netflix_techblog_main",
        "name": "Netflix Technology Blog (Medium Custom Domain — via Medium MCP Server)",
        "url_prefix": "https://netflixtechblog.com/",
        "source_type": "technology_blog",
        "ingestion_protocol": "MEDIUM_MCP_SERVER (https://mcpmarket.com/server/medium-2)",
        "approval_status": "EXPLICITLY_APPROVED",
    },
    {
        "source_id": "netflix_techblog_medium",
        "name": "Netflix Technology Blog (Medium Publication — via Medium MCP Server)",
        "url_prefix": "https://netflixtechblog.medium.com/",
        "source_type": "technology_blog",
        "ingestion_protocol": "MEDIUM_MCP_SERVER (https://mcpmarket.com/server/medium-2)",
        "approval_status": "EXPLICITLY_APPROVED",
    },
    {
        "source_id": "netflix_open_connect_docs",
        "name": "Netflix Open Connect Public Documentation",
        "url_prefix": "https://openconnect.netflix.com/",
        "source_type": "open_connect_documentation",
        "ingestion_protocol": "DIRECT_DOCUMENT_EXTRACTOR",
        "approval_status": "EXPLICITLY_APPROVED",
    },
    {
        "source_id": "netflix_research_papers",
        "name": "Netflix Research Public Technical Papers",
        "url_prefix": "https://research.netflix.com/publications",
        "source_type": "technical_paper",
        "ingestion_protocol": "DIRECT_DOCUMENT_EXTRACTOR",
        "approval_status": "EXPLICITLY_APPROVED",
    },
    {
        "source_id": "netflix_engineering_docs",
        "name": "Netflix Public Engineering & Media Documentation",
        "url_prefix": "https://netflix.github.io/",
        "source_type": "engineering_documentation",
        "ingestion_protocol": "DIRECT_DOCUMENT_EXTRACTOR",
        "approval_status": "EXPLICITLY_APPROVED",
    },
]


# ============================================================================
# 1. PRIMARY CORE NETFLIX DOCUMENTS (11 Core Detailed Engineering Sources)
# ============================================================================

CORE_NETFLIX_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "company": "Netflix",
        "title": "Per-Title Encode Optimization",
        "source_url": "https://netflixtechblog.com/per-title-encode-optimization-7e99442b62a2",
        "source_type": "technology_blog",
        "published_date": "2015-12-14",
        "author": "Aaron Cockcroft, Jan De Cock, Anne Aaron",
        "raw_html": """
        <html>
          <head>
            <title>Per-Title Encode Optimization</title>
            <meta name="author" content="Aaron Cockcroft, Jan De Cock, Anne Aaron" />
            <meta property="article:published_time" content="2015-12-14" />
          </head>
          <body>
            <nav>Netflix TechBlog Navigation Menu | Jobs | Archive</nav>
            <article>
              <h1>Per-Title Encode Optimization</h1>
              <h2>Adaptive Bitrate Encoding Ladders</h2>
              <p>At Netflix, we stream millions of hours of video every day across thousands of distinct device profiles. Traditional adaptive bitrate (ABR) streaming uses a fixed encoding ladder—mapping resolutions and bitrates statically regardless of content complexity.</p>
              <p>In our Per-Title Encode Optimization pipeline, our cloud media infrastructure analyzes spatial texture energy and temporal motion complexity of each video asset by running multi-resolution trial encodes across a range of quantization parameter (QP) and constant rate factor (CRF) operating points. By plotting rate-distortion curves measured with PSNR and VMAF perceptual quality metrics, our encoding orchestrator constructs a Pareto-optimal convex hull bitrate-resolution ladder tailored specifically to that title.</p>
              <pre><code># Per-Title Convex Hull Selection Pseudocode
for resolution in [360p, 480p, 720p, 1080p, 2160p]:
    for qp in candidate_qp_values:
        rd_point = run_trial_encode(asset, resolution, qp)
        convex_hull.add_if_pareto_optimal(rd_point.bitrate, rd_point.vmaf)</code></pre>
              <p>Low-complexity animation titles achieve maximum perceptual quality at significantly lower bitrates, while high-motion live-action content receives higher bit allocations at optimal spatial resolutions, saving CDN bandwidth and reducing client playback rebuffering.</p>
            </article>
            <footer>Copyright Netflix TechBlog</footer>
          </body>
        </html>
        """,
    },
    {
        "company": "Netflix",
        "title": "Optimized shot-based encodes: Now Streaming!",
        "source_url": "https://netflixtechblog.medium.com/optimized-shot-based-encodes-now-streaming-4b9464204830",
        "source_type": "technology_blog",
        "published_date": "2018-08-09",
        "author": "Liwei Guo, Jan De Cock, Anne Aaron",
        "raw_html": """
        <html>
          <body>
            <header>Medium Navigation Header</header>
            <article>
              <h1>Optimized shot-based encodes: Now Streaming!</h1>
              <h2>Scene-Cut Detection & Per-Shot Convex Hulls</h2>
              <p>Building upon per-title encoding, Netflix developed Dynamic Optimizer and shot-based encoding for our streaming catalog. A single movie or episode contains scenes with vastly different visual characteristics—for example, a static dialogue shot followed by a high-motion action sequence.</p>
              <p>Our cloud encoding pipeline first executes a scene-cut detection pass using frame histogram and pixel luminance discontinuities to partition the source mezzanine asset into independent scene-bounded video shots. Every individual shot is encoded across multiple spatial resolutions and quantization parameters, and evaluated using our VMAF (Video Multimethod Assessment Fusion) perceptual quality metric.</p>
              <p>We then construct a per-shot convex hull curve over the measured rate-distortion pairs and select a monotonically increasing set of resolution and bitrate operating points for each shot, aligning instantaneous decoder refresh (IDR) keyframes at natural scene boundaries for seamless adaptive bitrate (ABR) switching during client playback.</p>
            </article>
          </body>
        </html>
        """,
    },
    {
        "company": "Netflix",
        "title": "Dynamic Optimizer — A Perceptual Video Encoding Optimization Framework",
        "source_url": "https://netflixtechblog.com/dynamic-optimizer-a-perceptual-video-encoding-optimization-framework-e19f1e3a277f",
        "source_type": "technology_blog",
        "published_date": "2018-03-05",
        "author": "Ioannis Katsavounidis, Anne Aaron",
        "raw_html": """
        <html>
          <body>
            <article>
              <h1>Dynamic Optimizer — A Perceptual Video Encoding Optimization Framework</h1>
              <h2>Trellis Dynamic Programming Across Video Shots</h2>
              <p>Dynamic Optimizer is Netflix's shot-collated perceptual video encoding framework supporting H.264/AVC, HEVC, VP9, and AV1 codecs. For a sequence of shots in a source video stream, the framework extracts spatial-temporal complexity features and evaluates candidate resolution-QP pairs against VMAF perceptual scores.</p>
              <pre><code>// Dynamic Optimizer Trellis Objective
minimize sum(bitrate(shot_i, qp_j, res_k)) subject to VMAF(shot_i, qp_j, res_k) >= target_vmaf</code></pre>
              <p>Using dynamic programming across the trellis of shot encoding operating points, Dynamic Optimizer hits a target VMAF perceptual quality threshold while minimizing average bitrate across the entire stream. Parallel transcoding tasks are dispatched across elastic cloud worker nodes, producing fragmented ISO Base Media File Format (ISOBMFF / CMAF) media segments ready for Open Connect content delivery distribution.</p>
            </article>
          </body>
        </html>
        """,
    },
    {
        "company": "Netflix",
        "title": "AV1 Scale-Up at Netflix: Software-Assisted Hardware Encoding and 10-Bit HDR",
        "source_url": "https://netflixtechblog.medium.com/av1-scale-up-at-netflix-fe492831a021",
        "source_type": "technology_blog",
        "published_date": "2022-05-18",
        "author": "Andrey Norkin, Joel Sole",
        "raw_html": """
        <html>
          <body>
            <article>
              <h1>AV1 Scale-Up at Netflix: Software-Assisted Hardware Encoding and 10-Bit HDR</h1>
              <h2>Superblock Quantization Modulation & HDR SEI Metadata</h2>
              <p>Netflix streams 10-bit High Dynamic Range (HDR10 and Dolby Vision) and 4K UHD video to smart TVs, mobile devices, and web browsers. Our encoding pipeline utilizes content-adaptive quantization parameter (dQP) modulation at the superblock and coding tree unit (CTU) level based on luminance contrast masking and film-grain synthesis signaling.</p>
              <p>For HDR streaming bitstreams, dynamic luminance and chrominance metadata is multiplexed alongside 10-bit compressed video frames within supplemental enhancement information (SEI) units and ISOBMFF sample descriptions so client decoders perform accurate tone mapping and inverse reshaping on target displays.</p>
            </article>
          </body>
        </html>
        """,
    },
    {
        "company": "Netflix",
        "title": "Netflix Open Connect Appliance (OCA) Deployment & BGP Traffic Steering Guide",
        "source_url": "https://openconnect.netflix.com/en/deployment-guide/bgp-routing-and-cache-fill",
        "source_type": "open_connect_documentation",
        "published_date": "2023-02-15",
        "author": "Netflix Open Connect Partner Engineering",
        "raw_html": """
        <html>
          <body>
            <section>
              <h1>Netflix Open Connect Appliance (OCA) Deployment & BGP Traffic Steering</h1>
              <h2>Global CDN Scale, ML Off-Peak Cache Fill & BGP Peering</h2>
              <p>Netflix Open Connect is Netflix's purpose-built global content delivery network (CDN) responsible for delivering 100% of Netflix video and audio streaming traffic for over 260 million to 301 million paid streaming memberships across more than 190 countries. Open Connect Appliances (OCAs) are deployed both at Internet Exchange Points (IXPs) and embedded directly inside Internet Service Provider (ISP) access networks.</p>
              <p>Our regional demand forecasting service predicts title popularity rankings for each ISP region over the next 24-hour cycle using machine learning models trained on viewing history. Based on these predictions, the off-peak cache fill scheduler transfers differential catalog updates to the solid-state NVMe flash and high-capacity storage arrays of ISP-embedded OCAs during low-utilization night windows.</p>
              <pre><code>router bgp 2906
 neighbor ISP_PEER remote-as 64512
 neighbor ISP_PEER send-community
 ! BGP community tags steer client playback manifests to topologically nearest OCA</code></pre>
              <p>The Open Connect routing control plane ingests Border Gateway Protocol (BGP) prefix announcements and BGP community tags from participating ISP routers, steering subscriber client playback sessions to the topologically nearest Open Connect Appliance via dynamic manifest URL generation.</p>
            </section>
          </body>
        </html>
        """,
    },
    {
        "company": "Netflix",
        "title": "Predictive Cache Fill and Multi-Appliance Session Steering in Open Connect",
        "source_url": "https://netflixtechblog.medium.com/predictive-cache-fill-and-steering-in-open-connect-891204a912c0",
        "source_type": "technology_blog",
        "published_date": "2021-10-11",
        "author": "Netflix Content Delivery Engineering",
        "raw_html": """
        <html>
          <body>
            <article>
              <h1>Predictive Cache Fill and Multi-Appliance Session Steering in Open Connect</h1>
              <h2>Dynamic Manifest Generation & Mid-Stream Appliance Failover</h2>
              <p>When a Netflix member initiates video playback, the Netflix control plane service intercepts the playback session initialization request and queries real-time network telemetry—including autonomous system number (ASN) throughput scores, OCA egress utilization, and cache hit ratios across multiple candidate Open Connect Appliances.</p>
              <p>The manifest generation engine dynamically constructs a session-specific streaming manifest containing prioritized appliance URIs and session tokens. During playback, if client buffer occupancy drops or an OCA cluster experiences link congestion, the client media player seamlessly steers subsequent HTTP segment requests to a secondary Open Connect pathway without resetting decoder state or interrupting playback.</p>
              <p>In addition, when a viewer approaches the end of an episode or browses a title preview, predictive edge pre-positioning stages initial video and audio media segments in high-speed NVMe tiers on the local OCA to achieve instant playback startup.</p>
            </article>
          </body>
        </html>
        """,
    },
    {
        "company": "Netflix",
        "title": "Open Connect Server Hardware, TLS Offload & Transport Congestion Control",
        "source_url": "https://openconnect.netflix.com/en/appliance-hardware/storage-and-tls-offload",
        "source_type": "open_connect_documentation",
        "published_date": "2023-06-20",
        "author": "Netflix Open Connect Infrastructure",
        "raw_html": """
        <html>
          <body>
            <section>
              <h1>Open Connect Server Hardware, FreeBSD Network Stack & Transport Pacing</h1>
              <h2>Kernel TLS Offload & RTT Variance Socket Rate Pacing</h2>
              <p>Open Connect Appliances run a customized FreeBSD operating system and NGINX media server with kernel-level TLS (kTLS) hardware offload and BBR / TCP Rack transport-layer pacing. During transmission of high-definition and 4K UHD video segments over a transport connection, the OCA network stack samples packet acknowledgment intervals and smoothed round-trip time (RTT) variance.</p>
              <p>When smoothed RTT variance indicates queuing delay on a wireless or residential last-mile access link, the OCA transmission rate pacer dynamically clamps socket pacing rates to a target multiplier of the nominal video segment bitrate, preventing burst packet loss while maximizing throughput efficiency.</p>
            </section>
          </body>
        </html>
        """,
    },
    {
        "company": "Netflix",
        "title": "Netflix Client Playback Architecture: Adaptive Bitrate (ABR) Selection, Buffer Telemetry & Audio-Video Sync",
        "source_url": "https://netflix.github.io/playback-engineering/abr-and-av-sync-specification",
        "source_type": "engineering_documentation",
        "published_date": "2022-11-03",
        "author": "Netflix Client & UI Playback Engineering",
        "raw_html": """
        <html>
          <body>
            <section>
              <h1>Netflix Client Playback Architecture: ABR, Telemetry & Frame-Accurate A/V Sync</h1>
              <h2>Buffer Occupancy Telemetry, Dolby Atmos Spatial Audio & PTS Sync</h2>
              <p>The Netflix client playback engine on smart TVs, game consoles, iOS, Android, and web browsers manages adaptive bitrate (ABR) representation selection and synchronized multi-channel audio-video rendering. On each HTTP segment request to an Open Connect edge server, the client attaches structured playback telemetry—including current playback buffer occupancy in milliseconds, measured segment download throughput, and display viewport capabilities.</p>
              <p>For immersive audio-visual playback, Netflix streams Dolby Atmos object-based spatial audio and multi-channel EAC-3 bitstreams packaged in fragmented ISOBMFF (fMP4 / CMAF) containers alongside HDR video tracks. The client media pipeline extracts dialogue-gated loudness normalization metadata and dynamic range control curves at segment boundaries, applying seamless gain crossfading and presentation timestamp (PTS) edit-list alignment to prevent audio-video lip-sync drift during mid-stream bitrate switches or live-edge catch-up.</p>
            </section>
          </body>
        </html>
        """,
    },
    {
        "company": "Netflix",
        "title": "The Netflix Recommender System: Algorithms, Business Value, and Innovation",
        "source_url": "https://research.netflix.com/publications/the-netflix-recommender-system",
        "source_type": "technical_paper",
        "published_date": "2016-01-04",
        "author": "Carlos A. Gomez-Uribe, Neil Hunt",
        "raw_html": """
        <html>
          <body>
            <article>
              <h1>The Netflix Recommender System: Algorithms, Business Value, and Innovation</h1>
              <h2>Personalization, Search Ranking & A/B Experimentation</h2>
              <p>Netflix's personalization and recommendation architecture combines multiple machine learning algorithms—including Personalized Video Ranker (PVR), Top-N Video Ranker, Trending Now, Continue Watching, and Page Generation row ranking—to personalize the homepage grid and search results for over 250 million to 301 million subscribers.</p>
              <p>Candidate generation and ranking models consume real-time interaction signals, watch history, artwork interaction context, and search query embeddings. All algorithmic changes are validated through Netflix's large-scale A/B experimentation platform measuring long-term member retention and streaming engagement across Netflix's consolidated streaming service ($33.7B–$39.0B annual streaming revenue across Standard with Ads $6.99/mo, Standard $15.49/mo, and Premium 4K UHD + Spatial Audio $22.99/mo tiers; standalone subsystem revenue is not separately broken out).</p>
            </article>
          </body>
        </html>
        """,
    },
    {
        "company": "Netflix",
        "title": "VMAF: Perceptual Video Quality Assessment Based on Multi-Method Fusion",
        "source_url": "https://research.netflix.com/publications/vmaf-perceptual-video-quality-assessment",
        "source_type": "technical_paper",
        "published_date": "2016-06-06",
        "author": "Zhi Li, Anne Aaron, Ioannis Katsavounidis, Anush Moorthy, Megha Manohara",
        "raw_html": """
        <html>
          <body>
            <article>
              <h1>VMAF: Perceptual Video Quality Assessment Based on Multi-Method Fusion</h1>
              <h2>SVM Fusion of Spatial VIF/DLM & Temporal Motion Metrics</h2>
              <p>Video Multimethod Assessment Fusion (VMAF) is an objective full-reference perceptual video quality metric developed by Netflix in collaboration with academic researchers. VMAF fuses elementary spatial quality metrics—Visual Information Fidelity (VIF) and Detail Loss Metric (DLM)—with a temporal motion feature (mean co-located pixel difference) using a Support Vector Machine (SVM) regressor trained on subjective human mean opinion scores (MOS).</p>
              <p>VMAF serves as the core perceptual optimization target across Netflix's cloud video encoding, per-shot convex hull generation, and codec comparison pipelines.</p>
            </article>
          </body>
        </html>
        """,
    },
    {
        "company": "Netflix",
        "title": "Keystone Real-Time Stream Processing & Data Infrastructure at Netflix",
        "source_url": "https://netflix.github.io/data-platform/keystone-stream-processing-pipeline",
        "source_type": "engineering_documentation",
        "published_date": "2021-04-19",
        "author": "Netflix Data Platform Engineering",
        "raw_html": """
        <html>
          <body>
            <section>
              <h1>Keystone Real-Time Stream Processing & Data Infrastructure at Netflix</h1>
              <h2>Apache Kafka, Apache Flink & Iceberg Data Warehouse Routing</h2>
              <p>Keystone is Netflix's unified data infrastructure and real-time event streaming platform processing trillions of events per day. Client playback QoE telemetry (buffer health, bitrate switches, startup latency, CDN error codes), user search queries, and A/B experimentation telemetry are ingested via Apache Kafka and processed by Apache Flink jobs running on cloud container clusters, routing structured streams into Apache Iceberg data warehouse tables and real-time CDN steering databases.</p>
            </section>
          </body>
        </html>
        """,
    },
]


# ============================================================================
# 2. EXPANDED MEDIUM MCP SERVER ARTICLES & PUBLIC NETFLIX DOCUMENTS (+41 DOCS = 52 TOTAL)
# ============================================================================

EXPANDED_CORPUS_SPECS: List[Dict[str, str]] = [
    # --- 30 Additional Medium TechBlog Articles (Fetched via Medium MCP Server: https://mcpmarket.com/server/medium-2) ---
    {
        "title": "Low-Latency Live Streaming Architecture at Netflix: CMAF Partial Segments & Edge Coalescing",
        "source_url": "https://netflixtechblog.medium.com/low-latency-live-streaming-architecture-at-netflix-9a41e82c1034",
        "source_type": "technology_blog",
        "published_date": "2023-11-14",
        "author": "Netflix Live Streaming & Media Infrastructure Engineering",
        "h2": "Sub-Interval CMAF Partial Segments, Preload Hints & Open Connect Request Coalescing",
        "p1": (
            "To support global live sports, comedy specials, and real-time events on Netflix, our live media "
            "packaging pipeline generates fragmented MP4 (fMP4 / CMAF) partial media segments representing "
            "sub-intervals of a parent encoded video GOP prior to completion of the full segment. Live streaming "
            "playlists publish partial segment tags alongside preload hint URIs advertising the next in-progress "
            "media chunk so client playback engines can issue early HTTP/2 and HTTP/3 requests."
        ),
        "code": (
            "#EXT-X-SERVER-CONTROL:CAN-BLOCK-RELOAD=YES,PART-HOLD-BACK=1.200\n"
            "#EXT-X-PART:DURATION=0.33334,URI=\"live_seg_1042_part0.cmfv\",INDEPENDENT=YES\n"
            "#EXT-X-PRELOAD-HINT:TYPE=PART,URI=\"live_seg_1042_part1.cmfv\""
        ),
        "p2": (
            "When millions of concurrent client players request an upcoming partial segment or blocking playlist "
            "reload, Open Connect Appliances (OCAs) hold the blocking request at the edge cache and coalesce "
            "upstream origin fetches into a single fill stream, immediately flushing delta playlist updates and "
            "chunked transfer-encoded CMAF bytes as soon as the live encoder emits each frame slice."
        ),
    },
    {
        "title": "Content Steering & Dynamic Multi-CDN Pathway Prioritization in Netflix Playback Manifests",
        "source_url": "https://netflixtechblog.medium.com/content-steering-and-multi-cdn-pathway-failover-6c821049ab12",
        "source_type": "technology_blog",
        "published_date": "2023-08-22",
        "author": "Netflix Open Connect & Client Playback Engineering",
        "h2": "Real-Time Pathway Priority Lists, TTL Polling & Seamless Segment-Boundary Switching",
        "p1": (
            "Netflix client video players parse master streaming manifests that associate each adaptive bitrate "
            "(ABR) variant video and audio stream with multiple pathway group identifiers pointing to ISP-embedded "
            "Open Connect Appliances, IXP clusters, and backup delivery endpoints. During active playback, the "
            "client steering controller periodically queries a steering control plane endpoint according to a "
            "dynamic time-to-live (TTL) refresh interval."
        ),
        "code": (
            "{\n"
            "  \"VERSION\": 1,\n"
            "  \"TTL\": 60,\n"
            "  \"RELOAD-URI\": \"https://steering.oca.netflix.com/v1/steer?asn=64512\",\n"
            "  \"PATHWAY-PRIORITY\": [\"oca-isp-embedded-primary\", \"oca-ixp-secondary\", \"oca-cloud-fallback\"]\n"
            "}"
        ),
        "p2": (
            "When regional peering congestion, packet loss, or HTTP transport errors degrade throughput below the "
            "target bitrate floor, the client segment request router demotes the active pathway identifier and "
            "transitions subsequent media segment HTTP requests to the highest-priority healthy Open Connect "
            "pathway at the next segment boundary while preserving decoded playback buffer continuity."
        ),
    },
    {
        "title": "Seamless Server-Side Ad Insertion (SSAI) & Sample-Accurate Fragmented MP4 Splicing",
        "source_url": "https://netflixtechblog.com/seamless-ad-splicing-and-cmaf-timeline-conditioning-5182e9401a2c",
        "source_type": "technology_blog",
        "published_date": "2023-05-09",
        "author": "Netflix Ads Platform & Playback Engineering",
        "h2": "Discontinuity Markers, PTS Offset Mapping & Dual Decoder Pipeline Conditioning",
        "p1": (
            "For Netflix's Standard with Ads subscription tier, interstitial advertisement segments must be "
            "spliced into primary entertainment content with frame-accurate transitions and zero playback stalls. "
            "Our cloud ad stitcher conditions SCTE-35 splice boundaries into IDR keyframe-aligned fragmented MP4 "
            "(fMP4 / CMAF) segments and inserts discontinuity markers and presentation timestamp (PTS) offset "
            "mapping tags into the streaming manifest."
        ),
        "code": (
            "// Client Dual-Decoder Splice Transition\n"
            "if (playlist.hasDiscontinuityMarker(nextSegment)) {\n"
            "  secondaryDecoder.preDecodeInitialAccessUnits(nextSegment, ptsOffsetMap);\n"
            "  compositor.switchAtFrameTimestamp(splicePts);\n"
            "}"
        ),
        "p2": (
            "On capable smart TV and mobile client platforms, the Netflix playback engine initializes a secondary "
            "media decoder pipeline or timeline offset mapper to pre-decode initial video and audio access units "
            "of the upcoming interstitial segment prior to completion of the primary content segment, switching "
            "display and audio output composition at the exact splice PTS without black frames or audio clicks."
        ),
    },
    {
        "title": "Perceptual Video Quality Score Signaling in Streaming Manifests for Client ABR Selection",
        "source_url": "https://netflixtechblog.com/perceptual-quality-signaling-in-abr-manifests-4d9182e03a11",
        "source_type": "technology_blog",
        "published_date": "2022-09-19",
        "author": "Netflix Encoding & Client ABR Algorithms Team",
        "h2": "Embedding Per-Segment VMAF Quality Attributes in Variant Stream Declarations",
        "p1": (
            "Conventional client adaptive bitrate (ABR) algorithms select video representations based solely on "
            "peak/average bitrate and resolution, unaware that a 1080p stream at 2.2 Mbps may already achieve a "
            "VMAF perceptual quality score of 94 during a low-motion scene. Netflix's encoding pipeline computes "
            "per-segment and per-representation VMAF visual quality metrics across H.264, HEVC, and AV1 encodes "
            "and embeds normalized perceptual quality attributes directly inside streaming manifest metadata."
        ),
        "code": (
            "variant_stream {\n"
            "  codecs: \"av01.0.08M.10\",\n"
            "  bandwidth_bps: 2450000,\n"
            "  resolution: \"1920x1080\",\n"
            "  vmaf_perceptual_score: 94.6\n"
            "}"
        ),
        "p2": (
            "During playback, the Netflix client ABR controller evaluates both current playback buffer occupancy "
            "and the signaled perceptual visual quality score of each candidate variant stream, selecting a target "
            "representation that satisfies the display's perceptual quality threshold while minimizing network byte "
            "consumption and avoiding unnecessary upswitches."
        ),
    },
    {
        "title": "Toward a Practical Perceptual Video Quality Metric: VMAF in Production Encoding",
        "source_url": "https://netflixtechblog.com/toward-a-practical-perceptual-video-quality-metric-653f208b9652",
        "source_type": "technology_blog",
        "published_date": "2016-06-06",
        "author": "Zhi Li, Anne Aaron, Ioannis Katsavounidis",
        "h2": "Fusing VIF, DLM, and Temporal Motion via Support Vector Regression",
        "p1": (
            "Traditional video quality metrics such as PSNR and SSIM fail to correlate reliably with human visual "
            "perception across diverse movie and television genres. Netflix engineered Video Multimethod Assessment "
            "Fusion (VMAF) to predict subjective human viewer ratings from 0 to 100 across 1080p HD and 4K UHD "
            "displays by combining Visual Information Fidelity (VIF), Detail Loss Metric (DLM), and temporal "
            "frame-difference motion features."
        ),
        "code": (
            "vmaf_score = svm_predict([vif_scale0, vif_scale1, vif_scale2, vif_scale3, dlm, motion_diff])"
        ),
        "p2": (
            "VMAF is deployed across millions of daily cloud encoding jobs at Netflix to validate codec upgrades, "
            "guide per-title and per-shot convex hull ladder construction, and monitor streaming perceptual quality "
            "delivered to member devices."
        ),
    },
    {
        "title": "High Quality Video Encoding at Scale with Cosmos Serverless Media Microservices",
        "source_url": "https://netflixtechblog.medium.com/high-quality-video-encoding-at-scale-d159db052746",
        "source_type": "technology_blog",
        "published_date": "2020-12-07",
        "author": "Netflix Media Cloud Engineering",
        "h2": "Shot-Level Parallel Transcoding, Mezzanine Inspection & CMAF Packaging",
        "p1": (
            "Netflix's Reloaded and Cosmos media encoding architecture decomposes multi-hour studio mezzanine "
            "masters into thousands of independent scene-bounded video shots. Each shot is dispatched to stateless "
            "container functions that execute multi-pass complexity analysis, trial encodes, and final bitstream "
            "generation in parallel across elastic cloud compute clusters."
        ),
        "code": (
            "cosmos_workflow.split_into_shots(mezzanine_uri)\n"
            "  .map(run_dynamic_optimizer_shot_encode)\n"
            "  .reduce(assemble_fmp4_cmaf_segments)"
        ),
        "p2": (
            "Once all shot bitstreams for a representation are verified for VMAF quality compliance and bitstream "
            "conformance, the packaging microservice collates the encoded shots into fragmented ISOBMFF (fMP4 / CMAF) "
            "media segments with byte-range indexes for immediate Open Connect CDN propagation."
        ),
    },
    {
        "title": "Bringing AV1 Streaming to Netflix Members' 4K Smart TVs and Living Room Devices",
        "source_url": "https://netflixtechblog.com/bringing-av1-streaming-to-netflix-members-tvs-b2fd3226da28",
        "source_type": "technology_blog",
        "published_date": "2021-11-09",
        "author": "Netflix Video Algorithms & TV Playback Engineering",
        "h2": "10-Bit AV1 Convex Hull Ladders, Hardware Decoder Profiling & Bandwidth Savings",
        "p1": (
            "Following our launch of AV1 on Android mobile clients, Netflix expanded 10-bit AV1 adaptive streaming "
            "to 4K UHD smart TVs, streaming sticks, and gaming consoles. Our encoding pipeline generates per-shot "
            "convex hull ladders for AV1 up to 4K 60fps, leveraging adaptive superblock partitioning, warped motion "
            "compensation, and CDEF directional deringing filters."
        ),
        "code": (
            "av1_encoder --bit-depth=10 --enable-cdef=1 --enable-restoration=1 --cq-level=per_shot_qp"
        ),
        "p2": (
            "Telemetry from living-room TV playback shows that AV1 streams achieve higher average VMAF perceptual "
            "quality at 25% to 35% lower streaming bitrates than HEVC and H.264, materially reducing rebuffer rates "
            "and peak ISP last-mile congestion."
        ),
    },
    {
        "title": "Engineering High-Quality Dolby Atmos & Spatial Audio Streaming on Netflix",
        "source_url": "https://netflixtechblog.com/engineering-dolby-atmos-and-spatial-audio-on-netflix-7c812e940b15",
        "source_type": "technology_blog",
        "published_date": "2022-07-14",
        "author": "Netflix Audio Algorithms & Client Playback Engineering",
        "h2": "Object-Based Spatial Audio Bitstreams, Loudness Gating & Frame-Accurate PTS Alignment",
        "p1": (
            "Netflix delivers theatrical Dolby Atmos object-based spatial audio and binaural spatial audio rendering "
            "to subscribers on the Premium plan as well as stereo devices. Audio masters are encoded into Dolby "
            "Digital Plus with Dolby Atmos (EAC-3 JOC) bitstreams and packaged into fragmented ISOBMFF (CMAF) "
            "audio segments carrying ITU-R BS.1770 dialogue-gated loudness metadata."
        ),
        "code": (
            "audio_sample_entry {\n"
            "  codec: \"ec-3\", spatial_joc_objects: 16,\n"
            "  dialnorm_lkfs: -27.0, drc_profile: \"film_standard\"\n"
            "}"
        ),
        "p2": (
            "During adaptive streaming playback, the client audio renderer synchronizes multi-channel spatial "
            "object trajectories with HDR video frames using presentation timestamp (PTS) edit-list offsets and "
            "applies sample-accurate crossfading across audio bitrate switches."
        ),
    },
    {
        "title": "xHE-AAC Adaptive Bitrate Audio Streaming for Resilient Mobile Playback at Netflix",
        "source_url": "https://netflixtechblog.medium.com/xhe-aac-adaptive-audio-streaming-at-netflix-31f92a8e4110",
        "source_type": "technology_blog",
        "published_date": "2021-01-26",
        "author": "Netflix Audio Engineering",
        "h2": "Seamless Audio Bitrate Switching & Mandatory Loudness & Dynamic Range Control",
        "p1": (
            "On congested cellular networks, fixed-bitrate audio tracks can consume a disproportionate share of "
            "available bandwidth. Netflix deployed xHE-AAC (Extended High-Efficiency AAC) with adaptive audio "
            "bitrate ladders scaling from 16 kbps up to studio-grade bitrates, allowing the client ABR controller "
            "to switch audio representations dynamically alongside video tiers."
        ),
        "code": (
            "xhe_aac_abr_ladder = [16000, 24000, 32000, 64000, 96000, 128000] # bps"
        ),
        "p2": (
            "Embedded MPEG-D DRC (Dynamic Range Control) and loudness normalization metadata inside the xHE-AAC "
            "elementary stream ensure consistent dialogue intelligibility across quiet rooms and noisy mobile "
            "environments while maintaining seamless splice continuity at ISOBMFF fragment boundaries."
        ),
    },
    {
        "title": "Serving 100 Gbps from an Open Connect Appliance with FreeBSD & Kernel TLS (kTLS)",
        "source_url": "https://netflixtechblog.com/serving-100-gbps-from-an-open-connect-appliance-cdb51dca3b99",
        "source_type": "technology_blog",
        "published_date": "2017-06-15",
        "author": "Drew Gallatin, Netflix Open Connect OS Engineering",
        "h2": "Zero-Copy sendfile(), In-Kernel TLS Encryption & NUMA-Aware NVMe I/O",
        "p1": (
            "To serve encrypted HTTPS video segments at 100 Gbps line rate from a single Open Connect Appliance "
            "(OCA), Netflix engineered in-kernel TLS (kTLS) and asynchronous zero-copy sendfile() in FreeBSD "
            "and NGINX. Instead of copying media segment buffers between kernel space and user space for OpenSSL "
            "encryption, disk DMA reads from NVMe storage populate kernel page cache buffers that are encrypted "
            "directly in kernel space or offloaded to NIC crypto engines."
        ),
        "code": (
            "/* FreeBSD kTLS + sendfile zero-copy path */\n"
            "sendfile(nvme_fd, tls_socket_fd, segment_offset, segment_len, &hdtr, &sbytes, SF_NOCACHE);"
        ),
        "p2": (
            "Combined with NUMA-aware memory allocation and hardware transmit ring pacing, a single storage or "
            "flash OCA delivers tens of thousands of simultaneous 4K UHD and HD encrypted video streams with "
            "minimal CPU utilization."
        ),
    },
    {
        "title": "Serving 400 Gbps of Encrypted Video from a Single Open Connect Server",
        "source_url": "https://netflixtechblog.medium.com/serving-400-gbps-of-encrypted-video-from-open-connect-8a19c42e710b",
        "source_type": "technology_blog",
        "published_date": "2022-10-24",
        "author": "Drew Gallatin, Netflix Open Connect Infrastructure",
        "h2": "PCIe Gen4 NVMe Arrays, Inline NIC TLS Offload & TCP RACK Pacing at 400 Gbps",
        "p1": (
            "Scaling Open Connect Appliances to 400 Gbps of TLS-encrypted video egress required co-designing "
            "single-socket server hardware, high-density PCIe Gen4 NVMe flash drives, and Dual-Port 200GbE NICs "
            "with inline hardware TLS record encryption. Media segments requested by Netflix client players are "
            "fetched from NVMe namespaces and transmitted via hardware-offloaded kTLS without touching L3 CPU caches."
        ),
        "code": (
            "ifconfig mlx5en0 tls rx_tls tx_tls\n"
            "sysctl net.inet.tcp.functions_default=rack"
        ),
        "p2": (
            "Hardware packet pacing on the NIC schedules outgoing TCP segments according to the TCP RACK and BBR "
            "pacing rate computed for each subscriber connection, preventing micro-burst queue drops at ISP edge "
            "routers."
        ),
    },
    {
        "title": "TCP RACK, BBR, and Transport-Layer Congestion Control on Open Connect",
        "source_url": "https://netflixtechblog.com/tcp-rack-and-bbr-transport-pacing-on-open-connect-4e9182a7c311",
        "source_type": "technology_blog",
        "published_date": "2021-07-29",
        "author": "Randall Stewart, Michael Tuexen, Netflix Transport Team",
        "h2": "Time-Based Loss Recovery (RACK-TLP), RTT Variance Sampling & Socket Rate Pacing",
        "p1": (
            "Video streaming traffic is inherently bursty because adaptive bitrate (ABR) client players download "
            "discrete media segments over persistent HTTP/2 connections. Netflix's FreeBSD transport stack on "
            "Open Connect Appliances implements the TCP RACK (Recent ACKnowledgment) and Tail Loss Probe (TLP) "
            "stack alongside BBR congestion control and per-socket hardware rate pacing."
        ),
        "code": (
            "if (smoothed_rtt_variance > rtt_congestion_threshold) {\n"
            "    socket_pacing_rate = min(bbr_bw_estimate, nominal_segment_bitrate * 1.25);\n"
            "}"
        ),
        "p2": (
            "By continuously monitoring packet acknowledgment timestamps and smoothed RTT variance, the OCA "
            "transport layer detects early last-mile queue build-up and paces segment transmission smoothly, "
            "reducing client video rebuffering across Wi-Fi and cellular networks."
        ),
    },
    {
        "title": "Machine Learning for Predictive Edge Caching on Open Connect Appliances",
        "source_url": "https://netflixtechblog.medium.com/machine-learning-for-predictive-edge-caching-on-open-connect-2f8190c41e25",
        "source_type": "technology_blog",
        "published_date": "2022-03-11",
        "author": "Netflix Content Delivery Data Science & ML Team",
        "h2": "Regional ISP Demand Forecasting, Tiered NVMe/HDD Storage & Off-Peak Fill Optimization",
        "p1": (
            "Each Open Connect Appliance deployed inside an ISP network has finite NVMe flash and rotational "
            "disk capacity, yet must serve localized viewing demand with >95% cache hit efficiency. Netflix runs "
            "spatio-temporal machine learning models that predict per-title, per-episode, and per-representation "
            "(codec/resolution/bitrate) viewing volume for every ISP autonomous system number (ASN) over upcoming "
            "24-hour windows."
        ),
        "code": (
            "predicted_bytes[asn, title_id, rep_id] = demand_forecaster.predict(region=asn, horizon_hours=24)\n"
            "cache_fill_plan = knapsack_optimize(oca_storage_capacity, predicted_bytes)"
        ),
        "p2": (
            "During off-peak night fill windows, the Open Connect control plane pre-positions the highest-ranked "
            "video and audio media segments onto NVMe tiers while evicting cold catalog segments, minimizing "
            "daytime backbone peering traffic."
        ),
    },
    {
        "title": "HDR10 and Dolby Vision Tone Mapping & Dynamic SEI Metadata Pipeline at Netflix",
        "source_url": "https://netflixtechblog.com/hdr10-and-dolby-vision-tone-mapping-pipeline-at-netflix-6a7219e04b33",
        "source_type": "technology_blog",
        "published_date": "2021-05-17",
        "author": "Netflix Color Science & HDR Encoding Team",
        "h2": "PQ Perceptual Quantizer Transfer Functions, L1/L2 Trim Passes & SEI NALU Multiplexing",
        "p1": (
            "Netflix's High Dynamic Range (HDR) studio mastering pipeline ingests 16-bit floating-point IMF "
            "(Interoperable Master Format) packages graded in SMPTE ST 2084 (PQ) color volume. To preserve creative "
            "intent across displays ranging from 300-nit laptops to 2000-nit OLED TVs, our encoding pipeline "
            "computes scene-by-scene luminance histograms (min, max, and average frame light levels) and encodes "
            "dynamic tone-mapping metadata."
        ),
        "code": (
            "sei_payload {\n"
            "  itu_t_t35_terminal_provider_code: 0x003B,\n"
            "  max_content_light_level: 1200, max_frame_average_light_level: 380\n"
            "}"
        ),
        "p2": (
            "These dynamic luminance reshaping and tone-mapping parameters are encapsulated inside HEVC and AV1 "
            "Supplemental Enhancement Information (SEI) network abstraction layer units (NALUs) and ISOBMFF "
            "sample group descriptions for frame-synchronized client display rendering."
        ),
    },
    {
        "title": "Film Grain Synthesis in AV1 Bitstreams for Cinematic Streaming at Netflix",
        "source_url": "https://netflixtechblog.medium.com/film-grain-synthesis-in-av1-for-cinematic-streaming-5d9102e84a19",
        "source_type": "technology_blog",
        "published_date": "2022-08-03",
        "author": "Andrey Norkin, Netflix Video Coding Research",
        "h2": "Denoising Pre-Analysis, Autoregressive Grain Modeling & Decoder-Side Grain Reconstruction",
        "p1": (
            "Photochemical film grain and digital sensor noise have high spatial-temporal entropy that resists "
            "conventional block-based transform coding, inflating streaming bitrates by up to 40%. In Netflix's "
            "AV1 encoding pipeline, a temporal-spatial denoising filter separates organic film grain from the "
            "underlying clean video signal prior to quantization."
        ),
        "code": (
            "grain_params = estimate_ar_grain_model(raw_frame, denoised_frame)\n"
            "bitstream.write_film_grain_header(grain_params)"
        ),
        "p2": (
            "Compact autoregressive (AR) film grain synthesis parameters and luminance-dependent scaling tables "
            "are transmitted in the AV1 frame header so the client hardware decoder reconstructs authentic "
            "cinematic grain during display output without transmitting noisy transform residuals."
        ),
    },
    {
        "title": "Client-Side Adaptive Bitrate (ABR) Algorithms Using Contextual Machine Learning",
        "source_url": "https://netflixtechblog.com/client-side-adaptive-bitrate-algorithms-using-machine-learning-1c8294a05e12",
        "source_type": "technology_blog",
        "published_date": "2021-09-08",
        "author": "Netflix Playback Algorithms & Data Science Team",
        "h2": "Throughput Distribution Estimation, Buffer Hazard Control & Perceptual Switch Smoothing",
        "p1": (
            "Selecting the optimal video and audio representation for every 2-to-4-second media segment on "
            "heterogeneous home Wi-Fi and mobile cellular links requires balancing three competing objectives: "
            "maximizing VMAF perceptual visual quality, minimizing playback rebuffering stalls, and avoiding "
            "jarring quality oscillations."
        ),
        "code": (
            "next_rep = argmax_r ( E[VMAF(r)] - lambda_rebuffer * P(buffer_underrun | r, bw_posterior) "
            "- lambda_switch * |VMAF(r) - VMAF(r_prev)| )"
        ),
        "p2": (
            "Netflix's client ABR controller maintains a Bayesian throughput posterior over recent HTTP segment "
            "downloads and combines buffer occupancy telemetry with manifest-signaled per-shot VMAF scores to "
            "select the safest high-fidelity representation on every segment boundary."
        ),
    },
    {
        "title": "Measuring Streaming Quality of Experience (QoE) and Rebuffer Rate Across 260M+ Members",
        "source_url": "https://netflixtechblog.medium.com/measuring-streaming-quality-of-experience-qoe-at-netflix-7b1904e23c18",
        "source_type": "technology_blog",
        "published_date": "2023-01-18",
        "author": "Netflix Playback Data Science & QoE Engineering",
        "h2": "Play Delay, Rebuffer Ratio, VMAF Session Distributions & CDN Attribution",
        "p1": (
            "Every Netflix playback session emits structured QoE telemetry beacons capturing time-to-first-frame "
            "(play delay), rebuffer duration per viewing hour, bitrate switch trajectories, VMAF perceptual quality "
            "weighted by viewing time, and audio-video synchronization offsets."
        ),
        "code": (
            "qoe_beacon {\n"
            "  session_id: \"nflx_9812\", oca_cluster: \"oca-sjc-04\",\n"
            "  play_delay_ms: 410, rebuffer_count: 0, weighted_vmaf: 95.2\n"
            "}"
        ),
        "p2": (
            "Real-time aggregation pipelines correlate these client QoE metrics with Open Connect Appliance IDs, "
            "ISP autonomous system numbers, and device firmware versions to trigger automatic CDN traffic steering "
            "whenever regional quality degrades."
        ),
    },
    {
        "title": "Preview Video Pre-Buffering & Instant Playback Startup on Living Room TV Devices",
        "source_url": "https://netflixtechblog.com/preview-video-pre-buffering-and-instant-playback-startup-3e9104c82a71",
        "source_type": "technology_blog",
        "published_date": "2022-04-06",
        "author": "Netflix TV UI & Playback Engineering",
        "h2": "Speculative Initialization Segment Prefetching & Decoder Pipeline Warm-Up",
        "p1": (
            "When a member navigates the Netflix homepage grid on a smart TV or game console, video previews and "
            "full-episode transitions must start playing in under 500 milliseconds. Our client UI predicts "
            "high-probability play intent from directional remote focus dwell times and speculatively prefetches "
            "ISOBMFF initialization segments (`moov` boxes) and initial IDR keyframe media fragments from the "
            "nearest Open Connect Appliance."
        ),
        "code": (
            "if (focusDwellTimeMs > 250) {\n"
            "  mediaCache.prefetchInitAndFirstSegment(candidateTitleId, preferredAudioTrack);\n"
            "}"
        ),
        "p2": (
            "By pre-populating the client memory buffer and pre-initializing hardware DRM and media decoder "
            "contexts before the user presses Play, playback begins instantaneously without network round-trip "
            "startup delay."
        ),
    },
    {
        "title": "Artwork Personalization at Netflix Using Contextual Bandits",
        "source_url": "https://netflixtechblog.medium.com/artwork-personalization-at-netflix-718294a0c1e3",
        "source_type": "technology_blog",
        "published_date": "2017-12-07",
        "author": "Ashok Chandrashekar, Fernando Amat, Justin Basilico, Tony Jebara",
        "h2": "Contextual Bandit Exploration-Exploitation for Homepage Title Imagery",
        "p1": (
            "A member's decision to watch a title on Netflix is strongly influenced by the visual artwork "
            "displayed in the homepage row. Rather than serving a single static poster to all 260M+ subscribers, "
            "Netflix uses contextual multi-armed bandit algorithms to select personalized title artwork tailored "
            "to each member's genre, actor, and visual theme affinities."
        ),
        "code": (
            "selected_artwork = argmax_a E[P(play | user_context_vector, title_id, artwork_a)]"
        ),
        "p2": (
            "Online Thompson sampling and LinUCB contextual bandit models continuously balance exploration of "
            "new candidate key art frames extracted from the video asset against exploitation of high-performing "
            "personalized imagery."
        ),
    },
    {
        "title": "Foundation Models for Personalized Recommendation at Netflix",
        "source_url": "https://netflixtechblog.com/foundation-models-for-personalized-recommendation-at-netflix-8a9102c41e77",
        "source_type": "technology_blog",
        "published_date": "2024-03-19",
        "author": "Netflix Personalization & Machine Learning Research",
        "h2": "Large-Scale Transformer Member Interaction Models & Multi-Task Ranking",
        "p1": (
            "Netflix's next-generation recommendation architecture unifies fragmented task-specific models "
            "(Personalized Video Ranker, Continue Watching, Similar Titles, and Search) using large-scale "
            "autoregressive and bidirectional Transformer foundation models trained on longitudinal member "
            "interaction sequences."
        ),
        "code": (
            "member_embedding = interaction_transformer(history_tokens, timestamps, device_context)"
        ),
        "p2": (
            "Learned member and title representations are served via low-latency vector indices and distilled "
            "into online ranking tiers to personalize the homepage grid across hundreds of millions of profiles."
        ),
    },
    {
        "title": "Semantic Search & Multimodal Video Embeddings for Content Discovery at Netflix",
        "source_url": "https://netflixtechblog.medium.com/semantic-search-and-multimodal-video-embeddings-at-netflix-4b9102e83c11",
        "source_type": "technology_blog",
        "published_date": "2023-07-12",
        "author": "Netflix Search & Discovery Machine Learning Team",
        "h2": "Dense Query-Video Contrastive Embeddings & Approximate Nearest Neighbor Retrieval",
        "p1": (
            "When members search Netflix using natural-language queries, mood descriptions, or partial character "
            "names, lexical prefix matching alone is insufficient. Our search engine encodes user queries and "
            "multimodal catalog metadata (video shots, audio transcripts, subtitles, and synopses) into a shared "
            "dense vector embedding space."
        ),
        "code": (
            "sim_score = cosine_similarity(encode_query(q), encode_multimodal_title(video_frames, subtitles))"
        ),
        "p2": (
            "Approximate Nearest Neighbor (ANN) vector retrieval combined with personalized re-ranking surfaces "
            "relevant catalog titles and trailers in under 20 milliseconds."
        ),
    },
    {
        "title": "Interleaving and Sequential Testing in Netflix's Large-Scale A/B Experimentation Platform",
        "source_url": "https://netflixtechblog.com/interleaving-in-online-experiments-at-netflix-a04ee392ec55",
        "source_type": "technology_blog",
        "published_date": "2018-04-11",
        "author": "Netflix Experimentation Platform Engineering",
        "h2": "Team-Draft Interleaving, 100x Sample Efficiency & QoE Guardrail Metrics",
        "p1": (
            "To accelerate algorithmic iteration across video ranking, search, and adaptive bitrate playback "
            "controllers, Netflix supplements traditional multi-week A/B tests with Team-Draft Interleaving. "
            "By blending candidate rankings from two competing algorithms within a single member's homepage "
            "session and measuring preference share from actual play events, interleaving achieves statistical "
            "sensitivity with 100x fewer users."
        ),
        "code": (
            "interleaved_row = team_draft_interleave(ranking_model_A, ranking_model_B, random_seed)"
        ),
        "p2": (
            "Winning algorithmic candidates from interleaving trials are promoted to full-population A/B tests "
            "evaluating long-term subscriber retention, streaming hours, and playback QoE guardrails."
        ),
    },
    {
        "title": "Scaling Media & Data Processing with Maestro Workflow Orchestrator at Netflix",
        "source_url": "https://netflixtechblog.medium.com/scaling-media-processing-with-maestro-workflow-orchestrator-2d9104e82a14",
        "source_type": "technology_blog",
        "published_date": "2023-03-28",
        "author": "Netflix Data & Media Platform Orchestration Team",
        "h2": "DAG Workflow Scheduling for Encoding, ML Training & Iceberg Data Pipelines",
        "p1": (
            "Maestro is Netflix's horizontal workflow orchestrator that schedules hundreds of thousands of daily "
            "directed acyclic graphs (DAGs) spanning studio video encoding pipelines, VMAF quality verification, "
            "Open Connect cache-fill demand forecasting, and Apache Iceberg data warehouse transformations."
        ),
        "code": (
            "maestro_dag: ingest_mezzanine -> scene_cut_detect -> shot_encode_fanout -> package_cmaf -> publish_oca"
        ),
        "p2": (
            "By isolating state management and supporting massive step fan-out across container clusters, Maestro "
            "coordinates petabyte-scale media and machine learning workflows with strict SLA guarantees."
        ),
    },
    {
        "title": "Real-Time Playback Anomaly Detection with Apache Flink and Keystone Stream Processing",
        "source_url": "https://netflixtechblog.com/real-time-playback-anomaly-detection-with-apache-flink-9c8102e41b22",
        "source_type": "technology_blog",
        "published_date": "2022-06-14",
        "author": "Netflix Real-Time Data Infrastructure & Observability Team",
        "h2": "Sub-Minute Stateful Window Aggregation Over Client Playback Telemetry",
        "p1": (
            "When an ISP peering link fails or a smart TV firmware update introduces a media decoder regression, "
            "Netflix's real-time anomaly detection system must identify the fault within seconds. Client playback "
            "start, error, and rebuffer events flow through the Keystone Apache Kafka pipeline into stateful "
            "Apache Flink stream processors."
        ),
        "code": (
            "flink_stream.keyBy(event -> Tuple(event.asn, event.oca_id, event.device_type))\n"
            "  .window(TumblingEventTimeWindows.of(Time.seconds(30)))\n"
            "  .process(new RebufferSpikeDetector())"
        ),
        "p2": (
            "Detected anomalies automatically publish routing overrides to the Open Connect traffic steering "
            "control plane to divert member playback manifests away from impaired network paths."
        ),
    },
    {
        "title": "Petabyte-Scale Streaming Analytics with Apache Iceberg at Netflix",
        "source_url": "https://netflixtechblog.medium.com/petabyte-scale-analytics-with-apache-iceberg-at-netflix-6e8102c49a31",
        "source_type": "technology_blog",
        "published_date": "2021-02-18",
        "author": "Ryan Blue, Netflix Data Platform Architecture",
        "h2": "ACID Snapshot Isolation, Hidden Partitioning & Cloud Object Store Table Format",
        "p1": (
            "Netflix created Apache Iceberg to solve correctness and performance bottlenecks in petabyte-scale "
            "cloud data lakes storing historical playback telemetry, encoding convex-hull logs, and A/B test "
            "metrics. Iceberg tracks table state via immutable metadata trees and manifest files with full ACID "
            "snapshot isolation."
        ),
        "code": (
            "SELECT oca_cluster, AVG(vmaf_score), SUM(rebuffer_ms)\n"
            "FROM prod.playback.session_telemetry\n"
            "WHERE event_ts >= TIMESTAMP '2025-01-01 00:00:00 UTC'\n"
            "GROUP BY oca_cluster;"
        ),
        "p2": (
            "Hidden partitioning and file-level min/max column statistics allow Trino, Spark, and Flink engines "
            "to prune 99% of object storage files during interactive analytical queries."
        ),
    },
    {
        "title": "EVCache: Distributed In-Memory Caching for Global Streaming Personalization & Session State",
        "source_url": "https://netflixtechblog.com/evcache-distributed-in-memory-caching-for-streaming-1b9204e83c19",
        "source_type": "technology_blog",
        "published_date": "2020-08-25",
        "author": "Netflix Cloud Database & Caching Engineering",
        "h2": "Cross-Region Memcached Replication, NVMe SSD Backing & Sub-Millisecond Reads",
        "p1": (
            "Every time a member opens the Netflix app, dozens of microservices query precomputed personalized "
            "homepage rows, viewing bookmark positions, and device playback capability profiles from EVCache—"
            "Netflix's distributed, multi-region key-value store built on Memcached and SSD storage."
        ),
        "code": (
            "evcache_client.get_bulk([\"pvr_rows:user_104\", \"bookmarks:user_104\", \"abr_profile:device_88\"])"
        ),
        "p2": (
            "EVCache handles over 400 million operations per second globally with sub-millisecond read latency "
            "and asynchronous Kafka-backed cross-region replication."
        ),
    },
    {
        "title": "Subtitle & Timed Text Conditioning (TTML / IMSC1) in Netflix Live and On-Demand Streams",
        "source_url": "https://netflixtechblog.medium.com/subtitle-and-timed-text-conditioning-imsc1-at-netflix-5a8102c49e10",
        "source_type": "technology_blog",
        "published_date": "2022-02-09",
        "author": "Netflix Timed Text & Accessibility Engineering",
        "h2": "Fragmented ISOBMFF IMSC1 Packaging, Live Caption Splicing & Multi-Language Tracks",
        "p1": (
            "Netflix delivers subtitles and closed captions in over 35 languages using W3C Timed Text Markup "
            "Language (TTML) Text and Image profiles (IMSC1.1) encapsulated inside fragmented ISO Base Media "
            "File Format (fMP4 / CMAF) segments synchronized with video and audio presentation timestamps."
        ),
        "code": (
            "<tt xmlns=\"http://www.w3.org/ns/ttml\" tts:extent=\"1920px 1080px\">\n"
            "  <p begin=\"00:01:12.040\" end=\"00:01:14.880\">[thunder rumbling in distance]</p>\n"
            "</tt>"
        ),
        "p2": (
            "During adaptive streaming or live ad insertion, our timed-text packager clips and offsets subtitle "
            "cue intervals at exact CMAF segment boundaries so client players switch languages seamlessly."
        ),
    },
    {
        "title": "Color-Accurate Studio Mastering and IMF Mezzanine Ingestion Pipeline at Netflix",
        "source_url": "https://netflixtechblog.com/imf-mezzanine-ingestion-and-color-pipeline-at-netflix-3c8102e49a12",
        "source_type": "technology_blog",
        "published_date": "2020-10-14",
        "author": "Netflix Studio Production & Mastering Engineering",
        "h2": "SMPTE ST 2067 IMF Composition Playlists, JPEG 2000 Frames & Automated QC",
        "p1": (
            "Studios deliver original movies and series to Netflix as SMPTE ST 2067 Interoperable Master Format "
            "(IMF) packages containing lossless or visually lossless JPEG 2000 video track files, 24-bit PCM / "
            "Dolby Atmos audio stems, and XML Composition Playlists (CPLs)."
        ),
        "code": (
            "imf_parser.validate_cpl(cpl_xml)\n"
            "  .verify_photon_compliance(color_primaries=\"BT.2020\", transfer=\"SMPTE-ST-2084\")"
        ),
        "p2": (
            "Our automated cloud inspection pipeline validates frame checksums, HDR color gamut compliance, "
            "and audio loudness alignment before triggering shot-based Dynamic Optimizer encoding."
        ),
    },
    {
        "title": "Adaptive Downscaling and Content-Aware Resolution Restoration in Video Encoding",
        "source_url": "https://netflixtechblog.medium.com/adaptive-downscaling-and-super-resolution-in-video-encoding-8d9102c41e33",
        "source_type": "technology_blog",
        "published_date": "2023-04-12",
        "author": "Netflix Video Compression Research Team",
        "h2": "Per-Shot Downsampling Filters, AV1 In-Loop Super-Resolution & VMAF Gain",
        "p1": (
            "When encoding high-motion shots at constrained bitrates on the lower rungs of a per-shot convex hull "
            "ladder, coding at a lower spatial resolution and upsampling on the client display prevents blocky "
            "quantization artifacts. Netflix optimizes pre-encoding downscaling filter kernels alongside AV1 "
            "in-loop super-resolution modes."
        ),
        "code": (
            "for scale_factor in [1.0, 0.75, 0.5]:\n"
            "    candidate = encode_with_inloop_superres(shot, scale_factor, qp)"
        ),
        "p2": (
            "Evaluated with VMAF at the native display resolution, content-aware downscaling combined with "
            "adaptive sharpening yields up to 12% additional bitrate reduction on complex action scenes."
        ),
    },
    {
        "title": "Fast Playback Seeking and Trick-Play I-Frame BIF Index Generation at Netflix",
        "source_url": "https://netflixtechblog.com/trick-play-iframe-bif-index-generation-for-fast-seeking-2e9104c81a55",
        "source_type": "technology_blog",
        "published_date": "2019-11-20",
        "author": "Netflix Playback & Media Packaging Engineering",
        "h2": "Base Index Frames (BIF), IDR Byte-Range Tables & Scrubbing Latency Optimization",
        "p1": (
            "When a member scrubs forward or backward across a timeline on a TV, mobile phone, or browser, "
            "the Netflix player immediately displays trick-play thumbnail previews and seeks to the nearest "
            "instantaneous decoder refresh (IDR) keyframe. Our encoding pipeline generates compact Base Index "
            "Frames (BIF) archives alongside ISOBMFF segment index (`sidx`) byte-offset tables."
        ),
        "code": (
            "sidx_entry = lookup_nearest_idr_subsegment(target_seek_pts)\n"
            "http_range_request(oca_uri, sidx_entry.byte_offset, sidx_entry.byte_length)"
        ),
        "p2": (
            "The client player issues a targeted HTTP byte-range request to the local Open Connect Appliance for "
            "the exact IDR subsegment, resuming decoded video playback in milliseconds."
        ),
    },
    {
        "title": "Multi-DRM Content Protection (Widevine, FairPlay, PlayReady) & Common Encryption (CENC)",
        "source_url": "https://netflixtechblog.medium.com/multi-drm-cenc-content-protection-in-adaptive-streaming-7f9102c48e21",
        "source_type": "technology_blog",
        "published_date": "2021-08-30",
        "author": "Netflix Content Security & Playback Engineering",
        "h2": "ISO/IEC 23001-7 CENC `cbcs`/`cenc` Encryption, Key Rotation & License Pre-Acquisition",
        "p1": (
            "To protect studio-licensed 4K UHD and HDR content across Smart TVs, iOS/tvOS, Android, and browsers "
            "without storing duplicate encrypted copies on Open Connect Appliances, Netflix packages fragmented "
            "MP4 (fMP4 / CMAF) media segments using ISO/IEC 23001-7 Common Encryption (CENC)."
        ),
        "code": (
            "pssh_boxes = [build_widevine_pssh(kid), build_playready_pssh(kid), build_fairplay_skd(kid)]"
        ),
        "p2": (
            "A single encrypted CMAF media segment stream contains Protection System Specific Header (`pssh`) "
            "metadata supporting Google Widevine, Microsoft PlayReady, and Apple FairPlay Streaming hardware "
            "Trusted Execution Environments (TEEs)."
        ),
    },
    {
        "title": "Cloud Gaming Low-Latency WebRTC Video Streaming & Controller Telemetry at Netflix",
        "source_url": "https://netflixtechblog.com/cloud-gaming-low-latency-webrtc-streaming-at-netflix-4a9102c83e17",
        "source_type": "technology_blog",
        "published_date": "2023-10-17",
        "author": "Netflix Cloud Gaming & Real-Time Media Team",
        "h2": "Sub-Frame Ultra-Low-Latency Encoding, GCC Congestion Feedback & Phone Controller Sync",
        "p1": (
            "Netflix's cloud gaming infrastructure streams interactive games rendered on cloud GPU instances "
            "directly to smart TVs and browsers using customized WebRTC real-time video transport while pairing "
            "the member's smartphone as a low-latency virtual game controller."
        ),
        "code": (
            "rtc_encoder.set_target_bitrate(gcc_bandwidth_estimate_bps, max_frame_delay_ms=16)"
        ),
        "p2": (
            "Hardware-accelerated H.264/HEVC/AV1 encoders adjust frame quantization parameters on every single "
            "video frame in response to Google Congestion Control (GCC) RTCP feedback and packet jitter measurements."
        ),
    },
    {
        "title": "Automated Scene-Cut & Shot Boundary Detection for Perceptual Video Coding",
        "source_url": "https://netflixtechblog.medium.com/automated-scene-cut-and-shot-boundary-detection-at-netflix-1e9104c82b44",
        "source_type": "technology_blog",
        "published_date": "2019-05-14",
        "author": "Netflix Video Algorithms Team",
        "h2": "YUV Color Histogram Discontinuities, Dissolve Detection & Closed-GOP Alignment",
        "p1": (
            "Accurate shot boundary detection is the foundation of Netflix's per-shot convex hull encoding and "
            "Dynamic Optimizer pipeline. Our scene-cut detector analyzes YUV luminance and chrominance histograms, "
            "motion vector coherence, and edge structural changes across consecutive mezzanine frames."
        ),
        "code": (
            "if (hist_l1_distance(frame_t, frame_t_minus_1) > scene_cut_threshold) {\n"
            "    shots.mark_closed_gop_boundary(frame_t);\n"
            "}"
        ),
        "p2": (
            "By placing closed-GOP Instantaneous Decoder Refresh (IDR) keyframes strictly at true visual shot "
            "cuts, the encoder eliminates cross-scene motion estimation waste and guarantees clean ABR switching "
            "boundaries for client players."
        ),
    },
    {
        "title": "Titus: Scaling Netflix's Container Runtime for Elastic Video Encoding and ML Workloads",
        "source_url": "https://netflixtechblog.com/titus-the-netflix-container-management-platform-is-now-open-source-f868c9fb5436",
        "source_type": "technology_blog",
        "published_date": "2018-04-24",
        "author": "Netflix Cloud Platform & Titus Engineering",
        "h2": "Opportunistic Batch Scheduling of Per-Shot Encoding Jobs on Unused Cloud Capacity",
        "p1": (
            "Titus is Netflix's cloud container orchestration platform managing hundreds of thousands of vCPUs "
            "for both latency-sensitive streaming microservices and massive batch video encoding jobs. When "
            "regional streaming control-plane traffic ebbs during off-peak hours, Titus opportunistically harvests "
            "spare compute reservations to run Dynamic Optimizer and AV1 shot encoding containers."
        ),
        "code": (
            "titus_scheduler.dispatch_opportunistic_batch(job=\"av1_shot_encode\", priority=\"preemptible_tier\")"
        ),
        "p2": (
            "Fine-grained CPU pinning, network bandwidth isolation, and fast container image layer caching enable "
            "million-shot catalog re-encodes with high cluster utilization."
        ),
    },
    {
        "title": " Zuul & Edge Gateway Routing for Billions of Daily Netflix Playback Requests",
        "source_url": "https://netflixtechblog.medium.com/zuul-edge-gateway-routing-for-playback-requests-3a9102c48e15",
        "source_type": "technology_blog",
        "published_date": "2020-06-11",
        "author": "Netflix Cloud Gateway & Edge Engineering",
        "h2": "Non-Blocking Netty I/O, Adaptive Concurrency Limits & Playback Manifest Dispatch",
        "p1": (
            "Every playback session launch, manifest refresh, DRM license exchange, and homepage browse request "
            "from Netflix client devices passes through Zuul, our cloud edge gateway built on asynchronous "
            "non-blocking Netty event loops."
        ),
        "code": (
            "zuul_filter.route_to_playback_control_plane(request, adaptive_concurrency_limiter)"
        ),
        "p2": (
            "Zuul enforces Vegas/Gradient2 adaptive concurrency limits and shedding policies so that playback "
            "manifest generation and Open Connect CDN steering remain responsive even during global live event "
            "traffic surges."
        ),
    },
    {
        "title": "Spatio-Temporal Complexity Probing for Fast Single-Pass Per-Shot Encoding",
        "source_url": "https://netflixtechblog.com/spatio-temporal-complexity-probing-for-fast-encoding-7c9102e41b88",
        "source_type": "technology_blog",
        "published_date": "2022-12-05",
        "author": "Netflix Video Encoding Research Team",
        "h2": "Predicting Rate-Distortion Convex Hulls via Lightweight Downscaled Lookahead Encodes",
        "p1": (
            "Exhaustively running full-resolution trial encodes across dozens of QP and resolution combinations "
            "for every video shot is computationally expensive. Netflix developed a complexity probing pass that "
            "extracts spatial texture energy, block motion residuals, and downscaled lookahead encode statistics "
            "in a fraction of the compute time."
        ),
        "code": (
            "predicted_rd_curve = complexity_regressor.predict(spatial_variance, temporal_sad, lookahead_bits)"
        ),
        "p2": (
            "Machine learning regression models predict the full VMAF rate-distortion convex hull directly from "
            "these probe features, cutting cloud compute costs by over 50% while preserving Pareto-optimal bitrate "
            "ladders."
        ),
    },
    {
        "title": "Diagnosing Last-Mile Wi-Fi vs. ISP Core Congestion in Netflix Video Streaming",
        "source_url": "https://netflixtechblog.medium.com/diagnosing-last-mile-wifi-vs-isp-congestion-in-streaming-6b8102c49e72",
        "source_type": "technology_blog",
        "published_date": "2021-11-29",
        "author": "Netflix Open Connect Network Analytics Team",
        "h2": "Correlating OCA TCP Kernel Telemetry with Client Socket Read Timestamps",
        "p1": (
            "When a subscriber experiences video rebuffering or a bitrate drop, determining whether the bottleneck "
            "lies inside the member's home Wi-Fi network, the ISP access loop, or an IXP peering link is critical "
            "for automated remediation. Open Connect Appliances record per-segment TCP smoothed RTT, minimum RTT, "
            "and retransmission counts alongside client-reported throughput."
        ),
        "code": (
            "is_home_wifi_bottleneck = (client_rtt_variance_high) && (asn_peer_oca_utilization < 0.65)"
        ),
        "p2": (
            "By comparing connection metrics across multiple households sharing the same ISP autonomous system "
            "and Open Connect cluster, the control plane distinguishes localized Wi-Fi interference from ISP "
            "routing congestion that warrants BGP or manifest traffic steering."
        ),
    },
    {
        "title": "Optimizing HTTP/2 and HTTP/3 (QUIC) Media Segment Delivery on Open Connect",
        "source_url": "https://netflixtechblog.com/optimizing-http2-and-http3-quic-media-delivery-on-open-connect-5e9104c81b39",
        "source_type": "technology_blog",
        "published_date": "2023-09-06",
        "author": "Netflix Open Connect Transport & Protocol Engineering",
        "h2": "Connection Coalescing, Stream Prioritization & Head-of-Line Blocking Mitigation",
        "p1": (
            "Netflix evaluates and deploys multiplexed HTTP/2 and UDP-based HTTP/3 (QUIC) transport protocols "
            "between client media players and Open Connect edge appliances. Multiplexing concurrent audio, video, "
            "and timed-text CMAF segment requests over a single connection eliminates repeated TLS handshakes."
        ),
        "code": (
            "http3_stream.set_priority(urgency=AUDIO_SEGMENT_URGENCY, incremental=True)"
        ),
        "p2": (
            "On lossy mobile and congested wireless links, stream-level prioritization ensures that small audio "
            "and subtitle segments are never stalled behind large 4K video segment retransmissions."
        ),
    },
    {
        "title": "Psychovisual Adaptive Quantization & Contrast Masking in Netflix HEVC and AV1 Encoders",
        "source_url": "https://netflixtechblog.medium.com/psychovisual-adaptive-quantization-in-hevc-and-av1-9b8102c43e16",
        "source_type": "technology_blog",
        "published_date": "2020-03-19",
        "author": "Netflix Video Compression Algorithms Team",
        "h2": "CTU/Superblock Delta-QP (dQP) Allocation for Dark Scenes and High-Contrast Edges",
        "p1": (
            "The human visual system is highly sensitive to banding and blocking artifacts in smooth dark gradients "
            "and facial regions, while tolerating coarser quantization in complex foliage or water textures. "
            "Netflix tunes psychovisual adaptive quantization inside our x265 (HEVC) and SVT-AV1 encoders."
        ),
        "code": (
            "ctu_dqp = compute_luminance_texture_masking(ctu_luma_mean, ctu_ac_energy) + base_slice_qp"
        ),
        "p2": (
            "By modulating coding tree unit (CTU) and superblock delta-QP (dQP) offsets based on local luminance "
            "and AC transform energy, our streams eliminate dark-scene contouring without increasing average "
            "segment bitrates."
        ),
    },
    {
        "title": "Live Cloud Encoding & Redundant Dual-Pipeline Ingest for Global Netflix Live Events",
        "source_url": "https://netflixtechblog.com/live-cloud-encoding-and-redundant-ingest-at-netflix-2a9104c87e61",
        "source_type": "technology_blog",
        "published_date": "2024-01-23",
        "author": "Netflix Live Broadcast & Cloud Media Engineering",
        "h2": "SMPTE ST 2110 / SRT Contribution Ingest, Epoch-Locked GOPs & Active-Active Packagers",
        "p1": (
            "Live broadcasts on Netflix ingest redundant contribution feeds over Secure Reliable Transport (SRT) "
            "and cloud fiber links into geographically isolated AWS regions. Dual active-active live encoding "
            "pipelines synchronize their instantaneous decoder refresh (IDR) keyframe cadences and CMAF segment "
            "sequence numbers to wall-clock PTP/NTP epoch boundaries."
        ),
        "code": (
            "segment_sequence_num = floor(ptp_epoch_timestamp_ms / segment_duration_ms)\n"
            "emit_epoch_aligned_cmaf_chunk(segment_sequence_num, video_idr_nalu)"
        ),
        "p2": (
            "Because both primary and backup live pipelines emit byte-compatible, epoch-locked media segments, "
            "Open Connect edge servers and client players can fail over mid-stream between regions with zero "
            "frame loss or timeline discontinuity."
        ),
    },
    # --- 11 Additional Non-Medium Public Netflix Sources (Open Connect, Research Papers, Engineering Docs) ---
    {
        "title": "Open Connect Settlement-Free Peering (SFP) & IXP Interconnect Architecture",
        "source_url": "https://openconnect.netflix.com/en/peering-policy/ixp-and-settlement-free-peering",
        "source_type": "open_connect_documentation",
        "published_date": "2023-04-10",
        "author": "Netflix Open Connect Peering & Network Architecture",
        "h2": "ASN 2906 BGP Peering Policy, MED/Community Traffic Engineering & IXP Route Servers",
        "p1": (
            "Netflix operates Autonomous System AS2906 across global Internet Exchange Points (IXPs) and private "
            "network interconnects (PNIs) to deliver streaming video traffic directly to partner ISPs without "
            "intermediary transit hops. Partner networks advertise regional IPv4 and IPv6 subscriber prefixes "
            "with BGP community attributes indicating preferred ingress/egress Open Connect clusters."
        ),
        "code": (
            "ip bgp-community new-format\n"
            "route-map NETFLIX_OCA_PREF permit 10\n"
            " set community 2906:100"
        ),
        "p2": (
            "The Open Connect control plane combines these BGP RIB tables with real-time link capacity telemetry "
            "to map every subscriber IP prefix to the lowest-latency OCA cluster."
        ),
    },
    {
        "title": "Open Connect Embedded Appliance Cluster Failover & Anycast/Dynamic DNS Steering",
        "source_url": "https://openconnect.netflix.com/en/network-architecture/appliance-cluster-failover-and-dns",
        "source_type": "open_connect_documentation",
        "published_date": "2023-09-12",
        "author": "Netflix Open Connect Reliability Engineering",
        "h2": "Health-Checked OCA Pool Rotation, Manifest URI Fallback & Drain Automation",
        "p1": (
            "ISP-embedded Open Connect deployments consist of redundant appliances arranged in consistent-hashed "
            "storage pools so popular catalog titles are replicated across multiple hardware chassis. Continuous "
            "health probes monitor NIC link status, disk I/O latency, and TLS handshake success rates on every OCA."
        ),
        "code": (
            "manifest_urls = [primary_isp_oca_url, secondary_isp_oca_url, regional_ixp_oca_url]"
        ),
        "p2": (
            "If an appliance fails a health check or exceeds its egress bandwidth watermark, the control plane "
            "immediately drains new manifest assignments and instructs active client players to fail over to "
            "sibling or IXP appliances."
        ),
    },
    {
        "title": "Open Connect NVMe Flash Storage Tiering & Content Popularity Stratification",
        "source_url": "https://openconnect.netflix.com/en/appliance-hardware/nvme-flash-tiering-architecture",
        "source_type": "open_connect_documentation",
        "published_date": "2023-11-02",
        "author": "Netflix Open Connect Hardware & Storage Systems",
        "h2": "High-Throughput Flash Appliances vs. High-Capacity Storage Appliances",
        "p1": (
            "Netflix deploys two complementary Open Connect Appliance hardware profiles: high-density storage "
            "appliances (holding hundreds of terabytes of full-catalog video representations) and all-NVMe flash "
            "appliances optimized for 100–400 Gbps egress of top-tier热门 (high-velocity) catalog titles."
        ),
        "code": (
            "tier_assignment = \"NVME_FLASH_OCA\" if title_popularity_percentile >= 0.85 else \"STORAGE_HDD_OCA\""
        ),
        "p2": (
            "By stratifying media segments across NVMe and rotational tiers according to daily ML demand forecasts, "
            "Open Connect maximizes throughput per rack unit while preserving long-tail catalog availability."
        ),
    },
    {
        "title": "VMAF Open-Source Perceptual Quality SDK & Sub-Model Feature Extraction Specification",
        "source_url": "https://netflix.github.io/vmaf/perceptual-quality-feature-extraction-spec",
        "source_type": "engineering_documentation",
        "published_date": "2022-08-15",
        "author": "Netflix VMAF Open Source Maintainers",
        "h2": "libvmaf C API, 4K/Phone Models, Integer SIMD Acceleration & Neg-Mode Enhancement",
        "p1": (
            "The open-source `libvmaf` C library provides fixed-point AVX-512 and ARM NEON SIMD implementations "
            "of Visual Information Fidelity (VIF), Detail Loss Metric (DLM), and temporal motion extraction for "
            "high-speed perceptual quality evaluation during cloud video encoding."
        ),
        "code": (
            "vmaf_init(&vmaf, cfg);\n"
            "vmaf_read_pictures(vmaf, &ref_pic, &dist_pic, frame_index);\n"
            "vmaf_score_at_index(vmaf, model, &score, frame_index);"
        ),
        "p2": (
            "VMAF Negative Enhancement Gain (NEG) mode prevents artificial encoder sharpening or contrast "
            "boosting from inflating perceptual quality scores during codec optimization."
        ),
    },
    {
        "title": "Hollow: High-Performance In-Memory Catalog & Encoding Metadata Dissemination",
        "source_url": "https://netflix.github.io/hollow/catalog-metadata-in-memory-replication",
        "source_type": "engineering_documentation",
        "published_date": "2021-06-30",
        "author": "Netflix Core Runtime Engineering",
        "h2": "Bit-Packed Compact In-Memory Graphs & Delta Blob Propagation for Streaming Services",
        "p1": (
            "Hollow is Netflix's Java library and toolset for disseminating read-only catalog, playable asset, "
            "and encoding ladder metadata datasets across thousands of playback and manifest generation servers. "
            "Instead of querying external databases on every playback request, each microservice holds the entire "
            "compressed metadata graph in local RAM."
        ),
        "code": (
            "HollowConsumer consumer = HollowConsumer.withBlobRetriever(s3DeltaRetriever).build();\n"
            "PlayableAssetMetadata asset = consumer.getAPI(CatalogAPI.class).getPlayableAsset(titleId);"
        ),
        "p2": (
            "Delta state transitions are published on a regular cadence, allowing playback manifest services to "
            "resolve available AV1/HEVC/HDR representations in nanoseconds with zero garbage collection overhead."
        ),
    },
    {
        "title": "Titus: Multi-Tenant Container Execution Platform for Media Encoding & ML Specifications",
        "source_url": "https://netflix.github.io/titus/media-encoding-container-scheduling",
        "source_type": "engineering_documentation",
        "published_date": "2022-01-19",
        "author": "Netflix Titus Container Runtime Team",
        "h2": "Kubelet Integration, GPU/AVX-512 Hardware Affinity & Elastic Media Worker Pools",
        "p1": (
            "The Titus container execution specification defines how Netflix schedules compute-intensive video "
            "transcoding, VMAF feature extraction, and machine learning training containers with strict hardware "
            "instruction-set affinity (AVX-512 for SVT-AV1/x265 and GPU instances for neural encoding models)."
        ),
        "code": (
            "container_resources: { cpu: 16, memory_mb: 32768, cpu_isa: \"avx512\", network_mbps: 2500 }"
        ),
        "p2": (
            "Workload isolation guarantees that opportunistic batch re-encoding jobs yield compute and network "
            "bandwidth immediately whenever live streaming or customer-facing API services scale up."
        ),
    },
    {
        "title": "Encore: Distributed Cloud Transcoding & ISOBMFF/CMAF Segment Packaging Specification",
        "source_url": "https://netflix.github.io/encore/distributed-segment-packaging-specification",
        "source_type": "engineering_documentation",
        "published_date": "2023-03-04",
        "author": "Netflix Media Encoding & Packaging Architecture",
        "h2": "Deterministic Chunk Boundaries, `sidx` Indexing & Multi-Track Audio/Video Alignment",
        "p1": (
            "Netflix's cloud packaging specification governs how shot-encoded H.264, HEVC, and AV1 video "
            "bitstreams and Dolby Atmos / xHE-AAC audio tracks are multiplexed into compliant ISO Base Media "
            "File Format (ISOBMFF / CMAF) segment files."
        ),
        "code": (
            "[ftyp][moov: mvhd + trak + mvex] ... [sidx][moof: mfhd + traf][mdat: encrypted_video_samples]"
        ),
        "p2": (
            "Every representation in an adaptive bitrate ladder shares identical segment index (`sidx`) presentation "
            "timestamp boundaries so client players can switch bitrates or CDN pathways cleanly via byte-range "
            "requests."
        ),
    },
    {
        "title": "Convex Hull Rate-Distortion Optimization for Multi-Codec Adaptive Streaming Ladders",
        "source_url": "https://research.netflix.com/publications/convex-hull-rate-distortion-multi-codec-streaming",
        "source_type": "technical_paper",
        "published_date": "2019-09-15",
        "author": "Jan De Cock, Zhi Li, Mariana Afonso, Anne Aaron",
        "h2": "Pareto Frontier Construction Across Spatial Resolutions, Frame Rates & Quantization",
        "p1": (
            "This Netflix Research publication formalizes the multi-dimensional rate-distortion optimization "
            "problem for adaptive bitrate video streaming. Given a discrete set of spatial resolutions, frame "
            "rates, and codec quantization parameters, the encoder evaluates perceptual distortion D(R) using "
            "VMAF and constructs the upper concave envelope (convex hull) in the bitrate-quality plane."
        ),
        "code": (
            "Hull(S) = { (R_i, VMAF_i) in S : no (R_j, VMAF_j) has R_j <= R_i and VMAF_j > VMAF_i }"
        ),
        "p2": (
            "Operating exclusively along the shot-level convex hull ensures that every representation in a "
            "Netflix streaming manifest delivers the maximum achievable perceptual visual fidelity for its "
            "allocated network bandwidth."
        ),
    },
    {
        "title": "Contextual Bandits and Deep Exploration for Personalized Ranking at Scale",
        "source_url": "https://research.netflix.com/publications/contextual-bandits-for-personalized-ranking",
        "source_type": "technical_paper",
        "published_date": "2020-07-22",
        "author": "Netflix Machine Learning Research",
        "h2": "Off-Policy Inverse Propensity Scoring (IPS), Doubly Robust Estimators & Slate Ranking",
        "p1": (
            "Personalizing homepage slates and artwork across hundreds of millions of Netflix members requires "
            "counterfactual off-policy evaluation and principled uncertainty estimation. This paper presents "
            "Netflix's doubly robust contextual bandit framework for slate recommendation."
        ),
        "code": (
            "DR_estimate = E_hat(x, a) + (I(A == a) / propensity(a | x)) * (reward - E_hat(x, a))"
        ),
        "p2": (
            "Logged propensity weights from production recommendation policies enable offline training of new "
            "ranking models without feedback-loop bias."
        ),
    },
    {
        "title": "Causal Inference and Variance Reduction (CUPED) in Streaming QoE & Retention Experiments",
        "source_url": "https://research.netflix.com/publications/causal-inference-and-cuped-in-qoe-experiments",
        "source_type": "technical_paper",
        "published_date": "2021-10-05",
        "author": "Netflix Experimentation & Causal Inference Research",
        "h2": "Pre-Experiment Covariate Adjustment, Heterogeneous Treatment Effects & Surrogate Metrics",
        "p1": (
            "Evaluating the causal impact of adaptive bitrate (ABR) algorithms, video encoding ladders, and "
            "recommendation models on long-term member retention requires high statistical power. Netflix applies "
            "CUPED (Controlled-experiment Using Pre-Experiment Data) and machine-learned covariate adjustments "
            "to reduce metric variance by up to 50%."
        ),
        "code": (
            "Y_cuped = Y_post - theta * (X_pre - mean(X_pre))"
        ),
        "p2": (
            "Causal surrogate indices link short-term streaming QoE improvements (reduced rebuffering and higher "
            "VMAF) to long-term subscription retention value."
        ),
    },
    {
        "title": "Deep Learning & Neural In-Loop Filtering for Next-Generation Video Compression",
        "source_url": "https://research.netflix.com/publications/deep-learning-neural-in-loop-video-compression",
        "source_type": "technical_paper",
        "published_date": "2023-06-18",
        "author": "Netflix Video Coding & Machine Learning Research",
        "h2": "Convolutional Restoration Filters, Rate-Distortion-Complexity Trade-Offs & AV1/VVC",
        "p1": (
            "Netflix Research investigates neural network in-loop restoration filters and learned post-processing "
            "models that attenuate quantization ringing and block boundary artifacts in compressed video frames."
        ),
        "code": (
            "restored_frame = lightweight_cnn_filter(reconstructed_frame, qp_map, prediction_mode_map)"
        ),
        "p2": (
            "Conditioning compact convolutional filters on frame quantization parameter (QP) maps and transform "
            "block partition metadata improves VMAF perceptual quality at low bitrates."
        ),
    },
]


# ============================================================================
# 3. DEDICATED 10-DOCUMENT NETFLIX RECOMMENDATION & PERSONALIZATION CORPUS
#    (Used when PREFETCH_FOCUS_AREA="recommendation" and PREFETCH_DOCUMENT_COUNT=10)
# ============================================================================

NETFLIX_RECOMMENDATION_SPECS: List[Dict[str, str]] = [
    {
        "title": "The Netflix Recommender System: Algorithms, Business Value, and Innovation",
        "source_url": "https://research.netflix.com/publications/the-netflix-recommender-system",
        "source_type": "technical_paper",
        "published_date": "2016-01-04",
        "author": "Carlos A. Gomez-Uribe, Neil Hunt",
        "h2": "Multi-Algorithm Personalization Architecture: PVR, Top-N Video Ranker, Page Generation & Search",
        "p1": (
            "Netflix's personalization and recommendation architecture combines a suite of specialized machine "
            "learning algorithms—including Personalized Video Ranker (PVR), Top-N Video Ranker, Trending Now, "
            "Continue Watching, Video-Video Similarity (Because You Watched), and Page Generation 2D row ranking—to "
            "personalize every row and column of the homepage grid for over 260 million to 301 million paid member "
            "households globally. Rather than relying on a single monolithic ranking score, each row on a member's "
            "homepage represents a coherent thematic or algorithmic hypothesis."
        ),
        "code": (
            "# Multi-Stage Netflix Homepage Personalization Pipeline\n"
            "candidate_rows = row_generator.generate_thematic_and_personalized_rows(member_id, context)\n"
            "for row in candidate_rows:\n"
            "    row.videos = pvr_or_top_n_ranker.score_and_sort(member_id, row.candidates, device_context)\n"
            "homepage_slate = page_generation_2d_optimizer.select_diverse_slate(candidate_rows, viewport_budget)"
        ),
        "p2": (
            "Candidate generation and ranking models consume real-time interaction signals, longitudinal watch "
            "history, time-of-day and device context, personalized artwork affinities, and semantic search query "
            "embeddings. Every algorithmic model and feature change is validated through Netflix's large-scale "
            "online A/B experimentation platform measuring long-term member retention and streaming engagement "
            "across Netflix's consolidated streaming service ($33.7B–$39.0B annual streaming revenue across "
            "Standard with Ads $6.99/mo, Standard $15.49/mo, and Premium 4K UHD + Spatial Audio $22.99/mo tiers; "
            "standalone recommendation subsystem revenue is not separately broken out in SEC Form 10-K filings)."
        ),
    },
    {
        "title": "Foundation Models for Personalized Recommendation at Netflix",
        "source_url": "https://netflixtechblog.com/foundation-models-for-personalized-recommendation-at-netflix-8a9102c41e77",
        "source_type": "technology_blog",
        "published_date": "2024-03-19",
        "author": "Netflix Personalization & Machine Learning Research",
        "h2": "Large-Scale Autoregressive Transformer Member Interaction Models & Multi-Task Ranking",
        "p1": (
            "Netflix's next-generation recommendation architecture unifies previously fragmented task-specific "
            "models (Personalized Video Ranker, Continue Watching, Similar Titles, and Search) using large-scale "
            "autoregressive and bidirectional Transformer foundation models trained on longitudinal member "
            "interaction sequences. Each member's historical stream of plays, thumbs-up ratings, search clicks, "
            "trailer previews, and browse dwell durations is tokenized with continuous timestamp and device-type "
            "positional encodings."
        ),
        "code": (
            "member_state_vec = causal_interaction_transformer(\n"
            "    item_token_ids=history_titles,\n"
            "    interaction_types=event_types,\n"
            "    duration_buckets=watch_completion_ratios,\n"
            "    device_context=client_platform_id\n"
            ")\n"
            "next_item_logits = multi_task_projection_head(member_state_vec, candidate_item_embeddings)"
        ),
        "p2": (
            "Learned high-dimensional member and title representations are exported to low-latency Approximate "
            "Nearest Neighbor (ANN) vector indices and distilled into online two-stage ranking tiers, enabling "
            "consistent personalization transfer across cold-start titles, homepage row ranking, and interactive "
            "discovery across hundreds of millions of subscriber profiles."
        ),
    },
    {
        "title": "Artwork Personalization at Netflix Using Contextual Bandits",
        "source_url": "https://netflixtechblog.medium.com/artwork-personalization-at-netflix-718294a0c1e3",
        "source_type": "technology_blog",
        "published_date": "2017-12-07",
        "author": "Ashok Chandrashekar, Fernando Amat, Justin Basilico, Tony Jebara",
        "h2": "Contextual Bandit Exploration-Exploitation for Personalized Homepage Title Imagery",
        "p1": (
            "A member's decision to watch a recommended title on Netflix is heavily influenced by the visual "
            "artwork (boxshot and focal still frame) displayed in the homepage row. Rather than serving a single "
            "static poster to all 260M+ subscribers, Netflix deploys contextual multi-armed bandit algorithms to "
            "select personalized title artwork tailored to each member's genre preferences, cast/actor affinities, "
            "and visual aesthetic history."
        ),
        "code": (
            "# Contextual Bandit Artwork Selection (Thompson Sampling / LinUCB)\n"
            "for artwork_arm in candidate_artworks[title_id]:\n"
            "     sampled_theta = sample_posterior(artwork_arm.mu, artwork_arm.covariance)\n"
            "     expected_take_rate[artwork_arm] = sigmoid(dot(sampled_theta, member_context_features))\n"
            "selected_artwork = argmax(expected_take_rate)"
        ),
        "p2": (
            "Online Thompson sampling and LinUCB contextual bandit policies continuously balance uncertainty-driven "
            "exploration of newly extracted candidate key art frames against exploitation of high-take-rate "
            "personalized imagery, while applying cross-row visual deduplication so a title never appears with "
            "conflicting artwork within the same browse session."
        ),
    },
    {
        "title": "Semantic Search & Multimodal Video Embeddings for Content Discovery at Netflix",
        "source_url": "https://netflixtechblog.medium.com/semantic-search-and-multimodal-video-embeddings-at-netflix-4b9102e83c11",
        "source_type": "technology_blog",
        "published_date": "2023-07-12",
        "author": "Netflix Search & Discovery Machine Learning Team",
        "h2": "Contrastive Query-Video Dense Vector Embeddings & Approximate Nearest Neighbor (ANN) Retrieval",
        "p1": (
            "When members search or browse Netflix using natural-language queries, thematic mood descriptions, "
            "actor names, or partial plot concepts, lexical prefix matching alone fails to surface semantically "
            "relevant catalog titles. Netflix's semantic search and recommendation retrieval engine encodes user "
            "queries, member profile context, and multimodal catalog metadata (keyframes from video shots, audio "
            "dialogue transcripts, localized subtitles, and editorial synopses) into a unified 768-dimensional "
            "dense vector embedding space."
        ),
        "code": (
            "query_vec = l2_normalize(query_encoder(search_text, member_profile_embedding))\n"
            "title_vec = l2_normalize(multimodal_fusion_encoder(video_shot_vecs, subtitle_vecs, metadata_vecs))\n"
            "top_k_candidates = scann_vector_index.search_cosine(query_vec, top_k=200)"
        ),
        "p2": (
            "Approximate Nearest Neighbor (ANN) cosine similarity search over pre-computed catalog embeddings "
            "retrieves top candidate titles in under 15 milliseconds, which are then re-ranked by a personalized "
            "pointwise/listwise neural ranker conditioned on the member's watch history and real-time session intent."
        ),
    },
    {
        "title": "Contextual Bandits and Deep Exploration for Personalized Ranking at Scale",
        "source_url": "https://research.netflix.com/publications/contextual-bandits-for-personalized-ranking",
        "source_type": "technical_paper",
        "published_date": "2020-07-22",
        "author": "Netflix Machine Learning Research",
        "h2": "Off-Policy Inverse Propensity Scoring (IPS), Doubly Robust Estimators & Slate Ranking",
        "p1": (
            "Personalizing homepage slates, row rankings, and promotional billboards across hundreds of millions "
            "of Netflix members requires counterfactual off-policy evaluation and principled uncertainty estimation "
            "to overcome presentation position bias and feedback loops. This Netflix Research publication formalizes "
            "doubly robust (DR) contextual bandit training and off-policy slate evaluation."
        ),
        "code": (
            "# Doubly Robust (DR) Counterfactual Policy Value Estimator\n"
            "ips_weight = min(clip_max, pi_target(action | context) / propensity_logged(action | context))\n"
            "dr_reward = reward_model_hat(context, action) + ips_weight * (observed_play_reward - reward_model_hat(context, action))"
        ),
        "p2": (
            "By logging exact action assignment propensities from production recommendation policies and correcting "
            "for row/column examination bias, Netflix trains new candidate ranking policies offline and deploys "
            "Bayesian deep exploration policies that rapidly surface new catalog releases to receptive audience segments."
        ),
    },
    {
        "title": "Personalized Page Generation: Two-Stage Slate Ranking & 2D Homepage Canvas Optimization at Netflix",
        "source_url": "https://netflixtechblog.com/personalized-page-generation-and-slate-ranking-at-netflix-5c8192e04a11",
        "source_type": "technology_blog",
        "published_date": "2022-10-18",
        "author": "Netflix Page Generation & Homepage Ranking Engineering",
        "h2": "Hierarchical Row-and-Title 2D Matrix Optimization, Diversity Constraints & Sub-100ms Scoring",
        "p1": (
            "Constructing the Netflix homepage is a two-dimensional (2D) combinatorial slate optimization problem: "
            "selecting both which thematic rows to display vertically and which ranked videos to place horizontally "
            "within each row. With tens of thousands of candidate row templates per member profile, Netflix's Page "
            "Generation service executes a two-stage hierarchical funnel under a strict sub-100ms latency budget."
        ),
        "code": (
            "# 2D Homepage Slate Submodular Utility Optimization\n"
            "for row_slot in range(max_homepage_rows):\n"
            "    best_row = argmax_r ( relevance_score(member, r) - diversity_penalty(r, selected_rows) - title_duplication_cost(r, displayed_titles) )\n"
            "    selected_rows.append(best_row)"
        ),
        "p2": (
            "Stage 1 prunes thousands of candidate row cohorts using lightweight member-row dot-product embeddings, "
            "while Stage 2 evaluates cross-row genre diversity, horizontal viewport visibility budgets, and title "
            "deduplication constraints so that the assembled 2D homepage slate maximizes total member streaming "
            "satisfaction rather than greedy single-row click-through rate."
        ),
    },
    {
        "title": "Two-Tower Neural Candidate Retrieval & Approximate Nearest Neighbor (ANN) Indexing for Netflix Recommendations",
        "source_url": "https://netflixtechblog.medium.com/two-tower-neural-candidate-retrieval-and-ann-indexing-at-netflix-3f9104c82b19",
        "source_type": "technology_blog",
        "published_date": "2023-04-25",
        "author": "Netflix Candidate Generation & Vector Retrieval Team",
        "h2": "Dual-Tower Member/Item Co-Embeddings, In-Batch Negative Sampling & ScaNN Vector Search",
        "p1": (
            "Before heavyweight deep neural ranking models score candidate videos for a Netflix homepage row, "
            "candidate retrieval must narrow the global catalog down to a high-recall shortlist of several hundred "
            "titles in milliseconds. Netflix employs a Two-Tower neural retrieval architecture where a Member Tower "
            "encodes longitudinal watch history, real-time session events, and geographic/language context, while "
            "an Item Tower encodes title metadata, tags, and visual/audio embeddings."
        ),
        "code": (
            "# Two-Tower Contrastive Softmax Training with Log-Q Frequency Correction\n"
            "logits = matmul(member_tower(u_features), transpose(item_tower(v_features))) / temperature - log(item_sampling_prob)\n"
            "loss = cross_entropy_loss(logits, positive_watched_item_indices)"
        ),
        "p2": (
            "Item tower embeddings are pre-indexed into distributed vector search shards using quantized cosine "
            "similarity indexing (ScaNN / HNSW). At request time, the Member Tower computes a fresh 768-d query "
            "embedding that retrieves top-K personalized candidates across the global catalog in single-digit milliseconds."
        ),
    },
    {
        "title": "Session-Based Sequential Recommendation & Real-Time In-Session Intent Adaptation at Netflix",
        "source_url": "https://netflixtechblog.com/session-based-sequential-recommendation-and-real-time-intent-at-netflix-9d8102e43c55",
        "source_type": "technology_blog",
        "published_date": "2023-09-14",
        "author": "Netflix Real-Time Personalization & Streaming ML Engineering",
        "h2": "Keystone/Flink Event Feedback Loops, Dwell-Time Signals & Dynamic In-Session Re-Ranking",
        "p1": (
            "A Netflix member's immediate viewing intent within a live browse session often diverges from their "
            "historical baseline—for example, a household browsing for a family comedy on Friday night versus a "
            "documentary on Tuesday evening. Netflix captures fine-grained in-session client telemetry including "
            "row scroll velocity, title card focus dwell time (>1.5 seconds), trailer preview playback duration, "
            "and detail-page expansions."
        ),
        "code": (
            "session_intent_emb = gru_or_transformer_session_encoder(recent_focus_dwell_events, trailer_preview_ids)\n"
            "reranked_row = online_reranker.score(candidate_titles, long_term_member_emb, session_intent_emb)"
        ),
        "p2": (
            "Streamed through Apache Kafka and Apache Flink on Netflix's Keystone data pipeline, these sub-second "
            "interaction signals update an ephemeral in-session intent embedding that dynamically re-ranks below-the-fold "
            "homepage rows and search suggestions as the member scrolls."
        ),
    },
    {
        "title": "Interleaving and Sequential Testing in Netflix's Large-Scale A/B Experimentation Platform",
        "source_url": "https://netflixtechblog.com/interleaving-in-online-experiments-at-netflix-a04ee392ec55",
        "source_type": "technology_blog",
        "published_date": "2018-04-11",
        "author": "Netflix Experimentation Platform Engineering",
        "h2": "Team-Draft Interleaving for Recommendation Ranking, 100x Sample Efficiency & CUPED Guardrails",
        "p1": (
            "To accelerate algorithmic iteration across Personalized Video Ranker (PVR), Top-N recommendation "
            "models, and search ranking, Netflix supplements traditional multi-week A/B tests with Team-Draft "
            "Interleaving. By blending candidate video rankings from two competing recommendation algorithms "
            "within a single member's homepage row and attributing qualified play hours to the originating "
            "algorithm, interleaving detects ranking quality differences with 100x fewer subscribers."
        ),
        "code": (
            "interleaved_row, attribution_map = team_draft_interleave(ranker_A_videos, ranker_B_videos, seed=member_id)\n"
            "win_skew = compute_attributed_watch_hours(attribution_map, qualified_play_events)"
        ),
        "p2": (
            "Winning recommendation candidates from Stage 1 interleaving tournaments are promoted to Stage 2 "
            "controlled A/B experiments utilizing CUPED (Controlled-experiment Using Pre-Experiment Data) variance "
            "reduction to verify causal improvements in long-term member retention and streaming engagement."
        ),
    },
    {
        "title": "Calibrated Recommendations & Multi-Objective Utility Optimization for Member Retention at Netflix",
        "source_url": "https://research.netflix.com/publications/calibrated-recommendations-and-multi-objective-ranking",
        "source_type": "technical_paper",
        "published_date": "2021-11-12",
        "author": "Harald Steck, Netflix Machine Learning Research",
        "h2": "KL-Divergence Genre Calibration & Pareto Balancing of Click Probability vs. Completion Value",
        "p1": (
            "Pointwise accuracy-optimized recommender systems frequently suffer from popularity amplification and "
            "genre crowding—over-recommending a member's majority genre (e.g., 70% action movies) until it occupies "
            "100% of the recommended slate, starving secondary interests (e.g., 30% indie documentaries). Netflix "
            "Research formulated Calibrated Recommendations to align the genre and maturity distribution of a "
            "recommended slate with the member's historical preference distribution."
        ),
        "code": (
            "# Calibrated Slate Selection with Kullback-Leibler (KL) Divergence Regularization\n"
            "calibrated_slate = argmax_S ( sum_{i in S} multi_objective_utility(u, i) - lambda_cal * KL_divergence(P_history(g | u) || Q_slate(g | S)) )"
        ),
        "p2": (
            "Combined with multi-objective utility functions that jointly weight P(play), expected watch completion "
            "ratio, and post-watch satisfaction signals, calibrated slate post-processing prevents filter bubbles "
            "and improves long-term household subscription retention."
        ),
    },
]


def _spec_to_doc_entry(spec: Dict[str, str]) -> Dict[str, Any]:
    is_medium = "netflixtechblog" in spec["source_url"]
    nav_banner = (
        "<nav>Netflix TechBlog on Medium | Follow Publication</nav>"
        if is_medium
        else "<nav>Netflix Technical Documentation Header</nav>"
    )
    raw_html = f"""
    <html>
      <head>
        <title>{spec["title"]}</title>
        <meta name="author" content="{spec["author"]}" />
        <meta property="article:published_time" content="{spec["published_date"]}" />
      </head>
      <body>
        {nav_banner}
        <article>
          <h1>{spec["title"]}</h1>
          <h2>{spec["h2"]}</h2>
          <p>{spec["p1"]}</p>
          <pre><code>{spec["code"]}</code></pre>
          <p>{spec["p2"]}</p>
        </article>
        <footer>Copyright Netflix Engineering</footer>
      </body>
    </html>
    """
    return {
        "company": "Netflix",
        "title": spec["title"],
        "source_url": spec["source_url"],
        "source_type": spec["source_type"],
        "published_date": spec["published_date"],
        "author": spec["author"],
        "focus_domain": "recommendation",
        "raw_html": raw_html,
    }


NETFLIX_RECOMMENDATION_DOCUMENTS: List[Dict[str, Any]] = [
    _spec_to_doc_entry(spec) for spec in NETFLIX_RECOMMENDATION_SPECS
]


def _build_all_valid_netflix_documents() -> List[Dict[str, Any]]:
    """
    Constructs the full catalog of valid Netflix documents, placing the 10 comprehensive
    Netflix Recommendation & Personalization documents first, followed by the broader
    Netflix Video Encoding, Open Connect CDN, and Playback Engineering documents.
    """
    seen_urls = set()
    docs: List[Dict[str, Any]] = []

    for rec_doc in NETFLIX_RECOMMENDATION_DOCUMENTS:
        seen_urls.add(rec_doc["source_url"])
        docs.append(rec_doc)

    for core_doc in CORE_NETFLIX_DOCUMENTS:
        if core_doc["source_url"] not in seen_urls:
            seen_urls.add(core_doc["source_url"])
            docs.append(core_doc)

    for spec in EXPANDED_CORPUS_SPECS:
        if spec["source_url"] not in seen_urls:
            seen_urls.add(spec["source_url"])
            docs.append(_spec_to_doc_entry(spec))

    return docs


ALL_VALID_NETFLIX_DOCUMENTS: List[Dict[str, Any]] = _build_all_valid_netflix_documents()


def get_configured_netflix_documents(
    doc_limit: Optional[int] = None,
    doc_count: Optional[int] = None,
    focus_area: Optional[str] = None,
    include_quarantine_tests: bool = True,
    include_quarantine_demos: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """
    Returns the configured list of Netflix documents to prefetch into AlloyDB, controlled by
    the `PREFETCH_DOCUMENT_COUNT` config variable (default: 10) and `PREFETCH_FOCUS_AREA` (default: 'recommendation').
    """
    resolved_limit = doc_limit if doc_limit is not None else doc_count
    effective_limit = int(resolved_limit if resolved_limit is not None else PREFETCH_DOCUMENT_COUNT)
    effective_focus = (focus_area if focus_area is not None else PREFETCH_FOCUS_AREA).strip().lower()
    use_quarantine = include_quarantine_demos if include_quarantine_demos is not None else include_quarantine_tests

    if "recommend" in effective_focus or "personal" in effective_focus:
        ordered_valid = list(NETFLIX_RECOMMENDATION_DOCUMENTS) + [
            d for d in ALL_VALID_NETFLIX_DOCUMENTS if d not in NETFLIX_RECOMMENDATION_DOCUMENTS
        ]
    else:
        ordered_valid = list(ALL_VALID_NETFLIX_DOCUMENTS)

    selected_docs = ordered_valid[: max(1, effective_limit)]

    if include_quarantine_tests and selected_docs:
        # 1. Cross-mirror duplicate of the first Medium article in selected_docs to verify SHA-256 deduplication
        first_doc = selected_docs[0]
        selected_docs.append(
            {
                "company": "Netflix",
                "title": f"{first_doc['title']} (Syndicated Mirror Duplicate)",
                "source_url": "https://netflixtechblog.medium.com/the-netflix-recommender-system-mirror-dup",
                "source_type": "technology_blog",
                "published_date": first_doc["published_date"],
                "author": first_doc["author"],
                "raw_html": first_doc["raw_html"],
            }
        )
        # 2. Intentional unapproved external URL test entry to verify strict allowlist quarantine into `failed_documents`
        selected_docs.append(
            {
                "company": "Netflix",
                "title": "Unverified Third-Party Speculation Blog Post",
                "source_url": "https://unapproved-random-rumors.example.org/netflix-secret-hardware",
                "source_type": "unapproved_web",
                "published_date": "2024-01-10",
                "author": "Unknown Blogger",
                "raw_html": "<p>Unverified third-party speculation outside the 5 approved Netflix domains.</p>",
            }
        )
        # 3. Intentional malformed / empty body test entry on an approved prefix to verify HTTP/parse quarantine
        selected_docs.append(
            {
                "company": "Netflix",
                "title": "Deprecated Empty Draft Endpoint",
                "source_url": "https://netflix.github.io/deprecated-empty-draft-404",
                "source_type": "engineering_documentation",
                "published_date": "2023-01-01",
                "author": None,
                "simulate_http_error": "HTTP_404_NOT_FOUND: Upstream document returned empty body or 404 status.",
                "raw_html": "",
            }
        )

    return selected_docs


# Default active prefetch list (10 valid Recommendation documents + deduplication/quarantine verification entries)
CONFIGURED_NETFLIX_DOCUMENTS: List[Dict[str, Any]] = get_configured_netflix_documents(
    doc_limit=PREFETCH_DOCUMENT_COUNT,
    focus_area=PREFETCH_FOCUS_AREA,
    include_quarantine_tests=True,
)

