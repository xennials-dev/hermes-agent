"""AgentQL web extraction plugin — bundled, auto-loaded.

Uses the AgentQL REST API (https://api.agentql.com) for AI-powered
structured data extraction from web pages. Unlike the MCP server
(optional-mcps/agentql/), this provider integrates directly into
Hermes' ``web_extract`` tool so it can be selected as a backend via
``web.extract_backend: agentql`` in config.yaml.

AgentQL's strength is *structured* extraction via natural language
queries — you describe what you want and it returns it as structured
data. It complements Firecrawl/Tavily (which return raw markdown/text).

Requires: AGENTQL_API_KEY from https://dev.agentql.com
"""

from __future__ import annotations

from plugins.web.agentql.provider import AgentQLWebSearchProvider


def register(ctx) -> None:
    """Register the AgentQL provider with the plugin context."""
    ctx.register_web_search_provider(AgentQLWebSearchProvider())
