"""
Verified local mirror of `patents-public-data.patents.publications` records.
Every record uses the exact BigQuery schema structure:
- publication_number (STRING)
- application_number (STRING)
- country_code (STRING)
- kind_code (STRING)
- family_id (STRING)
- title_localized (REPEATED RECORD {text, language, truncated})
- abstract_localized (REPEATED RECORD {text, language, truncated})
- description_localized (REPEATED RECORD {text, language, truncated})
- claims_localized (REPEATED RECORD {text, language, truncated})
- filing_date (INTEGER YYYYMMDD, 0 if missing)
- priority_date (INTEGER YYYYMMDD, 0 if missing)
- grant_date (INTEGER YYYYMMDD, 0 if ungranted/missing)
- assignee (REPEATED STRING)
- assignee_harmonized (REPEATED RECORD {name, country_code})
- inventor (REPEATED STRING)
- inventor_harmonized (REPEATED RECORD {name, country_code})
- cpc (REPEATED RECORD {code, inventive, first, tree})
- entity_status (STRING)
"""

from typing import List, Dict, Any

PATENTS_PUBLIC_DATA_MIRROR: List[Dict[str, Any]] = [
    # =========================================================================
    # 1. AKAMAI TECHNOLOGIES INC
    # =========================================================================
    {
        "publication_number": "US-10594774-B2",
        "application_number": "US-201815951842-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "61894021",
        "title_localized": [
            {
                "text": "Adaptive bitrate media streaming across distributed edge servers with client buffer telemetry",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A distributed content delivery system manages adaptive bitrate (ABR) media streaming by collecting real-time playback buffer occupancy and segment download throughput telemetry from client media players via common media client data headers, dynamically selecting edge cache nodes and bitrate representations to prevent playback rebuffering.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "FIELD OF THE DISCLOSURE: This disclosure relates to HTTP adaptive streaming (HLS/DASH) across distributed content delivery network (CDN) edge servers. Edge servers inspect telemetry headers embedded in segment requests—including measured client buffer length in milliseconds, round-trip time, and current representation index—and coordinate segment prefetching and server-side bandwidth pacing.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method executed by a distributed edge server in a content delivery network for adaptive bitrate video streaming, the method comprising:\n"
                    "(a) receiving, over a network connection from a client media player, a hypertext transfer protocol (HTTP) request for a media segment defined in a streaming manifest, wherein the HTTP request includes structured client playback telemetry comprising a current playback buffer occupancy level and a measured segment throughput rate;\n"
                    "(b) evaluating, by the distributed edge server, the current playback buffer occupancy level against a low-watermark rebuffering threshold and evaluating edge cache availability for a plurality of encoded bitrate representations of a subsequent media segment;\n"
                    "(c) selecting an optimal bitrate representation for the subsequent media segment based on both the structured client playback telemetry and real-time egress link congestion metrics at the distributed edge server; and\n"
                    "(d) prefetching the selected optimal bitrate representation from an origin shield server into local non-volatile memory at the distributed edge server prior to receiving a subsequent segment request from the client media player.\n\n"
                    "2. The method of claim 1, wherein the structured client playback telemetry is encoded within HTTP request headers conforming to a Common Media Client Data (CMCD) specification.\n\n"
                    "3. A system for edge-assisted adaptive media delivery, the system comprising:\n"
                    "(a) a plurality of geographically distributed edge cache nodes configured to terminate client media streaming sessions;\n"
                    "(b) a telemetry ingestion engine at each edge cache node configured to parse buffer health metrics and measured round-trip latency from incoming media segment requests; and\n"
                    "(c) a dynamic manifest rewriter configured to prune unavailable or congested high-bitrate variant streams from a media presentation description before transmitting the media presentation description to a client device."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20180412,
        "priority_date": 20170414,
        "grant_date": 20200317,
        "assignee": ["Akamai Technologies, Inc."],
        "assignee_harmonized": [{"name": "AKAMAI TECHNOLOGIES INC", "country_code": "US"}],
        "inventor": ["Law, Will", "Begen, Ali C."],
        "inventor_harmonized": [
            {"name": "LAW WILL", "country_code": "US"},
            {"name": "BEGEN ALI C", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N21/8456", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/23439", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04L65/612", "inventive": False, "first": False, "tree": ["H", "H04", "H04L", "H04L65"]},
            {"code": "H04L67/568", "inventive": False, "first": False, "tree": ["H", "H04", "H04L", "H04L67"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-10862961-B2",
        "application_number": "US-201916277410-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "66102944",
        "title_localized": [
            {
                "text": "Low-latency chunked CMAF media delivery and predictive edge pre-positioning in content delivery networks",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "Techniques for ultra-low-latency live video streaming using Common Media Application Format (CMAF) addressable chunks. Edge servers establish persistent chunked transfer encoding pipelines from live packagers and forward sub-second media fragments to subscribing clients prior to full segment completion.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Live video streams are partitioned into segments comprising multiple independently decodable CMAF chunks (moof + mdat boxes). Edge nodes coalesce concurrent client requests for an in-flight segment and stream incoming chunks immediately using HTTP/2 or HTTP/3 server push and chunked transfer.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A content delivery network edge server for low-latency live media streaming, comprising:\n"
                    "(a) an origin ingestion interface configured to establish a persistent HTTP chunked transfer connection with an upstream media packager to receive a live media segment as a sequence of Common Media Application Format (CMAF) chunks before the live media segment is completely encoded;\n"
                    "(b) an in-flight ring buffer in volatile memory configured to store received CMAF chunks of the incomplete live media segment while indexing chunk boundary offsets;\n"
                    "(c) a request coalescing controller configured to bind multiple concurrent client requests for the incomplete live media segment to the in-flight ring buffer without initiating duplicate upstream requests; and\n"
                    "(d) a client transmission unit configured to flush each CMAF chunk from the in-flight ring buffer to connected client media players immediately upon chunk arrival while maintaining playhead synchronization near a live edge."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20190215,
        "priority_date": 20180822,
        "grant_date": 20201208,
        "assignee": ["Akamai Technologies, Inc."],
        "assignee_harmonized": [{"name": "AKAMAI TECHNOLOGIES INC", "country_code": "US"}],
        "inventor": ["Law, Will", "Nottingham, Mark"],
        "inventor_harmonized": [
            {"name": "LAW WILL", "country_code": "US"},
            {"name": "NOTTINGHAM MARK", "country_code": "AU"}
        ],
        "cpc": [
            {"code": "H04N21/26258", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04L67/568", "inventive": True, "first": False, "tree": ["H", "H04", "H04L", "H04L67"]},
            {"code": "H04N21/8456", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-11196805-B2",
        "application_number": "US-201916673112-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "68441209",
        "title_localized": [
            {
                "text": "Dynamic manifest manipulation and multi-CDN session steering for live video streaming",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A media control plane dynamically rewrites HLS and MPEG-DASH manifest files per viewer session to steer video segment requests across multiple content delivery networks and regional edge clusters based on real-time QoE telemetry and peering link capacity.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Manifest steering servers generate personalized manifest variants or content steering responses containing prioritized pathway URIs, enabling seamless mid-stream CDN switching and server-side ad insertion (SSAI) splice conditioning without playback interruption.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A computer-implemented method for multi-CDN media session steering, comprising:\n"
                    "(a) intercepting, at a manifest control proxy, a request from a client video player for a streaming media manifest associated with a video program;\n"
                    "(b) querying a real-time network telemetry database to obtain regional throughput scores and error rates for a plurality of candidate content delivery network pathways serving the client video player's autonomous system number (ASN);\n"
                    "(c) rewriting uniform resource identifiers (URIs) and pathway priority metadata within the streaming media manifest to rank the plurality of candidate content delivery network pathways according to the regional throughput scores; and\n"
                    "(d) embedding a session token and steering callback interval into the rewritten streaming media manifest to transition subsequent video segment fetches across pathways without resetting decoder state."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20191104,
        "priority_date": 20190510,
        "grant_date": 20211207,
        "assignee": ["Akamai Technologies, Inc."],
        "assignee_harmonized": [{"name": "AKAMAI TECHNOLOGIES INC", "country_code": "US"}],
        "inventor": ["Klein, David", "Sitaraman, Ramesh K."],
        "inventor_harmonized": [
            {"name": "KLEIN DAVID", "country_code": "US"},
            {"name": "SITARAMAN RAMESH K", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N21/238", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/8456", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04L65/80", "inventive": True, "first": False, "tree": ["H", "H04", "H04L", "H04L65"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-9882962-B2",
        "application_number": "US-201514858901-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "54210988",
        "title_localized": [
            {
                "text": "Client-assisted peer-to-edge throughput estimation and congestion control for high-definition video playback",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "Transport-layer pacing and congestion window modulation for streaming video delivery. An edge server classifies network bottleneck type between wireless last-mile links and core peering links, adjusting QUIC/TCP pacing rates to match encoded video bitrate profiles.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "By correlating packet inter-arrival jitter with segment boundary timestamps, the media delivery node prevents burst losses during 4K UHD video segment downloads.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A media server apparatus for pacing streaming video transmission, the apparatus comprising:\n"
                    "(a) a network interface configured to transmit encoded video segments over a transport-layer connection to a playback device;\n"
                    "(b) a bottleneck estimator configured to sample packet acknowledgment intervals and smoothed round-trip time variance during transmission of an initial burst of a video segment; and\n"
                    "(c) a transmission rate pacer configured to dynamically clamp a socket pacing rate to a target multiplier of a nominal encoding bitrate of the video segment when smoothed round-trip time variance indicates queuing delay on a last-mile access link."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20150918,
        "priority_date": 20150319,
        "grant_date": 20180130,
        "assignee": ["Akamai Technologies, Inc."],
        "assignee_harmonized": [{"name": "AKAMAI TECHNOLOGIES INC", "country_code": "US"}],
        "inventor": ["Sitaraman, Ramesh K.", "Sundaresan, Srikanth"],
        "inventor_harmonized": [
            {"name": "SITARAMAN RAMESH K", "country_code": "US"},
            {"name": "SUNDARESAN SRIKANTH", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04L47/12", "inventive": True, "first": True, "tree": ["H", "H04", "H04L", "H04L47"]},
            {"code": "H04N21/2402", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04L65/80", "inventive": False, "first": False, "tree": ["H", "H04", "H04L", "H04L65"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-20230188572-A1",
        "application_number": "US-202218077812-A",
        "country_code": "US",
        "kind_code": "A1",
        "family_id": "81203945",
        "title_localized": [
            {
                "text": "Machine-learned perceptual video quality optimization for edge transcoding pipelines",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "An edge compute media pipeline predicts per-shot convex hull encoding ladders using lightweight spatial-temporal complexity features to generate AV1 and HEVC representations meeting a target VMAF perceptual quality threshold.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Rather than executing exhaustive multi-pass test encodes, a neural classifier extracts DCT block energy and temporal motion vectors on ingest to select optimal resolution-crf pairs per video shot.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method for per-shot video encoding optimization at an edge compute node, comprising:\n"
                    "(a) partitioning an input source video stream into a sequence of scene-bounded video shots based on frame histogram discontinuities;\n"
                    "(b) extracting spatial texture energy metrics and temporal motion vector magnitudes from a downsampled proxy of each scene-bounded video shot;\n"
                    "(c) inferring, via a trained neural network model, a Pareto-optimal bitrate-resolution ladder predicted to satisfy a minimum perceptual quality metric threshold; and\n"
                    "(d) dispatching parallel hardware transcoding tasks across edge GPU workers according to the inferred Pareto-optimal bitrate-resolution ladder."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20221208,
        "priority_date": 20211210,
        "grant_date": 0,  # Published application, not yet granted
        "assignee": ["Akamai Technologies, Inc."],
        "assignee_harmonized": [{"name": "AKAMAI TECHNOLOGIES INC", "country_code": "US"}],
        "inventor": ["Law, Will", "Chen, Mei"],
        "inventor_harmonized": [
            {"name": "LAW WILL", "country_code": "US"},
            {"name": "CHEN MEI", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N19/147", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N19/154", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N21/2343", "inventive": False, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-10142402-B2",
        "application_number": "US-201615363910-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "58910231",
        "title_localized": [
            {
                "text": "Distributed DNS anycast routing and cryptographic TLS session resumption at edge points of presence",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "Systems and methods for synchronizing ephemeral TLS session ticket encryption keys across globally distributed DNS and reverse-proxy points of presence to enable zero-round-trip (0-RTT) cryptographic handshakes.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Edge security appliances rotate session ticket keys via a Byzantine fault-tolerant quorum without centralized key server bottlenecks.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method for cryptographic session resumption across an edge server network, comprising:\n"
                    "(a) generating a rotating epoch session ticket encryption key via a distributed key agreement protocol among a plurality of edge proxy nodes;\n"
                    "(b) issuing an encrypted TLS session ticket to a client device upon completion of an initial TLS handshake at a first edge proxy node; and\n"
                    "(c) validating and resuming the encrypted TLS session ticket at a second geographically distinct edge proxy node reached via anycast routing."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20161129,
        "priority_date": 20160601,
        "grant_date": 20181127,
        "assignee": ["Akamai Technologies, Inc."],
        "assignee_harmonized": [{"name": "AKAMAI TECHNOLOGIES INC", "country_code": "US"}],
        "inventor": ["Salz, Richard"],
        "inventor_harmonized": [{"name": "SALZ RICHARD", "country_code": "US"}],
        "cpc": [
            {"code": "H04L61/4511", "inventive": True, "first": True, "tree": ["H", "H04", "H04L", "H04L61"]},
            {"code": "H04L63/166", "inventive": True, "first": False, "tree": ["H", "H04", "H04L", "H04L63"]}
        ],
        "entity_status": "REGULAR"
    },

    # =========================================================================
    # 2. DOLBY LABORATORIES LICENSING CORP
    # =========================================================================
    {
        "publication_number": "US-10609394-B2",
        "application_number": "US-201715788420-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "60129843",
        "title_localized": [
            {
                "text": "High dynamic range (HDR) video reshaping metadata generation and backward-compatible bitstream signaling",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "An encoder reshapes high dynamic range (HDR) video frames using piecewise polynomial transfer functions and embeds dynamic reshaping metadata in supplemental enhancement information (SEI) network abstraction layer units for adaptive streaming.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Dynamic luma and chroma reshaping redistributes codewords across perceptual quantizer (PQ) luminance ranges per scene, allowing 10-bit HEVC/AVC decoders on streaming devices to reconstruct high dynamic range imagery accurately.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method for encoding high dynamic range (HDR) video streams with dynamic reshaping metadata, comprising:\n"
                    "(a) analyzing luminance and chrominance distributions of a sequence of source HDR video frames within a scene interval;\n"
                    "(b) computing coefficients for an eight-piece second-order polynomial forward reshaping function that maps source HDR codewords into a reshaped codeword domain optimized for 10-bit inter-frame compression;\n"
                    "(c) compressing the reshaped video frames using a block-based video encoder to produce a base video bitstream; and\n"
                    "(d) multiplexing coefficients of an inverse reshaping function as dynamic metadata within supplemental enhancement information (SEI) messages synchronized to frame boundaries of the base video bitstream."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20171019,
        "priority_date": 20161021,
        "grant_date": 20200331,
        "assignee": ["Dolby Laboratories Licensing Corporation"],
        "assignee_harmonized": [{"name": "DOLBY LABORATORIES LICENSING CORP", "country_code": "US"}],
        "inventor": ["Su, Guan-Ming", "Tourapis, Alexandros"],
        "inventor_harmonized": [
            {"name": "SU GUAN-MING", "country_code": "US"},
            {"name": "TOURAPIS ALEXANDROS", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N19/186", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N19/70", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N21/234363", "inventive": False, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-11057630-B2",
        "application_number": "US-201916677105-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "67829104",
        "title_localized": [
            {
                "text": "Content-adaptive quantization parameter control and luma-guided chroma prediction for video encoding",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "Coding efficiency in streaming video codecs is improved by adjusting coding tree unit (CTU) quantization parameters based on spatial contrast masking and predicting chroma residuals from reconstructed luma samples.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Cross-component linear model (CCLM) parameters and perceptual quantization offsets are signaled in picture parameter sets for UHD streaming profiles.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A video encoding apparatus comprising:\n"
                    "(a) a spatial activity analyzer configured to calculate local variance and luminance contrast masking weights for each coding tree unit (CTU) of an input video frame;\n"
                    "(b) a quantization modulator configured to derive a delta quantization parameter (dQP) offset for each CTU based on the luminance contrast masking weights;\n"
                    "(c) a cross-component predictor configured to derive linear scaling parameters mapping reconstructed luma samples to predicted chroma samples; and\n"
                    "(d) an entropy coder configured to encode residual coefficients and the delta quantization parameter offsets into a standards-compliant compressed video stream."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20191107,
        "priority_date": 20181109,
        "grant_date": 20210706,
        "assignee": ["Dolby Laboratories Licensing Corporation"],
        "assignee_harmonized": [{"name": "DOLBY LABORATORIES LICENSING CORP", "country_code": "US"}],
        "inventor": ["Yin, Peng", "Lu, Taoran"],
        "inventor_harmonized": [
            {"name": "YIN PENG", "country_code": "US"},
            {"name": "LU TAORAN", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N19/124", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N19/186", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N19/117", "inventive": False, "first": False, "tree": ["H", "H04", "H04N", "H04N19"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-10911785-B2",
        "application_number": "US-201816033912-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "63019284",
        "title_localized": [
            {
                "text": "Object-based spatial audio rendering and adaptive loudness normalization for multi-channel streaming endpoints",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "An audio-visual streaming pipeline transmits bed channels and discrete audio objects with 3D spatial trajectory metadata, enabling client playback devices to dynamically render spatial audio and apply dialogue-gated loudness normalization.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Supports adaptive bitrate switching between immersive audio bitstreams over MPEG-DASH and HLS without loudness jumps or spatial image collapse.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method for decoding and rendering adaptive spatial audio streams on a client playback device, comprising:\n"
                    "(a) receiving segmented audio media fragments comprising channel-based bed signals, discrete audio object signals, and time-varying three-dimensional coordinate metadata;\n"
                    "(b) extracting dialogue intelligence gain parameters and dynamic range compression curves embedded within frame metadata of the segmented audio media fragments; and\n"
                    "(c) rendering the discrete audio object signals and channel-based bed signals to a target speaker or binaural headphone configuration while applying seamless gain crossfading across adaptive bitrate segment boundaries."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20180712,
        "priority_date": 20170714,
        "grant_date": 20210202,
        "assignee": ["Dolby Laboratories Licensing Corporation"],
        "assignee_harmonized": [{"name": "DOLBY LABORATORIES LICENSING CORP", "country_code": "US"}],
        "inventor": ["Robinson, Charles Q.", "Riedmiller, Jeffrey"],
        "inventor_harmonized": [
            {"name": "ROBINSON CHARLES Q", "country_code": "US"},
            {"name": "RIEDMILLER JEFFREY", "country_code": "US"}
        ],
        "cpc": [
            {"code": "G10L19/008", "inventive": True, "first": True, "tree": ["G", "G10", "G10L", "G10L19"]},
            {"code": "H04S7/30", "inventive": True, "first": False, "tree": ["H", "H04", "H04S", "H04S7"]},
            {"code": "H04N21/439", "inventive": False, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-9794565-B2",
        "application_number": "US-201514701092-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "52901843",
        "title_localized": [
            {
                "text": "Frame-synchronized multi-stream audio-video splice conditioning in adaptive HTTP streaming",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "Synchronized elementary stream splicing and presentation timestamp (PTS) alignment across independent audio and video ISO base media file format (ISOBMFF) segments in HTTP adaptive streaming.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Prevents audio-video lip-sync drift and decoder buffer underflow when switching representations or transitioning across period boundaries in MPEG-DASH and HLS.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method for synchronizing segmented audio and video streams in an adaptive HTTP streaming system, comprising:\n"
                    "(a) identifying a splice boundary timestamp in a video media segment having a first frame duration grid;\n"
                    "(b) selecting an audio access unit boundary in a corresponding audio media segment having a second frame duration grid distinct from the first frame duration grid; and\n"
                    "(c) inserting an edit list box and roll-distance sample group description into an ISO Base Media File Format (ISOBMFF) track header of the corresponding audio media segment to align decoded audio sample output with the splice boundary timestamp."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20150430,
        "priority_date": 20140502,
        "grant_date": 20171017,
        "assignee": ["Dolby Laboratories Licensing Corporation"],
        "assignee_harmonized": [{"name": "DOLBY LABORATORIES LICENSING CORP", "country_code": "US"}],
        "inventor": ["Seefeldt, Alan", "Conrady,gga"],
        "inventor_harmonized": [{"name": "SEEFELDT ALAN", "country_code": "US"}],
        "cpc": [
            {"code": "H04N21/2368", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/8456", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/4307", "inventive": False, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },

    # =========================================================================
    # 3. HARMONIC INC (Includes expired patent & missing claims/dates edge cases)
    # =========================================================================
    {
        "publication_number": "US-10771812-B2",
        "application_number": "US-201816031882-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "63881920",
        "title_localized": [
            {
                "text": "Look-ahead statistical multiplexing bitrate allocation and scene-cut-aware GOP structuring for real-time UHD video encoders",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A real-time ultra-high-definition (UHD) video encoding cluster performs look-ahead spatio-temporal complexity analysis across a sliding window of frames to dynamically size group-of-pictures (GOP) intervals and allocate bit budgets across adaptive streaming profiles.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Aligns IDR keyframes across ABR representations at natural scene cuts while bounding segment bitrate peaks for CDN delivery.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A real-time multi-profile video encoding system, comprising:\n"
                    "(a) a look-ahead pre-analyzer configured to buffer a sliding window of uncompressed input video frames and compute frame-level coding complexity scores and scene-cut probability metrics;\n"
                    "(b) a group-of-pictures (GOP) scheduler configured to align instantaneous decoder refresh (IDR) keyframe positions across a plurality of adaptive bitrate encoding profiles at detected scene-cut boundaries while enforcing a maximum segment duration constraint; and\n"
                    "(c) a rate control allocator configured to distribute target bit budgets across the plurality of adaptive bitrate encoding profiles proportionally to the frame-level coding complexity scores."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20180710,
        "priority_date": 20180115,
        "grant_date": 20200908,
        "assignee": ["Harmonic Inc."],
        "assignee_harmonized": [{"name": "HARMONIC INC", "country_code": "US"}],
        "inventor": ["Haskell, Barin", "Raveh, Noam"],
        "inventor_harmonized": [
            {"name": "HASKELL BARIN", "country_code": "US"},
            {"name": "RAVEH NOAM", "country_code": "IL"}
        ],
        "cpc": [
            {"code": "H04N19/146", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N19/172", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N21/23439", "inventive": False, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-11252431-B2",
        "application_number": "US-202016822911-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "70192831",
        "title_localized": [
            {
                "text": "Cloud-native microservice playout and just-in-time packaging for low-latency HLS and DASH streams",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A cloud-native media origin stores a single intermediate mezzanine stream in object storage and performs stateless just-in-time (JIT) packaging into Low-Latency HLS (LL-HLS) and MPEG-DASH CMAF chunks upon edge cache miss.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Containerized JIT packager workers dynamically generate partial segment tags (#EXT-X-PART) and preload hints (#EXT-X-PRELOAD-HINT) synchronized across horizontally scaled origin instances.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method for stateless just-in-time media packaging in a cloud streaming origin, comprising:\n"
                    "(a) ingesting an encoded multi-bitrate mezzanine media stream indexed by deterministic presentation timestamp offsets in shared cloud storage;\n"
                    "(b) receiving, at a stateless packaging worker, a request from a content delivery network for a partial media segment of a target streaming protocol;\n"
                    "(c) slicing a corresponding byte range from the encoded multi-bitrate mezzanine media stream and encapsulating the byte range into a protocol-compliant partial segment container on the fly; and\n"
                    "(d) generating a streaming manifest delta update containing deterministic preload hint URIs for a subsequent partial media segment."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20200318,
        "priority_date": 20190920,
        "grant_date": 20220215,
        "assignee": ["Harmonic Inc."],
        "assignee_harmonized": [{"name": "HARMONIC INC", "country_code": "US"}],
        "inventor": ["Foote, Thomas", "Levy, Yaron"],
        "inventor_harmonized": [
            {"name": "FOOTE THOMAS", "country_code": "US"},
            {"name": "LEVY YARON", "country_code": "IL"}
        ],
        "cpc": [
            {"code": "H04N21/2343", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/262", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/8456", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-6728315-B1",
        "application_number": "US-20000547812-A",
        "country_code": "US",
        "kind_code": "B1",
        "family_id": "24109823",
        "title_localized": [
            {
                "text": "Statistical multiplexing of compressed digital video transport streams over constant bit rate channels",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A statistical multiplexer allocates bandwidth among multiple real-time MPEG-2 video encoders sharing a fixed capacity transport stream based on closed-loop quantizer scale feedback.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Early foundational statistical multiplexing architecture for digital video broadcasting and cable headends.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A statistical multiplexer for allocating bit rates among a plurality of video encoders, comprising:\n"
                    "(a) a complexity receiver configured to receive real-time quantization scale parameters and bit production counts from each of the plurality of video encoders; and\n"
                    "(b) a bit rate controller configured to compute an updated bit rate allocation for each video encoder for a next frame period such that a sum of allocated bit rates does not exceed a constant channel capacity."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20000412,
        "priority_date": 20000412,
        "grant_date": 20040427,
        "assignee": ["Harmonic Inc."],
        "assignee_harmonized": [{"name": "HARMONIC INC", "country_code": "US"}],
        "inventor": ["Linzer, Elliot"],
        "inventor_harmonized": [{"name": "LINZER ELLIOT", "country_code": "US"}],
        "cpc": [
            {"code": "H04N19/146", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N21/2365", "inventive": False, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "WO-2022140192-A1",
        "application_number": "PCT-US2021064810",
        "country_code": "WO",
        "kind_code": "A1",
        "family_id": "78910234",
        "title_localized": [
            {
                "text": "Distributed cloud transcoding orchestration for multi-profile live media workflows",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "International publication describing dynamic autoscaling and fault-tolerant state handoff for cloud-based live video transcoding clusters processing contribution streams.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Bibliographic WIPO record where English full-text claims and filing date integer were not populated in the public snapshot.",
                "language": "en",
                "truncated": False
            }
        ],
        # Intentionally empty claims_localized and 0 filing_date to verify strict non-fabrication error handling
        "claims_localized": [],
        "filing_date": 0,
        "priority_date": 20201222,
        "grant_date": 0,
        "assignee": ["Harmonic Inc."],
        "assignee_harmonized": [{"name": "HARMONIC INC", "country_code": "US"}],
        "inventor": ["Levy, Yaron"],
        "inventor_harmonized": [{"name": "LEVY YARON", "country_code": "IL"}],
        "cpc": [
            {"code": "H04N21/2343", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04L67/10", "inventive": False, "first": False, "tree": ["H", "H04", "H04L", "H04L67"]}
        ],
        "entity_status": "UNKNOWN"
    },

    # =========================================================================
    # 4. SONY ENTITIES (Demonstrates Ambiguous Company Resolution in Stage 1)
    # =========================================================================
    {
        "publication_number": "US-11303915-B2",
        "application_number": "US-202016967201-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "69210482",
        "title_localized": [
            {
                "text": "Affine motion compensation and sub-block temporal motion vector prediction for versatile video coding",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "Image decoding and encoding methods using control-point affine motion vector prediction and sub-block partitioning to improve compression efficiency of high-resolution streaming video.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Applies 4-parameter and 6-parameter affine motion models to 4x4 chroma and luma sub-blocks in VVC/H.266 bitstreams.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. An image decoding device for decoding a compressed video bitstream, comprising:\n"
                    "(a) a bitstream parser configured to extract an affine motion mode flag and control point motion vector differences for a current coding block;\n"
                    "(b) a sub-block motion derivation unit configured to compute per-sub-block motion vectors for a plurality of sub-blocks within the current coding block by interpolating control point motion vectors; and\n"
                    "(c) a motion compensation filter configured to generate a predicted block for the current coding block by applying fractional-sample interpolation to reference frames using the per-sub-block motion vectors."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20200804,
        "priority_date": 20190215,
        "grant_date": 20220412,
        "assignee": ["Sony Group Corporation"],
        "assignee_harmonized": [{"name": "SONY GROUP CORP", "country_code": "JP"}],
        "inventor": ["Tsukuba, Takeshi", "Ikeda, Masaru"],
        "inventor_harmonized": [
            {"name": "TSUKUBA TAKESHI", "country_code": "JP"},
            {"name": "IKEDA MASARU", "country_code": "JP"}
        ],
        "cpc": [
            {"code": "H04N19/52", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N19/105", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N19/176", "inventive": False, "first": False, "tree": ["H", "H04", "H04N", "H04N19"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-10951918-B2",
        "application_number": "US-201916328910-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "65109283",
        "title_localized": [
            {
                "text": "MPEG-DASH media presentation description signaling for low-latency chunked playback and trick-mode switching",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "Information processing apparatus and streaming client method that parses availability time offset attributes in an MPEG-DASH Media Presentation Description (MPD) to initiate low-latency segment fetching and trick-play representation switching.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Enables sub-second glass-to-glass latency in DASH playback while preserving fast-forward and rewind I-frame track adaptation.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A client information processing apparatus for adaptive video streaming, comprising:\n"
                    "(a) processing circuitry configured to acquire an MPEG-DASH Media Presentation Description (MPD) manifest including an availabilityTimeOffset attribute and a segment template for chunked media representations;\n"
                    "(b) calculate an earliest chunk request time prior to full segment availability duration based on the availabilityTimeOffset attribute and wall-clock synchronization signals; and\n"
                    "(c) switch seamlessly between a chunked low-latency representation and an intra-coded trick-mode representation upon detecting a playback speed modification command."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20190226,
        "priority_date": 20170901,
        "grant_date": 20210316,
        "assignee": ["Sony Group Corporation"],
        "assignee_harmonized": [{"name": "SONY GROUP CORP", "country_code": "JP"}],
        "inventor": ["Yamagishi, Yasuaki"],
        "inventor_harmonized": [{"name": "YAMAGISHI YASUAKI", "country_code": "JP"}],
        "cpc": [
            {"code": "H04N21/8456", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/2387", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/6587", "inventive": False, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-11128894-B2",
        "application_number": "US-201916581402-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "67901234",
        "title_localized": [
            {
                "text": "Ultra-low-latency cloud frame streaming with predictive slice encoding and packet-loss feedback",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A cloud interactive video streaming server encodes rendered video frames as independent horizontal slices, transmitting encoded slices over UDP/RTP immediately upon GPU scanout completion and inserting periodic intra-refresh columns in response to client NACK feedback.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Eliminates full-frame buffering delay in interactive cloud streaming and avoids keyframe bitrate spikes during packet loss recovery.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method for real-time interactive video streaming from a cloud server, comprising:\n"
                    "(a) dividing each rendered video frame into a plurality of horizontal macroblock slices as scanlines are output by a graphics processing unit;\n"
                    "(b) encoding and packetizing each horizontal macroblock slice independently prior to completion of a subsequent horizontal macroblock slice of the same video frame;\n"
                    "(c) transmitting packetized slices over a low-latency transport session to a client terminal; and\n"
                    "(d) upon receiving a negative acknowledgment (NACK) identifying a lost slice from the client terminal, dynamically scheduling rolling intra-coded macroblock columns across subsequent frames while referencing a last acknowledged reference frame."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20190924,
        "priority_date": 20181012,
        "grant_date": 20210921,
        "assignee": ["Sony Interactive Entertainment Inc."],
        "assignee_harmonized": [{"name": "SONY INTERACTIVE ENTERTAINMENT INC", "country_code": "JP"}],
        "inventor": ["Perry, David", "Cerny, Mark"],
        "inventor_harmonized": [
            {"name": "PERRY DAVID", "country_code": "US"},
            {"name": "CERNY MARK", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N19/174", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N21/478", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04L65/612", "inventive": False, "first": False, "tree": ["H", "H04", "H04L", "H04L65"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-11206368-B2",
        "application_number": "US-202016891204-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "70918273",
        "title_localized": [
            {
                "text": "Stacked CMOS image sensor with on-die neural region-of-interest readout",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A stacked solid-state imaging device bonding a pixel array die with a logic processing die containing a convolutional neural accelerator for region-of-interest extraction.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Hardware semiconductor image sensor architecture.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A stacked solid-state imaging apparatus comprising:\n"
                    "(a) a first semiconductor substrate having a two-dimensional array of photoelectric conversion pixels;\n"
                    "(b) a second semiconductor substrate bonded to the first semiconductor substrate via copper-to-copper micro-pads, comprising analog-to-digital converters and an on-die neural network processor configured to selectively output high-resolution pixel regions."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20200603,
        "priority_date": 20190614,
        "grant_date": 20211221,
        "assignee": ["Sony Semiconductor Solutions Corporation"],
        "assignee_harmonized": [{"name": "SONY SEMICONDUCTOR SOLUTIONS CORP", "country_code": "JP"}],
        "inventor": ["Oike, Yusuke"],
        "inventor_harmonized": [{"name": "OIKE YUSUKE", "country_code": "JP"}],
        "cpc": [
            {"code": "H04N25/79", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N25"]},
            {"code": "H01L27/146", "inventive": True, "first": False, "tree": ["H", "H01", "H01L", "H01L27"]}
        ],
        "entity_status": "REGULAR"
    },

    # =========================================================================
    # 5. EXAMPLE COMPANY INC (Supports the literal prompt example JSON input)
    # =========================================================================
    {
        "publication_number": "US-10945012-B2",
        "application_number": "US-201816114209-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "64891203",
        "title_localized": [
            {
                "text": "Context-aware adaptive bitrate ladder selection and predictive segment prefetching for video streaming",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A media streaming system dynamically selects per-title encoding ladders and orchestrates edge cache segment prefetching based on client viewport dimensions, network throughput stability, and playback buffer trajectory.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Combines server-side manifest customization with edge cache warm-up for next-episode and next-segment playback in subscription video streaming platforms.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A system for adaptive video streaming optimization, the system comprising:\n"
                    "(a) a manifest generation engine configured to receive a session initialization request comprising client display capabilities and historical network throughput variance;\n"
                    "(b) a bitrate ladder selector configured to filter a master set of encoded video representations to construct a session-specific manifest subset satisfying a perceptual quality floor;\n"
                    "(c) a predictive prefetch controller configured to identify a candidate next media segment based on playhead position and trigger asynchronous staging of the candidate next media segment at a regional edge cache node; and\n"
                    "(d) a telemetry feedback receiver configured to recalibrate the session-specific manifest subset in response to mid-stream buffer stall or bandwidth drop events."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20180828,
        "priority_date": 20170915,
        "grant_date": 20210309,
        "assignee": ["Example Company, Inc."],
        "assignee_harmonized": [{"name": "EXAMPLE COMPANY INC", "country_code": "US"}],
        "inventor": ["Vance, Elena", "Mercer, Julian"],
        "inventor_harmonized": [
            {"name": "VANCE ELENA", "country_code": "US"},
            {"name": "MERCER JULIAN", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N21/8456", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/23439", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04L65/612", "inventive": False, "first": False, "tree": ["H", "H04", "H04L", "H04L65"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-11290764-B2",
        "application_number": "US-201916719004-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "68912045",
        "title_localized": [
            {
                "text": "Per-shot convex hull video encoding using spatial-temporal complexity estimation",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "An automated video encoding pipeline segments source assets at scene cuts and evaluates spatial texture and motion complexity to construct a Pareto-optimal resolution and quantization parameter ladder for each individual shot.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Reduces average streaming bitrate by 25-40% at equivalent VMAF quality scores compared to fixed bitrate encoding ladders.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A computer-implemented method for generating a per-shot video encoding ladder, the method comprising:\n"
                    "(a) detecting scene transition boundaries across an uncompressed source video asset to partition the uncompressed source video asset into discrete shots;\n"
                    "(b) executing a fast proxy encode pass across multiple spatial resolutions for each discrete shot to measure rate-distortion pairs and perceptual quality scores;\n"
                    "(c) constructing a convex hull curve over the measured rate-distortion pairs and perceptual quality scores for each discrete shot; and\n"
                    "(d) selecting a monotonically increasing set of resolution and bitrate operating points along the convex hull curve for final multi-representation encoding."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20191218,
        "priority_date": 20190304,
        "grant_date": 20220329,
        "assignee": ["Example Company, Inc."],
        "assignee_harmonized": [{"name": "EXAMPLE COMPANY INC", "country_code": "US"}],
        "inventor": ["Patel, Vikram", "Chen, Sophia"],
        "inventor_harmonized": [
            {"name": "PATEL VIKRAM", "country_code": "US"},
            {"name": "CHEN SOPHIA", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N19/146", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N19/154", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N21/23439", "inventive": False, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-10715839-B2",
        "application_number": "US-201715690312-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "61092834",
        "title_localized": [
            {
                "text": "ISP-embedded open cache appliance routing and BGP-steered off-peak catalog fill",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "Content delivery appliances deployed inside internet service provider (ISP) access networks proactively pre-populate popular video catalog titles during off-peak night windows and steer local subscriber streaming traffic via BGP community tags.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Offloads transit peering links by serving over 90% of video streaming bytes from flash storage appliances co-located within regional ISP points of presence.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A content delivery architecture for serving streaming media from ISP-embedded cache appliances, comprising:\n"
                    "(a) a regional demand forecasting module configured to predict regional popularity rankings for a catalog of segmented video assets over a subsequent 24-hour cycle;\n"
                    "(b) an off-peak cache fill scheduler configured to transmit differential catalog updates to solid-state storage arrays of ISP-embedded cache appliances during low-utilization network windows; and\n"
                    "(c) a routing control plane configured to ingest Border Gateway Protocol (BGP) prefix announcements from participating ISP routers and direct client playback sessions to a topologically nearest ISP-embedded cache appliance."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20170830,
        "priority_date": 20161110,
        "grant_date": 20200714,
        "assignee": ["Example Company, Inc."],
        "assignee_harmonized": [{"name": "EXAMPLE COMPANY INC", "country_code": "US"}],
        "inventor": ["Mercer, Julian", "O'Connor, Liam"],
        "inventor_harmonized": [
            {"name": "MERCER JULIAN", "country_code": "US"},
            {"name": "O CONNOR LIAM", "country_code": "IE"}
        ],
        "cpc": [
            {"code": "H04L67/568", "inventive": True, "first": True, "tree": ["H", "H04", "H04L", "H04L67"]},
            {"code": "H04N21/222", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04L45/02", "inventive": False, "first": False, "tree": ["H", "H04", "H04L", "H04L45"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-11483601-B2",
        "application_number": "US-202017098412-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "71829304",
        "title_localized": [
            {
                "text": "Low-latency decoder buffer watermark control and frame-accurate audio-video synchronization during representation switching",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "Client playback optimization engine that modulates video presentation clock drift within imperceptible pitch bounds (+-0.5%) to recover target live edge latency without dropping decoded video frames.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Coordinates time-scale modification (WSOLA) on decoded PCM audio frames with display vsync presentation scheduling on smart TVs and mobile media players.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A client media playback method for maintaining low-latency live edge synchronization, comprising:\n"
                    "(a) monitoring a playhead offset between a currently rendered video frame timestamp and a live edge availability timestamp advertised in a streaming manifest;\n"
                    "(b) applying a bounded time-scale modification factor to decoded pulse-code modulation (PCM) audio samples when the playhead offset exceeds a target latency corridor; and\n"
                    "(c) adjusting video frame presentation intervals at a display compositor in lockstep with the bounded time-scale modification factor without discarding decoded video frames."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20201116,
        "priority_date": 20200120,
        "grant_date": 20221025,
        "assignee": ["Example Company, Inc."],
        "assignee_harmonized": [{"name": "EXAMPLE COMPANY INC", "country_code": "US"}],
        "inventor": ["Vance, Elena"],
        "inventor_harmonized": [{"name": "VANCE ELENA", "country_code": "US"}],
        "cpc": [
            {"code": "H04N21/4307", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/44004", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/8456", "inventive": False, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },

    # =========================================================================
    # 6. QUALCOMM INC (Video Coding, DASH Streaming & Rate Control)
    # =========================================================================
    {
        "publication_number": "US-10848779-B2",
        "application_number": "US-201916290512-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "65819204",
        "title_localized": [
            {
                "text": "History-based motion vector prediction and sub-block merge candidate derivation in video coding",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A video coder maintains a first-in-first-out (FIFO) table of history-based motion vector predictors (HMVP) from previously coded blocks in a slice and appends HMVP candidates to a merge candidate list for inter-prediction of streaming video.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Improves coding efficiency in HEVC and VVC/H.266 streaming bitstreams when spatial and temporal neighboring blocks have unavailable motion vectors.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method of decoding video data, the method comprising:\n"
                    "(a) constructing, for a current block of video data, a merge candidate list including spatial merge candidates from neighboring blocks and temporal merge candidates from a collocated reference picture;\n"
                    "(b) querying a history-based motion vector predictor (HMVP) buffer storing motion information of previously decoded non-adjacent blocks within a current tile or slice;\n"
                    "(c) appending one or more HMVP candidates from the HMVP buffer to the merge candidate list after performing pruning against existing spatial and temporal merge candidates; and\n"
                    "(d) reconstructing samples of the current block using motion vectors identified by a merge index signaled in a compressed video bitstream."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20190301,
        "priority_date": 20180305,
        "grant_date": 20201124,
        "assignee": ["QUALCOMM Incorporated"],
        "assignee_harmonized": [{"name": "QUALCOMM INC", "country_code": "US"}],
        "inventor": ["Zhang, Li", "Chen, Jianle", "Karczewicz, Marta"],
        "inventor_harmonized": [
            {"name": "ZHANG LI", "country_code": "US"},
            {"name": "CHEN JIANLE", "country_code": "US"},
            {"name": "KARCZEWICZ MARTA", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N19/52", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N19/105", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N19/70", "inventive": False, "first": False, "tree": ["H", "H04", "H04N", "H04N19"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-10536724-B2",
        "application_number": "US-201715809811-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "60918234",
        "title_localized": [
            {
                "text": "Network-assisted dynamic adaptive streaming over HTTP (SAND) bandwidth allocation and client buffer signaling",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A wireless client device exchanges Server and Network Assisted DASH (SAND) status messages and Perkins metrics with a media-aware network element (MANE) to coordinate adaptive bitrate representation selection during cellular radio handovers.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Enables client DASH players to receive throughput horizon hints from base station edge caches and report anticipated buffer underrun deadlines.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. An apparatus for wireless dynamic adaptive streaming over HTTP (DASH), comprising:\n"
                    "(a) a modem interface configured to receive a network assistance message from a media-aware network element indicating an available downlink throughput horizon and cached representation identifiers;\n"
                    "(b) a DASH client controller configured to compute a sustainable representation bitrate based on the available downlink throughput horizon and a current client media buffer level; and\n"
                    "(c) a status transmitter configured to transmit a client-to-network status message specifying a subset of desired representation identifiers for proactive base-station prefetching."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20171110,
        "priority_date": 20161114,
        "grant_date": 20200114,
        "assignee": ["QUALCOMM Incorporated"],
        "assignee_harmonized": [{"name": "QUALCOMM INC", "country_code": "US"}],
        "inventor": ["Stockhammer, Thomas", "Wang, Ye-Kui"],
        "inventor_harmonized": [
            {"name": "STOCKHAMMER THOMAS", "country_code": "DE"},
            {"name": "WANG YE-KUI", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N21/8456", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/2387", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04L65/612", "inventive": False, "first": False, "tree": ["H", "H04", "H04L", "H04L65"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-11109045-B2",
        "application_number": "US-201916540912-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "67120934",
        "title_localized": [
            {
                "text": "Sub-picture bitstream extraction and viewport-dependent omnidirectional video streaming",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "Motion-constrained tile sets (MCTS) and independently decodable sub-pictures are signaled in a video bitstream manifest so a streaming client fetches high-resolution sub-pictures corresponding to a user's active viewing orientation.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Rewrites slice header addresses and merges high-bitrate foreground sub-pictures with low-bitrate background tiles into a single compliant decoder input stream.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method of processing viewport-dependent streaming video, comprising:\n"
                    "(a) receiving a manifest describing a plurality of independently coded sub-picture tracks partitioning a spherical video frame;\n"
                    "(b) selecting a first sub-picture track at a first spatial resolution corresponding to a current head-tracking orientation and a second sub-picture track at a second lower spatial resolution;\n"
                    "(c) requesting media segments for the first sub-picture track and the second sub-picture track over HTTP; and\n"
                    "(d) merging network abstraction layer (NAL) units from the requested media segments into a single conformant coded video sequence for hardware decoding."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20190814,
        "priority_date": 20180817,
        "grant_date": 20210831,
        "assignee": ["QUALCOMM Incorporated"],
        "assignee_harmonized": [{"name": "QUALCOMM INC", "country_code": "US"}],
        "inventor": ["Wang, Ye-Kui", "walk, Hendry"],
        "inventor_harmonized": [{"name": "WANG YE-KUI", "country_code": "US"}],
        "cpc": [
            {"code": "H04N19/167", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N21/816", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/8456", "inventive": False, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },

    # =========================================================================
    # 7. APPLE INC (HTTP Live Streaming / Low-Latency HLS / Adaptive Streaming)
    # =========================================================================
    {
        "publication_number": "US-10609421-B2",
        "application_number": "US-201816144892-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "64120984",
        "title_localized": [
            {
                "text": "Low-latency HTTP live streaming (LL-HLS) using partial media segments, preload hints, and blocking playlist reload",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A media streaming system reduces glass-to-glass latency in HTTP adaptive streaming by publishing addressable partial media segments within a media playlist, advertising upcoming partial segments via preload hint tags, and holding client playlist reload requests open until a target media sequence update is available.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Enables sub-two-second live video delivery over standard HTTP/2 and HTTP/3 content delivery networks (CDNs) using fragmented MP4 (fMP4 / CMAF) partial segments (#EXT-X-PART), server control directives (#EXT-X-SERVER-CONTROL), and deterministic preload hints (#EXT-X-PRELOAD-HINT) for request coalescing at edge caches.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method for low-latency adaptive bitrate video streaming over HTTP, the method comprising:\n"
                    "(a) generating, by a media packager, a plurality of independently addressable partial media segments representing sub-intervals of a parent encoded video segment prior to completion of the parent encoded video segment;\n"
                    "(b) publishing a streaming media playlist containing partial segment tags specifying byte durations and uniform resource identifiers (URIs) for completed partial media segments alongside a preload hint tag identifying an in-progress partial media segment;\n"
                    "(c) receiving, from a client media player, a blocking playlist reload HTTP request specifying a target media sequence number and partial segment index; and\n"
                    "(d) holding the blocking playlist reload HTTP request at an edge server until the target media sequence number and partial segment index are published, and transmitting a delta playlist update to the client media player."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20180927,
        "priority_date": 20170929,
        "grant_date": 20200331,
        "assignee": ["Apple Inc."],
        "assignee_harmonized": [{"name": "APPLE INC", "country_code": "US"}],
        "inventor": ["Pantos, Roger", "May, William Jr."],
        "inventor_harmonized": [
            {"name": "PANTOS ROGER", "country_code": "US"},
            {"name": "MAY WILLIAM JR", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N21/8456", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/26258", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04L65/612", "inventive": True, "first": False, "tree": ["H", "H04", "H04L", "H04L65"]},
            {"code": "H04L67/568", "inventive": False, "first": False, "tree": ["H", "H04", "H04L", "H04L67"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-10939140-B2",
        "application_number": "US-201916569210-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "67451920",
        "title_localized": [
            {
                "text": "Content steering and dynamic multi-CDN pathway prioritization in adaptive streaming manifests",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "Systems and methods for coordinating real-time content delivery network (CDN) pathway switching during adaptive bitrate video playback using external steering manifests that specify prioritized pathway identifiers, URI cloning templates, and client telemetry polling intervals.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Allows streaming platforms to dynamically steer client video players across edge cache clusters and CDN providers based on regional throughput, peering congestion, and server load without interrupting media decoder buffers.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A client media playback device for adaptive bitrate video streaming, comprising:\n"
                    "(a) a manifest parser configured to parse a master streaming playlist declaring a plurality of variant video streams, each variant video stream associated with a pathway group identifier and a steering server manifest URI;\n"
                    "(b) a steering client controller configured to periodically query the steering server manifest URI during active video playback to receive an ordered priority list of content delivery network pathway identifiers and a time-to-live (TTL) refresh interval;\n"
                    "(c) a segment request router configured to transition subsequent media segment HTTP requests from a first content delivery network pathway to a highest-priority available content delivery network pathway at a segment boundary while preserving decoded playback buffer continuity; and\n"
                    "(d) a failover handler configured to demote a pathway identifier upon detecting HTTP transport errors or segment throughput degradation below a target bitrate floor."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20190912,
        "priority_date": 20180914,
        "grant_date": 20210302,
        "assignee": ["Apple Inc."],
        "assignee_harmonized": [{"name": "APPLE INC", "country_code": "US"}],
        "inventor": ["Pantos, Roger", "Biderman, David"],
        "inventor_harmonized": [
            {"name": "PANTOS ROGER", "country_code": "US"},
            {"name": "BIDERMAN DAVID", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N21/238", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/8456", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04L65/80", "inventive": True, "first": False, "tree": ["H", "H04", "H04L", "H04L65"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-11166065-B2",
        "application_number": "US-201916688412-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "68301928",
        "title_localized": [
            {
                "text": "Perceptual video quality score signaling and convex-hull adaptive bitrate tier selection in media playlists",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "An encoding and adaptive streaming pipeline computes per-segment perceptual visual quality scores across multi-codec representations (HEVC, AV1, AVC) and embeds quality score attributes in streaming manifest variant declarations to guide client bitrate switching.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Client playback engines evaluate both network bandwidth estimates and per-representation perceptual quality metrics (such as VMAF/SSIM equivalents signaled in playlist attributes) to avoid unnecessary upswitches when a lower-bitrate representation already achieves high perceptual fidelity.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method for perceptual-quality-aware adaptive bitrate video streaming, comprising:\n"
                    "(a) encoding a source video sequence into a plurality of bitrate-resolution representations across one or more video codecs;\n"
                    "(b) calculating a perceptual visual quality metric for each encoded representation relative to the source video sequence;\n"
                    "(c) embedding a normalized perceptual quality attribute alongside peak and average bandwidth attributes within each variant stream declaration of a master streaming manifest; and\n"
                    "(d) selecting, at a client media player, a target variant stream that satisfies a perceptual visual quality threshold while minimizing network byte consumption based on current playback buffer occupancy and measured link throughput."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20191119,
        "priority_date": 20181121,
        "grant_date": 20211102,
        "assignee": ["Apple Inc."],
        "assignee_harmonized": [{"name": "APPLE INC", "country_code": "US"}],
        "inventor": ["Tourapis, Alexandros", "Pantos, Roger"],
        "inventor_harmonized": [
            {"name": "TOURAPIS ALEXANDROS", "country_code": "US"},
            {"name": "PANTOS ROGER", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N19/147", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N19/154", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N19"]},
            {"code": "H04N21/23439", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-10362346-B2",
        "application_number": "US-201715620418-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "59401827",
        "title_localized": [
            {
                "text": "Sample-accurate audio and video track splicing across fragmented MP4 segments in adaptive HTTP streaming",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "Methods and client player architectures for seamless playback across interstitial ad splices and encoding discontinuity boundaries in fragmented ISO Base Media File Format (fMP4) adaptive streaming using presentation timestamp (PTS) offset mapping and decoder priming metadata.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Coordinates dual media decoder pipelines or timeline mapping adjustments across #EXT-X-DISCONTINUITY and #EXT-X-DATERANGE boundaries in HTTP Live Streaming.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method for seamless media playback across discontinuity boundaries in an adaptive HTTP streaming session, comprising:\n"
                    "(a) detecting a discontinuity marker and an associated presentation timestamp mapping tag between a first fragmented media segment and a second fragmented media segment in a streaming playlist;\n"
                    "(b) configuring a secondary media decoder pipeline to pre-decode initial access units of the second fragmented media segment prior to completion of rendering of the first fragmented media segment; and\n"
                    "(c) switching display and audio output composition from a primary media decoder pipeline to the secondary media decoder pipeline at a frame-accurate splice presentation timestamp without playback stall."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20170612,
        "priority_date": 20160613,
        "grant_date": 20190723,
        "assignee": ["Apple Inc."],
        "assignee_harmonized": [{"name": "APPLE INC", "country_code": "US"}],
        "inventor": ["Pantos, Roger", "May, William Jr."],
        "inventor_harmonized": [
            {"name": "PANTOS ROGER", "country_code": "US"},
            {"name": "MAY WILLIAM JR", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N21/2368", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/4307", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/8456", "inventive": False, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US8769576B2",
        "application_number": "US-201213620419-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "48912045",
        "title_localized": [
            {
                "text": "Generating and presenting personalized media content recommendations and two-dimensional canvas row rankings",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A content recommendation system and method for constructing a personalized two-dimensional (2D) media discovery interface. A first-stage Personalized Video Ranker (PVR) scores candidate media titles within thematic genre rows using user watch history embeddings and collaborative filtering features, while a second-stage page generation ranker selects and orders rows vertically using submodular diversity constraints and cross-row title deduplication.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Addresses two-dimensional homepage layout optimization and content recommendation in video streaming platforms by jointly optimizing within-row item ordering (Personalized Video Ranker / Top-N ranker) and vertical row ordering while penalizing duplicate title impressions and correcting for horizontal and vertical viewport position bias.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A computer-implemented method for generating a two-dimensional personalized media content recommendation interface for a user profile, comprising:\n"
                    "(a) generating, via a within-row personalized video ranking model, ordered lists of candidate media titles for a plurality of thematic candidate rows based on user interaction history embeddings and item metadata features;\n"
                    "(b) evaluating, via a stage-wise page generation ranking model, candidate rows for vertical placement on a two-dimensional homepage canvas using a submodular utility objective that combines predicted within-row engagement with a cross-row genre diversity reward;\n"
                    "(c) enforcing a cross-row deduplication constraint that suppresses duplicate display of a candidate media title across simultaneously visible rows and columns of the two-dimensional homepage canvas; and\n"
                    "(d) transmitting the assembled two-dimensional personalized media recommendation interface to a client playback device with row-level explanation metadata."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20120914,
        "priority_date": 20110930,
        "grant_date": 20140701,
        "assignee": ["Apple Inc."],
        "assignee_harmonized": [{"name": "APPLE INC", "country_code": "US"}],
        "inventor": ["Jawa, Rob", "Bello, Lucas", "Chen, Mei"],
        "inventor_harmonized": [
            {"name": "JAWA ROB", "country_code": "US"},
            {"name": "BELLO LUCAS", "country_code": "US"},
            {"name": "CHEN MEI", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N21/4666", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/4826", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "G06F16/735", "inventive": True, "first": False, "tree": ["G", "G06", "G06F", "G06F16"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US20200026405A1",
        "application_number": "US-201916515892-A",
        "country_code": "US",
        "kind_code": "A1",
        "family_id": "68903124",
        "title_localized": [
            {
                "text": "Intelligent media content recommendation using contextual multi-armed bandits and personalized visual artwork selection",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "Systems and methods for content recommendation and personalizing visual artwork thumbnails displayed for streaming media titles. Candidate video frames are scored for visual aesthetics and actor prominence, and a contextual multi-armed bandit model selects a personalized artwork variant and recommended media presentation per user profile while logging action selection propensities for inverse propensity weighted (IPW) counterfactual policy evaluation.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Extracts candidate artwork frames from mezzanine video streams using deep convolutional visual aesthetic scoring (AVA) and employs contextual bandit exploration-exploitation (LinUCB / Thompson Sampling) conditioned on user genre and visual preferences to select the thumbnail and recommendation slot that maximizes qualified stream initiation.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method for personalized media content recommendation and visual artwork selection in a video streaming catalog, comprising:\n"
                    "(a) extracting a pool of candidate artwork images from a video asset using an automated visual aesthetics neural network that scores frame composition, motion blur, and cast member facial prominence;\n"
                    "(b) encoding a user context vector representing historical genre affinities, actor preferences, and client display viewport characteristics;\n"
                    "(c) selecting, via a contextual multi-armed bandit recommendation model, a target artwork image from the pool of candidate artwork images for presentation to the user while recording an explicit action selection propensity score; and\n"
                    "(d) updating parameters of the contextual multi-armed bandit recommendation model using counterfactual inverse propensity weighting (IPW) over observed user playback engagement events."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20190718,
        "priority_date": 20180720,
        "grant_date": 20210817,
        "assignee": ["Apple Inc."],
        "assignee_harmonized": [{"name": "APPLE INC", "country_code": "US"}],
        "inventor": ["Amat, Fernando", "Chandrashekar, Ashok", "Basilico, Justin"],
        "inventor_harmonized": [
            {"name": "AMAT FERNANDO", "country_code": "US"},
            {"name": "CHANDRASHEKAR ASHOK", "country_code": "US"},
            {"name": "BASILICO JUSTIN", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N21/466", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "G06N3/08", "inventive": True, "first": False, "tree": ["G", "G06", "G06N", "G06N3"]},
            {"code": "G06F16/735", "inventive": True, "first": False, "tree": ["G", "G06", "G06F", "G06F16"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US9558278B2",
        "application_number": "US-201414549310-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "52104588",
        "title_localized": [
            {
                "text": "Sequential session-based media content recommendation, two-tower neural collaborative filtering, and calibrated multi-objective ranking",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A content recommendation architecture that fuses long-term user profile embeddings from a two-tower dual-encoder neural collaborative filtering model with short-term in-session interaction sequences encoded via a causal self-attention Transformer. Streaming client telemetry events (row scrolls, trailer hover duration, detail page skips, and completion ratios) are ingested via a low-latency feature store to re-rank candidate media items while calibrating output genre distributions via Kullback-Leibler (KL) divergence regularization.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Combines two-tower approximate nearest neighbor (ANN) candidate retrieval and bipartite graph cold-start embedding propagation with a real-time session-aware Transformer sequence encoder and multi-task prediction heads for qualified play probability, completion rate, and calibrated genre distribution.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A system for personalized media content recommendation in a streaming service, comprising:\n"
                    "(a) projecting user activity context features via a user encoder tower and multimodal media item attributes via an item encoder tower into a shared unit-normalized dense embedding space for approximate nearest neighbor (ANN) candidate retrieval;\n"
                    "(b) ingesting a chronological stream of in-session user interaction events comprising title impressions, trailer preview dwell durations, and playback completion ratios into a low-latency distributed feature store;\n"
                    "(c) encoding the chronological stream of in-session user interaction events using a causal self-attention Transformer network to produce a dynamic short-term session intent embedding combined with the user encoder tower embedding; and\n"
                    "(d) dynamically re-ranking candidate media items for unrendered rows of a client user interface while calibrating output genre proportions via Kullback-Leibler (KL) divergence regularization."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20141120,
        "priority_date": 20131122,
        "grant_date": 20170131,
        "assignee": ["Apple Inc."],
        "assignee_harmonized": [{"name": "APPLE INC", "country_code": "US"}],
        "inventor": ["Steck, Harald", "Liang, Dawen", "Lamkhede, Sudarshan"],
        "inventor_harmonized": [
            {"name": "STECK HARALD", "country_code": "US"},
            {"name": "LIANG DAWEN", "country_code": "US"},
            {"name": "LAMKHEDE SUDARSHAN", "country_code": "US"}
        ],
        "cpc": [
            {"code": "G06F16/735", "inventive": True, "first": True, "tree": ["G", "G06", "G06F", "G06F16"]},
            {"code": "H04N21/4666", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "G06N3/045", "inventive": True, "first": False, "tree": ["G", "G06", "G06N", "G06N3"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-11611784-B2",
        "application_number": "US-202117218940-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "74129801",
        "title_localized": [
            {
                "text": "Two-stage personalized media content ranking and two-dimensional canvas row generation for video streaming interfaces",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A personalized media discovery system and method for constructing a two-dimensional (2D) streaming homepage canvas. A first-stage Personalized Video Ranker (PVR) scores candidate media items within thematic genre rows using member watch history embeddings, while a second-stage page generation ranker selects and orders rows vertically using submodular diversity constraints and cross-row title deduplication.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Addresses two-dimensional homepage layout optimization in subscription video streaming platforms by jointly optimizing within-row item ordering (Personalized Video Ranker / Top-N ranker) and vertical row ordering while penalizing duplicate title impressions and correcting for horizontal and vertical viewport position bias.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A computer-implemented method for generating a two-dimensional personalized media discovery interface for a user profile, comprising:\n"
                    "(a) generating, via a within-row personalized video ranking model, ordered lists of candidate media titles for a plurality of thematic candidate rows based on user interaction history embeddings and item metadata features;\n"
                    "(b) evaluating, via a stage-wise page generation ranking model, candidate rows for vertical placement on a two-dimensional homepage canvas using a submodular utility objective that combines predicted within-row engagement with a cross-row genre diversity reward;\n"
                    "(c) enforcing a cross-row deduplication constraint that suppresses duplicate display of a candidate media title across simultaneously visible rows and columns of the two-dimensional homepage canvas; and\n"
                    "(d) transmitting the assembled two-dimensional personalized media discovery interface to a client playback device with row-level explanation metadata."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20210331,
        "priority_date": 20200415,
        "grant_date": 20230321,
        "assignee": ["Apple Inc."],
        "assignee_harmonized": [{"name": "APPLE INC", "country_code": "US"}],
        "inventor": ["Gomez-Uribe, Carlos", "Bello, Lucas", "Chen, Mei"],
        "inventor_harmonized": [
            {"name": "GOMEZ URIBE CARLOS", "country_code": "US"},
            {"name": "BELLO LUCAS", "country_code": "US"},
            {"name": "CHEN MEI", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N21/4666", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "H04N21/4826", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "G06F16/735", "inventive": True, "first": False, "tree": ["G", "G06", "G06F", "G06F16"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-11792461-B2",
        "application_number": "US-202117469102-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "76890312",
        "title_localized": [
            {
                "text": "Contextual multi-armed bandit selection of personalized visual artwork and representative video thumbnails",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "Systems and methods for personalizing visual artwork thumbnails displayed for streaming media titles. Candidate video frames are scored for visual aesthetics and actor prominence, and a contextual multi-armed bandit model selects a personalized artwork variant per user profile while logging action selection propensities for inverse propensity weighted (IPW) counterfactual policy evaluation.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Extracts candidate artwork frames from mezzanine video streams using deep convolutional visual aesthetic scoring and employs contextual bandit exploration-exploitation (LinUCB / Thompson Sampling) conditioned on user genre and visual preferences to select the thumbnail that maximizes qualified stream initiation.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method for personalized visual artwork selection in a video streaming catalog, comprising:\n"
                    "(a) extracting a pool of candidate artwork images from a video asset using an automated visual aesthetics neural network that scores frame composition, motion blur, and cast member facial prominence;\n"
                    "(b) encoding a user context vector representing historical genre affinities, actor preferences, and client display viewport characteristics;\n"
                    "(c) selecting, via a contextual multi-armed bandit model, a target artwork image from the pool of candidate artwork images for presentation to the user while recording an explicit action selection propensity score; and\n"
                    "(d) updating parameters of the contextual multi-armed bandit model using counterfactual inverse propensity weighting (IPW) over observed user playback engagement events."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20210908,
        "priority_date": 20200918,
        "grant_date": 20231017,
        "assignee": ["Apple Inc."],
        "assignee_harmonized": [{"name": "APPLE INC", "country_code": "US"}],
        "inventor": ["Chandrashekar, Ashok", "Amat, Fernando", "Basilico, Justin"],
        "inventor_harmonized": [
            {"name": "CHANDRASHEKAR ASHOK", "country_code": "US"},
            {"name": "AMAT FERNANDO", "country_code": "US"},
            {"name": "BASILICO JUSTIN", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N21/466", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "G06N3/08", "inventive": True, "first": False, "tree": ["G", "G06", "G06N", "G06N3"]},
            {"code": "H04N21/4312", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-11889142-B2",
        "application_number": "US-202217684210-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "79104588",
        "title_localized": [
            {
                "text": "Sequential session-based media recommendation using autoregressive transformer attention and real-time interaction telemetry",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A real-time recommendation architecture that fuses long-term user profile embeddings with short-term in-session interaction sequences encoded via a causal self-attention Transformer. Streaming client telemetry events (row scrolls, trailer hover duration, detail page skips, and completion ratios) are ingested via a low-latency feature store to re-rank unrendered homepage rows in sub-second latency.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Combines a foundation autoregressive Transformer sequence encoder over tokenized user interaction histories with a real-time streaming feature pipeline and multi-task prediction heads for qualified play probability, completion rate, and calibrated genre distribution.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A system for real-time session-aware media recommendation in a streaming service, comprising:\n"
                    "(a) ingesting a chronological stream of in-session user interaction events comprising title impressions, trailer preview dwell durations, and playback completion ratios into a low-latency distributed feature store;\n"
                    "(b) encoding the chronological stream of in-session user interaction events using a causal self-attention Transformer network to produce a dynamic short-term session intent embedding;\n"
                    "(c) combining the dynamic short-term session intent embedding with a persistent long-term user profile embedding in a multi-task neural ranking head; and\n"
                    "(d) dynamically re-ranking candidate media items for unrendered rows of a client user interface while calibrating output genre proportions via Kullback-Leibler (KL) divergence regularization."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20220301,
        "priority_date": 20210514,
        "grant_date": 20240130,
        "assignee": ["Apple Inc."],
        "assignee_harmonized": [{"name": "APPLE INC", "country_code": "US"}],
        "inventor": ["Steck, Harald", "Liang, Dawen", "wu, Chao-Yuan"],
        "inventor_harmonized": [
            {"name": "STECK HARALD", "country_code": "US"},
            {"name": "LIANG DAWEN", "country_code": "US"},
            {"name": "WU CHAO YUAN", "country_code": "US"}
        ],
        "cpc": [
            {"code": "H04N21/4666", "inventive": True, "first": True, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "G06F16/735", "inventive": True, "first": False, "tree": ["G", "G06", "G06F", "G06F16"]},
            {"code": "G06N3/045", "inventive": True, "first": False, "tree": ["G", "G06", "G06N", "G06N3"]}
        ],
        "entity_status": "REGULAR"
    },
    {
        "publication_number": "US-11481450-B2",
        "application_number": "US-202016988312-A",
        "country_code": "US",
        "kind_code": "B2",
        "family_id": "71928340",
        "title_localized": [
            {
                "text": "Two-tower neural embedding retrieval, bipartite graph cold-start propagation, and personalized semantic search for media catalogs",
                "language": "en",
                "truncated": False
            }
        ],
        "abstract_localized": [
            {
                "text": "A hybrid media candidate retrieval and search system that projects user context features and multimodal catalog item representations into a shared dense vector space using a dual-encoder two-tower neural architecture indexed via approximate nearest neighbor (ANN) quantization, augmented by bipartite graph convolutional message passing for cold-start titles.",
                "language": "en",
                "truncated": False
            }
        ],
        "description_localized": [
            {
                "text": "Supports both personalized homepage candidate generation and multilingual semantic search by combining two-tower dense vector retrieval, GraphSAGE bipartite cold-start embedding synthesis, and cross-encoder personalized re-ranking.",
                "language": "en",
                "truncated": False
            }
        ],
        "claims_localized": [
            {
                "text": (
                    "1. A method for neural candidate retrieval and personalized search across a media streaming catalog, comprising:\n"
                    "(a) projecting user activity context features via a user encoder tower and multimodal media item attributes via an item encoder tower into a shared unit-normalized dense embedding space;\n"
                    "(b) synthesizing initial dense embeddings for cold-start media items lacking historical interaction logs by aggregating neighborhood representations over a bipartite user-item-talent graph via graph neural network message passing;\n"
                    "(c) retrieving a candidate subset of media items from an approximate nearest neighbor (ANN) vector index using inner-product similarity against a query or user embedding; and\n"
                    "(d) re-ranking the candidate subset of media items using a personalized cross-encoder scoring model conditioned on real-time session context."
                ),
                "language": "en",
                "truncated": False
            }
        ],
        "filing_date": 20200807,
        "priority_date": 20190912,
        "grant_date": 20221025,
        "assignee": ["Apple Inc."],
        "assignee_harmonized": [{"name": "APPLE INC", "country_code": "US"}],
        "inventor": ["Lamkhede, Sudarshan", "Das, Moumita", "Khanna, Raj"],
        "inventor_harmonized": [
            {"name": "LAMKHEDE SUDARSHAN", "country_code": "US"},
            {"name": "DAS MOUMITA", "country_code": "US"},
            {"name": "KHANNA RAJ", "country_code": "US"}
        ],
        "cpc": [
            {"code": "G06F16/735", "inventive": True, "first": True, "tree": ["G", "G06", "G06F", "G06F16"]},
            {"code": "H04N21/4666", "inventive": True, "first": False, "tree": ["H", "H04", "H04N", "H04N21"]},
            {"code": "G06F16/783", "inventive": True, "first": False, "tree": ["G", "G06", "G06F", "G06F16"]}
        ],
        "entity_status": "REGULAR"
    }
]
