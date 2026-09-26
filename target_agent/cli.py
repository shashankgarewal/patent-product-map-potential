"""
CLI Entrypoint for the Google ADK Target Retrieval & Analysis Agent.
Reads strictly from the pre-fetched `target_knowledge.sqlite` database.
"""

import argparse
import json
import sys

from target_agent.agent import execute_target_retrieval_pipeline
from target_agent.tools import search_target_knowledge


def main() -> None:
    parser = argparse.ArgumentParser(description="Target Retrieval Agent ADK CLI")
    parser.add_argument(
        "--action",
        type=str,
        default="run_agent",
        choices=["run_agent", "search_tool"],
    )
    parser.add_argument("--payload_json", type=str, default="")
    parser.add_argument("--target_company", type=str, default="Netflix")
    parser.add_argument("--query", type=str, default="")
    parser.add_argument("--technology_area", type=str, default="video streaming")
    parser.add_argument("--top_k", type=int, default=5)

    args = parser.parse_args()

    if args.action == "search_tool":
        res = search_target_knowledge(
            target_company=args.target_company,
            query=args.query,
            technology_area=args.technology_area,
            top_k=args.top_k,
        )
        print(json.dumps(res))
        return

    if args.payload_json:
        payload = json.loads(args.payload_json)
        target_company = payload.get("target_company", "Netflix")
        technology_area = payload.get("technology_area", "")
        client_patent_context = payload.get("client_patent_context", [])
        top_k = int(payload.get("top_k", 4))
    else:
        target_company = args.target_company
        technology_area = args.technology_area
        client_patent_context = []
        top_k = args.top_k

    res = execute_target_retrieval_pipeline(
        target_company=target_company,
        technology_area=technology_area,
        client_patent_context=client_patent_context,
        top_k_per_query=top_k,
    )
    print(json.dumps(res))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            json.dumps({
                "evidence_status": "insufficient",
                "error": str(exc),
            })
        )
        sys.exit(0)
