"""
Unit Tests for Earnings RAG System

Tests vector store, ingestion, and query engine functionality.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from llama_index.core import Document


class TestEarningsVectorStore:
    """Test vector store initialization and operations"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary directory for test database"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_vector_store_init(self, temp_db_path):
        """Test vector store initialization"""
        from src.rag.vector_store import EarningsVectorStore

        vector_store = EarningsVectorStore(
            db_path=temp_db_path,
            table_name="test_earnings"
        )

        assert vector_store.db_path == Path(temp_db_path)
        assert vector_store.table_name == "test_earnings"
        assert vector_store.embedding_model == "text-embedding-3-small"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_get_stats_empty(self, temp_db_path):
        """Test stats for empty vector store"""
        from src.rag.vector_store import EarningsVectorStore

        vector_store = EarningsVectorStore(db_path=temp_db_path)
        stats = vector_store.get_stats()

        assert stats["exists"] is False
        assert stats["count"] == 0

    def test_missing_api_key(self, temp_db_path):
        """Test that missing API key raises error"""
        from src.rag.vector_store import EarningsVectorStore

        # Temporarily remove API key
        api_key = os.environ.pop("OPENAI_API_KEY", None)

        try:
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                EarningsVectorStore(db_path=temp_db_path)
        finally:
            # Restore API key
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_get_storage_context(self, temp_db_path):
        """Test storage context creation"""
        from src.rag.vector_store import EarningsVectorStore

        vector_store = EarningsVectorStore(db_path=temp_db_path)
        storage_context = vector_store.get_storage_context()

        assert storage_context is not None
        assert hasattr(storage_context, 'vector_store')


class TestEarningsIngestion:
    """Test document ingestion pipeline"""

    @pytest.fixture
    def temp_pdf_dir(self):
        """Create temporary directory with mock PDFs"""
        temp_dir = tempfile.mkdtemp()

        # Create mock PDF files (just empty files for testing)
        pdf_files = [
            "TCS_Q4FY24_Results.pdf",
            "INFY_Q4FY24_Earnings.pdf",
            "WIPRO_2024-03-31_Results.pdf"
        ]

        for pdf_file in pdf_files:
            Path(temp_dir, pdf_file).touch()

        yield temp_dir

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary directory for test database"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_ingestion_init(self, temp_db_path):
        """Test ingestion pipeline initialization"""
        from src.rag.earnings_ingestion import EarningsDocumentIngestion

        with patch('src.rag.earnings_ingestion.get_earnings_vector_store'):
            ingestion = EarningsDocumentIngestion(chunk_size=1024)

            assert ingestion.chunk_size == 1024
            assert ingestion.chunk_overlap == 200

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_extract_metadata_from_filename(self, temp_db_path):
        """Test metadata extraction from PDF filenames"""
        from src.rag.earnings_ingestion import EarningsDocumentIngestion

        with patch('src.rag.earnings_ingestion.get_earnings_vector_store'):
            ingestion = EarningsDocumentIngestion()

            # Test different filename patterns
            test_cases = [
                ("TCS_Q4FY24_Results.pdf", {
                    "company": "TCS",
                    "quarter": "Q4FY24",
                    "fiscal_year": "2024"
                }),
                ("RELIANCE_2024-03-31_Earnings.pdf", {
                    "company": "RELIANCE",
                    "earnings_date": "2024-03-31"
                }),
                ("INFY_Q1FY25_Results.pdf", {
                    "company": "INFY",
                    "quarter": "Q1FY25",
                    "fiscal_year": "2025"
                })
            ]

            for filename, expected_fields in test_cases:
                # Create temporary file for test
                pdf_path = Path(temp_db_path) / filename
                pdf_path.touch()  # Create empty file

                metadata = ingestion._extract_metadata(pdf_path, "sample text")

                for key, value in expected_fields.items():
                    assert metadata.get(key) == value, \
                        f"Failed for {filename}: {key}={metadata.get(key)}, expected={value}"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_pdf_text_extraction(self, temp_db_path):
        """Test PDF text extraction"""
        from src.rag.earnings_ingestion import EarningsDocumentIngestion

        with patch('src.rag.earnings_ingestion.get_earnings_vector_store'):
            ingestion = EarningsDocumentIngestion()

            # Mock PDF extraction
            with patch('pypdf.PdfReader') as mock_reader:
                mock_page = Mock()
                mock_page.extract_text.return_value = "Sample earnings report text"
                mock_reader_instance = Mock()
                mock_reader_instance.pages = [mock_page]
                mock_reader.return_value = mock_reader_instance

                pdf_path = Path("/tmp/test.pdf")
                text = ingestion._extract_pdf_text(pdf_path)

                assert text is not None
                assert "Sample earnings report text" in text

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_directory_scan(self, temp_pdf_dir):
        """Test directory scanning for PDFs"""
        from src.rag.earnings_ingestion import EarningsDocumentIngestion

        with patch('src.rag.earnings_ingestion.get_earnings_vector_store'):
            ingestion = EarningsDocumentIngestion()

            pdf_dir = Path(temp_pdf_dir)
            pdf_files = list(pdf_dir.glob("*.pdf"))

            assert len(pdf_files) == 3
            assert all(p.suffix == ".pdf" for p in pdf_files)


class TestEarningsQueryEngine:
    """Test semantic query engine"""

    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store with data"""
        with patch('src.rag.earnings_query.get_earnings_vector_store') as mock:
            mock_instance = Mock()
            mock_instance.get_stats.return_value = {
                "exists": True,
                "count": 10,
                "table_name": "test_earnings"
            }
            mock_instance.get_vector_store.return_value = Mock()
            mock.return_value = mock_instance
            yield mock

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_query_engine_init(self, mock_vector_store):
        """Test query engine initialization"""
        from src.rag.earnings_query import EarningsQueryEngine

        with patch('src.rag.earnings_query.VectorStoreIndex'):
            engine = EarningsQueryEngine(similarity_top_k=10)

            assert engine.similarity_top_k == 10
            assert engine.response_mode == "refine"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_build_filters(self, mock_vector_store):
        """Test metadata filter construction"""
        from src.rag.earnings_query import EarningsQueryEngine

        with patch('src.rag.earnings_query.VectorStoreIndex'):
            engine = EarningsQueryEngine()

            filters = {"company": "TCS", "quarter": "Q4FY24"}
            metadata_filters = engine._build_filters(filters)

            assert metadata_filters is not None
            assert len(metadata_filters.filters) == 2

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_search_by_company(self, mock_vector_store):
        """Test company-specific search"""
        from src.rag.earnings_query import EarningsQueryEngine

        with patch('src.rag.earnings_query.VectorStoreIndex'):
            engine = EarningsQueryEngine()

            # Mock the query method
            with patch.object(engine, 'query') as mock_query:
                mock_query.return_value = Mock(response="Test response")

                result = engine.search_by_company("TCS", "revenue growth")

                # Verify query was called with correct filters
                mock_query.assert_called_once()
                call_args = mock_query.call_args
                assert call_args[1]['filters']['company'] == "TCS"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_search_by_quarter(self, mock_vector_store):
        """Test quarter-specific search"""
        from src.rag.earnings_query import EarningsQueryEngine

        with patch('src.rag.earnings_query.VectorStoreIndex'):
            engine = EarningsQueryEngine()

            with patch.object(engine, 'query') as mock_query:
                mock_query.return_value = Mock(response="Test response")

                result = engine.search_by_quarter("Q4FY24", "strong growth")

                call_args = mock_query.call_args
                assert call_args[1]['filters']['quarter'] == "Q4FY24"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    def test_compare_companies(self, mock_vector_store):
        """Test multi-company comparison"""
        from src.rag.earnings_query import EarningsQueryEngine, QueryResult

        with patch('src.rag.earnings_query.VectorStoreIndex'):
            engine = EarningsQueryEngine()

            # Mock search_by_company
            mock_result = QueryResult(
                response="Test response",
                source_nodes=[],
                metadata={}
            )

            with patch.object(engine, 'search_by_company', return_value=mock_result):
                companies = ["TCS", "INFY", "WIPRO"]
                results = engine.compare_companies(companies, "profit margin")

                assert len(results) == 3
                for company in companies:
                    assert company in results
                    assert results[company] is not None


class TestEndToEndRAG:
    """End-to-end integration tests"""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing"""
        return [
            Document(
                text="TCS reported strong Q4FY24 results with 15% QoQ revenue growth. "
                     "Profit margins improved to 25%. The IT services segment showed robust demand.",
                metadata={
                    "company": "TCS",
                    "quarter": "Q4FY24",
                    "sector": "IT Services",
                    "earnings_date": "2024-04-10"
                }
            ),
            Document(
                text="Infosys Q4FY24 earnings beat estimates. Revenue grew 12% QoQ. "
                     "Management provided positive guidance for FY25.",
                metadata={
                    "company": "INFY",
                    "quarter": "Q4FY24",
                    "sector": "IT Services",
                    "earnings_date": "2024-04-13"
                }
            )
        ]

    @pytest.mark.skip(reason="Requires OpenAI API key and actual embedding calls")
    @patch.dict(os.environ, {"OPENAI_API_KEY": "real-key-here"})
    def test_full_ingestion_and_query(self, sample_documents, temp_db_path):
        """
        Full integration test: ingest documents and query them

        Note: This test is skipped by default as it requires:
        - Valid OPENAI_API_KEY
        - Actual API calls for embeddings
        - Network connectivity

        Run with: pytest -v -k test_full_ingestion_and_query --run-integration
        """
        from src.rag.earnings_ingestion import EarningsDocumentIngestion
        from src.rag.earnings_query import EarningsQueryEngine

        # Ingest documents
        ingestion = EarningsDocumentIngestion()
        success = ingestion.ingest_documents(sample_documents)
        assert success, "Document ingestion failed"

        # Query
        engine = EarningsQueryEngine()
        result = engine.query("Which companies showed QoQ revenue growth?")

        assert result is not None
        assert len(result.response) > 0
        assert len(result.source_nodes) > 0


# Test runner configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
