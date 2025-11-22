"""
Semantic Query Engine for Earnings Documents

Provides semantic search, retrieval, and synthesis capabilities for earnings analysis.
Supports metadata filtering, top-k retrieval, and response synthesis.

Source: Learned from awesome-ai-apps/mcp_ai_agents/doc_mcp
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters, FilterOperator
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core import get_response_synthesizer as get_synth
from llama_index.core import Settings

from src.rag.vector_store import get_earnings_vector_store

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """
    Result from semantic query

    Attributes:
        response: Synthesized response text
        source_nodes: List of source documents with scores
        metadata: Additional metadata about the query
    """
    response: str
    source_nodes: List[Dict]
    metadata: Dict[str, Any]


class EarningsQueryEngine:
    """
    Query engine for semantic search over earnings documents

    Features:
    - Semantic similarity search
    - Metadata filtering (company, sector, quarter, date)
    - Top-k retrieval (configurable)
    - Response synthesis (refine mode for comprehensive answers)
    - Source tracking (which documents contributed to answer)
    """

    def __init__(
        self,
        similarity_top_k: int = 5,
        response_mode: str = "refine"
    ):
        """
        Initialize query engine

        Args:
            similarity_top_k: Number of similar documents to retrieve
            response_mode: Response synthesis mode ('refine', 'compact', 'tree_summarize')
        """
        self.similarity_top_k = similarity_top_k
        self.response_mode = response_mode

        # Initialize vector store
        self.vector_store_wrapper = get_earnings_vector_store()

        # Check if vector store has data
        stats = self.vector_store_wrapper.get_stats()
        if not stats.get("exists") or stats.get("count", 0) == 0:
            logger.warning(
                "Vector store is empty. Run earnings_ingestion.py first to index documents."
            )

        # Create index from vector store
        self._init_index()

        logger.info(
            f"Initialized query engine (top_k={similarity_top_k}, mode={response_mode})"
        )

    def _init_index(self):
        """Initialize vector store index"""
        try:
            vector_store = self.vector_store_wrapper.get_vector_store()
            self.index = VectorStoreIndex.from_vector_store(vector_store)
            logger.info("Created index from existing vector store")
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            raise

    def query(
        self,
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None
    ) -> QueryResult:
        """
        Execute semantic query

        Args:
            query_text: Natural language query
            filters: Metadata filters (e.g., {"company": "TCS", "quarter": "Q4FY24"})
            top_k: Override default similarity_top_k

        Returns:
            QueryResult with response and sources

        Example:
            >>> engine = EarningsQueryEngine()
            >>> result = engine.query(
            ...     "Which companies showed QoQ revenue growth > 20%?",
            ...     filters={"quarter": "Q4FY24"}
            ... )
            >>> print(result.response)
        """
        try:
            # Build metadata filters if provided
            metadata_filters = None
            if filters:
                metadata_filters = self._build_filters(filters)

            # Get retriever
            k = top_k if top_k is not None else self.similarity_top_k
            retriever = self.index.as_retriever(
                similarity_top_k=k,
                filters=metadata_filters
            )

            # Get response synthesizer
            response_synthesizer = get_response_synthesizer(
                response_mode=self.response_mode
            )

            # Create query engine
            query_engine = RetrieverQueryEngine(
                retriever=retriever,
                response_synthesizer=response_synthesizer
            )

            # Execute query
            response = query_engine.query(query_text)

            # Extract source nodes
            source_nodes = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    source_nodes.append({
                        "text": node.node.text[:200] + "...",  # Preview
                        "score": node.score,
                        "metadata": node.node.metadata
                    })

            # Build result
            result = QueryResult(
                response=str(response),
                source_nodes=source_nodes,
                metadata={
                    "query": query_text,
                    "filters": filters,
                    "top_k": k,
                    "num_sources": len(source_nodes)
                }
            )

            logger.info(f"Query executed: {len(source_nodes)} sources retrieved")
            return result

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    def _build_filters(self, filters: Dict[str, Any]) -> MetadataFilters:
        """
        Build LlamaIndex metadata filters from dictionary

        Args:
            filters: Dictionary of metadata key-value pairs

        Returns:
            MetadataFilters object
        """
        filter_list = []
        for key, value in filters.items():
            filter_list.append(
                MetadataFilter(
                    key=key,
                    value=value,
                    operator=FilterOperator.EQ
                )
            )

        return MetadataFilters(filters=filter_list)

    def retrieve_similar(
        self,
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve similar documents without synthesis (faster)

        Args:
            query_text: Query text
            filters: Metadata filters
            top_k: Number of documents to retrieve

        Returns:
            List of similar documents with scores

        Example:
            >>> engine = EarningsQueryEngine()
            >>> docs = engine.retrieve_similar("earnings beat estimates", top_k=3)
            >>> for doc in docs:
            ...     print(f"{doc['metadata']['company']}: {doc['score']:.3f}")
        """
        try:
            metadata_filters = None
            if filters:
                metadata_filters = self._build_filters(filters)

            k = top_k if top_k is not None else self.similarity_top_k

            retriever = self.index.as_retriever(
                similarity_top_k=k,
                filters=metadata_filters
            )

            nodes = retriever.retrieve(query_text)

            results = []
            for node in nodes:
                results.append({
                    "text": node.node.text,
                    "score": node.score,
                    "metadata": node.node.metadata
                })

            logger.info(f"Retrieved {len(results)} similar documents")
            return results

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            raise

    def search_by_company(
        self,
        company: str,
        query_text: str,
        top_k: int = 3
    ) -> QueryResult:
        """
        Search earnings for specific company

        Args:
            company: Company symbol (e.g., "TCS", "RELIANCE")
            query_text: Query about the company
            top_k: Number of results

        Returns:
            QueryResult filtered to company

        Example:
            >>> engine = EarningsQueryEngine()
            >>> result = engine.search_by_company(
            ...     "TCS",
            ...     "What was the revenue growth in Q4?"
            ... )
        """
        return self.query(
            query_text,
            filters={"company": company.upper()},
            top_k=top_k
        )

    def search_by_quarter(
        self,
        quarter: str,
        query_text: str,
        top_k: int = 5
    ) -> QueryResult:
        """
        Search earnings for specific quarter

        Args:
            quarter: Quarter (e.g., "Q4FY24", "Q1FY25")
            query_text: Query about the quarter
            top_k: Number of results

        Returns:
            QueryResult filtered to quarter

        Example:
            >>> engine = EarningsQueryEngine()
            >>> result = engine.search_by_quarter(
            ...     "Q4FY24",
            ...     "Which companies had strong earnings growth?"
            ... )
        """
        return self.query(
            query_text,
            filters={"quarter": quarter.upper()},
            top_k=top_k
        )

    def compare_companies(
        self,
        companies: List[str],
        query_text: str
    ) -> Dict[str, QueryResult]:
        """
        Compare multiple companies

        Args:
            companies: List of company symbols
            query_text: Comparison query

        Returns:
            Dictionary mapping company -> QueryResult

        Example:
            >>> engine = EarningsQueryEngine()
            >>> results = engine.compare_companies(
            ...     ["TCS", "INFY", "WIPRO"],
            ...     "What was the profit margin in Q4FY24?"
            ... )
            >>> for company, result in results.items():
            ...     print(f"{company}: {result.response}")
        """
        results = {}
        for company in companies:
            try:
                result = self.search_by_company(company, query_text, top_k=2)
                results[company] = result
            except Exception as e:
                logger.error(f"Failed to query {company}: {e}")
                results[company] = None

        return results


def get_earnings_query_engine(
    similarity_top_k: int = 5,
    response_mode: str = "refine"
) -> EarningsQueryEngine:
    """
    Factory function to get query engine

    Args:
        similarity_top_k: Number of similar documents to retrieve
        response_mode: Response synthesis mode

    Returns:
        Configured EarningsQueryEngine

    Example:
        >>> engine = get_earnings_query_engine()
        >>> result = engine.query("Find companies with strong QoQ growth")
    """
    return EarningsQueryEngine(
        similarity_top_k=similarity_top_k,
        response_mode=response_mode
    )


if __name__ == "__main__":
    # Test query engine
    logging.basicConfig(level=logging.INFO)

    import sys

    # Initialize engine
    engine = get_earnings_query_engine()

    # Check if vector store has data
    stats = engine.vector_store_wrapper.get_stats()
    if stats.get("count", 0) == 0:
        print("\n❌ Vector store is empty!")
        print("Run earnings_ingestion.py first to index documents:")
        print("  python src/rag/earnings_ingestion.py data/earnings_pdfs")
        sys.exit(1)

    print(f"\n=== Earnings Query Engine ===")
    print(f"Documents indexed: {stats.get('count', 0)}")
    print(f"Top-k retrieval: {engine.similarity_top_k}")
    print(f"Response mode: {engine.response_mode}")
    print("="*30 + "\n")

    # Example query
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Which companies showed strong earnings growth?"

    print(f"Query: {query}\n")

    try:
        result = engine.query(query)

        print("Response:")
        print(result.response)
        print("\n" + "="*30)

        print(f"\nSources ({len(result.source_nodes)}):")
        for idx, source in enumerate(result.source_nodes, 1):
            print(f"\n{idx}. {source['metadata'].get('company', 'Unknown')}")
            print(f"   Score: {source['score']:.3f}")
            print(f"   Quarter: {source['metadata'].get('quarter', 'N/A')}")
            print(f"   Preview: {source['text'][:100]}...")

    except Exception as e:
        print(f"\n❌ Query failed: {e}")
        sys.exit(1)
