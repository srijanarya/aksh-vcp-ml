"""
Hypothesis Validator - Your A+ Safety Net

This tool FORCES you to validate hypotheses before building.
Use this at the start of EVERY new project.

Usage:
    python tools/hypothesis_validator.py --hypothesis "Stock growth predicts returns"
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class ValidationResult:
    """Results from hypothesis validation"""
    hypothesis: str
    correlation: float
    p_value: float
    sample_size: int
    win_rate: float
    baseline_win_rate: float
    effect_size: float
    confidence_interval: Tuple[float, float]
    decision: str  # "PROCEED", "STOP", "PIVOT"
    reasoning: str
    timestamp: str

    def to_dict(self) -> Dict:
        return {
            'hypothesis': self.hypothesis,
            'correlation': round(self.correlation, 4),
            'p_value': round(self.p_value, 6),
            'sample_size': self.sample_size,
            'win_rate': round(self.win_rate, 4),
            'baseline_win_rate': round(self.baseline_win_rate, 4),
            'effect_size': round(self.effect_size, 4),
            'confidence_interval': [round(ci, 4) for ci in self.confidence_interval],
            'decision': self.decision,
            'reasoning': self.reasoning,
            'timestamp': self.timestamp
        }

    def print_report(self) -> None:
        """Print human-readable validation report"""
        print("\n" + "="*70)
        print("🎯 HYPOTHESIS VALIDATION REPORT")
        print("="*70)

        print(f"\n📋 Hypothesis: {self.hypothesis}")
        print(f"📅 Date: {self.timestamp}")
        print(f"📊 Sample Size: {self.sample_size}")

        print(f"\n📈 STATISTICAL RESULTS:")
        print(f"  • Correlation: {self.correlation:.4f}")
        print(f"  • P-value: {self.p_value:.6f} {'✅ Significant' if self.p_value < 0.05 else '❌ Not Significant'}")
        print(f"  • Effect Size (Cohen's d): {self.effect_size:.4f}")
        print(f"  • 95% CI: [{self.confidence_interval[0]:.4f}, {self.confidence_interval[1]:.4f}]")

        print(f"\n🎲 PERFORMANCE:")
        print(f"  • Your Win Rate: {self.win_rate*100:.1f}%")
        print(f"  • Baseline (Random): {self.baseline_win_rate*100:.1f}%")
        print(f"  • Edge: {(self.win_rate - self.baseline_win_rate)*100:+.1f}%")

        print(f"\n🚦 DECISION: {self.decision}")
        print(f"📝 Reasoning: {self.reasoning}")

        print("\n" + "="*70)

        if self.decision == "PROCEED":
            print("✅ GREEN LIGHT: Proceed to MVP phase (Week 2)")
        elif self.decision == "PIVOT":
            print("⚠️  YELLOW LIGHT: Weak signal - consider pivoting approach")
        else:
            print("🛑 RED LIGHT: Stop this project or pivot completely")

        print("="*70 + "\n")


class HypothesisValidator:
    """
    Validates trading/prediction hypotheses before building systems.

    This enforces the scientific method:
    1. State hypothesis
    2. Collect data
    3. Test statistically
    4. Make GO/NO-GO decision
    """

    def __init__(self, significance_level: float = 0.05, min_sample_size: int = 30):
        self.significance_level = significance_level
        self.min_sample_size = min_sample_size

    def validate_correlation(
        self,
        hypothesis: str,
        predictor: np.ndarray,
        outcome: np.ndarray,
        baseline_win_rate: Optional[float] = None
    ) -> ValidationResult:
        """
        Test if predictor correlates with outcome.

        Args:
            hypothesis: String describing what you're testing
            predictor: Independent variable (e.g., earnings growth)
            outcome: Dependent variable (e.g., price returns)
            baseline_win_rate: Expected win rate for random selection

        Returns:
            ValidationResult with decision
        """
        # Input validation
        if len(predictor) != len(outcome):
            raise ValueError("Predictor and outcome must have same length")

        if len(predictor) < self.min_sample_size:
            return ValidationResult(
                hypothesis=hypothesis,
                correlation=0.0,
                p_value=1.0,
                sample_size=len(predictor),
                win_rate=0.0,
                baseline_win_rate=baseline_win_rate or 0.5,
                effect_size=0.0,
                confidence_interval=(0.0, 0.0),
                decision="STOP",
                reasoning=f"Insufficient sample size ({len(predictor)} < {self.min_sample_size})",
                timestamp=datetime.now().isoformat()
            )

        # Calculate correlation
        correlation, p_value = stats.pearsonr(predictor, outcome)

        # Calculate win rate (assuming binary outcome: 1=win, 0=loss)
        binary_outcome = (outcome > 0).astype(int)
        win_rate = binary_outcome.mean()

        if baseline_win_rate is None:
            baseline_win_rate = 0.5  # Assume 50/50 for random

        # Calculate effect size (Cohen's d)
        wins = outcome[binary_outcome == 1]
        losses = outcome[binary_outcome == 0]

        if len(wins) > 0 and len(losses) > 0:
            pooled_std = np.sqrt((wins.std()**2 + losses.std()**2) / 2)
            effect_size = (wins.mean() - losses.mean()) / pooled_std if pooled_std > 0 else 0.0
        else:
            effect_size = 0.0

        # Calculate confidence interval
        ci = self._calculate_confidence_interval(correlation, len(predictor))

        # Make decision
        decision, reasoning = self._make_decision(
            correlation, p_value, win_rate, baseline_win_rate,
            effect_size, len(predictor)
        )

        return ValidationResult(
            hypothesis=hypothesis,
            correlation=correlation,
            p_value=p_value,
            sample_size=len(predictor),
            win_rate=win_rate,
            baseline_win_rate=baseline_win_rate,
            effect_size=effect_size,
            confidence_interval=ci,
            decision=decision,
            reasoning=reasoning,
            timestamp=datetime.now().isoformat()
        )

    def _calculate_confidence_interval(
        self,
        correlation: float,
        n: int,
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for correlation using Fisher's Z transformation"""
        if abs(correlation) >= 1.0:
            return (correlation, correlation)

        # Fisher's Z transformation
        z = 0.5 * np.log((1 + correlation) / (1 - correlation))
        se = 1 / np.sqrt(n - 3)

        # Z-score for confidence level
        z_score = stats.norm.ppf((1 + confidence) / 2)

        # CI in Z space
        z_lower = z - z_score * se
        z_upper = z + z_score * se

        # Transform back to correlation space
        r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
        r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)

        return (r_lower, r_upper)

    def _make_decision(
        self,
        correlation: float,
        p_value: float,
        win_rate: float,
        baseline_win_rate: float,
        effect_size: float,
        sample_size: int
    ) -> Tuple[str, str]:
        """
        Make GO/NO-GO decision based on multiple factors.

        Decision Rules:
        - PROCEED: Strong statistical significance + meaningful edge
        - PIVOT: Weak signals but some promise
        - STOP: No statistical significance or no edge
        """
        edge = win_rate - baseline_win_rate

        # PROCEED criteria (all must be true)
        proceed_conditions = [
            p_value < self.significance_level,  # Statistically significant
            abs(correlation) > 0.3,              # Moderate+ correlation
            edge > 0.10,                         # >10% edge over baseline
            abs(effect_size) > 0.3,              # Small+ effect size
            sample_size >= self.min_sample_size  # Sufficient samples
        ]

        if all(proceed_conditions):
            return (
                "PROCEED",
                f"Strong statistical significance (p={p_value:.4f}) with {edge*100:.1f}% edge over baseline. "
                f"Effect size {effect_size:.2f} indicates meaningful real-world impact."
            )

        # PIVOT criteria (some promise)
        pivot_conditions = [
            p_value < 0.10,                      # Trending significant
            abs(correlation) > 0.2,              # Weak+ correlation
            edge > 0.05,                         # >5% edge
        ]

        if sum(pivot_conditions) >= 2:
            return (
                "PIVOT",
                f"Weak signals detected (p={p_value:.4f}, edge={edge*100:.1f}%). "
                f"Consider refining hypothesis, increasing sample size, or adjusting approach."
            )

        # STOP (default)
        reasons = []
        if p_value >= self.significance_level:
            reasons.append(f"not statistically significant (p={p_value:.4f})")
        if abs(correlation) <= 0.2:
            reasons.append(f"weak correlation ({correlation:.4f})")
        if edge <= 0.05:
            reasons.append(f"insufficient edge ({edge*100:.1f}%)")
        if abs(effect_size) <= 0.2:
            reasons.append(f"negligible effect size ({effect_size:.2f})")

        return (
            "STOP",
            f"Hypothesis not validated: {', '.join(reasons)}. "
            f"Recommend stopping or completely rethinking approach."
        )

    def save_report(self, result: ValidationResult, output_path: str) -> None:
        """Save validation report to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"\n📄 Report saved to: {output_path}")


def quick_validate(
    hypothesis: str,
    predictor_values: List[float],
    outcome_values: List[float],
    baseline_win_rate: Optional[float] = None
) -> ValidationResult:
    """
    Quick validation helper function.

    Example:
        predictor = [0.5, 0.3, 0.8, 0.1, ...]  # e.g., earnings growth
        outcome = [0.05, -0.02, 0.12, -0.01, ...]  # e.g., 3-day returns

        result = quick_validate(
            "Earnings growth predicts returns",
            predictor,
            outcome
        )
        result.print_report()
    """
    validator = HypothesisValidator()
    result = validator.validate_correlation(
        hypothesis=hypothesis,
        predictor=np.array(predictor_values),
        outcome=np.array(outcome_values),
        baseline_win_rate=baseline_win_rate
    )
    return result


# Example usage
if __name__ == "__main__":
    print("🧪 Hypothesis Validator - Your A+ Safety Net\n")

    # Example: Test if earnings growth predicts returns
    print("Example: Testing if QoQ growth >50% predicts 3-day returns >3%\n")

    # Simulated data (in real use, load your actual data)
    np.random.seed(42)
    n_samples = 50

    # Predictor: QoQ growth (0-1 scale)
    qoq_growth = np.random.uniform(0.2, 0.8, n_samples)

    # Outcome: 3-day returns with some correlation to growth
    noise = np.random.normal(0, 0.03, n_samples)
    returns_3d = 0.05 * qoq_growth + noise  # Weak positive correlation

    # Run validation
    result = quick_validate(
        hypothesis="Companies with >50% QoQ growth will have >3% returns in 3 days",
        predictor_values=qoq_growth.tolist(),
        outcome_values=returns_3d.tolist(),
        baseline_win_rate=0.50
    )

    # Print report
    result.print_report()

    # Save to file
    validator = HypothesisValidator()
    validator.save_report(result, "validation_report.json")

    print("\n" + "="*70)
    print("💡 NEXT STEPS:")
    print("="*70)

    if result.decision == "PROCEED":
        print("""
1. ✅ Proceed to Week 2: Build MVP
2. Use out-of-sample data for MVP test
3. Confirm results match Week 1 validation
4. Only build production system if MVP confirms
        """)
    elif result.decision == "PIVOT":
        print("""
1. ⚠️  Refine your hypothesis
2. Increase sample size (collect more data)
3. Try different predictors
4. Re-run validation before building anything
        """)
    else:
        print("""
1. 🛑 STOP this approach
2. Brainstorm completely different hypothesis
3. Don't build any infrastructure for this idea
4. Move on to next idea quickly (fail fast!)
        """)

    print("="*70 + "\n")
