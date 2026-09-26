"""
Explicit Source Allowlist Configuration for the Offline Target Company Knowledge Prefetch Pipeline.

Target Company:
    Netflix

Approved Initial Sources (Strict Allowlist):
    1. https://netflixtechblog.com/
    2. https://netflixtechblog.medium.com/
    3. https://openconnect.netflix.com/
    4. https://research.netflix.com/publications
    5. https://netflix.github.io/

Any URL outside these explicitly configured prefixes MUST be rejected and logged to the
quarantine table (`failed_documents`).
"""

from typing import List, Dict, Any

TARGET_COMPANY = "Netflix"

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
        "name": "Netflix Technology Blog (Primary Domain)",
        "url_prefix": "https://netflixtechblog.com/",
        "source_type": "technology_blog",
        "approval_status": "EXPLICITLY_APPROVED",
    },
    {
        "source_id": "netflix_techblog_medium",
        "name": "Netflix Technology Blog (Medium Publication)",
        "url_prefix": "https://netflixtechblog.medium.com/",
        "source_type": "technology_blog",
        "approval_status": "EXPLICITLY_APPROVED",
    },
    {
        "source_id": "netflix_open_connect_docs",
        "name": "Netflix Open Connect Public Documentation",
        "url_prefix": "https://openconnect.netflix.com/",
        "source_type": "open_connect_documentation",
        "approval_status": "EXPLICITLY_APPROVED",
    },
    {
        "source_id": "netflix_research_papers",
        "name": "Netflix Research Public Technical Papers",
        "url_prefix": "https://research.netflix.com/publications",
        "source_type": "technical_paper",
        "approval_status": "EXPLICITLY_APPROVED",
    },
    {
        "source_id": "netflix_engineering_docs",
        "name": "Netflix Public Engineering & Media Documentation",
        "url_prefix": "https://netflix.github.io/",
        "source_type": "engineering_documentation",
        "approval_status": "EXPLICITLY_APPROVED",
    },
]


# Curated manifest of explicitly configured Netflix documents for offline ingestion.
# Includes full HTML structure (navigation/footer noise to be stripped, headings, paragraphs,
# and code blocks to be preserved), plus:
# - an intentional cross-mirror SHA-256 duplicate entry to demonstrate deduplication
# - an intentional unapproved external URL to demonstrate strict allowlist rejection into `failed_documents`
# - an intentional malformed/HTTP-error source to demonstrate error quarantine logging into `failed_documents`
CONFIGURED_NETFLIX_DOCUMENTS: List[Dict[str, Any]] = [
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
    # Intentional cross-mirror duplicate entry to verify SHA-256 content_hash deduplication
    {
        "company": "Netflix",
        "title": "Per-Title Encode Optimization (Medium Syndicated Mirror)",
        "source_url": "https://netflixtechblog.medium.com/per-title-encode-optimization-7e99442b62a2",
        "source_type": "technology_blog",
        "published_date": "2015-12-14",
        "author": "Aaron Cockcroft, Jan De Cock, Anne Aaron",
        "raw_html": """
        <html>
          <body>
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
          </body>
        </html>
        """,
    },
    # Intentional unapproved external URL test entry to verify strict allowlist quarantine into `failed_documents`
    {
        "company": "Netflix",
        "title": "Unverified Third-Party Speculation Blog Post",
        "source_url": "https://unapproved-random-rumors.example.org/netflix-secret-hardware",
        "source_type": "unapproved_web",
        "published_date": "2024-01-10",
        "author": "Unknown Blogger",
        "raw_html": "<p>Unverified third-party speculation outside the 5 approved Netflix domains.</p>",
    },
    # Intentional malformed / empty body test entry on an approved prefix to verify HTTP/parse quarantine into `failed_documents`
    {
        "company": "Netflix",
        "title": "Deprecated Empty Draft Endpoint",
        "source_url": "https://netflix.github.io/deprecated-empty-draft-404",
        "source_type": "engineering_documentation",
        "published_date": "2023-01-01",
        "author": None,
        "simulate_http_error": "HTTP_404_NOT_FOUND: Upstream document returned empty body or 404 status.",
        "raw_html": "",
    },
]
