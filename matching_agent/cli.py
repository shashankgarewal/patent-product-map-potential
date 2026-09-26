"""
CLI Entrypoint for the Patent–Target Matching and Commercial Opportunity Agent (`matching_agent`).
Invoked by `server.ts` or directly via command line.
"""

import argparse
import json
import sys

from matching_agent.agent import execute_patent_target_matching_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Patent–Product Intelligence Engine — Patent–Target Matching & Commercial Agent CLI"
    )
    parser.add_argument(
        "--action",
        type=str,
        default="run_matching",
        choices=["run_matching"],
    )
    parser.add_argument(
        "--payload_json",
        type=str,
        default="",
        help="JSON payload containing client_company, target_company, technology_area, client_patents, target_technology_areas",
    )
    args = parser.parse_args()

    payload = {}
    if args.payload_json:
        try:
            payload = json.loads(args.payload_json)
        except Exception as exc:
            print(json.dumps({"matching_status": "INVALID_JSON", "error": str(exc)}))
            sys.exit(0)

    result = execute_patent_target_matching_pipeline(
        client_company=payload.get("client_company", "Apple"),
        target_company=payload.get("target_company", "Netflix"),
        technology_area=payload.get("technology_area", "video streaming"),
        client_patents=payload.get("client_patents"),
        target_technology_areas=payload.get("target_technology_areas"),
        max_candidates=int(payload.get("max_candidates", 6)),
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
