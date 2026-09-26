"""
Command-Line Interface for the Offline Target Company Knowledge Prefetch Pipeline (`target_prefetch/cli.py`).

Supports:
- Initial ingestion mode:
    python3 -m target_prefetch.cli --mode initial
- Incremental ingestion mode:
    python3 -m target_prefetch.cli --mode incremental
- Status & search inspection:
    python3 -m target_prefetch.cli --action status --company Netflix --query "open connect"
- Custom source ingestion / quarantine test:
    python3 -m target_prefetch.cli --action ingest_custom --custom_doc_json '{...}'
"""

import argparse
import json
import sys

from target_prefetch.pipeline import (
    run_prefetch_pipeline,
    get_target_knowledge_status,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline Target Company Knowledge Prefetch Pipeline CLI (Netflix)"
    )
    parser.add_argument(
        "--action",
        type=str,
        default="run_prefetch",
        choices=["run_prefetch", "status", "ingest_custom"],
        help="Action to perform: 'run_prefetch' (default), 'status', or 'ingest_custom'",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="initial",
        choices=["initial", "incremental"],
        help="Ingestion mode: 'initial' (rebuild & seed) or 'incremental' (deduplicate against existing URL & SHA-256 hash)",
    )
    parser.add_argument("--company", type=str, default="Netflix")
    parser.add_argument("--query", type=str, default="")
    parser.add_argument("--tag", type=str, default="")
    parser.add_argument("--source_type", type=str, default="")
    parser.add_argument(
        "--custom_doc_json",
        type=str,
        default="",
        help="JSON string for testing custom source ingestion or allowlist quarantine logging",
    )

    args = parser.parse_args()

    if args.action == "status":
        result = get_target_knowledge_status(
            company=args.company,
            query=args.query,
            tag=args.tag,
            source_type=args.source_type,
        )
        print(json.dumps(result))
        return

    if args.action == "ingest_custom":
        if not args.custom_doc_json:
            print(json.dumps({"status": "ERROR", "error": "Missing --custom_doc_json"}))
            sys.exit(1)
        custom_doc = json.loads(args.custom_doc_json)
        result = run_prefetch_pipeline(
            mode="incremental",
            custom_documents=[custom_doc],
        )
        print(json.dumps(result))
        return

    # Default action: run_prefetch with --mode initial or --mode incremental
    result = run_prefetch_pipeline(mode=args.mode)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
