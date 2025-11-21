# ✅ A+ Quick Checklist
**Print this. Put it on your wall. Use it for EVERY project.**

---

## 🚦 Day 1: Project Start

- [ ] Copy template: `cp .claude/templates/NEW_PROJECT_TEMPLATE.md [PROJECT].md`
- [ ] Write hypothesis (one sentence): "If X, then Y"
- [ ] Define success metrics (3 quantitative metrics)
- [ ] Set kill criteria: `python tools/kill_criteria_checker.py setup`
- [ ] Create TodoWrite list for Week 1
- [ ] **NO PRODUCTION CODE YET**

**Time:** 2 hours

---

## 🧪 Day 2-3: Quick Validation

- [ ] Write `validation_test.py` (<100 lines, single file)
- [ ] Collect 50-100 samples (historical data)
- [ ] Run hypothesis validator:
  ```python
  from tools.hypothesis_validator import quick_validate
  result = quick_validate("hypothesis", predictor, outcome)
  result.print_report()
  ```
- [ ] Save results screenshot
- [ ] **STILL NO PRODUCTION CODE**

**Time:** 4 hours

---

## 📊 Day 4-5: Validation Report

- [ ] Create `WEEK_1_VALIDATION_REPORT.md`
- [ ] Include: correlation, p-value, sample size, win rate
- [ ] Add visualization (chart/graph)
- [ ] Check kill criteria: `python tools/kill_criteria_checker.py check`
- [ ] **DECISION: ✅ PROCEED / ⚠️ PIVOT / 🛑 STOP**

**Time:** 3 hours

---

## 🎯 Day 6-7: Commit

- [ ] Review results with fresh eyes
- [ ] Write down decision + reasoning
- [ ] **If STOP:** Archive and move to next idea
- [ ] **If PROCEED:** Plan Week 2 MVP (<500 lines)
- [ ] Sign commitment (put it in writing)

**Time:** 2 hours

---

## 📅 Every Friday: Weekly Checkpoint

- [ ] Run `/weekly-checkpoint` command
- [ ] Test on **fresh data** (not training set)
- [ ] Check kill criteria: `python tools/kill_criteria_checker.py check`
- [ ] Update TodoWrite with next week's tasks
- [ ] **If 2+ criteria fail: STOP immediately**

**Time:** 1 hour

---

## 🚨 NEVER BREAK THESE RULES

1. ⛔ **NO production code until Week 1 validation passes**
2. ⛔ **NO rationalizing weak results** (honor kill criteria)
3. ⛔ **NO skipping Friday checkpoints**
4. ⛔ **NO building infrastructure before MVP works**
5. ⛔ **NO changing success criteria after seeing results**

---

## ✅ A+ Achieved When:

- [ ] Week 1 validation done before infrastructure
- [ ] Kill criteria set on Day 1 (not after)
- [ ] Weekly checkpoints every Friday
- [ ] Stopped ≥1 project after validation failed
- [ ] Used TodoWrite every session
- [ ] Zero 3-month failures

**All 6 checks = Official A+ 🏆**

---

## 🆘 Emergency Contacts

**Tempted to skip validation?**
→ Read: `TECHNICAL_POST_MORTEM.md`
→ Remember: You wasted 3 months last time

**Validation failed but want to continue?**
→ Run: `python tools/kill_criteria_checker.py check`
→ Ask: "Am I rationalizing or is there signal?"
→ When in doubt: STOP

**Feeling stuck?**
→ Use: TodoWrite to break down task
→ Run: `/weekly-checkpoint`
→ Review: A+ Contract in `YOUR_A+_PLAYBOOK.md`

---

**Print this checklist. Follow it religiously. Get your A+. 🎓**
