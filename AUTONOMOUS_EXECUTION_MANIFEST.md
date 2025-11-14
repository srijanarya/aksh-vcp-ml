# Autonomous Execution Manifest

**System:** ML Upper Circuit Prediction - Blockbuster Results Predictor
**Methodology:** BMAD Method + Autonomous Multi-Agent Execution
**Status:** Ready for Autonomous Execution
**Date:** 2025-11-13

---

## 🤖 Autonomous Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  AUTONOMOUS EXECUTOR                         │
│                  (agents/autonomous_executor.py)              │
│                                                              │
│  Orchestrates: Epic → Stories → Phases → Agents             │
│  Checkpoint/Resume: For long-running tasks                  │
│  Circuit Breaker: Pause on 10 failures                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴───────────┬──────────────────┬────────────┐
        │                      │                  │            │
  ┌─────▼──────┐       ┌──────▼──────┐    ┌─────▼─────┐  ┌──▼───┐
  │  DevAgent  │       │ ReviewAgent │    │TestAgent  │  │PMAgent│
  │   (TDD)    │       │ (Quality)   │    │(Coverage) │  │(Specs)│
  └─────┬──────┘       └──────┬──────┘    └─────┬─────┘  └──┬───┘
        │                     │                  │           │
        └──────────┬──────────┴──────────────────┘           │
                   │                                          │
           ┌───────▼────────┐                        ┌───────▼────────┐
           │   TOOLS        │                        │   SKILLS       │
           │ (Reusable Fns) │                        │(Domain Logic)  │
           │                │                        │                │
           │ • BhavCopy     │                        │• PDF Extract   │
           │ • PDF DL       │                        │• Sentiment     │
           │ • ISIN Match   │                        │• VCP Integrate │
           │ • Fuzzy Match  │                        │• Tech Indic.   │
           │ • Rate Limit   │                        │• Circuit Detect│
           │ • DB Utils     │                        │                │
           │ • Validation   │                        │                │
           └────────────────┘                        └────────────────┘
                   │                                          │
                   └──────────────┬───────────────────────────┘
                                  │
                          ┌───────▼────────┐
                          │  MCP SERVERS   │
                          │  (External)    │
                          │                │
                          │ • yfinance     │
                          │ • Telegram     │
                          │ • BSE API      │
                          │ • NSE API      │
                          └────────────────┘
```

---

## 📦 Component Structure

### 1. Autonomous Executor (Orchestrator Layer)

**File:** `agents/autonomous_executor.py` (600 lines)

**Responsibilities:**
- Read epic/story markdown files
- Parse acceptance criteria and Definition of Done
- Spawn specialist agents via Task tool
- Track execution state with checkpoint/resume
- Generate execution reports

**Key Methods:**
```python
class AutonomousExecutor:
    execute_epic(epic_id: str, parallel: bool) -> Dict[str, ExecutionReport]
    execute_story(story_id: str, epic_id: str) -> ExecutionReport
    _spawn_dev_agent_write_tests(story_id, story_data) -> Dict
    _spawn_dev_agent_implement(story_id, story_data) -> Dict
    _spawn_review_agent(story_id, story_data) -> Dict
    _run_tests(test_file, with_coverage) -> Dict
    _verify_definition_of_done(story_id, story_data) -> Dict
```

**Usage:**
```bash
# Execute entire Epic 1 in parallel
python agents/autonomous_executor.py execute-epic epic-1-data-collection --parallel

# Execute single story
python agents/autonomous_executor.py execute-story EPIC1-S1 epic-1-data-collection
```

### 2. Specialist Agents (Execution Layer)

#### DevAgent (TDD Mode)

**Spawned by:** AutonomousExecutor
**Responsibility:** Write tests FIRST, then implement code
**Access to:** Tools, Skills, MCP servers
**Prompt Template:**
```
You are a DevAgent executing Story {story_id} using TDD.

USER STORY:
{user_story}

ACCEPTANCE CRITERIA:
{acceptance_criteria}

PHASE 1: Write Tests
- Create: {test_file_path}
- Write ≥20 test cases covering all ACs
- Use pytest with fixtures
- Mock external dependencies
- Target ≥90% coverage

TECHNICAL SPECS:
{technical_specs}

TOOLS AVAILABLE:
- bhav_copy_downloader
- pdf_downloader
- isin_matcher
- rate_limiter
- db_utils

SKILLS AVAILABLE:
- pdf_financial_extraction
- sentiment_analysis
- vcp_integration

Execute Phase 1 now. Return test file path when complete.
```

#### ReviewAgent (Quality Check)

**Spawned by:** AutonomousExecutor after implementation
**Responsibility:** Code review, suggest refactoring
**Checks:**
- Follows PEP8 (via ruff)
- Type hints present (via mypy)
- Docstrings complete
- Error handling robust
- No hardcoded secrets
- Follows 8 critical rules from architecture.md

#### TestAgent (Coverage Validation)

**Spawned by:** AutonomousExecutor after tests written
**Responsibility:** Run pytest, verify ≥90% coverage
**Outputs:**
- Coverage percentage
- List of uncovered lines
- Failing test details

#### PMAgent (SpecKit Generation)

**Spawned by:** For creating new epics/stories
**Responsibility:** Generate ultra-specific stories from high-level requirements
**Output:** Epic markdown with 6-7 stories, each with 7-8 ACs

### 3. Tools Library (Utility Layer)

**Location:** `tools/`

#### BhavCopy Downloader (`tools/bhav_copy_downloader.py`)

```python
def download_bse_bhav_copy(date: str, cache_dir: str = "/tmp/bhav_cache") -> str:
    """
    Download BSE BhavCopy CSV for given date.

    Args:
        date: Date in YYYY-MM-DD format
        cache_dir: Directory to cache downloaded files

    Returns:
        Path to downloaded CSV file

    Raises:
        HTTPError: If download fails (404 = non-trading day)

    Example:
        >>> csv_path = download_bse_bhav_copy("2024-10-15")
        >>> df = pd.read_csv(csv_path)
    """

def download_nse_bhav_copy(date: str, cache_dir: str = "/tmp/bhav_cache") -> str:
    """Download NSE BhavCopy CSV (requires special headers)"""

def parse_bhav_copy(csv_path: str, source: str = "bse") -> pd.DataFrame:
    """
    Parse BhavCopy CSV to standardized DataFrame.

    Returns DataFrame with columns:
    - code (BSE code or NSE symbol)
    - name (company name)
    - open, high, low, close
    - volume
    - prev_close
    - circuit_indicator
    """
```

#### PDF Downloader (`tools/pdf_downloader.py`)

```python
def download_pdf_with_retry(
    url: str,
    output_path: str,
    max_retries: int = 3,
    timeout: int = 30
) -> bool:
    """
    Download PDF with exponential backoff retry.

    Args:
        url: PDF URL (BSE format: https://www.bseindia.com/...)
        output_path: Where to save PDF
        max_retries: Number of retry attempts (default: 3)
        timeout: Request timeout in seconds (default: 30)

    Returns:
        True if successful, False otherwise

    Example:
        >>> success = download_pdf_with_retry(
        ...     "https://www.bseindia.com/...",
        ...     "/tmp/pdfs/500325_Q2_2024.pdf"
        ... )
    """

def cache_pdf(bse_code: str, quarter: str, year: int) -> Optional[str]:
    """Check if PDF already cached, return path if exists"""
```

#### ISIN Matcher (`tools/isin_matcher.py`)

```python
def build_isin_index(
    bse_bhav_path: str,
    nse_bhav_path: str
) -> Dict[str, Dict]:
    """
    Build ISIN→NSE symbol index from BhavCopy files.

    Returns:
        {
            "INE002A01018": {
                "bse_code": "500325",
                "nse_symbol": "RELIANCE",
                "company_name": "RELIANCE INDUSTRIES LTD"
            }
        }
    """

def match_by_isin(
    bse_code: str,
    isin_index: Dict[str, Dict]
) -> Optional[str]:
    """Return NSE symbol for BSE code via ISIN match"""
```

#### Fuzzy Name Matcher (`tools/fuzzy_name_matcher.py`)

```python
def clean_company_name(name: str) -> str:
    """
    Clean company name for fuzzy matching.

    Removes: LIMITED, LTD, PVT, punctuation
    Converts: Uppercase

    Example:
        >>> clean_company_name("Tata Motors Limited")
        'TATA MOTORS'
    """

def fuzzy_match_companies(
    target_name: str,
    candidates: Dict[str, str],  # {nse_symbol: company_name}
    threshold: float = 0.90
) -> List[Tuple[str, float]]:
    """
    Fuzzy match company name against candidates.

    Returns:
        List of (nse_symbol, confidence_score) sorted by score descending

    Example:
        >>> matches = fuzzy_match_companies("TATA MOTORS LTD", {...}, 0.90)
        >>> [(TATAMOTORS, 0.95), (TATAMTRDVR, 0.88)]
    """
```

#### Rate Limiter (`tools/rate_limiter.py`)

```python
class RateLimiter:
    """
    Token bucket rate limiter.

    Example:
        >>> bse_limiter = RateLimiter(rate=2.0, capacity=10)  # 2 req/sec, burst 10
        >>> bse_limiter.wait_if_needed()  # Blocks if limit exceeded
        >>> # Make BSE request
    """
    def __init__(self, rate: float, capacity: int):
        """rate: requests per second, capacity: burst size"""

    def wait_if_needed(self) -> float:
        """Block if rate limit exceeded, return wait time"""

@contextmanager
def respect_rate_limit(name: str = "default", rate: float = 1.0):
    """
    Context manager for rate limiting.

    Example:
        >>> with respect_rate_limit("yfinance", rate=1.0):
        ...     data = yf.download("RELIANCE.NS", ...)
    """
```

#### Database Utils (`tools/db_utils.py`)

```python
@contextmanager
def get_db_connection(db_path: str) -> sqlite3.Connection:
    """
    Context manager for SQLite connections.

    Example:
        >>> with get_db_connection("data/price_movements.db") as conn:
        ...     cursor = conn.execute("SELECT * FROM price_movements")
    """

def bulk_insert(
    conn: sqlite3.Connection,
    table: str,
    data: List[Tuple],
    batch_size: int = 1000
) -> int:
    """
    Bulk insert with batching for performance.

    Returns: Number of rows inserted
    """

def execute_query(
    db_path: str,
    query: str,
    params: Tuple = ()
) -> pd.DataFrame:
    """Execute query and return results as DataFrame"""
```

#### Validation Utils (`tools/validation_utils.py`)

```python
def validate_ohlc(
    open: float,
    high: float,
    low: float,
    close: float
) -> Tuple[bool, List[str]]:
    """
    Validate OHLC relationships.

    Returns: (is_valid, error_messages)

    Checks:
    - low ≤ open ≤ high
    - low ≤ close ≤ high
    - All positive
    """

def validate_financials(
    revenue_cr: float,
    pat_cr: float,
    opm: float,
    npm: float
) -> Tuple[bool, List[str]]:
    """
    Validate financial data quality.

    Checks:
    - Revenue > 0
    - -100% ≤ margins ≤ 100%
    """

def validate_date_range(
    start_date: str,
    end_date: str,
    max_years: int = 5
) -> Tuple[bool, str]:
    """Validate date range is reasonable"""
```

### 4. Skills Library (Domain Logic Layer)

**Location:** `skills/`

#### PDF Financial Extraction (`skills/pdf_financial_extraction.py`)

```python
def extract_financial_data(
    pdf_path: str,
    bse_code: str,
    quarter: str,
    year: int
) -> Optional[FinancialData]:
    """
    Wrapper around existing indian_pdf_extractor.py.

    Returns:
        FinancialData(
            revenue_cr: float,
            pat_cr: float,
            eps: float,
            opm: float,
            npm: float,
            extraction_confidence: float
        )

    Integrates with:
        - agents/indian_pdf_extractor.py (existing 80%+ success rate)
    """
```

#### Sentiment Analysis (`skills/sentiment_analysis.py`)

```python
def analyze_management_commentary(
    pdf_text: str,
    section: str = "management_discussion"
) -> float:
    """
    Analyze sentiment using FinBERT.

    Args:
        pdf_text: Full PDF text
        section: Section to analyze

    Returns:
        Sentiment score 0-1 (0=negative, 0.5=neutral, 1=positive)

    Uses:
        - transformers library (FinBERT model)
        - Cached to avoid recomputation
    """

def detect_forward_guidance_tone(pdf_text: str) -> float:
    """
    Detect tone in forward guidance sections.

    Searches for keywords: "outlook", "guidance", "future", "expect"
    Returns: 0 (negative), 0.5 (neutral), 1 (positive)
    """
```

#### VCP Integration (`skills/vcp_integration.py`)

```python
def get_vcp_features(
    nse_symbol: str,
    date: str,
    lookback_days: int = 180
) -> Dict[str, any]:
    """
    Integrate with existing vcp_detector.py.

    Returns:
        {
            "vcp_detected": bool,
            "vcp_stage": int (1-4),
            "volatility_contraction_depth": float
        }

    Integrates with:
        - /Users/srijan/vcp/agents/vcp_detector.py
    """
```

#### Technical Indicators (`skills/technical_indicators.py`)

```python
def calculate_rsi(
    prices: pd.Series,
    period: int = 14
) -> float:
    """Calculate RSI (Relative Strength Index)"""

def calculate_volume_spike_ratio(
    current_volume: float,
    historical_volumes: pd.Series,
    window: int = 30
) -> float:
    """Calculate volume spike ratio vs 30-day average"""

def calculate_distance_from_ma(
    current_price: float,
    prices: pd.Series,
    window: int = 50
) -> float:
    """Calculate distance from 50-day moving average (%)"""
```

#### Circuit Detection (`skills/circuit_detection.py`)

```python
def detect_upper_circuit(
    close: float,
    prev_close: float,
    circuit_limit: float,
    circuit_flag: str
) -> bool:
    """
    Detect if stock hit upper circuit.

    Criteria:
    1. Price increase ≥5%
    2. Either circuit_flag == 'C' OR close ≥ circuit_limit * 0.99

    Returns: True if both criteria met
    """

def count_previous_circuits(
    bse_code: str,
    date: str,
    lookback_months: int = 6,
    db_path: str = "data/price_movements.db"
) -> int:
    """Count upper circuits in last N months"""
```

### 5. MCP Servers (External Integration Layer)

**Location:** `mcp_servers/`

#### yfinance MCP Server (`mcp_servers/yfinance_server.py`)

```json
{
  "name": "yfinance",
  "version": "1.0.0",
  "capabilities": {
    "tools": [
      {
        "name": "get_stock_data",
        "description": "Fetch historical stock data from Yahoo Finance",
        "input_schema": {
          "type": "object",
          "properties": {
            "symbol": {"type": "string", "description": "NSE symbol (e.g., RELIANCE.NS)"},
            "start_date": {"type": "string"},
            "end_date": {"type": "string"}
          }
        }
      }
    ]
  }
}
```

#### Telegram MCP Server (`mcp_servers/telegram_server.py`)

```json
{
  "name": "telegram",
  "version": "1.0.0",
  "capabilities": {
    "tools": [
      {
        "name": "send_alert",
        "description": "Send alert to Telegram channel",
        "input_schema": {
          "type": "object",
          "properties": {
            "message": {"type": "string"},
            "channel_id": {"type": "string"}
          }
        }
      },
      {
        "name": "listen_for_bse_alerts",
        "description": "Listen for BSE earnings alerts from Telegram bot"
      }
    ]
  }
}
```

---

## 🚀 Autonomous Execution Workflow

### Phase 1: Epic Execution (Parallel Capable)

```bash
# Execute entire Epic 1 with parallel story execution
python agents/autonomous_executor.py execute-epic epic-1-data-collection --parallel
```

**What Happens:**
1. AutonomousExecutor reads `docs/epics/epic-1-data-collection.md`
2. Parses 6 stories with acceptance criteria
3. Identifies independent stories (Story 1.1, 1.2, 1.3 can run parallel)
4. Spawns 3 DevAgents in parallel via Task tool
5. Each DevAgent follows TDD: write tests → implement → review
6. Generates `docs/reports/epic-1_execution_report.md`

### Phase 2: Story Execution (TDD Workflow)

```bash
# Execute single story autonomously
python agents/autonomous_executor.py execute-story EPIC1-S1 epic-1-data-collection
```

**7-Phase TDD Workflow:**

#### Phase 1: Parse Story
- Read `docs/epics/epic-1-data-collection.md`
- Extract Story 1.1 section
- Parse 7 acceptance criteria
- Parse technical specifications
- Parse 7 Definition of Done items

#### Phase 2: Write Tests (RED)
```python
# Spawn DevAgent with prompt:
"""
Write tests for Story 1.1: MLDataCollectorAgent Orchestrator

Acceptance Criteria:
AC1: MLDataCollectorAgent class created at agents/ml/ml_data_collector.py
AC2: Agent coordinates 4 sub-collection tasks
AC3: Agent tracks progress in ml_collection_status.db
AC4: Agent provides progress reporting
AC5: Agent handles failures gracefully (retry 3x)
AC6: Agent respects rate limits
AC7: Agent validates outputs

Create: tests/unit/test_ml_data_collector.py
- Test AC1: test_init_creates_class()
- Test AC2: test_collect_all_data_orchestrates_4_tasks()
- Test AC3: test_progress_tracking_db_created()
- Test AC4: test_progress_reporting_every_100_companies()
- Test AC5: test_failure_handling_retry_3x()
- Test AC6: test_rate_limiting_05s_bse()
- Test AC7: test_output_validation()
... (≥20 tests total)

Use tools: db_utils, rate_limiter
Target: ≥90% coverage
"""
```

#### Phase 3: Run Tests (Expect Failures)
```bash
pytest tests/unit/test_ml_data_collector.py -v
# Output: 20 tests FAILED (expected - code not implemented yet)
```

#### Phase 4: Implement Code (GREEN)
```python
# Spawn DevAgent with prompt:
"""
Implement Story 1.1: MLDataCollectorAgent

Make these tests pass:
- tests/unit/test_ml_data_collector.py (20 tests)

Technical Specifications:
- Class: MLDataCollectorAgent
- Methods: __init__, collect_all_data, label_upper_circuits, ...
- Database: ml_collection_status.db with 3 tables
- Rate limiting: 0.5s BSE, 1s yfinance
- Retry: 3x exponential backoff

Create: agents/ml/ml_data_collector.py

Use tools from tools/:
- bhav_copy_downloader
- pdf_downloader
- rate_limiter
- db_utils

Use skills from skills/:
- pdf_financial_extraction
- circuit_detection
"""
```

#### Phase 5: Run Tests Again (GREEN)
```bash
pytest tests/unit/test_ml_data_collector.py -v --cov=agents.ml.ml_data_collector
# Output: 20 tests PASSED, Coverage: 92%
```

#### Phase 6: Code Review (REFACTOR)
```python
# Spawn ReviewAgent with prompt:
"""
Review: agents/ml/ml_data_collector.py

Check:
1. Follows PEP8 (run: ruff check)
2. Type hints present (run: mypy)
3. Docstrings complete
4. Error handling robust
5. No hardcoded secrets
6. Follows 8 critical rules from architecture.md

If issues found, provide refactoring suggestions.
"""
```

If refactor needed:
```python
# Spawn DevAgent with prompt:
"""
Refactor agents/ml/ml_data_collector.py

Suggestions from review:
- Add type hints to _handle_failure method
- Extract magic number 0.5 to constant RATE_LIMIT_BSE
- Add docstring to _validate_outputs

Ensure tests still pass after refactor.
"""
```

#### Phase 7: Verify Definition of Done
```python
# Check all 7 DoD items:
✓ Code implemented following TDD (Phase 2-5 complete)
✓ All 7 acceptance criteria passing (tests verify)
✓ Unit tests ≥90% coverage (92% achieved)
✓ Integration test: Collect 10 companies (run next)
✓ Code review passed (Phase 6 complete)
✓ Documentation complete (docstrings present)
✓ Linting passes (ruff, mypy clean)
```

### Phase 3: Checkpoint/Resume for Long Tasks

If execution interrupted (e.g., network failure during Phase 4):
```bash
# Resume from checkpoint
python agents/autonomous_executor.py execute-story EPIC1-S1 epic-1-data-collection
# Output: "Resuming from checkpoint: /tmp/ml_execution_checkpoints/EPIC1-S1_checkpoint.json"
# Continues from Phase 4 without repeating Phases 1-3
```

---

## 📊 Execution Metrics & Reporting

### Story-Level Report

After each story execution, generates:
```markdown
# Story Execution Report: EPIC1-S1

Status: SUCCESS
Duration: 3,245 seconds (54 minutes)

## Phases Completed
1. ✓ Epic Analysis (5s)
2. ✓ Story Planning (10s)
3. ✓ Test Writing (450s via DevAgent)
4. ✓ Code Implementation (2,100s via DevAgent)
5. ✓ Code Review (120s via ReviewAgent)
6. ✓ Integration Test (480s)
7. ✓ DoD Verification (80s)

## Test Results
- Coverage: 92%
- Tests Passed: 20/20
- ACs Verified: 7/7

## Artifacts Created
- agents/ml/ml_data_collector.py (1,250 lines)
- tests/unit/test_ml_data_collector.py (800 lines)
- data/ml_collection_status.db (3 tables)

## Errors
None
```

### Epic-Level Report

After epic execution, generates `docs/reports/epic-1_execution_report.md`:
```markdown
# Epic Execution Report: epic-1-data-collection

Generated: 2025-11-14T10:30:00

## Summary
- Total Stories: 6
- Successful: 6
- Failed: 0
- Success Rate: 100.0%
- Total Duration: 15,840s (4.4 hours)

## Story Results

### EPIC1-S1: SUCCESS
- Duration: 3,245s
- Test Coverage: 92%
- ACs Passed: 7/7

### EPIC1-S2: SUCCESS
- Duration: 4,120s
- Test Coverage: 94%
- ACs Passed: 7/7

### EPIC1-S3: SUCCESS
- Duration: 2,850s
- Test Coverage: 91%
- ACs Passed: 8/8

...

## Overall Metrics
- Average Test Coverage: 92.3%
- Total Code Written: 6,500 lines
- Total Tests Written: 3,200 lines
- Average Story Duration: 44 minutes
```

---

## 🎯 Next Immediate Actions

### 1. Execute Epic 1 Story 1.1 (MLDataCollectorAgent)

```bash
cd /Users/srijan/Desktop/aksh

# Option A: Fully autonomous (recommended)
python agents/autonomous_executor.py execute-story EPIC1-S1 epic-1-data-collection

# Option B: Manual verification at each phase
python agents/autonomous_executor.py execute-story EPIC1-S1 epic-1-data-collection --interactive
# Prompts for approval after each phase
```

### 2. Execute Remaining Epic 1 Stories

```bash
# Parallel execution (3 independent stories at once)
python agents/autonomous_executor.py execute-epic epic-1-data-collection --parallel

# Sequential (safer for first run)
python agents/autonomous_executor.py execute-epic epic-1-data-collection
```

### 3. Generate Epic 2-5 Stories

```bash
# Use PMAgent to generate Epic 2 stories
python agents/autonomous_executor.py generate-epic \
  --epic-id "epic-2-feature-engineering" \
  --template "docs/epics/epic-1-data-collection.md" \
  --requirements "Extract 25-30 features per company-quarter"
```

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Database paths
DB_BASE_PATH=/Users/srijan/Desktop/aksh/data
MODELS_PATH=/Users/srijan/Desktop/aksh/models
DATA_CACHE_PATH=/tmp/ml_cache

# Rate limits
RATE_LIMIT_BSE=0.5  # seconds between BSE requests
RATE_LIMIT_YFINANCE=1.0  # seconds between yfinance calls

# Execution settings
ENABLE_PARALLEL=true
MAX_CONCURRENT_TASKS=4
LOG_LEVEL=INFO

# API keys (if needed)
TELEGRAM_BOT_TOKEN=your_token_here
OPENAI_API_KEY=your_key_here  # For FinBERT/sentiment analysis
```

### Autonomous Executor Config

```python
# agents/autonomous_executor.py line 50
config = OrchestratorConfig(
    db_base_path="/Users/srijan/Desktop/aksh/data",
    models_path="/Users/srijan/Desktop/aksh/models",
    data_cache_path="/tmp/ml_cache",
    log_level="INFO",
    enable_parallel_execution=True,
    max_concurrent_tasks=4  # Spawn up to 4 DevAgents simultaneously
)
```

---

## 📈 Success Criteria

### Story-Level Success
- ✓ All acceptance criteria tests passing
- ✓ Test coverage ≥90%
- ✓ All Definition of Done items checked
- ✓ Code review passed (ruff, mypy clean)
- ✓ Integration test passed

### Epic-Level Success
- ✓ All 6 stories completed successfully
- ✓ Data quality validation: ≥4 of 5 checks passing
- ✓ Deliverables exist:
  - historical_upper_circuits.db (≥200K samples)
  - historical_financials.db (≥80K records)
  - price_movements.db (≥10M records)
  - bse_nse_mapping.json (≥80% coverage)
  - data_quality_validation_report.txt

---

## 🚨 Error Handling

### Circuit Breaker
- Triggers after 10 consecutive failures
- Pauses execution, saves checkpoint
- Sends admin alert
- Requires manual reset: `executor.reset_circuit_breaker()`

### Checkpoint Recovery
- Automatic checkpoint every phase completion
- Stored in `/tmp/ml_execution_checkpoints/{story_id}_checkpoint.json`
- Resume with same command: `execute-story EPIC1-S1 ...`

### Failure Reporting
- All errors logged to `logs/autonomous_execution.log`
- Story-level failures don't block epic execution
- Detailed error messages in execution reports

---

## 📚 Documentation References

- **PRD:** `docs/prd.md`
- **Architecture:** `docs/architecture.md`
- **Epic 1:** `docs/epics/epic-1-data-collection.md`
- **Roadmap:** `docs/IMPLEMENTATION_ROADMAP.md`
- **This Doc:** `AUTONOMOUS_EXECUTION_MANIFEST.md`

---

**Status:** Ready for Execution
**Last Updated:** 2025-11-13
**Estimated Epic 1 Duration:** 4-6 hours (with parallel execution)

🚀 **Start Autonomous Execution:**
```bash
python agents/autonomous_executor.py execute-epic epic-1-data-collection --parallel
```
