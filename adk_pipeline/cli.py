"""
CLI entrypoint for the Python Google ADK Client Patent Analysis Pipeline.
Invoked by the backend server (`server.ts`) or directly via command line.
"""

import argparse
import json
import sys

from adk_pipeline.schema_inspector import inspect_bigquery_publications_schema
from adk_pipeline.agent import execute_deterministic_adk_stages


def main() -> None:
    parser = argparse.ArgumentParser(description="Patent-Product Intelligence Engine — Client Patent ADK CLI")
    parser.add_argument("--action", type=str, default="run_pipeline", choices=["inspect_schema", "run_pipeline"])
    parser.add_argument("--client_company", type=str, default="")
    parser.add_argument("--technology_area", type=str, default="")
    parser.add_argument("--max_candidates", type=int, default=6)
    parser.add_argument("--live_check", action="store_true", help="Attempt live BigQuery metadata check")

    args = parser.parse_args()

    if args.action == "inspect_schema":
        res = inspect_bigquery_publications_schema(attempt_live_check=args.live_check)
        print(json.dumps(res))
        return

    res = execute_deterministic_adk_stages(
        client_company=args.client_company,
        technology_area=args.technology_area if args.technology_area else None,
        max_candidates=args.max_candidates
    )
    print(json.dumps(res))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({
            "pipeline_status": "PIPELINE_ERROR",
            "error": str(exc)
        }))
        sys.exit(0)
