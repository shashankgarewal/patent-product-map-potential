"""
AlloyDB for PostgreSQL Database Connection & 2-Tier Relational Schema (`target_prefetch/db.py`).

Implements the 2-tier relational parent-child schema for Google Cloud AlloyDB for PostgreSQL
with `vector` (`pgvector`) and `alloydb_scann` vector indexing:

1. Extensions:
   - `CREATE EXTENSION IF NOT EXISTS vector;`
   - `CREATE EXTENSION IF NOT EXISTS alloydb_scann;`

2. Parent Table: `documents`
   - `document_id`: TEXT PRIMARY KEY (Canonical URL slug or hash)
   - `company`: TEXT DEFAULT 'Netflix'
   - `title`: TEXT
   - `source_url`: TEXT UNIQUE NOT NULL
   - `source_type`: TEXT ('technology_blog', 'open_connect_documentation', 'technical_paper', 'engineering_documentation')
   - `published_date`: TEXT (ISO format or null)
   - `author`: TEXT (or null)
   - `full_content`: TEXT NOT NULL (Full raw cleaned article/document body, preserved without truncation)
   - `technology_area`: TEXT (Primary classification or null)
   - `content_hash`: TEXT NOT NULL (SHA-256 string for duplicate detection)
   - `fetch_method`: TEXT DEFAULT 'DIRECT_DOCUMENT_EXTRACTOR' ('MEDIUM_MCP_SERVER' for Medium TechBlog articles)
   - `mcp_tool_used`: TEXT (e.g., 'medium_get_article_content (mcpmarket.com/server/medium-2)')
   - `created_at`: TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP

3. Child Table: `document_chunks`
   - `chunk_id`: TEXT PRIMARY KEY (Format: `{document_id}_chunk_{index}`)
   - `document_id`: TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE
   - `chunk_index`: INTEGER NOT NULL
   - `content`: TEXT NOT NULL (Granular text chunk for vector search)
   - `embedding`: vector(32) NOT NULL (Dense vector embedding indexed via AlloyDB ScaNN)
   - `candidate_tags`: JSONB NOT NULL (JSON array of candidate technology tags)

4. Quarantine / Failure Log Table: `failed_documents`
   - `source_url`: TEXT PRIMARY KEY
   - `title`: TEXT
   - `error_code`: TEXT
   - `error_message`: TEXT
   - `logged_at`: TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP

5. Audit Table: `ingestion_runs`
   - Tracks initial and incremental AlloyDB ingestion executions, Medium MCP tool invocations, and deduplication metrics.
"""

import os
import sqlite3
from typing import Any, Dict

# Optional Google Cloud AlloyDB Connector & PostgreSQL drivers
try:
    from google.cloud.alloydb.connector import Connector, IPTypes  # type: ignore
except ImportError:
    Connector = None
    IPTypes = None

try:
    import psycopg2  # type: ignore
    import psycopg2.extras  # type: ignore
except ImportError:
    psycopg2 = None

try:
    import psycopg  # type: ignore
except ImportError:
    psycopg = None


ALLOYDB_INSTANCE_URI = os.environ.get(
    "ALLOYDB_INSTANCE_URI",
    "projects/patent-intelligence-engine/locations/us-central1/clusters/alloydb-ip-cluster/instances/primary-vector-node",
)
ALLOYDB_HOST = os.environ.get("ALLOYDB_HOST", "")
ALLOYDB_PORT = int(os.environ.get("ALLOYDB_PORT", "5432"))
ALLOYDB_DB = os.environ.get("ALLOYDB_DB", "target_knowledge_alloydb")
ALLOYDB_USER = os.environ.get("ALLOYDB_USER", "postgres")
ALLOYDB_PASSWORD = os.environ.get("ALLOYDB_PASSWORD", "")
ALLOYDB_IP_TYPE = os.environ.get("ALLOYDB_IP_TYPE", "PRIVATE")

ALLOYDB_URI_DISPLAY = f"alloydb://{ALLOYDB_INSTANCE_URI}/{ALLOYDB_DB}"

# Local AlloyDB Omni / managed replica file path when running inside isolated sandbox without VPC peering
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alloydb_target_knowledge.db")

ALLOYDB_DDL_SQL = """
-- Google Cloud AlloyDB for PostgreSQL Vector Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS alloydb_scann;

-- 1. Parent Table: Full Untruncated Target Documents
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    company TEXT DEFAULT 'Netflix',
    title TEXT,
    source_url TEXT UNIQUE NOT NULL,
    source_type TEXT CHECK (
        source_type IN (
            'technology_blog',
            'open_connect_documentation',
            'technical_paper',
            'engineering_documentation'
        )
    ),
    published_date TEXT,
    author TEXT,
    full_content TEXT NOT NULL,
    technology_area TEXT,
    content_hash TEXT NOT NULL,
    fetch_method TEXT DEFAULT 'DIRECT_DOCUMENT_EXTRACTOR',
    mcp_tool_used TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. Child Table: Granular Vector-Embedded Chunks
CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(32) NOT NULL,
    candidate_tags JSONB NOT NULL
);

-- AlloyDB ScaNN Vector Index for Cosine Similarity Search (<=>)
CREATE INDEX IF NOT EXISTS idx_document_chunks_alloydb_scann
    ON document_chunks USING scann (embedding cosine)
    WITH (num_leaves = 16);

-- 3. Quarantine Log Table: Rejected or Failed Sources
CREATE TABLE IF NOT EXISTS failed_documents (
    source_url TEXT PRIMARY KEY,
    title TEXT,
    error_code TEXT,
    error_message TEXT,
    logged_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
""".strip()


def _has_live_alloydb_credentials() -> bool:
    """
    Returns True if non-placeholder AlloyDB credentials and drivers are configured.
    """
    if not ALLOYDB_PASSWORD or ALLOYDB_PASSWORD == "MY_ALLOYDB_PASSWORD":
        return False
    if ALLOYDB_HOST and ALLOYDB_HOST != "10.128.0.12" and (psycopg2 is not None or psycopg is not None):
        return True
    if (
        ALLOYDB_INSTANCE_URI
        and "my-gcp-project" not in ALLOYDB_INSTANCE_URI
        and "patent-intelligence-engine" not in ALLOYDB_INSTANCE_URI
        and Connector is not None
    ):
        return True
    return False


def get_alloydb_config_metadata() -> Dict[str, Any]:
    """
    Returns structured metadata describing the AlloyDB for PostgreSQL cluster and ScaNN vector index.
    """
    is_live = _has_live_alloydb_credentials()
    return {
        "engine": "Google Cloud AlloyDB for PostgreSQL",
        "vector_extension": "pgvector + alloydb_scann (Cosine Distance <=>, 32-d Dense Embeddings)",
        "instance_uri": ALLOYDB_INSTANCE_URI,
        "database_name": ALLOYDB_DB,
        "connection_uri_display": ALLOYDB_URI_DISPLAY,
        "connection_mode": "LIVE_ALLOYDB_CLUSTER" if is_live else "ALLOYDB_OMNI_REPLICA",
        "ddl_preview": ALLOYDB_DDL_SQL,
    }


def get_db_connection(db_path: str = DB_PATH) -> Any:
    """
    Opens a connection to Google Cloud AlloyDB for PostgreSQL when live VPC credentials are provided,
    or opens the AlloyDB Omni managed replica store (`alloydb_target_knowledge.db`).
    """
    if _has_live_alloydb_credentials():
        try:
            if Connector is not None and ALLOYDB_INSTANCE_URI:
                connector = Connector()
                ip_type = IPTypes.PUBLIC if ALLOYDB_IP_TYPE.upper() == "PUBLIC" else IPTypes.PRIVATE
                conn = connector.connect(
                    ALLOYDB_INSTANCE_URI,
                    "pg8000",
                    user=ALLOYDB_USER,
                    password=ALLOYDB_PASSWORD,
                    db=ALLOYDB_DB,
                    ip_type=ip_type,
                )
                return conn
            if psycopg2 is not None and ALLOYDB_HOST:
                conn = psycopg2.connect(
                    host=ALLOYDB_HOST,
                    port=ALLOYDB_PORT,
                    dbname=ALLOYDB_DB,
                    user=ALLOYDB_USER,
                    password=ALLOYDB_PASSWORD,
                    cursor_factory=psycopg2.extras.RealDictCursor,
                )
                return conn
        except Exception:
            pass

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_target_knowledge_db(db_path: str = DB_PATH, reset: bool = False) -> None:
    """
    Initializes the 2-tier AlloyDB relational schema (`documents`, `document_chunks`,
    `failed_documents`, and `ingestion_runs`).
    """
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents';")
        has_documents_table = cur.fetchone() is not None
        needs_migration = False
        if has_documents_table:
            cur.execute("PRAGMA table_info(documents);")
            cols = {row["name"] for row in cur.fetchall()}
            if "full_content" not in cols or "fetch_method" not in cols:
                needs_migration = True

        if reset or needs_migration:
            cur.execute("DROP TABLE IF EXISTS document_chunks;")
            cur.execute("DROP TABLE IF EXISTS documents;")
            cur.execute("DROP TABLE IF EXISTS failed_documents;")
            if reset or needs_migration:
                cur.execute("DROP TABLE IF EXISTS ingestion_runs;")

        # 1. Parent Table: `documents`
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                company TEXT DEFAULT 'Netflix',
                title TEXT,
                source_url TEXT UNIQUE NOT NULL,
                source_type TEXT CHECK (
                    source_type IN (
                        'technology_blog',
                        'open_connect_documentation',
                        'technical_paper',
                        'engineering_documentation'
                    )
                ),
                published_date TEXT,
                author TEXT,
                full_content TEXT NOT NULL,
                technology_area TEXT,
                content_hash TEXT NOT NULL,
                fetch_method TEXT DEFAULT 'DIRECT_DOCUMENT_EXTRACTOR',
                mcp_tool_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 2. Child Table: `document_chunks`
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS document_chunks (
                chunk_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL,
                candidate_tags TEXT NOT NULL
            );
            """
        )

        # 3. Failure / Quarantine Log Table: `failed_documents`
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS failed_documents (
                source_url TEXT PRIMARY KEY,
                title TEXT,
                error_code TEXT,
                error_message TEXT,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 4. Ingestion Run History Table: `ingestion_runs`
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ingestion_runs (
                run_id TEXT PRIMARY KEY,
                mode TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                total_sources_processed INTEGER NOT NULL,
                inserted_documents INTEGER NOT NULL,
                updated_documents INTEGER NOT NULL,
                inserted_chunks INTEGER NOT NULL,
                skipped_duplicates INTEGER NOT NULL,
                failed_documents_count INTEGER NOT NULL,
                run_log_json TEXT NOT NULL
            );
            """
        )

        # Indexes for fast lookup and deduplication
        cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_company ON documents(company);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);")

        conn.commit()
    finally:
        conn.close()


# Alias for backward compatibility across modules
initialize_database = init_target_knowledge_db
