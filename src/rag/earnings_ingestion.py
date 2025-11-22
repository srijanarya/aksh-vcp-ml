"""
Earnings Document Ingestion Pipeline

Ingests BSE/NSE earnings PDFs into LanceDB vector store for semantic search.
Handles PDF extraction, chunking, metadata extraction, and incremental updates.

Source: Learned from awesome-ai-apps/mcp_ai_agents/doc_mcp
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union
from datetime import datetime
import hashlib

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings

from src.rag.vector_store import get_earnings_vector_store

logger = logging.getLogger(__name__)


class EarningsDocumentIngestion:
    """
    Ingestion pipeline for earnings documents

    Features:
    - PDF text extraction
    - Smart chunking (3072 tokens for OpenAI embeddings)
    - Metadata extraction (company, quarter, date, sector)
    - Incremental updates (only process new/modified files)
    - Progress tracking
    """

    def __init__(
        self,
        chunk_size: int = 3072,
        chunk_overlap: int = 200
    ):
        """
        Initialize ingestion pipeline

        Args:
            chunk_size: Size of text chunks for embeddings
            chunk_overlap: Overlap between chunks for context continuity
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize vector store
        self.vector_store = get_earnings_vector_store()

        # Initialize text splitter
        self.text_splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # Track ingested files (for incremental updates)
        self.ingested_hashes: Dict[str, str] = {}

        logger.info(f"Initialized ingestion pipeline (chunk_size={chunk_size})")

    def _extract_pdf_text(self, pdf_path: Path) -> Optional[str]:
        """
        Extract text from PDF file

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text or None if extraction fails
        """
        try:
            # Try pypdf first (already in requirements)
            from pypdf import PdfReader

            reader = PdfReader(str(pdf_path))
            text = ""

            for page in reader.pages:
                text += page.extract_text() + "\n"

            if not text.strip():
                logger.warning(f"No text extracted from {pdf_path}")
                return None

            return text.strip()

        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            return None

    def _extract_metadata(self, pdf_path: Path, text: str) -> Dict:
        """
        Extract metadata from PDF filename and content

        Args:
            pdf_path: Path to PDF file
            text: Extracted text content

        Returns:
            Dictionary with metadata fields

        Example filename patterns:
        - "TCS_Q4FY24_Results.pdf"
        - "RELIANCE_2024-03-31_Earnings.pdf"
        """
        filename = pdf_path.stem
        parts = filename.split('_')

        metadata = {
            "filename": pdf_path.name,
            "file_path": str(pdf_path),
            "file_size": pdf_path.stat().st_size,
            "ingestion_date": datetime.now().isoformat()
        }

        # Extract company symbol (usually first part)
        if parts:
            metadata["company"] = parts[0].upper()

        # Try to extract quarter from filename (Q1FY24, Q4FY23, etc.)
        for part in parts:
            if 'Q' in part.upper() and 'FY' in part.upper():
                metadata["quarter"] = part.upper()
                # Extract year from quarter (e.g., FY24 -> 2024)
                try:
                    fy_year = part.upper().split('FY')[1]
                    # Convert FY24 to full year 2024
                    full_year = f"20{fy_year}" if len(fy_year) == 2 else fy_year
                    metadata["fiscal_year"] = full_year
                except:
                    pass

        # Try to extract date (YYYY-MM-DD format)
        for part in parts:
            if '-' in part and len(part) == 10:
                try:
                    datetime.strptime(part, '%Y-%m-%d')
                    metadata["earnings_date"] = part
                except:
                    pass

        # Document type
        metadata["doc_type"] = "earnings_report"

        # Calculate content hash for incremental updates
        metadata["content_hash"] = hashlib.md5(text.encode()).hexdigest()

        return metadata

    def _create_documents(
        self,
        pdf_paths: List[Path],
        show_progress: bool = True
    ) -> List[Document]:
        """
        Create LlamaIndex documents from PDF files

        Args:
            pdf_paths: List of PDF file paths
            show_progress: Show progress during extraction

        Returns:
            List of Document objects with text and metadata
        """
        documents = []

        for idx, pdf_path in enumerate(pdf_paths):
            if show_progress and (idx + 1) % 10 == 0:
                logger.info(f"Processing {idx + 1}/{len(pdf_paths)} PDFs...")

            # Extract text
            text = self._extract_pdf_text(pdf_path)
            if not text:
                continue

            # Extract metadata
            metadata = self._extract_metadata(pdf_path, text)

            # Check if already ingested (incremental update)
            file_key = str(pdf_path)
            content_hash = metadata["content_hash"]

            if file_key in self.ingested_hashes:
                if self.ingested_hashes[file_key] == content_hash:
                    logger.debug(f"Skipping {pdf_path.name} (already ingested)")
                    continue

            # Create document
            doc = Document(
                text=text,
                metadata=metadata
            )
            documents.append(doc)

            # Track for incremental updates
            self.ingested_hashes[file_key] = content_hash

        logger.info(f"Created {len(documents)} documents from {len(pdf_paths)} PDFs")
        return documents

    def ingest_directory(
        self,
        directory: Union[str, Path],
        pattern: str = "*.pdf",
        show_progress: bool = True
    ) -> bool:
        """
        Ingest all PDFs from a directory

        Args:
            directory: Path to directory containing PDFs
            pattern: Glob pattern for PDF files
            show_progress: Show progress during ingestion

        Returns:
            True if successful, False otherwise

        Example:
            >>> ingestion = EarningsDocumentIngestion()
            >>> ingestion.ingest_directory("data/earnings_pdfs")
        """
        try:
            directory = Path(directory)
            if not directory.exists():
                logger.error(f"Directory not found: {directory}")
                return False

            # Find all PDFs
            pdf_paths = list(directory.glob(pattern))
            if not pdf_paths:
                logger.warning(f"No PDFs found in {directory} matching {pattern}")
                return False

            logger.info(f"Found {len(pdf_paths)} PDF files")

            # Create documents
            documents = self._create_documents(pdf_paths, show_progress)
            if not documents:
                logger.warning("No documents created from PDFs")
                return False

            # Ingest into vector store
            return self.ingest_documents(documents, show_progress)

        except Exception as e:
            logger.error(f"Failed to ingest directory: {e}")
            return False

    def ingest_documents(
        self,
        documents: List[Document],
        show_progress: bool = True
    ) -> bool:
        """
        Ingest documents into vector store

        Args:
            documents: List of Document objects
            show_progress: Show progress during indexing

        Returns:
            True if successful, False otherwise
        """
        try:
            if not documents:
                logger.warning("No documents to ingest")
                return False

            logger.info(f"Ingesting {len(documents)} documents...")

            # Get storage context
            storage_context = self.vector_store.get_storage_context()

            # Create index (this handles embedding and storage)
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                show_progress=show_progress
            )

            # Get final stats
            stats = self.vector_store.get_stats()
            logger.info(f"Ingestion complete. Total documents: {stats.get('count', 0)}")

            return True

        except Exception as e:
            logger.error(f"Failed to ingest documents: {e}")
            return False

    def ingest_single_file(
        self,
        pdf_path: Union[str, Path]
    ) -> bool:
        """
        Ingest a single PDF file

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if successful, False otherwise

        Example:
            >>> ingestion = EarningsDocumentIngestion()
            >>> ingestion.ingest_single_file("data/TCS_Q4FY24_Results.pdf")
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                logger.error(f"File not found: {pdf_path}")
                return False

            documents = self._create_documents([pdf_path], show_progress=False)
            return self.ingest_documents(documents, show_progress=False)

        except Exception as e:
            logger.error(f"Failed to ingest file: {e}")
            return False


def ingest_earnings_pdfs(
    directory: str,
    pattern: str = "*.pdf",
    chunk_size: int = 3072
) -> bool:
    """
    Convenience function to ingest earnings PDFs

    Args:
        directory: Path to directory containing PDFs
        pattern: Glob pattern for PDF files
        chunk_size: Size of text chunks

    Returns:
        True if successful, False otherwise

    Example:
        >>> ingest_earnings_pdfs("data/earnings_pdfs")
    """
    ingestion = EarningsDocumentIngestion(chunk_size=chunk_size)
    return ingestion.ingest_directory(directory, pattern, show_progress=True)


if __name__ == "__main__":
    # Test ingestion pipeline
    logging.basicConfig(level=logging.INFO)

    import sys

    if len(sys.argv) < 2:
        print("\nUsage: python earnings_ingestion.py <pdf_directory>")
        print("\nExample:")
        print("  python earnings_ingestion.py data/earnings_pdfs")
        sys.exit(1)

    pdf_dir = sys.argv[1]

    print(f"\n=== Ingesting Earnings PDFs ===")
    print(f"Directory: {pdf_dir}")
    print(f"Chunk size: 3072 tokens")
    print("="*30 + "\n")

    success = ingest_earnings_pdfs(pdf_dir)

    if success:
        print("\n✅ Ingestion successful!")

        # Show stats
        vector_store = get_earnings_vector_store()
        stats = vector_store.get_stats()
        print(f"\nTotal documents indexed: {stats.get('count', 0)}")
    else:
        print("\n❌ Ingestion failed. Check logs for details.")
        sys.exit(1)
