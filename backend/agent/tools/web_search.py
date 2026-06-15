import json
import logging
from typing import Optional

import httpx
from pydantic import BaseModel, Field

from kosong.tooling import CallableTool2, ToolOk, ToolError, ToolReturnValue

from agent.tools.query_knowledge_base import CitationState

logger = logging.getLogger("tool.web_search")


class WebSearchParams(BaseModel):
    query: str = Field(description="Search query.")
    max_results: int = Field(default=5, description="Number of results to return. Default is 5.")
    freshness: str = Field(
        default="noLimit",
        description=(
            "Time range: noLimit, oneDay, oneWeek, oneMonth, or oneYear."
        ),
    )


class WebSearchTool(CallableTool2[WebSearchParams]):
    name: str = "web_search"
    description: str = (
        "Search the internet for current information. Use it for news, industry "
        "updates, people or organization information, public reviews, related "
        "materials, or content not covered by the documents. Search results include "
        "citation markers in `[citation_X]` format; use them in the answer."
    )
    params: type[WebSearchParams] = WebSearchParams

    def __init__(
        self,
        citation_state: Optional[CitationState] = None,
        api_key: str = "",
        base_url: str = "",
    ):
        super().__init__()
        self.state = citation_state or CitationState()
        self.api_key = api_key
        self.base_url = base_url

    async def __call__(self, params: WebSearchParams) -> ToolReturnValue:
        query = params.query.strip()
        if not query:
            return ToolError(message="Search query must not be empty", brief="empty query")

        if not self.api_key:
            return ToolError(message="Web search is not configured. Add the Bocha API key in Settings.", brief="not configured")

        max_results = params.max_results
        freshness = params.freshness

        try:
            logger.info(f"联网搜索: {query}")

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.base_url}/web-search",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": query,
                        "count": max_results,
                        "freshness": freshness,
                        "summary": True,
                    },
                )

            if resp.status_code != 200:
                error_detail = ""
                try:
                    error_detail = resp.json().get("message", "")
                except Exception:
                    pass
                return ToolError(
                    message=f"Search request failed (status code: {resp.status_code}) {error_detail}",
                    brief="request failed",
                )

            data = resp.json()
            web_pages = data.get("data", {}).get("webPages", {}).get("value", [])

            if not web_pages:
                return ToolOk(output="No relevant search results found")

            state = self.state
            results = []
            for item in web_pages:
                citation_id = f"citation_{state.citation_counter}"

                title = item.get("name", "Untitled")
                url = item.get("url", "")
                snippet = item.get("summary") or item.get("snippet", "")
                source = item.get("siteName", "")
                published_date = item.get("datePublished", "")
                favicon = item.get("siteIcon", "")

                results.append({
                    "citation_id": f"[{citation_id}]",
                    "title": title,
                    "snippet": snippet[:300] if snippet else "",
                    "source": source,
                    "published_date": published_date,
                })

                state.citations_map[citation_id] = {
                    "type": "web",
                    "title": title,
                    "url": url,
                    "snippet": snippet[:500] if snippet else "",
                    "source": source,
                    "published_date": published_date,
                    "favicon": favicon,
                }
                state.citation_counter += 1

            logger.info(f"Search succeeded, got {len(results)} results")
            return ToolOk(output=json.dumps(results, ensure_ascii=False))

        except httpx.TimeoutException:
            return ToolError(message="Search request timed out. Try again later.", brief="timeout")
        except httpx.HTTPError as e:
            return ToolError(message=f"Network request failed: {e}", brief="network error")
        except Exception as e:
            logger.exception("Web search error")
            return ToolError(message=f"Search failed: {e}", brief="search error")
