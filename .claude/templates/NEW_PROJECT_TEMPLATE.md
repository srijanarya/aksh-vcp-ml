# 🎯 New Project: [PROJECT_NAME]

**Start Date:** [DATE]
**Success Deadline:** 30 days
**Kill Criteria Deadline:** Week 1

---

## 📋 WEEK 1: VALIDATION PHASE (NO CODE ALLOWED)

### Day 1: Define Hypothesis
**Time Budget:** 2 hours

- [ ] **Core Hypothesis:** [One sentence: "If X, then Y will happen"]
  - Example: "If stock has >50% QoQ growth, price will increase >3% in 3 days"

- [ ] **Success Criteria (Quantitative):**
  - Metric 1: ____________ (Target: ____)
  - Metric 2: ____________ (Target: ____)
  - Metric 3: ____________ (Target: ____)

- [ ] **Kill Criteria (When to STOP):**
  - If Metric 1 < ____ after Week 1 → STOP
  - If Metric 2 < ____ after Week 2 → STOP
  - If no edge by Week 3 → STOP or PIVOT

- [ ] **Baseline Comparison:**
  - What is "doing nothing" performance?
  - What is "random selection" performance?

---

### Day 2-3: Quick & Dirty Test
**Time Budget:** 4 hours
**Code Allowed:** <100 lines, single script only

```python
# validation_test.py - SIMPLE SCRIPT ONLY
# No classes, no agents, no infrastructure
# Just: Fetch data → Calculate → Report

def test_hypothesis():
    # 1. Get 50-100 samples (historical data)
    # 2. Calculate correlation
    # 3. Print results
    pass

if __name__ == "__main__":
    results = test_hypothesis()
    print(f"Correlation: {results.correlation}")
    print(f"Sample Size: {results.n}")
    print(f"P-value: {results.p_value}")

    # DECISION POINT
    if results.correlation > 0.3 and results.p_value < 0.05:
        print("✅ PROCEED TO WEEK 2")
    else:
        print("❌ STOP OR PIVOT")
```

**Deliverable:** `validation_test.py` + results report

---

### Day 4-5: Validation Report
**Time Budget:** 3 hours

Create: `WEEK_1_VALIDATION_REPORT.md`

```markdown
## Hypothesis Test Results

**Hypothesis:** [Repeat from Day 1]

**Results:**
- Correlation: ____
- P-value: ____
- Sample Size: ____
- Win Rate: ____% (vs ____ baseline)

**Statistical Significance:** YES / NO

**Visualization:** [Add simple chart/graph]

## Decision: ✅ PROCEED / ❌ STOP / ⚠️ PIVOT

**Reasoning:** [2-3 sentences]

**If Proceeding:**
- Expected signals per month: ____
- Expected win rate: ____%
- Expected ROI: ____%
- Time to profitability: ____ months

**Next Steps:** [Week 2 plan]
```

---

### Day 6-7: Review & Commit
**Time Budget:** 2 hours

- [ ] Review validation results with fresh eyes
- [ ] Check against kill criteria
- [ ] Make GO / NO-GO decision
- [ ] Commit to decision (don't rationalize weak results)

**MANDATORY CHECKPOINT:**
- If validation fails → STOP or PIVOT
- If validation passes → Proceed to Week 2
- **NO EXCEPTIONS** (this is the rule that makes you A+)

---

## 📋 WEEK 2: MVP PHASE (Minimal Infrastructure)

**ONLY START IF WEEK 1 PASSED**

### Goals:
- Build simplest possible working version
- <500 lines of code total
- Single file or max 3 files
- No agents, no fancy architecture
- Test on out-of-sample data

### Daily Validation:
- [ ] Monday: Core logic working
- [ ] Tuesday: Tested on validation set
- [ ] Wednesday: Results match Week 1 expectations
- [ ] Thursday: Error handling added
- [ ] Friday: Week 2 report (did MVP confirm Week 1?)

**Kill Criteria Check:**
- If MVP results << Week 1 results → STOP (false positive)
- If MVP results ≈ Week 1 results → PROCEED to Week 3

---

## 📋 WEEK 3: SCALE DECISION

### This Week's Question:
**"Should I build production infrastructure?"**

### Checklist:
- [ ] Week 1 validation: PASSED ✅
- [ ] Week 2 MVP: CONFIRMED ✅
- [ ] Out-of-sample test: PASSED ✅
- [ ] Baseline comparison: BEATING IT ✅
- [ ] ROI projection: POSITIVE ✅

**If all 5 checkboxes: YES → Build production system**
**If any NO → Stop or iterate MVP**

---

## 📋 WEEK 4+: BUILD PHASE

**ONLY START IF WEEKS 1-3 PASSED**

Now you can build all the fancy stuff:
- Multi-agent architecture
- Production deployment
- Comprehensive testing
- Full documentation

**Weekly Checkpoints:**
- Every Friday: Test on fresh data
- Results should match Week 1-2 expectations
- If diverging → Investigate immediately

---

## 🚨 MANDATORY RULES (Your A+ Contract)

### Rule 1: No Code in Week 1
**Exception:** Only `validation_test.py` (single file, <100 lines)
**Why:** Forces you to think, not build

### Rule 2: Honor Kill Criteria
**No rationalization allowed**
**Why:** Prevents sunk cost fallacy

### Rule 3: Use TodoWrite for Everything
**Every session starts with TodoWrite**
**Why:** Keeps you focused and on track

### Rule 4: Weekly Validation
**Fresh data test every Friday**
**Why:** Catches degradation early

### Rule 5: Public Commitment
**Share Week 1 results (even if failed)**
**Why:** Accountability prevents self-deception

---

## 📊 Success Metrics (For This Framework)

**You're using this correctly if:**
- ✅ Week 1 complete before any infrastructure code
- ✅ Kill criteria defined on Day 1
- ✅ Have validation report by Day 5
- ✅ Can explain "why this will work" with data, not intuition
- ✅ Have stopped at least one project after Week 1

**You're NOT using this correctly if:**
- ❌ Start building agents in Week 1
- ❌ Skip validation report
- ❌ Rationalize weak results to continue
- ❌ Haven't stopped any projects early
- ❌ Success criteria change after seeing results

---

## 🎯 This Template IS Your A+

**Use this template religiously, and you WILL:**
1. Save 2+ months per project (avoid building wrong things)
2. Have higher success rate (only build validated ideas)
3. Build portfolio of winners (not impressive failures)
4. Get to profitability faster (less wasted time)

---

**Template Version:** 1.0
**Created:** November 21, 2025
**Purpose:** Transform A- student to A+ by forcing validation-first workflow
