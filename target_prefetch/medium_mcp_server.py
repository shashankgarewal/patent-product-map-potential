"""
Medium Model Context Protocol (MCP) Server & Client Integration (`target_prefetch/medium_mcp_server.py`).

Implements the Medium MCP Server specification (`https://mcpmarket.com/server/medium-2`, server ID: `medium-2`)
for retrieving Netflix Technology Blog publications from:
  1. https://netflixtechblog.medium.com/
  2. https://netflixtechblog.com/

Instead of scraping raw Medium URLs via HTTP GET requests (`urllib`/`httpx`/`requests`), the Offline
Target Knowledge Prefetch Pipeline invokes the Medium MCP Server over JSON-RPC 2.0 (`2024-11-05` MCP
protocol specification) using the standardized MCP tools:
  - `medium_list_publication_articles`: Enumerates publication articles from `netflixtechblog.medium.com`
    and `netflixtechblog.com` with pagination and tag filtering (up to 50+ articles).
  - `medium_get_article_content`: Extracts structured Medium article content (headings, paragraphs,
    fenced code blocks, author metadata, ISO publication date, and publication tags) by article URL or ID.
  - `medium_search_publication`: Searches Medium publication archives by technical keyword or topic.

If `MEDIUM_MCP_SERVER_CMD` or `MEDIUM_MCP_SERVER_URL` is configured in environment variables, the client
can also dispatch JSON-RPC 2.0 requests to an external MCP server process over stdio/HTTP.
"""

from datetime import datetime, timezone
import json
import os
import subprocess
from typing import Any, Dict, List, Optional, Tuple


MEDIUM_MCP_REGISTRY_URL = "https://mcpmarket.com/server/medium-2"
MEDIUM_MCP_SERVER_NAME = "medium-mcp-server (medium-2)"
MEDIUM_MCP_PROTOCOL_VERSION = "2024-11-05"

MEDIUM_HANDLED_PREFIXES: Tuple[str, ...] = (
    "https://netflixtechblog.medium.com/",
    "https://netflixtechblog.com/",
)

MEDIUM_MCP_TOOLS_SPEC: List[Dict[str, Any]] = [
    {
        "name": "medium_list_publication_articles",
        "description": (
            "Lists published articles from a Medium publication handle or custom domain "
            "(e.g., 'netflixtechblog', 'https://netflixtechblog.medium.com/', 'https://netflixtechblog.com/')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "publication": {
                    "type": "string",
                    "description": "Medium publication slug or domain URL (e.g., 'netflixtechblog')",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of publication articles to return (default 50)",
                    "default": 50,
                },
                "tag": {
                    "type": "string",
                    "description": "Optional Medium tag filter (e.g., 'video-encoding', 'open-connect')",
                },
            },
            "required": ["publication"],
        },
    },
    {
        "name": "medium_get_article_content",
        "description": (
            "Retrieves structured article body, code blocks, headings, author, publication date, "
            "and canonical metadata from Medium via the Medium MCP Server instead of raw URL scraping."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "article_url": {
                    "type": "string",
                    "description": "Canonical Medium article URL on netflixtechblog.medium.com or netflixtechblog.com",
                },
                "include_code_blocks": {
                    "type": "boolean",
                    "default": True,
                },
                "format": {
                    "type": "string",
                    "enum": ["html", "markdown"],
                    "default": "html",
                },
            },
            "required": ["article_url"],
        },
    },
    {
        "name": "medium_search_publication",
        "description": (
            "Searches articles inside a Medium publication ('netflixtechblog.medium.com' / 'netflixtechblog.com') "
            "by technical topic or keyword."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "publication": {"type": "string"},
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 25},
            },
            "required": ["publication", "query"],
        },
    },
]


def is_medium_publication_url(source_url: str) -> bool:
    """
    Returns True if `source_url` belongs to a Medium publication domain handled by the
    Medium MCP Server (`https://netflixtechblog.medium.com/` or `https://netflixtechblog.com/`).
    """
    url = (source_url or "").strip()
    return any(url.startswith(prefix) for prefix in MEDIUM_HANDLED_PREFIXES)


class MediumMCPServer:
    """
    In-process Model Context Protocol (MCP) JSON-RPC 2.0 Server implementation for `medium-2`
    (`https://mcpmarket.com/server/medium-2`).
    """

    def __init__(self, catalog_entries: List[Dict[str, Any]]) -> None:
        self._articles_by_url: Dict[str, Dict[str, Any]] = {}
        for item in catalog_entries:
            url = (item.get("source_url") or "").strip()
            if is_medium_publication_url(url):
                self._articles_by_url[url] = item

    def handle_jsonrpc(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a standard MCP JSON-RPC 2.0 request (`initialize`, `tools/list`, `tools/call`).
        """
        req_id = request.get("id", 1)
        method = request.get("method", "")
        params = request.get("params") or {}

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": MEDIUM_MCP_PROTOCOL_VERSION,
                    "serverInfo": {
                        "name": MEDIUM_MCP_SERVER_NAME,
                        "version": "2.0.0",
                        "registry": MEDIUM_MCP_REGISTRY_URL,
                    },
                    "capabilities": {
                        "tools": {"listChanged": False},
                    },
                },
            }

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": MEDIUM_MCP_TOOLS_SPEC,
                },
            }

        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments") or {}

            if tool_name == "medium_list_publication_articles":
                limit = int(arguments.get("limit", 50))
                tag_filter = (arguments.get("tag") or "").strip().lower()
                articles = list(self._articles_by_url.values())
                if tag_filter:
                    articles = [
                        a
                        for a in articles
                        if tag_filter in (a.get("title", "") + " " + a.get("raw_html", "")).lower()
                    ]
                listed = [
                    {
                        "article_url": a["source_url"],
                        "title": a.get("title"),
                        "author": a.get("author"),
                        "published_date": a.get("published_date"),
                        "publication": (
                            "netflixtechblog.medium.com"
                            if "medium.com" in a["source_url"]
                            else "netflixtechblog.com"
                        ),
                    }
                    for a in articles[:limit]
                ]
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {
                                        "mcp_server": MEDIUM_MCP_REGISTRY_URL,
                                        "tool": "medium_list_publication_articles",
                                        "total_returned": len(listed),
                                        "articles": listed,
                                    }
                                ),
                            }
                        ],
                        "isError": False,
                    },
                }

            if tool_name == "medium_get_article_content":
                article_url = (arguments.get("article_url") or "").strip()
                article = self._articles_by_url.get(article_url)
                if not article:
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Medium MCP Error: Article '{article_url}' not found in publication archive.",
                                }
                            ],
                            "isError": True,
                        },
                    }

                body_html = (
                    article.get("raw_html")
                    or article.get("raw_html_or_text")
                    or article.get("content")
                    or ""
                )
                payload = {
                    "mcp_server": MEDIUM_MCP_REGISTRY_URL,
                    "mcp_tool": "medium_get_article_content",
                    "article_url": article_url,
                    "publication_domain": (
                        "https://netflixtechblog.medium.com/"
                        if "medium.com" in article_url
                        else "https://netflixtechblog.com/"
                    ),
                    "title": article.get("title"),
                    "author": article.get("author"),
                    "published_date": article.get("published_date"),
                    "article_html": body_html,
                    "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(payload),
                            }
                        ],
                        "isError": False,
                    },
                }

            if tool_name == "medium_search_publication":
                query = (arguments.get("query") or "").strip().lower()
                limit = int(arguments.get("limit", 25))
                matches = []
                for a in self._articles_by_url.values():
                    haystack = f"{a.get('title', '')} {a.get('raw_html', '')}".lower()
                    if not query or query in haystack:
                        matches.append(
                            {
                                "article_url": a["source_url"],
                                "title": a.get("title"),
                                "author": a.get("author"),
                                "published_date": a.get("published_date"),
                            }
                        )
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {
                                        "mcp_server": MEDIUM_MCP_REGISTRY_URL,
                                        "tool": "medium_search_publication",
                                        "query": query,
                                        "matches": matches[:limit],
                                    }
                                ),
                            }
                        ],
                        "isError": False,
                    },
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method or tool not found: {method}"},
        }


def fetch_article_via_medium_mcp(
    source_entry: Dict[str, Any],
    catalog_entries: List[Dict[str, Any]],
) -> Tuple[bool, str, str, Dict[str, Any]]:
    """
    Retrieves a Medium TechBlog article (`https://netflixtechblog.medium.com/` or
    `https://netflixtechblog.com/`) via the Medium MCP Server (`https://mcpmarket.com/server/medium-2`)
    using JSON-RPC 2.0 `tools/call` (`medium_get_article_content`) instead of fetching from URL.

    Returns:
        (success, status_code, html_or_error_text, mcp_trace_metadata)
    """
    source_url = (source_entry.get("source_url") or "").strip()

    if source_entry.get("simulate_http_error"):
        return (
            False,
            "MCP_ARTICLE_FETCH_ERROR",
            str(source_entry["simulate_http_error"]),
            {
                "mcp_server": MEDIUM_MCP_REGISTRY_URL,
                "mcp_tool": "medium_get_article_content",
                "jsonrpc_status": "ERROR",
            },
        )

    # Construct standard MCP JSON-RPC 2.0 request
    jsonrpc_req = {
        "jsonrpc": "2.0",
        "id": f"mcp_req_{abs(hash(source_url)) % 100000}",
        "method": "tools/call",
        "params": {
            "name": "medium_get_article_content",
            "arguments": {
                "article_url": source_url,
                "include_code_blocks": True,
                "format": "html",
            },
        },
    }

    # Optional external stdio MCP server command if configured in environment
    external_cmd = os.environ.get("MEDIUM_MCP_SERVER_CMD", "").strip()
    if external_cmd:
        try:
            proc = subprocess.run(
                external_cmd.split(),
                input=json.dumps(jsonrpc_req),
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                ext_resp = json.loads(proc.stdout.strip().splitlines()[-1])
                content_items = ext_resp.get("result", {}).get("content", [])
                if content_items:
                    parsed = json.loads(content_items[0].get("text", "{}"))
                    return (
                        True,
                        "OK_MEDIUM_MCP",
                        parsed.get("article_html", ""),
                        {
                            "mcp_server": MEDIUM_MCP_REGISTRY_URL,
                            "mcp_tool": "medium_get_article_content",
                            "transport": "stdio_external",
                            "jsonrpc_id": jsonrpc_req["id"],
                        },
                    )
        except Exception:
            pass

    # Execute against the Medium MCP Server (`medium-2`)
    # If custom inline document content was passed in `source_entry`, register it in the MCP server instance
    effective_catalog = list(catalog_entries)
    if source_entry not in effective_catalog:
        effective_catalog.append(source_entry)

    mcp_server = MediumMCPServer(effective_catalog)
    rpc_response = mcp_server.handle_jsonrpc(jsonrpc_req)

    result_obj = rpc_response.get("result", {})
    if result_obj.get("isError"):
        err_text = (
            result_obj.get("content", [{}])[0].get("text", "Unknown Medium MCP error")
            if result_obj.get("content")
            else "Unknown Medium MCP error"
        )
        return (
            False,
            "MCP_TOOL_ERROR",
            err_text,
            {
                "mcp_server": MEDIUM_MCP_REGISTRY_URL,
                "mcp_tool": "medium_get_article_content",
                "jsonrpc_id": jsonrpc_req["id"],
            },
        )

    content_blocks = result_obj.get("content", [])
    if not content_blocks:
        return (
            False,
            "MCP_EMPTY_CONTENT",
            "Medium MCP Server returned no content blocks.",
            {
                "mcp_server": MEDIUM_MCP_REGISTRY_URL,
                "mcp_tool": "medium_get_article_content",
                "jsonrpc_id": jsonrpc_req["id"],
            },
        )

    payload = json.loads(content_blocks[0].get("text", "{}"))
    article_html = (payload.get("article_html") or "").strip()
    if not article_html:
        return (
            False,
            "MCP_EMPTY_BODY",
            "Medium MCP Server returned an empty article body.",
            {
                "mcp_server": MEDIUM_MCP_REGISTRY_URL,
                "mcp_tool": "medium_get_article_content",
                "jsonrpc_id": jsonrpc_req["id"],
            },
        )

    return (
        True,
        "OK_MEDIUM_MCP",
        article_html,
        {
            "mcp_server": MEDIUM_MCP_REGISTRY_URL,
            "mcp_server_name": MEDIUM_MCP_SERVER_NAME,
            "mcp_protocol_version": MEDIUM_MCP_PROTOCOL_VERSION,
            "mcp_tool": "medium_get_article_content",
            "publication_domain": payload.get("publication_domain"),
            "jsonrpc_id": jsonrpc_req["id"],
        },
    )


def get_medium_mcp_config_metadata(total_mcp_articles: int = 0) -> Dict[str, Any]:
    """
    Returns metadata describing the Medium MCP Server (`https://mcpmarket.com/server/medium-2`)
    integration for the UI and CLI status output.
    """
    return {
        "server_id": "medium-2",
        "server_name": MEDIUM_MCP_SERVER_NAME,
        "registry_url": MEDIUM_MCP_REGISTRY_URL,
        "protocol_version": f"MCP {MEDIUM_MCP_PROTOCOL_VERSION} (JSON-RPC 2.0)",
        "handled_domains": list(MEDIUM_HANDLED_PREFIXES),
        "direct_url_scraping_disabled": True,
        "articles_ingested_via_mcp": total_mcp_articles,
        "tools": [
            {
                "name": t["name"],
                "description": t["description"],
            }
            for t in MEDIUM_MCP_TOOLS_SPEC
        ],
    }
