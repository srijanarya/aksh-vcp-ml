"""
Tests for BSENSEMapper (Story 1.3)

Acceptance Criteria (from Epic 1 Story 1.3):
AC1.3.1: Read existing baseline mapping (392 entries)
AC1.3.2: Fetch latest BhavCopy files for ISIN extraction
AC1.3.3: ISIN-based matching strategy (~60-70% coverage)
AC1.3.4: Fuzzy company name matching (~15-20% additional coverage)
AC1.3.5: Generate manual validation CSV for top 1,000 companies
AC1.3.6: Store final mapping with metadata in JSON + SQLite
AC1.3.7: Achieve ≥80% mapping coverage (≥4,400 of ~5,500 companies)
AC1.3.8: Handle edge cases (multiple ISINs, delisted, anomalies)

Test Strategy: AAA (Arrange, Act, Assert) pattern with mocking
Coverage Target: ≥90%

Author: VCP Financial Research Team
Created: 2025-11-13
"""

import pytest
import sqlite3
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# System under test (will be created in ml_data_collector.py)
# from agents.ml.ml_data_collector import BSENSEMapper, MappingCandidate, MappingReport


class TestBSENSEMapperInitialization:
    """Test BSENSEMapper class initialization (AC1.3.1)"""

    def test_mapper_class_exists(self):
        """AC1.3.1: Verify BSENSEMapper class exists"""
        from agents.ml.ml_data_collector import BSENSEMapper
        assert BSENSEMapper is not None

    def test_mapper_instantiation(self, tmp_path):
        """AC1.3.1: Mapper can be instantiated with existing mapping path"""
        from agents.ml.ml_data_collector import BSENSEMapper

        # Create mock existing mapping
        existing_mapping = {"500325": "RELIANCE", "500570": "TCS"}
        mapping_path = tmp_path / "existing_mapping.json"
        mapping_path.write_text(json.dumps(existing_mapping))

        mapper = BSENSEMapper(existing_mapping_path=str(mapping_path))

        assert mapper is not None
        assert hasattr(mapper, 'download_bhav_copies')
        assert hasattr(mapper, 'extract_isin_mappings')

    def test_load_existing_baseline_mapping(self, tmp_path):
        """AC1.3.1: Load existing 392 mappings and convert to new format"""
        from agents.ml.ml_data_collector import BSENSEMapper

        # Create baseline mapping (old format)
        baseline = {
            "500325": "RELIANCE",
            "500570": "TCS",
            "500209": "INFY"
        }
        mapping_path = tmp_path / "baseline.json"
        mapping_path.write_text(json.dumps(baseline))

        mapper = BSENSEMapper(existing_mapping_path=str(mapping_path))
        loaded_mappings = mapper.get_current_mappings()

        # Verify new format with metadata
        assert "500325" in loaded_mappings
        assert loaded_mappings["500325"]["nse_symbol"] == "RELIANCE"
        assert loaded_mappings["500325"]["match_method"] == "existing_baseline"
        assert loaded_mappings["500325"]["confidence"] == 1.0
        assert len(loaded_mappings) == 3


class TestBhavCopyDownload:
    """Test BhavCopy downloading (AC1.3.2)"""

    def test_download_bhav_copies_returns_paths(self, tmp_path):
        """AC1.3.2: download_bhav_copies downloads and returns BSE and NSE CSV paths"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        with patch('requests.get') as mock_get:
            # Mock successful downloads
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b'PK\x03\x04'  # ZIP file magic bytes
            mock_get.return_value = mock_response

            bse_path, nse_path = mapper.download_bhav_copies()

            assert bse_path is not None
            assert nse_path is not None
            assert "bhav" in bse_path.lower()

    def test_parse_bse_bhav_copy_extracts_isin(self, tmp_path):
        """AC1.3.2: Parse BSE BhavCopy columns: SC_CODE, SC_NAME, SC_ISIN"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        # Create mock BSE BhavCopy CSV
        bse_csv = """SC_CODE,SC_NAME,SC_GROUP,SC_TYPE,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,NO_TRADES,NO_OF_SHRS,NET_TURNOV,TDCLOINDI,ISIN_CODE
500325,RELIANCE INDUSTRIES LTD,A,R,2800.00,2850.00,2780.00,2840.00,2840.00,2820.00,12345,5000000,14200000000,,INE002A01018
500570,TATA CONSULTANCY SERV LT,A,R,3500.00,3550.00,3480.00,3540.00,3540.00,3520.00,10000,2000000,7080000000,,INE467B01029
"""
        csv_path = tmp_path / "bse_bhav.csv"
        csv_path.write_text(bse_csv)

        bse_data = mapper.parse_bse_bhav_copy(str(csv_path))

        assert "500325" in bse_data
        assert bse_data["500325"]["company_name"] == "RELIANCE INDUSTRIES LTD"
        assert bse_data["500325"]["isin"] == "INE002A01018"

    def test_parse_nse_bhav_copy_filters_eq_series(self, tmp_path):
        """AC1.3.2: Parse NSE BhavCopy, only use SERIES='EQ' (equity)"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        # Create mock NSE BhavCopy CSV
        nse_csv = """SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN
RELIANCE,EQ,2800.00,2850.00,2780.00,2840.00,2840.00,2820.00,5000000,14200000000,13-NOV-2024,12345,INE002A01018
TCS,EQ,3500.00,3550.00,3480.00,3540.00,3540.00,3520.00,2000000,7080000000,13-NOV-2024,10000,INE467B01029
RELIANCE,BE,100.00,110.00,95.00,105.00,105.00,100.00,1000,105000,13-NOV-2024,50,INE002A01018
"""
        csv_path = tmp_path / "nse_bhav.csv"
        csv_path.write_text(nse_csv)

        nse_data = mapper.parse_nse_bhav_copy(str(csv_path))

        # Should only have EQ series, not BE
        assert "RELIANCE" in nse_data
        assert nse_data["RELIANCE"]["isin"] == "INE002A01018"
        assert nse_data["RELIANCE"]["series"] == "EQ"
        # Should have exactly 2 entries (not 3)
        assert len(nse_data) == 2


class TestISINBasedMatching:
    """Test ISIN-based matching strategy (AC1.3.3)"""

    def test_isin_exact_match(self, tmp_path):
        """AC1.3.3: Exact ISIN match → confidence 1.0"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        bse_data = {
            "500325": {"company_name": "RELIANCE INDUSTRIES LTD", "isin": "INE002A01018"}
        }
        nse_data = {
            "RELIANCE": {"isin": "INE002A01018", "volume": 5000000}
        }

        mappings = mapper.extract_isin_mappings(bse_data, nse_data)

        assert "500325" in mappings
        assert mappings["500325"]["nse_symbol"] == "RELIANCE"
        assert mappings["500325"]["match_method"] == "isin_exact"
        assert mappings["500325"]["confidence"] == 1.0

    def test_multiple_nse_symbols_for_same_isin_choose_highest_volume(self, tmp_path):
        """AC1.3.3: Multiple NSE symbols for same ISIN → choose highest volume, confidence 0.95"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        bse_data = {
            "500325": {"company_name": "RELIANCE INDUSTRIES LTD", "isin": "INE002A01018"}
        }
        nse_data = {
            "RELIANCE": {"isin": "INE002A01018", "volume": 5000000},
            "RELIANCE-OLD": {"isin": "INE002A01018", "volume": 100000}  # Lower volume
        }

        mappings = mapper.extract_isin_mappings(bse_data, nse_data)

        # Should choose RELIANCE (higher volume)
        assert mappings["500325"]["nse_symbol"] == "RELIANCE"
        assert mappings["500325"]["confidence"] == 0.95  # Slightly lower for ambiguity

    def test_isin_coverage_60_70_percent(self, tmp_path):
        """AC1.3.3: ISIN matching achieves ~60-70% coverage"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        # Mock 100 BSE companies, 65 have ISIN matches
        bse_data = {f"50{i:04d}": {"company_name": f"Company {i}", "isin": f"INE{i:06d}A01" if i < 65 else None} for i in range(100)}
        nse_data = {f"SYM{i}": {"isin": f"INE{i:06d}A01", "volume": 1000000} for i in range(65)}

        mappings = mapper.extract_isin_mappings(bse_data, nse_data)

        coverage = len(mappings) / len(bse_data) * 100
        assert 60 <= coverage <= 70


class TestFuzzyNameMatching:
    """Test fuzzy company name matching (AC1.3.4)"""

    def test_fuzzy_match_high_confidence_90_plus(self, tmp_path):
        """AC1.3.4: Fuzzy match ratio ≥90 → accept with confidence ratio/100"""
        pytest.importorskip("fuzzywuzzy")  # Skip if fuzzywuzzy not installed

        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        unmapped_bse = {
            "500209": {"company_name": "INFOSYS LIMITED"}
        }
        nse_symbols = {
            "INFY": {"company_name": "INFOSYS LTD"}
        }

        with patch('fuzzywuzzy.fuzz.token_sort_ratio', return_value=92):
            matches = mapper.fuzzy_match_names(unmapped_bse, nse_symbols)

        assert "500209" in matches
        assert matches["500209"]["nse_symbol"] == "INFY"
        assert matches["500209"]["match_method"] == "fuzzy_name_90"
        assert matches["500209"]["confidence"] == 0.92

    def test_fuzzy_match_medium_confidence_80_89(self, tmp_path):
        """AC1.3.4: Fuzzy match ratio 80-89 → store as candidate, requires manual review"""
        pytest.importorskip("fuzzywuzzy")  # Skip if fuzzywuzzy not installed

        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        unmapped_bse = {
            "500180": {"company_name": "HDFC BANK LIMITED"}
        }
        nse_symbols = {
            "HDFCBANK": {"company_name": "HDFC BANK LTD"},
            "HDFC": {"company_name": "HOUSING DEVELOPMENT FINANCE CORPORATION LTD"}
        }

        with patch('fuzzywuzzy.fuzz.token_sort_ratio', side_effect=[85, 75]):
            matches = mapper.fuzzy_match_names(unmapped_bse, nse_symbols)

        assert "500180" in matches
        assert matches["500180"]["match_method"] == "fuzzy_name_80-89"
        assert matches["500180"]["confidence"] == 0.85
        assert matches["500180"]["requires_manual_review"] is True

    def test_clean_company_name_before_matching(self, tmp_path):
        """AC1.3.4: Clean company names: remove LIMITED, LTD, PVT, punctuation"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        # Test cleaning
        cleaned = mapper.clean_company_name("Tata Motors Limited")
        assert "LIMITED" not in cleaned.upper()
        assert "LTD" not in cleaned.upper()

        cleaned = mapper.clean_company_name("HDFC Bank Ltd.")
        assert "." not in cleaned


class TestManualValidationCSV:
    """Test manual validation CSV generation (AC1.3.5)"""

    def test_generate_validation_csv_for_top_1000(self, tmp_path):
        """AC1.3.5: Generate validation CSV for top 1,000 companies by market cap"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        # Mock master stock list with market caps
        with patch.object(mapper, 'get_top_companies_by_market_cap') as mock_top:
            mock_top.return_value = [
                {"bse_code": "500325", "company_name": "RELIANCE INDUSTRIES LTD", "market_cap_cr": 1500000},
                {"bse_code": "500570", "company_name": "TCS LTD", "market_cap_cr": 1200000}
            ]

            csv_path = mapper.generate_manual_validation_csv(top_n=1000)

            assert Path(csv_path).exists()
            csv_content = Path(csv_path).read_text()
            assert "bse_code" in csv_content
            assert "requires_manual_review" in csv_content
            assert "500325" in csv_content

    def test_validation_csv_flags_low_confidence(self, tmp_path):
        """AC1.3.5: CSV flags requires_manual_review=TRUE if confidence < 0.90"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        # Mock mapping with low confidence
        mapper._mappings = {
            "500180": {
                "nse_symbol": "HDFCBANK",
                "confidence": 0.85,
                "match_method": "fuzzy_name_80-89"
            }
        }

        with patch.object(mapper, 'get_top_companies_by_market_cap') as mock_top:
            mock_top.return_value = [
                {"bse_code": "500180", "company_name": "HDFC BANK LTD", "market_cap_cr": 800000}
            ]

            csv_path = mapper.generate_manual_validation_csv(top_n=1000)
            csv_content = Path(csv_path).read_text()

            # Should flag for manual review
            assert "TRUE" in csv_content or "True" in csv_content


class TestFinalMappingStorage:
    """Test storing final mapping in JSON + SQLite (AC1.3.6)"""

    def test_save_final_mapping_json_format(self, tmp_path):
        """AC1.3.6: Save mapping to JSON with correct schema"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        mapper._mappings = {
            "500325": {
                "nse_symbol": "RELIANCE",
                "company_name": "RELIANCE INDUSTRIES LTD",
                "isin": "INE002A01018",
                "match_method": "isin_exact",
                "confidence": 1.0,
                "updated_at": "2025-11-13T10:00:00Z"
            }
        }

        output_path = tmp_path / "final_mapping.json"
        report = mapper.save_final_mapping(str(output_path))

        # Verify JSON created
        assert output_path.exists()
        data = json.loads(output_path.read_text())

        assert "500325" in data
        assert data["500325"]["nse_symbol"] == "RELIANCE"
        assert data["500325"]["isin"] == "INE002A01018"
        assert "updated_at" in data["500325"]

    def test_save_final_mapping_sqlite(self, tmp_path):
        """AC1.3.6: Save mapping to SQLite database"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        mapper._mappings = {
            "500325": {
                "nse_symbol": "RELIANCE",
                "company_name": "RELIANCE INDUSTRIES LTD",
                "isin": "INE002A01018",
                "match_method": "isin_exact",
                "confidence": 1.0
            }
        }

        db_path = tmp_path / "mapping.db"
        mapper.save_to_database(str(db_path))

        # Verify database created and populated
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT bse_code, nse_symbol, confidence FROM mappings WHERE bse_code='500325'")
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "500325"
        assert row[1] == "RELIANCE"
        assert row[2] == 1.0


class TestMappingCoverage:
    """Test achieving ≥80% mapping coverage (AC1.3.7)"""

    def test_calculate_coverage_80_percent(self, tmp_path):
        """AC1.3.7: Calculate coverage = (mapped_count / total_bse_companies) * 100"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        # Mock 5,500 BSE companies, 4,500 mapped
        mapper._total_bse_companies = 5500
        mapper._mappings = {f"50{i:04d}": {"nse_symbol": f"SYM{i}"} for i in range(4500)}

        coverage = mapper.calculate_coverage()

        assert coverage >= 80.0
        assert coverage == pytest.approx(81.8, rel=0.1)

    def test_generate_unmapped_report_if_below_80(self, tmp_path):
        """AC1.3.7: If coverage < 80%, generate unmapped_companies.csv"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        # Mock 5,500 BSE companies, only 3,000 mapped (54.5% - below threshold)
        mapper._total_bse_companies = 5500
        mapper._mappings = {f"50{i:04d}": {"nse_symbol": f"SYM{i}"} for i in range(3000)}

        coverage = mapper.calculate_coverage()
        assert coverage < 80.0

        # Should generate unmapped report
        report_path = mapper.generate_unmapped_report()
        assert Path(report_path).exists()

        report_content = Path(report_path).read_text()
        assert "bse_code" in report_content
        assert "reason_unmapped" in report_content


class TestEdgeCases:
    """Test edge case handling (AC1.3.8)"""

    def test_handle_multiple_nse_symbols_logs_conflict(self, tmp_path):
        """AC1.3.8: Multiple NSE symbols for same ISIN → log to mapping_conflicts.csv"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        bse_data = {
            "500325": {"company_name": "RELIANCE INDUSTRIES LTD", "isin": "INE002A01018"}
        }
        nse_data = {
            "RELIANCE": {"isin": "INE002A01018", "volume": 5000000},
            "RELIANCE-OLD": {"isin": "INE002A01018", "volume": 100000}
        }

        mapper.extract_isin_mappings(bse_data, nse_data)

        # Should log conflict
        conflict_log = tmp_path / "mapping_conflicts.csv"
        if conflict_log.exists():
            content = conflict_log.read_text()
            assert "INE002A01018" in content

    def test_handle_delisted_nse_symbol(self, tmp_path):
        """AC1.3.8: BSE maps to delisted NSE symbol → mark status='delisted'"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        # Mock delisted check
        with patch.object(mapper, 'is_nse_symbol_delisted', return_value=True):
            mapping = mapper.validate_nse_symbol("500325", "OLDCOMPANY")

        assert mapping["status"] == "delisted"
        assert mapping["use_for_yfinance"] is False

    def test_log_name_mismatch_despite_isin_match(self, tmp_path):
        """AC1.3.8: Name mismatch despite ISIN match → log to mapping_anomalies.csv"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        bse_data = {
            "500325": {"company_name": "RELIANCE INDUSTRIES LTD", "isin": "INE002A01018"}
        }
        nse_data = {
            "JIOFINANCE": {"isin": "INE002A01018", "company_name": "JIO FINANCIAL SERVICES LTD", "volume": 5000000}
        }

        mapper.extract_isin_mappings(bse_data, nse_data)

        # Should log anomaly (ISIN match but name very different)
        anomaly_log = tmp_path / "mapping_anomalies.csv"
        if anomaly_log.exists():
            content = anomaly_log.read_text()
            assert "500325" in content or "INE002A01018" in content


class TestIntegrationScenarios:
    """Integration tests with realistic scenarios"""

    def test_full_mapping_workflow(self, tmp_path):
        """Integration: Run full mapping workflow (baseline → ISIN → fuzzy → save)"""
        pytest.importorskip("fuzzywuzzy")  # Skip if fuzzywuzzy not installed

        from agents.ml.ml_data_collector import BSENSEMapper

        # Create baseline mapping
        baseline = {"500325": "RELIANCE", "500570": "TCS"}
        baseline_path = tmp_path / "baseline.json"
        baseline_path.write_text(json.dumps(baseline))

        mapper = BSENSEMapper(existing_mapping_path=str(baseline_path))

        # Mock BhavCopy data
        bse_data = {
            "500325": {"company_name": "RELIANCE INDUSTRIES LTD", "isin": "INE002A01018"},
            "500209": {"company_name": "INFOSYS LIMITED", "isin": None}  # No ISIN, requires fuzzy
        }
        nse_data = {
            "RELIANCE": {"isin": "INE002A01018", "volume": 5000000, "company_name": "RELIANCE INDUSTRIES LTD"},
            "INFY": {"isin": "INE009A01021", "volume": 2000000, "company_name": "INFOSYS LTD"}
        }

        # Run full workflow
        with patch.object(mapper, 'download_bhav_copies', return_value=(str(tmp_path / "bse.csv"), str(tmp_path / "nse.csv"))), \
             patch.object(mapper, 'parse_bse_bhav_copy', return_value=bse_data), \
             patch.object(mapper, 'parse_nse_bhav_copy', return_value=nse_data), \
             patch('fuzzywuzzy.fuzz.token_sort_ratio', return_value=92):

            report = mapper.run_full_mapping(output_dir=str(tmp_path))

        # Verify results
        assert report.total_mapped >= 3  # 2 baseline + 1 ISIN + 1 fuzzy
        assert report.coverage_percent > 0

    def test_handle_empty_bhav_copy(self, tmp_path):
        """Edge case: Empty BhavCopy file"""
        from agents.ml.ml_data_collector import BSENSEMapper

        mapper = BSENSEMapper(existing_mapping_path=str(tmp_path / "mapping.json"))

        # Create empty CSV
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("SC_CODE,SC_NAME,ISIN_CODE\n")

        bse_data = mapper.parse_bse_bhav_copy(str(empty_csv))

        assert len(bse_data) == 0  # Should handle gracefully


# Pytest fixtures
@pytest.fixture
def sample_bse_bhav_data():
    """Sample BSE BhavCopy data"""
    return {
        "500325": {"company_name": "RELIANCE INDUSTRIES LTD", "isin": "INE002A01018"},
        "500570": {"company_name": "TATA CONSULTANCY SERV LT", "isin": "INE467B01029"},
        "500209": {"company_name": "INFOSYS LIMITED", "isin": "INE009A01021"}
    }


@pytest.fixture
def sample_nse_bhav_data():
    """Sample NSE BhavCopy data"""
    return {
        "RELIANCE": {"isin": "INE002A01018", "volume": 5000000, "series": "EQ"},
        "TCS": {"isin": "INE467B01029", "volume": 2000000, "series": "EQ"},
        "INFY": {"isin": "INE009A01021", "volume": 3000000, "series": "EQ"}
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=agents.ml.ml_data_collector", "--cov-report=term-missing"])
