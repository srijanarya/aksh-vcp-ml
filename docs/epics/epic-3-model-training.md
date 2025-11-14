# Epic 3: Model Training & Hyperparameter Optimization

**Epic ID**: EPIC-3
**Priority**: P0 (Critical Path)
**Status**: Ready to Start
**Estimated Effort**: 15 days (18 days with buffer)
**Dependencies**: EPIC-2 (Feature Engineering) - COMPLETE ✅

---

## Epic Goal

Train and optimize ML models using 25 selected features from Epic 2 to predict upper circuit hits on earnings announcement days with F1 score ≥ 0.70 on test set.

---

## Success Criteria

1. **Baseline Performance**: F1 ≥ 0.60 (Logistic Regression or Random Forest)
2. **Advanced Performance**: F1 ≥ 0.65 (XGBoost/LightGBM/Neural Network)
3. **Tuned Performance**: F1 ≥ 0.70 (Best model after hyperparameter tuning)
4. **ROC-AUC**: ≥ 0.75 (threshold-independent performance)
5. **Model Registry**: All models versioned and metadata tracked
6. **Evaluation Report**: Comprehensive HTML report with visualizations

---

## Stories (5 total)

### Story 3.1: Baseline Models
- Logistic Regression + Random Forest
- Target F1 ≥ 0.60
- **Effort**: 3 days

### Story 3.2: Advanced Models
- XGBoost + LightGBM + Neural Network
- Target F1 ≥ 0.65
- **Effort**: 3 days

### Story 3.3: Hyperparameter Tuning
- Optuna optimization
- Target F1 ≥ 0.70
- **Effort**: 4 days

### Story 3.4: Model Evaluation
- Comprehensive metrics + SHAP
- HTML report generation
- **Effort**: 3 days

### Story 3.5: Model Persistence
- Model registry with versioning
- Save/load models
- **Effort**: 2 days

---

## File Structure

```
agents/ml/
├── baseline_trainer.py              # Story 3.1
├── advanced_trainer.py              # Story 3.2
├── hyperparameter_tuner.py          # Story 3.3
├── model_evaluator.py               # Story 3.4
└── model_registry.py                # Story 3.5

data/models/
├── baseline/
├── advanced/
├── tuned/
└── registry.db

tests/unit/
├── test_baseline_trainer.py
├── test_advanced_trainer.py
├── test_hyperparameter_tuner.py
├── test_model_evaluator.py
└── test_model_registry.py
```

---

**Total Duration**: 15 days + 3 day buffer = 18 days
**Next Epic**: Epic 4 - Production Deployment

**Author**: VCP Financial Research Team
**Created**: 2025-11-14
