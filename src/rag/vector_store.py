"""
LanceDB Vector Store Configuration for Earnings Documents

This module sets up LanceDB for semantic search across Indian market earnings documents.
Integrates with LlamaIndex for production-grade RAG system.

Source: Learned from awesome-ai-apps/rag_apps/agentic_rag and mcp_ai_agents/doc_mcp
"""

import os
import logging
from pathlib import Path
from typing import Optional
import lancedb
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.lancedb import LanceDBVectorStore
from llama_index.core.storage import StorageContext

logger = logging.getLogger(__name__)


class EarningsVectorStore:
    """
    Vector store for earnings documents with semantic search capabilities

    Architecture:
    - LanceDB: Local vector database (fast, persistent)
    - OpenAI embeddings: text-embedding-3-small (1536 dimensions)
    - Metadata schema: company, sector, quarter, date, exchange
    """

    def __init__(
        self,
        db_path: str = "data/lancedb",
        table_name: str = "earnings_documents",
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize vector store

        Args:
            db_path: Path to LanceDB database
            table_name: Name of the vector store table
            embedding_model: OpenAI embedding model to use
        """
        self.db_path = Path(db_path)
        self.table_name = table_name
        self.embedding_model = embedding_model

        # Ensure database directory exists
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Initialize embeddings
        self._init_embeddings()

        # Initialize LanceDB connection
        self._init_lancedb()

        logger.info(f"Initialized EarningsVectorStore at {self.db_path}/{self.table_name}")

    def _init_embeddings(self):
        """Initialize OpenAI embeddings globally for LlamaIndex"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Required for semantic embeddings."
            )

        # Set global embedding model for LlamaIndex
        Settings.embed_model = OpenAIEmbedding(
            model=self.embedding_model,
            embed_batch_size=100  # Batch size for efficient processing
        )

        logger.info(f"Configured OpenAI embeddings: {self.embedding_model}")

    def _init_lancedb(self):
        """Initialize LanceDB connection"""
        try:
            # Connect to LanceDB
            self.db = lancedb.connect(str(self.db_path))

            # Check if table exists
            existing_tables = self.db.table_names()
            if self.table_name in existing_tables:
                self.table = self.db.open_table(self.table_name)
                logger.info(f"Opened existing table: {self.table_name}")
            else:
                self.table = None
                logger.info(f"Table {self.table_name} will be created on first ingest")

        except Exception as e:
            logger.error(f"Failed to initialize LanceDB: {e}")
            raise

    def get_vector_store(self) -> LanceDBVectorStore:
        """
        Get LlamaIndex vector store instance

        Returns:
            LanceDBVectorStore configured for earnings documents
        """
        # Check if table exists, use appropriate mode
        mode = "append" if self.table is not None else "overwrite"

        return LanceDBVectorStore(
            uri=str(self.db_path),
            table_name=self.table_name,
            mode=mode  # Append for existing, overwrite for new
        )

    def get_storage_context(self) -> StorageContext:
        """
        Get storage context for LlamaIndex indexing

        Returns:
            StorageContext with LanceDB vector store
        """
        vector_store = self.get_vector_store()
        return StorageContext.from_defaults(vector_store=vector_store)

    def get_stats(self) -> dict:
        """
        Get vector store statistics

        Returns:
            Dictionary with table stats (count, schema, etc.)
        """
        if self.table is None:
            return {
                "table_name": self.table_name,
                "exists": False,
                "count": 0
            }

        try:
            count = self.table.count_rows()
            schema = self.table.schema

            return {
                "table_name": self.table_name,
                "exists": True,
                "count": count,
                "schema": str(schema),
                "db_path": str(self.db_path)
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "table_name": self.table_name,
                "exists": True,
                "error": str(e)
            }

    def delete_all(self) -> bool:
        """
        Delete all documents from vector store (use with caution!)

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.table is not None:
                self.db.drop_table(self.table_name)
                self.table = None
                logger.warning(f"Deleted table: {self.table_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete table: {e}")
            return False


def get_earnings_vector_store(
    db_path: str = "data/lancedb",
    table_name: str = "earnings_documents"
) -> EarningsVectorStore:
    """
    Factory function to get earnings vector store instance

    Args:
        db_path: Path to LanceDB database
        table_name: Name of the vector store table

    Returns:
        Configured EarningsVectorStore instance

    Example:
        >>> vector_store = get_earnings_vector_store()
        >>> stats = vector_store.get_stats()
        >>> print(f"Documents indexed: {stats['count']}")
    """
    return EarningsVectorStore(db_path=db_path, table_name=table_name)


if __name__ == "__main__":
    # Test vector store initialization
    logging.basicConfig(level=logging.INFO)

    try:
        vector_store = get_earnings_vector_store()
        stats = vector_store.get_stats()

        print("\n=== Earnings Vector Store ===")
        print(f"Table: {stats['table_name']}")
        print(f"Exists: {stats['exists']}")
        print(f"Documents: {stats.get('count', 0)}")
        print(f"Path: {stats.get('db_path', 'N/A')}")
        print("="*30)

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure OPENAI_API_KEY is set in environment:")
        print("export OPENAI_API_KEY='your-api-key-here'")
