"""
Database Connection and 2-Tier Relational Schema Initialization (`target_prefetch/db.py`).

Implements the exact relational parent-child schema in SQLite (`target_knowledge.sqlite`):
1. Parent Table: `documents`
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
   - `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

2. Child Table: `document_chunks`
   - `chunk_id`: TEXT PRIMARY KEY (Format: `{document_id}_chunk_{index}`)
   - `document_id`: TEXT REFERENCES documents(document_id)
   - `chunk_index`: INTEGER NOT NULL
   - `content`: TEXT NOT NULL (Granular text chunk for vector search)
   - `embedding`: BLOB/JSON (Dense vector embedding)
   - `candidate_tags`: TEXT (JSON array of candidate technology tags)

3. Quarantine / Failure Log Table: `failed_documents`
   - `source_url`: TEXT PRIMARY KEY
   - `title`: TEXT
   - `error_code`: TEXT
   - `error_message`: TEXT
   - `logged_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

4. Audit Table: `ingestion_runs`
   - Tracks initial and incremental ingestion executions and deduplication metrics.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "target_knowledge.sqlite")


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Opens a SQLite connection with foreign key enforcement enabled and Row factory configured.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_target_knowledge_db(db_path: str = DB_PATH, reset: bool = False) -> None:
    """
    Initializes the 2-tier relational schema (`documents`, `document_chunks`, `failed_documents`,
    and `ingestion_runs`). If `reset=True` or if legacy single-tier tables are detected without
    `full_content`, recreates the relational tables cleanly.
    """
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()

        # Check if an older schema version exists where `documents` lacks `full_content`
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents';")
        has_documents_table = cur.fetchone() is not None
        needs_migration = False
        if has_documents_table:
            cur.execute("PRAGMA table_info(documents);")
            cols = {row["name"] for row in cur.fetchall()}
            if "full_content" not in cols:
                needs_migration = True

        if reset or needs_migration:
            cur.execute("DROP TABLE IF EXISTS document_chunks;")
            cur.execute("DROP TABLE IF EXISTS documents;")
            cur.execute("DROP TABLE IF EXISTS failed_documents;")
            cur.execute("DROP TABLE IF EXISTS target_chunks;")
            cur.execute("DROP TABLE IF EXISTS target_documents;")
            if reset:
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
