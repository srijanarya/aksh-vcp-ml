# Story 2.5: Feature Selection

**Story ID**: 2.5
**Epic**: Epic 2 - Feature Engineering
**Priority**: P0 (Critical Path)
**Estimated Effort**: 2 days
**Status**: In Progress
**Dependencies**:
- Stories 2.1-2.4 (All features extracted) - COMPLETE ✅

---

## Story Goal

Reduce the 42 extracted features to 20-30 most important features using correlation analysis and feature importance metrics, creating a final optimized feature set for model training.

---

## Background

We now have **42 features** from Stories 2.1-2.4:
- ✅ 13 technical features
- ✅ 15 financial features
- ✅ 8 sentiment features
- ✅ 6 seasonality features

**Challenge**: Too many features can lead to:
1. Overfitting in ML models
2. Slower training times
3. Multicollinearity issues
4. Harder to interpret model decisions

**Goal**: Select 20-30 best features that maximize predictive power while minimizing redundancy.

---

## Acceptance Criteria

### AC2.5.1: Feature Combination
- [ ] Load all features from 4 databases into single DataFrame
- [ ] Merge on `(bse_code, date)` keys
- [ ] Handle missing values (impute or flag)
- [ ] Output combined dataset with 42 features + label

### AC2.5.2: Correlation Analysis
- [ ] Calculate pairwise feature correlations
- [ ] Identify highly correlated pairs (|r| > 0.85)
- [ ] Remove redundant features (keep one from each pair)
- [ ] Generate correlation heatmap

### AC2.5.3: Feature Importance (Simple)
- [ ] Calculate feature variances (remove zero-variance features)
- [ ] Calculate feature-target correlation
- [ ] Rank features by importance
- [ ] Select top 20-30 features

### AC2.5.4: Final Feature List
- [ ] Output final feature list (20-30 features)
- [ ] Save to `selected_features.json`
- [ ] Document selection rationale
- [ ] Generate feature selection report

### AC2.5.5: Validation
- [ ] Verify no duplicate features
- [ ] Verify all features have valid data
- [ ] Check feature distributions
- [ ] Cross-validate on train/test split

---

## Technical Specifications

### FeatureSelector Class

```python
class FeatureSelector:
    def __init__(
        self,
        technical_db_path: str,
        financial_db_path: str,
        sentiment_db_path: str,
        seasonality_db_path: str,
        labels_db_path: str
    ):
        """Initialize with all feature database paths"""

    def combine_features(self) -> pd.DataFrame:
        """Combine all features into single DataFrame"""

    def remove_correlated_features(
        self,
        df: pd.DataFrame,
        threshold: float = 0.85
    ) -> List[str]:
        """Remove highly correlated features"""

    def calculate_feature_importance(
        self,
        df: pd.DataFrame,
        target: str = 'upper_circuit'
    ) -> pd.DataFrame:
        """Calculate simple feature importance metrics"""

    def select_features(
        self,
        target_count: int = 25
    ) -> List[str]:
        """Select final feature set"""

    def save_selected_features(
        self,
        features: List[str],
        output_path: str
    ):
        """Save selected features to JSON"""
```

---

## Feature Selection Process

### Step 1: Load and Combine (AC2.5.1)
```python
# Load from 4 databases
technical_df = load_features(technical_db)
financial_df = load_features(financial_db)
sentiment_df = load_features(sentiment_db)
seasonality_df = load_features(seasonality_db)
labels_df = load_labels(labels_db)

# Merge on (bse_code, date)
combined = technical_df.merge(financial_df, on=['bse_code', 'date'])
combined = combined.merge(sentiment_df, on=['bse_code', 'date'])
combined = combined.merge(seasonality_df, on=['bse_code', 'date'])
combined = combined.merge(labels_df, on=['bse_code', 'date'])
```

### Step 2: Correlation Analysis (AC2.5.2)
```python
# Calculate correlations
corr_matrix = combined.corr().abs()

# Find pairs with |r| > 0.85
high_corr_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        if corr_matrix.iloc[i, j] > 0.85:
            high_corr_pairs.append((cols[i], cols[j], corr_matrix.iloc[i, j]))

# Remove one from each pair (keep feature with higher target correlation)
features_to_remove = select_redundant_features(high_corr_pairs)
```

### Step 3: Feature Importance (AC2.5.3)
```python
# Calculate variance
variances = combined.var()
zero_var_features = variances[variances == 0].index.tolist()

# Calculate feature-target correlation
target_corrs = combined.corr()['upper_circuit'].abs().sort_values(ascending=False)

# Rank by importance
importance_df = pd.DataFrame({
    'feature': features,
    'target_corr': target_corrs,
    'variance': variances
})

# Select top features
selected = importance_df.nlargest(25, 'target_corr')['feature'].tolist()
```

---

## Output Format

### selected_features.json
```json
{
    "version": "1.0",
    "selection_date": "2025-11-13",
    "total_features_before": 42,
    "total_features_after": 25,
    "selection_method": "correlation_and_importance",
    "selected_features": [
        "rsi_14",
        "macd_histogram",
        "revenue_growth_yoy",
        "pat_growth_qoq",
        "net_profit_margin",
        "day0_reaction",
        "volume_spike_ratio",
        "is_q4",
        ...
    ],
    "removed_features": {
        "high_correlation": [
            {"feature": "bb_upper", "correlated_with": "bb_middle", "correlation": 0.92},
            ...
        ],
        "low_importance": [
            {"feature": "announcement_month", "target_corr": 0.02},
            ...
        ]
    },
    "feature_importance": [
        {"feature": "day0_reaction", "target_corr": 0.45, "rank": 1},
        {"feature": "volume_spike_ratio", "target_corr": 0.38, "rank": 2},
        ...
    ]
}
```

---

## Test Structure

1. `TestFeatureCombination` (3 tests)
   - Combine all databases
   - Verify merge correctness
   - Handle missing values

2. `TestCorrelationAnalysis` (3 tests)
   - Calculate correlation matrix
   - Identify high correlations
   - Remove redundant features

3. `TestFeatureImportance` (3 tests)
   - Calculate variance
   - Calculate target correlation
   - Rank features

4. `TestFeatureSelection` (3 tests)
   - Select top N features
   - Validate selection
   - Save to JSON

**Total Tests**: ~12 tests

---

## Timeline

**Estimated Effort**: 2 days
- Day 1: Combine features, correlation analysis
- Day 2: Feature importance, selection, validation

---

**Author**: VCP Financial Research Team
**Created**: 2025-11-13
