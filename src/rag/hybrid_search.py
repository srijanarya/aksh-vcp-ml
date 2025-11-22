"""
Hybrid Search Engine - Combines Local RAG + Web Search

Integrates:
1. Local LanceDB vector store (earnings PDFs)
2. EXA web search (real-time Indian market news)

Usage:
    from src.rag.hybrid_search import get_hybrid_search_engine

    engine = get_hybrid_search_engine()
    result = engine.search("TCS earnings guidance", sources=["local", "web"])
"""

import logging
from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import os

# Local RAG
from src.rag.earnings_query import get_earnings_query_engine, QueryResult

# Web search
try:
    from exa_py import Exa
    EXA_AVAILABLE = True
except ImportError:
    EXA_AVAILABLE = False
    logging.warning("exa_py not installed. Web search will be disabled.")

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchResult:
    """Result from hybrid search combining local + web sources"""
    query: str
    local_results: Optional[QueryResult] = None
    web_results: Optional[List[Dict[str, Any]]] = None
    combined_summary: str = ""
    sources_used: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    error: Optional[str] = None


class HybridSearchEngine:
    """
    Hybrid search combining local RAG and web search

    Features:
    - Local vector search for earnings documents
    - EXA web search for real-time news (Indian market focused)
    - Smart source selection based on query type
    - Result merging and ranking
    """

    def __init__(
        self,
        exa_api_key: Optional[str] = None,
        enable_web_search: bool = True,
        indian_market_domains: Optional[List[str]] = None
    ):
        """
        Initialize hybrid search engine

        Args:
            exa_api_key: EXA API key (defaults to env var)
            enable_web_search: Enable web search functionality
            indian_market_domains: Domains to search for Indian market news
        """
        self.enable_web_search = enable_web_search and EXA_AVAILABLE

        # Initialize local RAG
        try:
            self.local_engine = get_earnings_query_engine()
            logger.info("Local RAG engine initialized")
        except Exception as e:
            logger.warning(f"Local RAG initialization failed: {e}")
            self.local_engine = None

        # Initialize EXA web search
        self.exa_client = None
        if self.enable_web_search:
            api_key = exa_api_key or os.getenv("EXA_API_KEY")
            if api_key:
                try:
                    self.exa_client = Exa(api_key=api_key)
                    logger.info("EXA web search initialized")
                except Exception as e:
                    logger.warning(f"EXA initialization failed: {e}")
                    self.enable_web_search = False
            else:
                logger.warning("EXA_API_KEY not set, web search disabled")
                self.enable_web_search = False

        # Indian market focused domains
        self.indian_domains = indian_market_domains or [
            "moneycontrol.com",
            "economictimes.indiatimes.com",
            "business-standard.com",
            "livemint.com",
            "financialexpress.com",
            "thehindubusinessline.com",
            "nseindia.com",
            "bseindia.com"
        ]

        logger.info(f"Hybrid search engine ready (local={self.local_engine is not None}, web={self.enable_web_search})")

    async def search(
        self,
        query: str,
        sources: List[Literal["local", "web", "both"]] = ["both"],
        filters: Optional[Dict[str, Any]] = None,
        web_num_results: int = 5,
        local_top_k: int = 5
    ) -> HybridSearchResult:
        """
        Execute hybrid search across local and web sources

        Args:
            query: Search query
            sources: Which sources to use ("local", "web", or "both")
            filters: Metadata filters for local search (company, quarter, etc.)
            web_num_results: Number of web results to fetch
            local_top_k: Number of local results to fetch

        Returns:
            HybridSearchResult with combined results
        """
        start_time = datetime.now()
        sources_to_use = sources if "both" not in sources else ["local", "web"]

        # Determine if query needs web search
        real_time_keywords = ["today", "latest", "recent", "news", "announcement", "current"]
        needs_web = any(keyword in query.lower() for keyword in real_time_keywords)

        # Execute searches in parallel
        tasks = []
        sources_used = []

        if "local" in sources_to_use and self.local_engine:
            tasks.append(self._search_local(query, filters, local_top_k))
            sources_used.append("local")

        if "web" in sources_to_use and self.enable_web_search:
            tasks.append(self._search_web(query, web_num_results))
            sources_used.append("web")

        # Wait for all searches to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Parse results
        local_result = None
        web_result = None

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Search {i} failed: {result}")
                continue

            if sources_used[i] == "local":
                local_result = result
            elif sources_used[i] == "web":
                web_result = result

        # Combine and summarize
        combined_summary = self._synthesize_results(query, local_result, web_result)

        execution_time = (datetime.now() - start_time).total_seconds()

        return HybridSearchResult(
            query=query,
            local_results=local_result,
            web_results=web_result,
            combined_summary=combined_summary,
            sources_used=sources_used,
            execution_time=execution_time
        )

    async def _search_local(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        top_k: int
    ) -> Optional[QueryResult]:
        """Search local RAG vector store"""
        try:
            # Run in thread pool since local engine is synchronous
            result = await asyncio.to_thread(
                self.local_engine.query,
                query_text=query,
                filters=filters,
                top_k=top_k
            )
            logger.info(f"Local search found {len(result.source_nodes) if result else 0} results")
            return result
        except Exception as e:
            logger.error(f"Local search failed: {e}")
            return None

    async def _search_web(
        self,
        query: str,
        num_results: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Search web using EXA (Indian market focused)"""
        if not self.exa_client:
            return None

        try:
            # EXA search with Indian market domain filtering
            enhanced_query = f"{query} Indian stock market"

            # Run in thread pool since exa-py is synchronous
            search_response = await asyncio.to_thread(
                self.exa_client.search_and_contents,
                enhanced_query,
                num_results=num_results,
                include_domains=self.indian_domains,
                text=True,
                highlights=True
            )

            # Parse results
            web_results = []
            for result in search_response.results:
                web_results.append({
                    "title": result.title,
                    "url": result.url,
                    "text": result.text[:500] if result.text else "",  # First 500 chars
                    "highlights": result.highlights[:3] if hasattr(result, 'highlights') else [],
                    "published_date": result.published_date if hasattr(result, 'published_date') else None,
                    "score": result.score if hasattr(result, 'score') else 0.0
                })

            logger.info(f"Web search found {len(web_results)} results")
            return web_results

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return None

    def _synthesize_results(
        self,
        query: str,
        local: Optional[QueryResult],
        web: Optional[List[Dict[str, Any]]]
    ) -> str:
        """
        Synthesize combined summary from local and web results

        This is a simple concatenation. For production, consider using
        an LLM to create a coherent synthesis.
        """
        summary_parts = []

        summary_parts.append(f"# Hybrid Search Results for: {query}\n")

        # Local results
        if local and local.response:
            summary_parts.append("## 📊 From Local Earnings Documents:")
            summary_parts.append(local.response)
            summary_parts.append("")

        # Web results
        if web and len(web) > 0:
            summary_parts.append("## 🌐 From Web (Real-Time News):")
            for i, result in enumerate(web[:3], 1):  # Top 3
                summary_parts.append(f"\n**{i}. {result['title']}**")
                summary_parts.append(f"   Source: {result['url']}")
                if result['text']:
                    summary_parts.append(f"   {result['text'][:200]}...")
                if result['highlights']:
                    summary_parts.append(f"   Key: {', '.join(result['highlights'][:2])}")
            summary_parts.append("")

        # No results
        if not local and not web:
            summary_parts.append("No results found from any source.")

        return "\n".join(summary_parts)

    def search_by_company(
        self,
        company: str,
        query: str,
        include_web: bool = True
    ) -> HybridSearchResult:
        """
        Synchronous wrapper for company-specific search

        Args:
            company: Company symbol (e.g., "TCS")
            query: Query about the company
            include_web: Include web search for latest news

        Returns:
            HybridSearchResult
        """
        enhanced_query = f"{company} {query}"
        filters = {"company": company.upper()}
        sources = ["both"] if include_web else ["local"]

        # Run async search in sync context
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context
            raise RuntimeError("Use await search() instead of search_by_company() in async context")

        return loop.run_until_complete(
            self.search(enhanced_query, sources=sources, filters=filters)
        )


# Singleton instance
_hybrid_engine_instance = None


def get_hybrid_search_engine(
    exa_api_key: Optional[str] = None,
    enable_web_search: bool = True
) -> HybridSearchEngine:
    """
    Get singleton hybrid search engine instance

    Args:
        exa_api_key: EXA API key (optional, uses env var)
        enable_web_search: Enable web search functionality

    Returns:
        HybridSearchEngine instance
    """
    global _hybrid_engine_instance

    if _hybrid_engine_instance is None:
        _hybrid_engine_instance = HybridSearchEngine(
            exa_api_key=exa_api_key,
            enable_web_search=enable_web_search
        )

    return _hybrid_engine_instance


# Convenience function for quick searches
async def hybrid_search(
    query: str,
    company: Optional[str] = None,
    include_web: bool = True
) -> HybridSearchResult:
    """
    Convenience function for hybrid search

    Args:
        query: Search query
        company: Optional company filter
        include_web: Include web search

    Returns:
        HybridSearchResult
    """
    engine = get_hybrid_search_engine()

    filters = {"company": company.upper()} if company else None
    sources = ["both"] if include_web else ["local"]

    return await engine.search(query, sources=sources, filters=filters)
