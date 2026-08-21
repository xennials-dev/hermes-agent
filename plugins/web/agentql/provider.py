"""AgentQL web extraction provider — plugin form.

Subclasses :class:`agent.web_search_provider.WebSearchProvider`. One
capability advertised:

- ``supports_extract()`` -> True (AgentQL ``/v1/query-data``)
- ``supports_search()``  -> False (AgentQL is an extraction engine,
  not a search engine — use Brave/DuckDuckGo/Tavily for search)

AgentQL's REST API uses a natural language prompt to describe what data
to extract from a given URL. The API handles rendering, JavaScript
execution, and structured data parsing server-side.

Config keys this provider responds to::

    web:
      extract_backend: "agentql"     # explicit per-capability
      backend: "agentql"             # shared fallback (search will still
                                     # use another available provider)

Env vars::

    AGENTQL_API_KEY=...              # https://dev.agentql.com (required)
    AGENTQL_BASE_URL=...             # optional override (default: https://api.agentql.com)
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from agent.web_search_provider import WebSearchProvider

logger = logging.getLogger(__name__)

# AgentQL REST API default base URL
_DEFAULT_BASE_URL = "https://api.agentql.com"


def _agentql_request(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST to the AgentQL REST API and return parsed JSON.

    Raises ``ValueError`` when ``AGENTQL_API_KEY`` is unset.
    """
    import httpx

    from agent.web_search_provider import get_provider_env

    api_key = get_provider_env("AGENTQL_API_KEY")
    if not api_key:
        raise ValueError(
            "AGENTQL_API_KEY environment variable not set. "
            "Get your API key at https://dev.agentql.com"
        )

    base_url = get_provider_env("AGENTQL_BASE_URL") or _DEFAULT_BASE_URL
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    logger.info("AgentQL %s request to %s", endpoint, url)

    response = httpx.post(
        url,
        json=payload,
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def _normalize_agentql_response(
    raw: Dict[str, Any], url: str
) -> List[Dict[str, Any]]:
    """Map AgentQL ``/v1/query-data`` response to standard documents.

    AgentQL returns structured JSON data keyed by the fields in the
    natural language prompt. We serialize this to a readable string
    for the ``content`` field, and keep the raw JSON in ``raw_content``
    for downstream structured processing.

    Documents follow the legacy LLM post-processing shape::

        {"url", "title", "content", "raw_content", "metadata"}
    """
    # AgentQL response has a "data" key with the extracted fields
    data = raw.get("data", raw)

    # Format the structured data as readable content
    if isinstance(data, dict):
        content_parts = []
        for key, value in data.items():
            if isinstance(value, list):
                content_parts.append(f"## {key}")
                for item in value:
                    if isinstance(item, dict):
                        content_parts.append(
                            "  - " + ", ".join(
                                f"{k}: {v}" for k, v in item.items()
                            )
                        )
                    else:
                        content_parts.append(f"  - {item}")
            elif isinstance(value, dict):
                content_parts.append(f"## {key}")
                for k, v in value.items():
                    content_parts.append(f"  {k}: {v}")
            else:
                content_parts.append(f"**{key}**: {value}")
        content = "\n".join(content_parts)
    else:
        content = str(data)

    raw_content = json.dumps(data, indent=2, ensure_ascii=False)

    return [
        {
            "url": url,
            "title": f"AgentQL extraction from {url}",
            "content": content,
            "raw_content": raw_content,
            "metadata": {
                "sourceURL": url,
                "provider": "agentql",
                "structured": True,
            },
        }
    ]


class AgentQLWebSearchProvider(WebSearchProvider):
    """AgentQL structured web extraction provider.

    Extraction-only — does not support search. AgentQL shines at
    structured data extraction from specific URLs using natural
    language queries.
    """

    @property
    def name(self) -> str:
        return "agentql"

    @property
    def display_name(self) -> str:
        return "AgentQL (TinyFish)"

    def is_available(self) -> bool:
        """Return True when ``AGENTQL_API_KEY`` is set to a non-empty value."""
        from agent.web_search_provider import get_provider_env

        return bool(get_provider_env("AGENTQL_API_KEY"))

    def supports_search(self) -> bool:
        # AgentQL is a structured extraction engine, not a search engine.
        return False

    def supports_extract(self) -> bool:
        return True

    def extract(self, urls: List[str], **kwargs: Any) -> List[Dict[str, Any]]:
        """Extract structured data from one or more URLs via AgentQL.

        Sync — the underlying call is httpx.post(...). Returns the legacy
        list-of-results shape; per-URL failures become items with ``error``.

        The ``prompt`` kwarg (if provided) is forwarded as the AgentQL
        query prompt. If omitted, a generic extraction prompt is used.
        """
        prompt = kwargs.get("prompt", "Extract the main content, headings, and any structured data from this page")

        try:
            from tools.interrupt import is_interrupted

            if is_interrupted():
                return [
                    {"url": u, "error": "Interrupted", "title": ""} for u in urls
                ]
        except ImportError:
            pass

        documents: List[Dict[str, Any]] = []
        for url in urls:
            try:
                logger.info("AgentQL extract: %s", url)
                raw = _agentql_request(
                    "v1/query-data",
                    {
                        "url": url,
                        "prompt": prompt,
                    },
                )
                documents.extend(_normalize_agentql_response(raw, url))
            except ValueError as exc:
                documents.append(
                    {"url": url, "title": "", "content": "", "error": str(exc)}
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("AgentQL extract error for %s: %s", url, exc)
                documents.append(
                    {
                        "url": url,
                        "title": "",
                        "content": "",
                        "error": f"AgentQL extraction failed: {exc}",
                    }
                )

        return documents

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "AgentQL (TinyFish)",
            "badge": "freemium",
            "tag": "AI-powered structured data extraction. Natural language queries, works on dynamic + authenticated pages.",
            "env_vars": [
                {
                    "key": "AGENTQL_API_KEY",
                    "prompt": "AgentQL API key",
                    "url": "https://dev.agentql.com",
                },
            ],
        }
