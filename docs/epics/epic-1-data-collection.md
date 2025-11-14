# Epic 1: Historical Data Collection & Preparation

**Epic ID:** EPIC-1
**Status:** Ready for Development
**Priority:** P0 (Blocker)
**Estimated Effort:** 2 weeks
**Dependencies:** None (Foundation Epic)

## Epic Goal

Establish the ML training foundation by orchestrating multi-source data collection across 2-3 years (2022-2025) for all NSE/BSE listed companies (~11,000). The epic delivers labeled datasets identifying which stocks hit upper circuit after earnings announcements, fundamental financial metrics extracted from quarterly PDFs, price movement data from BhavCopy files, and improved BSE-NSE mapping from 33.9% to ≥80% coverage. Data quality validation ensures ≥90% complete feature vectors before training begins.

## Success Metrics

- ≥200,000 labeled samples collected (upper circuit Y/N)
- ≥80% BSE-NSE mapping coverage (from 33.9% baseline)
- ≥80% PDF extraction success rate for financial data
- ≥95% price data completeness (no more than 5% missing dates)
- Class balance: 5-15% upper circuits in labeled dataset
- Data validation: 100% pass on all 5 quality checks

## Technical Context

**Existing Assets to Leverage:**
- `indian_pdf_extractor.py` - 80%+ PDF extraction success rate
- `earnings_calendar.db` - Existing earnings announcement dates
- `bse_nse_mapping_current.json` - 392 mappings (33.9% baseline)

**New Assets to Create:**
- `ml_data_collector.py` - Orchestrator agent
- `historical_upper_circuits.db` - Training labels
- `historical_financials.db` - Quarterly financial data
- `price_movements.db` - Daily OHLCV + circuits
- `ml_collection_status.db` - Progress tracking

---

## Story 1.1: Create MLDataCollectorAgent Orchestrator

**Story ID:** EPIC1-S1
**Priority:** P0
**Estimated Effort:** 3 days
**Assignee:** ML Agent (TDD)

### User Story

**As a** ML System,
**I want** an orchestrator agent to coordinate all historical data collection tasks,
**so that** I can systematically collect 200K-300K labeled samples across 3 years without manual intervention.

### Acceptance Criteria

**AC1.1.1:** MLDataCollectorAgent class created at `/Users/srijan/Desktop/aksh/agents/ml_data_collector.py`
- Class inherits from `BaseAgent` (if exists) or standalone
- `__init__(self, config_path: str = ".env")` loads configuration
- Loads environment variables: `DB_BASE_PATH`, `RATE_LIMIT_BSE`, `RATE_LIMIT_YFINANCE`, `LOG_LEVEL`
- Sets up structured JSON logging with correlation ID per collection run
- Initializes connection to `ml_collection_status.db`

**AC1.1.2:** Agent coordinates 4 sub-collection tasks in sequence
- Method: `collect_all_data(bse_codes: List[str], start_date: str, end_date: str) -> CollectionReport`
- Sub-task 1: `label_upper_circuits(bse_codes, start_date, end_date)` - Calls UpperCircuitLabeler
- Sub-task 2: `improve_bse_nse_mapping(bse_codes)` - Calls BSENSEMapper
- Sub-task 3: `extract_historical_financials(bse_codes, start_date, end_date)` - Calls FinancialExtractor
- Sub-task 4: `collect_price_movements(bse_codes, start_date, end_date)` - Calls PriceCollector
- Each sub-task returns success count and failure list

**AC1.1.3:** Progress tracking in `ml_collection_status.db`
- Table `collection_runs`: `(run_id, start_time, end_time, total_companies, completed, failed, status)`
- Table `company_status`: `(run_id, bse_code, task_name, status, error_message, timestamp)`
- Table `error_logs`: `(log_id, run_id, bse_code, task_name, error_type, error_message, stack_trace, timestamp)`
- Method: `get_progress_report(run_id: int) -> ProgressReport` returns current status

**AC1.1.4:** Progress reporting with real-time updates
- Method: `report_progress()` prints to stdout every 100 companies: "Processed 1,200/11,000 (10.9%) | Success: 1,150 | Failed: 50 | ETA: 2h 15m"
- ETA calculated from: `(total_companies - completed) * avg_time_per_company`
- Final report: `CollectionReport(total_samples=205,432, bse_nse_coverage=82.1%, extraction_success=81.5%, price_completeness=96.2%)`

**AC1.1.5:** Graceful failure handling with retry logic
- Retry 3x with exponential backoff: 1s, 2s, 4s
- If all retries fail, log to `error_logs` table, mark company as `failed` in `company_status`, continue to next company
- At end, generate `failure_summary.csv` with: `(bse_code, company_name, failed_tasks, error_messages)`

**AC1.1.6:** Rate limiting for external APIs
- Before BSE requests: `time.sleep(0.5)` (respects 0.5s rate limit)
- Before yfinance calls: `time.sleep(1.0)` (respects 1s rate limit)
- Use `RateLimiter` class with token bucket algorithm for burst handling

**AC1.1.7:** Output validation before marking complete
- For upper circuit labels: Check `label IS NOT NULL`, `price_change_pct IS NOT NULL`, `earnings_date` in range
- For financials: Check `revenue_cr > 0`, `-100 < npm < 100`, no duplicates on `(bse_code, quarter, year)`
- For price data: Check `open <= high`, `low <= close`, `volume > 0`, no future dates
- If validation fails, mark company as `validation_failed`, log specific check that failed

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml_data_collector.py`

**Key Methods:**
```python
class MLDataCollectorAgent:
    def __init__(self, config_path: str = ".env")
    def collect_all_data(self, bse_codes: List[str], start_date: str, end_date: str) -> CollectionReport
    def label_upper_circuits(self, bse_codes: List[str], start_date: str, end_date: str) -> TaskReport
    def improve_bse_nse_mapping(self, bse_codes: List[str]) -> TaskReport
    def extract_historical_financials(self, bse_codes: List[str], start_date: str, end_date: str) -> TaskReport
    def collect_price_movements(self, bse_codes: List[str], start_date: str, end_date: str) -> TaskReport
    def get_progress_report(self, run_id: int) -> ProgressReport
    def validate_outputs(self, bse_code: str) -> ValidationResult
```

**Dependencies:**
- `python-dotenv` - Load .env configuration
- `sqlite3` - Database operations
- `logging` - Structured logging
- `time` - Rate limiting
- `typing` - Type hints

**Test File:** `tests/unit/test_ml_data_collector.py`

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD (tests written first)
- [ ] All 7 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Integration test: Full collection run on 10 companies (2022-2025)
- [ ] Manual verification: Progress tracking updates in real-time
- [ ] Code review: Passes ruff linter, mypy type checking
- [ ] Documentation: Docstrings for all public methods

---

## Story 1.2: Build UpperCircuitLabeler to Identify Training Labels

**Story ID:** EPIC1-S2
**Priority:** P0
**Estimated Effort:** 4 days
**Assignee:** ML Agent (TDD)
**Dependencies:** EPIC1-S1 (MLDataCollectorAgent framework)

### User Story

**As a** ML Model,
**I want** labeled data identifying which earnings announcements led to upper circuits,
**so that** I can learn patterns that predict future upper circuit movements.

### Acceptance Criteria

**AC1.2.1:** UpperCircuitLabeler class created in `ml_data_collector.py`
- Class: `UpperCircuitLabeler` with method: `label_upper_circuits(bse_code: str, date_range: Tuple[str, str]) -> List[UpperCircuitLabel]`
- UpperCircuitLabel dataclass: `@dataclass class UpperCircuitLabel: bse_code: str, nse_symbol: str, earnings_date: date, next_day_date: date, price_change_pct: float, hit_circuit: bool, label: int`
- Method returns list of all labeled earnings for company in date range

**AC1.2.2:** Fetch next-day price data from BhavCopy CSV
- For each earnings date in `earnings_calendar.db`, identify next trading day (skip weekends/holidays)
- Download BhavCopy CSV for next day: `https://www.bseindia.com/download/BhavCopy/Equity/EQ{DDMMYY}_CSV.ZIP`
- Parse CSV to extract: `SC_CODE` (BSE code), `SC_NAME`, `OPEN`, `HIGH`, `LOW`, `CLOSE`, `NO_OF_SHRS` (volume), `TDCLOINDI` (circuit indicator)
- Cache downloaded BhavCopy files in `/tmp/bhav_copy_cache/` to avoid re-download

**AC1.2.3:** Label as upper circuit based on dual criteria
- **Criteria A:** Price increase ≥5%: `price_change_pct = ((close - prev_close) / prev_close) * 100 >= 5.0`
- **Criteria B:** Circuit hit: `TDCLOINDI == 'C'` (circuit flag in BhavCopy) OR `close >= circuit_limit * 0.99` (within 1% of limit)
- **Label Logic:** `label = 1` if BOTH criteria met, else `label = 0`
- Handle edge cases: If `prev_close` unavailable, fetch from `price_movements.db`

**AC1.2.4:** Store labels in `historical_upper_circuits.db`
- Schema:
```sql
CREATE TABLE IF NOT EXISTS upper_circuit_labels (
    sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bse_code TEXT NOT NULL,
    nse_symbol TEXT,
    earnings_date DATE NOT NULL,
    next_day_date DATE NOT NULL,
    price_change_pct REAL,
    hit_circuit BOOLEAN,
    label INTEGER NOT NULL CHECK(label IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bse_code, earnings_date)
);
```
- Use `INSERT OR REPLACE` for idempotency
- Bulk insert in batches of 1,000 for performance

**AC1.2.5:** Collect ≥200,000 labeled samples
- Query all companies from master list (~11,000 BSE codes)
- For each company, query `earnings_calendar.db` for announcements in 2022-01-01 to 2025-11-13
- Expected: ~18 quarters × 11,000 companies = ~198,000 potential samples
- Account for data availability: Some companies may have <18 quarters (new listings, delistings)
- Target: ≥200,000 after filtering for data availability

**AC1.2.6:** Validate class distribution in expected range
- After labeling complete, calculate: `positive_ratio = COUNT(label=1) / COUNT(*) * 100`
- Expected range: 5% ≤ positive_ratio ≤ 15%
- If `positive_ratio < 5%`: Log WARNING "Class imbalance severe: {positive_ratio}%. Upper circuits may be under-represented. Consider relaxing criteria (e.g., ≥3% price change)."
- If `positive_ratio > 15%`: Log WARNING "Class imbalance low: {positive_ratio}%. Upper circuit criteria may be too lenient. Consider stricter criteria (e.g., ≥7% price change)."
- If outside range, generate report with distribution by year/quarter for investigation

**AC1.2.7:** Handle missing data gracefully
- If BhavCopy unavailable for next day (e.g., trading halt, holiday spillover): Try next available trading day (up to 5 days)
- If still no data after 5 days: Skip labeling, log to `unlabeled_samples.csv` with reason
- If `prev_close` unavailable: Fetch from yfinance as fallback, mark source as "yfinance_fallback"

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml_data_collector.py`

**Key Methods:**
```python
class UpperCircuitLabeler:
    def __init__(self, db_path: str)
    def label_upper_circuits(self, bse_code: str, date_range: Tuple[str, str]) -> List[UpperCircuitLabel]
    def fetch_next_trading_day(self, date: str, max_days: int = 5) -> Optional[str]
    def download_bhav_copy(self, date: str) -> str  # Returns path to CSV
    def parse_bhav_copy(self, csv_path: str, bse_code: str) -> Optional[BhavCopyRecord]
    def calculate_price_change(self, close: float, prev_close: float) -> float
    def check_circuit_hit(self, record: BhavCopyRecord) -> bool
    def store_labels(self, labels: List[UpperCircuitLabel]) -> int  # Returns count inserted
    def validate_class_distribution(self) -> ClassDistributionReport
```

**Dependencies:**
- `requests` - Download BhavCopy ZIP files
- `zipfile` - Extract CSV from ZIP
- `pandas` - Parse BhavCopy CSV
- `sqlite3` - Database operations

**Test File:** `tests/unit/test_upper_circuit_labeler.py`

**Test Cases:**
- Test upper circuit labeling: Price +6%, circuit hit → label=1
- Test no circuit labeling: Price +6%, no circuit → label=0
- Test below threshold: Price +3%, circuit hit → label=0
- Test missing BhavCopy: Falls back to next trading day
- Test class distribution validation: 8% positive → PASS
- Test class distribution warning: 3% positive → WARNING logged

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 7 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Integration test: Label 100 real earnings (2024 Q1) and validate against manual check of 10 samples
- [ ] Performance test: Label 11,000 companies in <6 hours
- [ ] Class distribution validation: Confirm 5-15% range on test set
- [ ] Code review: Passes linter, type checking
- [ ] Documentation: Algorithm documented with example BhavCopy parsing logic

---

## Story 1.3: Improve BSE-NSE Mapping from 33.9% to ≥80%

**Story ID:** EPIC1-S3
**Priority:** P0
**Estimated Effort:** 3 days
**Assignee:** ML Agent (TDD)
**Dependencies:** None (can run parallel with EPIC1-S1, EPIC1-S2)

### User Story

**As a** Price Data Fetcher,
**I want** accurate BSE-to-NSE symbol mapping for ≥80% of companies,
**so that** I can fetch price/volume data via yfinance for training and inference.

### Acceptance Criteria

**AC1.3.1:** Read existing baseline mapping
- Load `/Users/srijan/Desktop/aksh/bse_nse_mapping_current.json`
- Current format: `{bse_code: nse_symbol}` (392 entries)
- Convert to new format: `{bse_code: {nse_symbol, company_name, isin, match_method, confidence}}`
- Preserve existing 392 mappings, mark with `match_method: "existing_baseline"`, `confidence: 1.0`

**AC1.3.2:** Fetch latest BhavCopy files for ISIN extraction
- Download latest BSE BhavCopy: `https://www.bseindia.com/download/BhavCopy/Equity/EQ{DDMMYY}_CSV.ZIP`
- Download latest NSE BhavCopy: `https://archives.nseindia.com/content/historical/EQUITIES/{YEAR}/_{MONTH}/cm{DDMMM YYYY}bhav.csv.zip`
- Parse BSE BhavCopy columns: `SC_CODE` (BSE code), `SC_NAME` (company name), `SC_ISIN` (ISIN)
- Parse NSE BhavCopy columns: `SYMBOL` (NSE symbol), `ISIN`, `SERIES` (only use "EQ" equity series)

**AC1.3.3:** ISIN-based matching strategy
- For each BSE code with ISIN in BSE BhavCopy:
  - Search NSE BhavCopy for matching ISIN
  - If exact ISIN match found: Map BSE code → NSE symbol, mark `match_method: "isin_exact"`, `confidence: 1.0`
  - If multiple NSE symbols for same ISIN: Choose symbol with highest trading volume, mark `confidence: 0.95`
- Expected coverage from ISIN matching: ~60-70% of companies

**AC1.3.4:** Fuzzy company name matching for remaining unmapped
- For BSE codes without ISIN match:
  - Use `fuzzywuzzy.fuzz.token_sort_ratio(bse_name, nse_name)` for all NSE symbols
  - Accept match if ratio ≥90 (high confidence)
  - Store top 3 candidates if ratio 80-89 (medium confidence, requires manual review)
  - Mark `match_method: "fuzzy_name_90"` or `"fuzzy_name_80-89"`, store ratio as `confidence: ratio/100`
- Clean company names before matching: Remove "LIMITED", "LTD", "PVT", punctuation, convert to uppercase
- Expected additional coverage: ~15-20%

**AC1.3.5:** Generate manual validation CSV for top 1,000 companies
- Query master stock list for top 1,000 by market cap
- For each, check if mapping exists, generate CSV: `(bse_code, bse_name, proposed_nse_symbol, nse_name, match_method, confidence, market_cap_cr, requires_manual_review)`
- `requires_manual_review = TRUE` if: `confidence < 0.90` OR `match_method == "fuzzy_name_80-89"`
- Save to `/Users/srijan/Desktop/aksh/data/mapping_validation_top1000.csv`
- User reviews CSV, adds "approved=YES/NO" column, returns corrected file

**AC1.3.6:** Store final mapping with metadata
- Schema in `bse_nse_mapping.json`:
```json
{
  "500325": {
    "nse_symbol": "RELIANCE",
    "company_name": "RELIANCE INDUSTRIES LTD",
    "isin": "INE002A01018",
    "match_method": "isin_exact",
    "confidence": 1.0,
    "updated_at": "2025-11-13T10:30:00Z"
  }
}
```
- Also store in SQLite `bse_nse_mapping.db` for query performance:
```sql
CREATE TABLE mappings (
    bse_code TEXT PRIMARY KEY,
    nse_symbol TEXT NOT NULL,
    company_name TEXT,
    isin TEXT,
    match_method TEXT,
    confidence REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**AC1.3.7:** Achieve ≥80% mapping coverage
- Target: ≥4,400 companies mapped out of ~5,500 BSE listed
- After ISIN + fuzzy matching, calculate: `coverage = (mapped_count / total_bse_companies) * 100`
- If `coverage < 80%`: Generate report identifying characteristics of unmapped companies (e.g., small-cap, recently listed, suspended)
- Log unmapped companies to `unmapped_companies.csv`: `(bse_code, company_name, market_cap_cr, listing_date, reason_unmapped)`

**AC1.3.8:** Handle edge cases and conflicts
- **Multiple NSE symbols for same ISIN:** Choose by highest volume, log to `mapping_conflicts.csv`
- **BSE symbol maps to delisted NSE symbol:** Mark as `status: "delisted"`, don't use for yfinance
- **Name mismatch despite ISIN match:** Log to `mapping_anomalies.csv` for investigation

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml_data_collector.py`

**Key Methods:**
```python
class BSENSEMapper:
    def __init__(self, existing_mapping_path: str)
    def download_bhav_copies(self) -> Tuple[str, str]  # Returns (bse_path, nse_path)
    def extract_isin_mappings(self, bse_csv: str, nse_csv: str) -> Dict[str, MappingCandidate]
    def fuzzy_match_names(self, unmapped_bse: List[str], nse_symbols: Dict[str, str]) -> Dict[str, List[MappingCandidate]]
    def generate_manual_validation_csv(self, top_n: int = 1000) -> str
    def apply_manual_corrections(self, validation_csv: str) -> int  # Returns count corrected
    def save_final_mapping(self, output_path: str) -> MappingReport
    def calculate_coverage(self) -> float
```

**Dependencies:**
- `fuzzywuzzy` - Fuzzy string matching
- `pandas` - CSV parsing
- `requests` - Download BhavCopy files

**Test File:** `tests/unit/test_bse_nse_mapper.py`

**Test Cases:**
- Test ISIN exact match: BSE 500325 (RELIANCE) → NSE RELIANCE via ISIN
- Test fuzzy name match: "TATA MOTORS LTD" → "TATAMOTORS" (ratio 92)
- Test ambiguous ISIN: Multiple NSE symbols → choose highest volume
- Test coverage calculation: 4,500/5,500 → 81.8%
- Test manual correction application: Load validation CSV, update mappings

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 8 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Integration test: Run full mapping on real BhavCopy files, validate coverage ≥80%
- [ ] Manual review: Top 100 mappings spot-checked by user, accuracy ≥95%
- [ ] Performance: Complete mapping in <30 minutes
- [ ] Output files generated: `bse_nse_mapping.json`, `mapping_validation_top1000.csv`, `unmapped_companies.csv`
- [ ] Code review: Passes linter, type checking

---

## Story 1.4: Extract Historical Financials from Quarterly PDFs

**Story ID:** EPIC1-S4
**Priority:** P0
**Estimated Effort:** 5 days
**Assignee:** ML Agent (TDD)
**Dependencies:** EPIC1-S1 (MLDataCollectorAgent framework)

### User Story

**As a** Feature Engineer,
**I want** historical quarterly financial data (Revenue, PAT, EPS, Margins) for 2-3 years,
**so that** I can calculate fundamental features like QoQ growth, YoY growth, and margin trends.

### Acceptance Criteria

**AC1.4.1:** Reuse existing `indian_pdf_extractor.py` via importable function
- Import: `from agents.indian_pdf_extractor import extract_financial_data`
- Function signature: `extract_financial_data(pdf_path: str, bse_code: str, quarter: str, year: int) -> Optional[FinancialData]`
- FinancialData dataclass: `@dataclass class FinancialData: revenue_cr: float, pat_cr: float, eps: float, opm: float, npm: float, extraction_confidence: float`
- If function doesn't exist in this form, create wrapper with this interface

**AC1.4.2:** Query earnings announcements from existing database
- Connect to `/Users/srijan/vcp/data/earnings_calendar.db` (existing database)
- Query: `SELECT bse_code, announcement_date, pdf_url FROM earnings WHERE announcement_date BETWEEN '2022-01-01' AND '2025-11-13'`
- Identify quarter from announcement_date: Q1 (Apr-Jun), Q2 (Jul-Sep), Q3 (Oct-Dec), Q4 (Jan-Mar)
- Expected: ~11,000 companies × ~14 quarters × ~70% availability = ~107,800 PDFs

**AC1.4.3:** Download and extract financial data with caching
- For each earnings announcement:
  - Check if already extracted: Query `historical_financials.db` for `(bse_code, quarter, year)`
  - If exists and `extraction_confidence ≥ 0.7`: Skip (already processed successfully)
  - If missing or low confidence: Download PDF to `/tmp/earnings_pdfs_cache/{bse_code}_{quarter}_{year}.pdf`
  - Call `extract_financial_data(pdf_path, bse_code, quarter, year)`
  - If extraction returns `None`: Log to `extraction_failures.csv`, continue to next

**AC1.4.4:** Store extracted data in `historical_financials.db`
- Schema:
```sql
CREATE TABLE IF NOT EXISTS historical_financials (
    financial_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bse_code TEXT NOT NULL,
    quarter TEXT NOT NULL CHECK(quarter IN ('Q1', 'Q2', 'Q3', 'Q4')),
    year INTEGER NOT NULL CHECK(year BETWEEN 2019 AND 2030),
    revenue_cr REAL CHECK(revenue_cr >= 0),
    pat_cr REAL,  -- Can be negative
    eps REAL,
    opm REAL CHECK(opm BETWEEN -100 AND 100),
    npm REAL CHECK(npm BETWEEN -100 AND 100),
    extraction_date DATE DEFAULT (date('now')),
    extraction_confidence REAL CHECK(extraction_confidence BETWEEN 0 AND 1),
    pdf_url TEXT,
    UNIQUE(bse_code, quarter, year)
);
CREATE INDEX idx_bse_quarter_year ON historical_financials(bse_code, quarter, year);
CREATE INDEX idx_year_quarter ON historical_financials(year, quarter);
```
- Use `INSERT OR REPLACE` for idempotency (reprocess if new PDF available)

**AC1.4.5:** Achieve ≥80% extraction success rate
- After processing all PDFs, calculate: `success_rate = (successful_extractions / total_pdfs_attempted) * 100`
- Target: `success_rate ≥ 80%`
- If `success_rate < 80%`: Analyze failure patterns in `extraction_failures.csv`
- Common failure reasons: "PDF encrypted", "Table format unrecognized", "Revenue not found", "Timeout after 30s"
- For failures, attempt manual extraction strategies: OCR (Tesseract), alternative table parsers (Tabula, Camelot)

**AC1.4.6:** Log extraction failures for investigation
- CSV schema: `(bse_code, company_name, quarter, year, pdf_url, error_type, error_message, attempted_at)`
- Error types: `"PDF_DOWNLOAD_FAILED"`, `"PDF_ENCRYPTED"`, `"TABLE_NOT_FOUND"`, `"REVENUE_MISSING"`, `"EXTRACTION_TIMEOUT"`
- Save to `/Users/srijan/Desktop/aksh/data/extraction_failures.csv`
- Generate summary report: Count by error_type, identify companies with >50% failure rate

**AC1.4.7:** Validate extracted data quality
- **Check 1: Revenue > 0** - Revenue must be positive non-zero
- **Check 2: Margin bounds** - `-100% ≤ OPM ≤ 100%` and `-100% ≤ NPM ≤ 100%`
- **Check 3: No duplicates** - Enforce UNIQUE constraint on `(bse_code, quarter, year)`
- **Check 4: EPS consistency** - If PAT and shares outstanding available, verify `EPS ≈ PAT / shares` (within 10% tolerance)
- If validation fails, mark `extraction_confidence = 0.5` (low confidence), flag for manual review
- Store validation results in `data_quality_issues.csv`: `(bse_code, quarter, year, failed_checks, values)`

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml_data_collector.py`

**Key Methods:**
```python
class FinancialExtractor:
    def __init__(self, db_path: str, cache_dir: str = "/tmp/earnings_pdfs_cache")
    def extract_all_financials(self, start_date: str, end_date: str) -> ExtractionReport
    def download_pdf(self, pdf_url: str, bse_code: str, quarter: str, year: int) -> str  # Returns local path
    def extract_from_pdf(self, pdf_path: str, bse_code: str, quarter: str, year: int) -> Optional[FinancialData]
    def store_financial_data(self, data: FinancialData, bse_code: str, quarter: str, year: int) -> bool
    def validate_financial_data(self, data: FinancialData) -> ValidationResult
    def calculate_success_rate(self) -> float
    def analyze_failures(self) -> FailureAnalysisReport
```

**Dependencies:**
- `agents.indian_pdf_extractor` - Existing PDF extraction logic
- `requests` - PDF download
- `sqlite3` - Database operations
- `pandas` - Data validation

**Test File:** `tests/unit/test_financial_extractor.py`

**Test Cases:**
- Test successful extraction: Valid PDF → FinancialData with confidence ≥0.8
- Test PDF download failure: 404 error → logged to failures CSV
- Test extraction failure: Encrypted PDF → logged with error_type "PDF_ENCRYPTED"
- Test data validation: Revenue = -100 → validation fails, confidence = 0.5
- Test duplicate handling: Same (bse_code, quarter, year) → UPDATE existing record
- Test success rate calculation: 8,500 success / 10,000 attempts → 85%

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 7 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Integration test: Extract 100 real PDFs (mixed Q1-Q4 2024), validate extracted values against manual check of 20 samples
- [ ] Performance test: Extract 10,000 PDFs in <12 hours (avg 4.3s per PDF)
- [ ] Success rate validation: Achieved ≥80% on test set
- [ ] Failure analysis report generated with breakdown by error type
- [ ] Code review: Passes linter, type checking

---

## Story 1.5: Collect Historical Price & Volume Data from BhavCopy

**Story ID:** EPIC1-S5
**Priority:** P0
**Estimated Effort:** 4 days
**Assignee:** ML Agent (TDD)
**Dependencies:** EPIC1-S3 (BSE-NSE mapping for yfinance fallback)

### User Story

**As a** Technical Feature Engineer,
**I want** historical daily price, volume, and circuit data for 2-3 years,
**so that** I can calculate technical features like RSI, volume spikes, previous circuits, and price momentum.

### Acceptance Criteria

**AC1.5.1:** Download BSE BhavCopy CSV files for all trading days
- Date range: 2022-01-01 to 2025-11-13 (approx. 960 trading days)
- URL pattern: `https://www.bseindia.com/download/BhavCopy/Equity/EQ{DDMMYY}_CSV.ZIP`
- Download strategy: Sequential with 0.5s delay between requests, retry 3x on failure
- Cache downloaded files in `/Users/srijan/Desktop/aksh/data/bhav_copy_cache/bse/EQ{DDMMYY}.csv`
- Skip download if file already cached (check by filename and size >0)

**AC1.5.2:** Download NSE BhavCopy CSV files for all trading days
- Date range: Same as BSE
- URL pattern: `https://archives.nseindia.com/content/historical/EQUITIES/{YEAR}/_{MONTH}/cm{DDMMMYYYY}bhav.csv.zip`
- NSE requires headers: `{"User-Agent": "Mozilla/5.0", "Accept": "text/html,application/xhtml+xml"}`
- Cache in `/Users/srijan/Desktop/aksh/data/bhav_copy_cache/nse/cm{DDMMMYYYY}.csv`
- Handle weekends/holidays: If download returns 404, mark date as non-trading day in `trading_calendar.db`

**AC1.5.3:** Parse CSV files and store in `price_movements.db`
- BSE BhavCopy columns: `SC_CODE, SC_NAME, OPEN, HIGH, LOW, CLOSE, NO_OF_SHRS, NET_TURNOV, TDCLOINDI`
- NSE BhavCopy columns: `SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, TOTTRDQTY, TOTTRDVAL, PREV_CLOSE`
- Schema:
```sql
CREATE TABLE IF NOT EXISTS price_movements (
    price_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bse_code TEXT,
    nse_symbol TEXT,
    date DATE NOT NULL,
    open REAL NOT NULL CHECK(open > 0),
    high REAL NOT NULL CHECK(high >= open),
    low REAL NOT NULL CHECK(low <= open),
    close REAL NOT NULL CHECK(close > 0),
    volume INTEGER NOT NULL CHECK(volume >= 0),
    prev_close REAL,
    circuit_limit REAL,
    hit_upper_circuit BOOLEAN,
    hit_lower_circuit BOOLEAN,
    source TEXT CHECK(source IN ('bse_bhav_copy', 'nse_bhav_copy', 'yfinance_fallback')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bse_code, date) ON CONFLICT REPLACE
);
CREATE INDEX idx_bse_date ON price_movements(bse_code, date);
CREATE INDEX idx_nse_date ON price_movements(nse_symbol, date);
CREATE INDEX idx_date ON price_movements(date);
```

**AC1.5.4:** Use yfinance API as fallback for missing dates
- After parsing all BhavCopy files, identify gaps: Companies with <95% date coverage
- For each gap, fetch from yfinance: `yf.download(nse_symbol + ".NS", start=gap_start, end=gap_end)`
- yfinance returns: `Date, Open, High, Low, Close, Volume, Adj Close`
- Map to price_movements schema, mark `source='yfinance_fallback'`
- Respect rate limit: 1 second between yfinance calls

**AC1.5.5:** Achieve ≥95% data completeness per company
- After collection, calculate per company: `completeness = (dates_with_data / expected_trading_days) * 100`
- Expected trading days: ~250 per year × 3.9 years = ~975 days (excluding weekends/holidays)
- Target: `completeness ≥ 95%` for ≥90% of companies
- If company has `completeness < 95%`: Log to `incomplete_price_data.csv` with gap analysis

**AC1.5.6:** Validate OHLC data quality
- **Check 1: OHLC relationships** - `low ≤ open ≤ high` and `low ≤ close ≤ high`
- **Check 2: Volume > 0** - Volume must be positive (0 indicates no trading, which is valid)
- **Check 3: No future dates** - `date ≤ today()`
- **Check 4: Price continuity** - If `abs(close - prev_close) / prev_close > 0.5` (50% jump), flag as potential data error or corporate action
- If validation fails, mark record with `data_quality_flag='ANOMALY'`, log to `price_data_anomalies.csv`

**AC1.5.7:** Create indexes for fast querying
- Indexes already defined in schema (AC1.5.3)
- Verify index creation: `PRAGMA index_list('price_movements');`
- Test query performance: `SELECT * FROM price_movements WHERE bse_code='500325' AND date BETWEEN '2024-01-01' AND '2024-12-31'` should return in <10ms

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml_data_collector.py`

**Key Methods:**
```python
class PriceCollector:
    def __init__(self, db_path: str, cache_dir: str = "/data/bhav_copy_cache")
    def collect_all_price_data(self, bse_codes: List[str], start_date: str, end_date: str) -> PriceCollectionReport
    def download_bse_bhav_copies(self, start_date: str, end_date: str) -> List[str]  # Returns cached file paths
    def download_nse_bhav_copies(self, start_date: str, end_date: str) -> List[str]
    def parse_bhav_copy(self, csv_path: str, source: str) -> pd.DataFrame
    def store_price_data(self, df: pd.DataFrame) -> int  # Returns rows inserted
    def fill_gaps_with_yfinance(self, bse_codes: List[str]) -> int  # Returns gaps filled
    def calculate_completeness(self) -> Dict[str, float]  # {bse_code: completeness%}
    def validate_ohlc_data(self) -> ValidationReport
```

**Dependencies:**
- `requests` - Download BhavCopy ZIP files
- `zipfile` - Extract CSV from ZIP
- `pandas` - CSV parsing and data validation
- `yfinance` - Fallback price data
- `sqlite3` - Database operations

**Test File:** `tests/unit/test_price_collector.py`

**Test Cases:**
- Test BSE BhavCopy download: Download 5 days, verify cached files exist
- Test NSE BhavCopy download: Handle 404 for weekend gracefully
- Test CSV parsing: Parse sample BhavCopy, validate DataFrame schema
- Test yfinance fallback: Mock yfinance, fill gap for 10 missing dates
- Test OHLC validation: `high < low` → validation fails, flagged as ANOMALY
- Test completeness calculation: 930/975 dates → 95.4% completeness

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 7 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Integration test: Collect price data for 50 companies (Jan 2024 - Dec 2024), validate completeness ≥95%
- [ ] Performance test: Process 960 BhavCopy files (3.9 years) in <4 hours
- [ ] Data quality validation: <1% anomalies flagged in test set
- [ ] Indexes verified: Query performance <10ms for typical queries
- [ ] Code review: Passes linter, type checking

---

## Story 1.6: Validate Data Quality Before Training

**Story ID:** EPIC1-S6
**Priority:** P0
**Estimated Effort:** 2 days
**Assignee:** ML Agent (TDD)
**Dependencies:** EPIC1-S2, EPIC1-S3, EPIC1-S4, EPIC1-S5 (all data collection tasks complete)

### User Story

**As a** ML System,
**I want** comprehensive data quality validation before training begins,
**so that** I don't train models on incomplete or invalid data.

### Acceptance Criteria

**AC1.6.1:** DataQualityValidator class with validation report method
- Class: `DataQualityValidator` with method: `validate_training_readiness() -> ValidationReport`
- ValidationReport dataclass:
```python
@dataclass
class ValidationReport:
    timestamp: datetime
    checks_passed: int
    checks_failed: int
    total_samples: int
    usable_companies: int
    estimated_model_f1: float  # Based on data quality heuristics
    checks: List[CheckResult]
    remediation_steps: List[str]
```
- CheckResult: `@dataclass class CheckResult: check_name: str, status: str, metric_value: float, threshold: float, passed: bool, details: str`

**AC1.6.2:** Check 1 - Verify ≥200,000 labeled samples
- Query: `SELECT COUNT(*) FROM historical_upper_circuits.upper_circuit_labels`
- Threshold: `count ≥ 200,000`
- If PASS: `CheckResult(check_name="Labeled Samples Count", status="PASS", metric_value=205432, threshold=200000, passed=True, details="Sufficient samples for training")`
- If FAIL: `CheckResult(check_name="Labeled Samples Count", status="FAIL", metric_value=185000, threshold=200000, passed=False, details="15,000 samples below threshold")`, add remediation: "Extend date range to 2021 or relax earnings filter"

**AC1.6.3:** Check 2 - Verify class distribution 5-15%
- Query: `SELECT (SUM(CASE WHEN label=1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS positive_ratio FROM upper_circuit_labels`
- Threshold: `5.0 ≤ positive_ratio ≤ 15.0`
- If PASS: `metric_value=8.3, passed=True`
- If FAIL (too low): `metric_value=3.2, passed=False, details="Class imbalance severe. SMOTE may struggle."`, remediation: "Relax upper circuit criteria to ≥3% price change"
- If FAIL (too high): `metric_value=18.5, passed=False, details="Class imbalance low. Labels may be too lenient."`, remediation: "Tighten criteria to ≥7% price change"

**AC1.6.4:** Check 3 - Verify ≥80% companies have complete financial data
- Query:
```sql
SELECT (COUNT(DISTINCT bse_code) * 100.0 / (SELECT COUNT(*) FROM master_stock_list)) AS coverage
FROM historical_financials
WHERE bse_code IN (
    SELECT bse_code FROM historical_financials
    GROUP BY bse_code
    HAVING COUNT(DISTINCT quarter || year) >= 12  -- At least 12 quarters (3 years)
)
```
- Threshold: `coverage ≥ 80.0`
- If FAIL: `metric_value=72.5, passed=False`, remediation: "Missing data for 825 companies. Prioritize large-cap for manual extraction or extend collection to Q1 2021."

**AC1.6.5:** Check 4 - Verify ≥95% price data completeness
- Query:
```sql
SELECT AVG(completeness) AS avg_completeness FROM (
    SELECT bse_code, (COUNT(DISTINCT date) * 100.0 / 975) AS completeness
    FROM price_movements
    WHERE date BETWEEN '2022-01-01' AND '2025-11-13'
    GROUP BY bse_code
)
```
- Threshold: `avg_completeness ≥ 95.0`
- If FAIL: `metric_value=91.2, passed=False`, remediation: "Run yfinance gap filling for 1,200 companies with <95% completeness"

**AC1.6.6:** Check 5 - Verify ≥80% BSE-NSE mapping coverage
- Query: `SELECT (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM master_stock_list)) AS mapping_coverage FROM bse_nse_mapping`
- Threshold: `mapping_coverage ≥ 80.0`
- If FAIL: `metric_value=76.5, passed=False`, remediation: "Run fuzzy matching with threshold=85 (lower from 90) or manual map top 500 unmapped companies"

**AC1.6.7:** Generate comprehensive validation report
- Report format:
```
========================================
DATA QUALITY VALIDATION REPORT
========================================
Timestamp: 2025-11-13 18:45:32 IST
Total Checks: 5
Passed: 4
Failed: 1

CHECK RESULTS:
[✓] Labeled Samples Count: 205,432 samples (threshold: ≥200,000)
[✓] Class Distribution: 8.3% positive (threshold: 5-15%)
[✗] Financial Data Coverage: 72.5% companies (threshold: ≥80%)
[✓] Price Data Completeness: 96.8% average (threshold: ≥95%)
[✓] BSE-NSE Mapping: 82.1% coverage (threshold: ≥80%)

OVERALL STATUS: FAIL (1 critical check failed)

USABLE DATA:
- Total Companies: 5,535
- Companies with Complete Data: 4,011 (72.5%)
- Total Labeled Samples: 205,432
- Usable Samples (with features): 182,340 (88.8%)

ESTIMATED MODEL PERFORMANCE:
Based on data quality heuristics:
- Expected F1: 0.67 (below target 0.70)
- Reason: Financial data coverage below 80% will limit feature quality

REMEDIATION STEPS:
1. Extend financial data collection to Q1 2021 to increase coverage
2. Prioritize manual extraction for top 1,000 companies by market cap
3. Consider training model on 72.5% companies first, expand coverage iteratively

========================================
```
- Save report to `/Users/srijan/Desktop/aksh/data/data_quality_validation_report.txt`

**AC1.6.8:** Provide actionable remediation steps
- If any check fails, generate prioritized list of actions:
  - **Priority 1 (Critical):** Checks that block training entirely (e.g., <100,000 samples)
  - **Priority 2 (High):** Checks that significantly impact model quality (e.g., <70% data coverage)
  - **Priority 3 (Medium):** Checks that moderately impact quality (e.g., class distribution at 4.5%)
- For each failed check, provide 2-3 concrete remediation options with estimated effort

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml_data_collector.py`

**Key Methods:**
```python
class DataQualityValidator:
    def __init__(self, db_paths: Dict[str, str])  # Paths to all 5 databases
    def validate_training_readiness(self) -> ValidationReport
    def check_labeled_samples_count(self) -> CheckResult
    def check_class_distribution(self) -> CheckResult
    def check_financial_data_coverage(self) -> CheckResult
    def check_price_data_completeness(self) -> CheckResult
    def check_bse_nse_mapping_coverage(self) -> CheckResult
    def estimate_model_performance(self, checks: List[CheckResult]) -> float  # Heuristic F1 estimate
    def generate_remediation_steps(self, failed_checks: List[CheckResult]) -> List[str]
    def save_report(self, report: ValidationReport, output_path: str)
```

**Dependencies:**
- `sqlite3` - Query all databases
- `pandas` - Data aggregation
- `typing` - Type hints for dataclasses

**Test File:** `tests/unit/test_data_quality_validator.py`

**Test Cases:**
- Test all checks pass: Mock databases with passing values → report status "PASS"
- Test samples count fails: 180,000 samples → FAIL, remediation includes "Extend date range"
- Test class distribution fails: 3% positive → FAIL, remediation includes "Relax criteria"
- Test multiple failures: 3 checks fail → Priority 1/2/3 remediation steps generated
- Test report generation: Verify report format matches specification
- Test F1 estimation: 90% data quality → estimated_f1 ≈ 0.72

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 8 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Integration test: Run validator on real collected data, verify report accuracy
- [ ] Manual review: Confirm remediation steps are actionable and correctly prioritized
- [ ] Report format verified: Human-readable with clear pass/fail indicators
- [ ] Code review: Passes linter, type checking
- [ ] Documentation: Validation logic documented with threshold justifications

---

## Epic Completion Criteria

All 6 stories (EPIC1-S1 through EPIC1-S6) must meet Definition of Done:

- [ ] All acceptance criteria passing for all stories
- [ ] ≥90% unit test coverage across all agents
- [ ] Integration tests passing: Full end-to-end data collection for 100 companies
- [ ] Data quality validation report shows: ≥4 of 5 checks passing
- [ ] Performance validated: Complete data collection for 11,000 companies in <7 days
- [ ] Deliverables exist:
  - `ml_data_collector.py` (orchestrator + 4 sub-agents)
  - `historical_upper_circuits.db` (≥200K samples)
  - `historical_financials.db` (≥80K quarterly records)
  - `price_movements.db` (≥10M daily records)
  - `bse_nse_mapping.json` (≥4,400 mappings, 80%+ coverage)
  - `data_quality_validation_report.txt` (comprehensive validation)

**Ready for Epic 2:** Feature Engineering Pipeline