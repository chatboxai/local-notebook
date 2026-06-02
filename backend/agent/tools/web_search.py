import json
import logging
from typing import Optional

import httpx
from pydantic import BaseModel, Field

from kosong.tooling import CallableTool2, ToolOk, ToolError, ToolReturnValue

from agent.tools.query_knowledge_base import CitationState

logger = logging.getLogger("tool.web_search")


class WebSearchParams(BaseModel):
    query: str = Field(description="搜索关键词")
    max_results: int = Field(default=5, description="返回结果数量，默认 5 条")
    freshness: str = Field(
        default="noLimit",
        description="时间范围：noLimit(不限)/oneDay(一天内)/oneWeek(一周内)/oneMonth(一月内)/oneYear(一年内)",
    )


class WebSearchTool(CallableTool2[WebSearchParams]):
    name: str = "web_search"
    description: str = (
        "搜索互联网获取最新信息。"
        "用于查找时事新闻、行业动态、相关人物或机构信息、公开评价、同类资料、或文档中没有的内容。"
        "搜索结果会包含引用标记 [citation_X]，请在回答中使用。"
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
            return ToolError(message="搜索关键词不能为空", brief="空查询")

        if not self.api_key:
            return ToolError(message="联网搜索未配置，请在设置中填写博查 API Key", brief="未配置")

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
                    message=f"搜索请求失败 (状态码: {resp.status_code}) {error_detail}",
                    brief="请求失败",
                )

            data = resp.json()
            web_pages = data.get("data", {}).get("webPages", {}).get("value", [])

            if not web_pages:
                return ToolOk(output="未找到相关搜索结果")

            state = self.state
            results = []
            for item in web_pages:
                citation_id = f"citation_{state.citation_counter}"

                title = item.get("name", "无标题")
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

            logger.info(f"搜索成功，获取 {len(results)} 条结果")
            return ToolOk(output=json.dumps(results, ensure_ascii=False))

        except httpx.TimeoutException:
            return ToolError(message="搜索请求超时，请稍后重试", brief="超时")
        except httpx.HTTPError as e:
            return ToolError(message=f"网络请求失败: {e}", brief="网络错误")
        except Exception as e:
            logger.exception("Web search error")
            return ToolError(message=f"搜索失败: {e}", brief="搜索异常")
