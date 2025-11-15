# VCP ML System - Implementation Roadmap

**Last Updated**: November 15, 2025
**Current Status**: Foundation Complete, Integration Phase Starting
**Timeline**: 4-6 weeks to full production

---

## 🎯 Executive Summary

This roadmap outlines the path to integrate the newly deployed ML prediction system with your existing VCP alert infrastructure, creating a unified intelligent trading alert platform.

**Current State**:
- ✅ ML API deployed on AWS (13.200.109.29:8002)
- ✅ VCP system running with Telegram/Gmail alerts
- ✅ 141/141 ML tests passing (F1: 0.73)
- ⏳ Systems operating independently

**Target State**:
- 🎯 Unified ML-enhanced alert system
- 🎯 Real-time predictions for all VCP detections
- 🎯 Intelligent alert filtering (reduce noise by 60%)
- 🎯 Coverage expansion: 100 → 11,000 stocks

---

## 📅 Phase 1: Foundation & Integration (Week 1-2)

### Week 1: Immediate Actions

#### Day 1-2: AWS & Infrastructure
**Owner**: DevOps/You
**Effort**: 2-4 hours

- [ ] **Open Port 8002** (Manual - AWS Console)
  - File: `OPEN_AWS_PORT_8002.md`
  - Follow step-by-step guide
  - Test external access
  - Verify all endpoints work

- [ ] **Deploy ML Alert Bridge**
  ```bash
  cd /Users/srijan/Desktop/aksh
  python3 agents/ml_alert_bridge.py
  ```
  - Test with existing VCP detections
  - Verify ML API calls work
  - Check Telegram message formatting

- [ ] **Setup Monitoring**
  ```bash
  # Add to crontab for auto-start
  @reboot cd /Users/srijan/Desktop/aksh && python3 agents/ml_alert_bridge.py > /tmp/ml_bridge.log 2>&1
  ```

**Deliverables**:
- ✅ Port 8002 accessible externally
- ✅ ML Alert Bridge running
- ✅ First ML-enhanced alert sent

---

#### Day 3-5: ML Model Deployment
**Owner**: ML Team/You
**Effort**: 1-2 days

**Task**: Replace placeholder ML API with actual trained models

**Step 1**: Train production model locally
```bash
cd /Users/srijan/Desktop/aksh
python3 agents/ml/baseline_trainer.py \
  --data-path data/training_data.db \
  --output-dir data/models/production