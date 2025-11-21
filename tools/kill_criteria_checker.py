"""
Kill Criteria Checker - Your Project Survival System

This tool helps you set and check "stop conditions" for projects.
Use this to avoid spending 3 months on ideas that won't work.

Usage:
    # Setup kill criteria (Day 1 of new project)
    python tools/kill_criteria_checker.py setup

    # Check criteria (Every Friday)
    python tools/kill_criteria_checker.py check
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class KillCriterion:
    """A single kill criterion"""
    name: str
    metric: str
    threshold: float
    operator: str  # "<", ">", "<=", ">="
    description: str
    deadline_days: int  # Check after X days
    is_critical: bool  # True = instant kill, False = warning

    def check(self, current_value: float, days_elapsed: int) -> Dict:
        """Check if this criterion is triggered"""
        if days_elapsed < self.deadline_days:
            return {
                'triggered': False,
                'status': 'NOT_YET',
                'message': f"Check after day {self.deadline_days} (currently day {days_elapsed})"
            }

        # Evaluate condition
        triggered = False
        if self.operator == "<":
            triggered = current_value < self.threshold
        elif self.operator == ">":
            triggered = current_value > self.threshold
        elif self.operator == "<=":
            triggered = current_value <= self.threshold
        elif self.operator == ">=":
            triggered = current_value >= self.threshold

        status = "CRITICAL" if (triggered and self.is_critical) else \
                 "WARNING" if triggered else "PASSING"

        message = self._get_message(triggered, current_value)

        return {
            'triggered': triggered,
            'status': status,
            'message': message,
            'current_value': current_value,
            'threshold': self.threshold
        }

    def _get_message(self, triggered: bool, current_value: float) -> str:
        if not triggered:
            return f"✅ {self.name}: {current_value:.2f} (threshold: {self.operator}{self.threshold})"
        elif self.is_critical:
            return f"🛑 CRITICAL: {self.name} triggered! {current_value:.2f} {self.operator} {self.threshold}"
        else:
            return f"⚠️  WARNING: {self.name} triggered! {current_value:.2f} {self.operator} {self.threshold}"


@dataclass
class ProjectKillCriteria:
    """Complete kill criteria for a project"""
    project_name: str
    start_date: str
    hypothesis: str
    criteria: List[KillCriterion]
    created_at: str

    def to_dict(self) -> Dict:
        return {
            'project_name': self.project_name,
            'start_date': self.start_date,
            'hypothesis': self.hypothesis,
            'criteria': [asdict(c) for c in self.criteria],
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectKillCriteria':
        criteria = [KillCriterion(**c) for c in data['criteria']]
        return cls(
            project_name=data['project_name'],
            start_date=data['start_date'],
            hypothesis=data['hypothesis'],
            criteria=criteria,
            created_at=data['created_at']
        )


class KillCriteriaChecker:
    """Manages kill criteria for projects"""

    def __init__(self, config_path: str = ".kill_criteria.json"):
        self.config_path = Path(config_path)

    def setup_interactive(self) -> ProjectKillCriteria:
        """Interactive setup of kill criteria"""
        print("\n" + "="*70)
        print("🎯 KILL CRITERIA SETUP")
        print("="*70)
        print("\nSetting stop conditions prevents wasting months on bad ideas.")
        print("Be honest and strict with yourself!\n")

        project_name = input("📋 Project Name: ").strip()
        hypothesis = input("🔬 Core Hypothesis (one sentence): ").strip()

        print("\n" + "-"*70)
        print("📅 TIMING")
        print("-"*70)
        start_date = input("Start Date (YYYY-MM-DD, or press Enter for today): ").strip()
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")

        print("\n" + "-"*70)
        print("🚨 KILL CRITERIA")
        print("-"*70)
        print("\nDefine 3-5 criteria. If triggered, you MUST stop or pivot.")
        print("\nExamples:")
        print("  • Correlation < 0.3 after Week 1")
        print("  • Win rate < 55% after Week 2")
        print("  • Sample size < 100 after Week 3")
        print("  • No paying customers after Week 8")
        print()

        criteria = []
        for i in range(1, 6):
            print(f"\n--- Criterion {i} ---")
            add = input(f"Add criterion {i}? (y/n, press n to finish): ").lower()
            if add != 'y':
                break

            name = input(f"  Name (e.g., 'Week 1 Correlation'): ").strip()
            metric = input(f"  Metric to track (e.g., 'correlation', 'win_rate'): ").strip()
            threshold = float(input(f"  Threshold value: ").strip())
            operator = input(f"  Operator (<, >, <=, >=): ").strip()
            description = input(f"  Description (why this matters): ").strip()
            deadline_days = int(input(f"  Check after how many days? ").strip())
            is_critical = input(f"  Is this critical? (y/n, y=instant stop, n=warning): ").lower() == 'y'

            criteria.append(KillCriterion(
                name=name,
                metric=metric,
                threshold=threshold,
                operator=operator,
                description=description,
                deadline_days=deadline_days,
                is_critical=is_critical
            ))

        project_criteria = ProjectKillCriteria(
            project_name=project_name,
            start_date=start_date,
            hypothesis=hypothesis,
            criteria=criteria,
            created_at=datetime.now().isoformat()
        )

        # Save to file
        self.save_criteria(project_criteria)

        print("\n✅ Kill criteria saved to:", self.config_path)
        self._print_summary(project_criteria)

        return project_criteria

    def save_criteria(self, project_criteria: ProjectKillCriteria) -> None:
        """Save criteria to JSON file"""
        with open(self.config_path, 'w') as f:
            json.dump(project_criteria.to_dict(), f, indent=2)

    def load_criteria(self) -> Optional[ProjectKillCriteria]:
        """Load criteria from JSON file"""
        if not self.config_path.exists():
            return None

        with open(self.config_path, 'r') as f:
            data = json.load(f)

        return ProjectKillCriteria.from_dict(data)

    def check_criteria(self, metrics: Dict[str, float]) -> Dict:
        """Check all kill criteria against current metrics"""
        project_criteria = self.load_criteria()

        if not project_criteria:
            return {
                'error': 'No kill criteria found. Run setup first.',
                'decision': 'UNKNOWN'
            }

        # Calculate days elapsed
        start_date = datetime.fromisoformat(project_criteria.start_date)
        days_elapsed = (datetime.now() - start_date).days

        print("\n" + "="*70)
        print("🚨 KILL CRITERIA CHECK")
        print("="*70)
        print(f"\n📋 Project: {project_criteria.project_name}")
        print(f"🔬 Hypothesis: {project_criteria.hypothesis}")
        print(f"📅 Started: {project_criteria.start_date} ({days_elapsed} days ago)")
        print(f"📊 Checking {len(project_criteria.criteria)} criteria")

        results = []
        critical_triggered = 0
        warnings = 0

        print("\n" + "-"*70)
        print("RESULTS")
        print("-"*70 + "\n")

        for criterion in project_criteria.criteria:
            if criterion.metric not in metrics:
                print(f"⚠️  Missing metric: {criterion.metric}")
                continue

            result = criterion.check(metrics[criterion.metric], days_elapsed)
            results.append({
                'criterion': criterion.name,
                'result': result
            })

            print(result['message'])
            if result['status'] == 'CRITICAL':
                critical_triggered += 1
            elif result['status'] == 'WARNING':
                warnings += 1

        # Make decision
        decision = self._make_decision(critical_triggered, warnings, len(project_criteria.criteria))

        print("\n" + "="*70)
        print("🚦 DECISION")
        print("="*70 + "\n")

        if decision == "STOP":
            print("🛑 RED LIGHT: STOP THIS PROJECT")
            print(f"   {critical_triggered} critical criteria triggered")
            print("   You MUST stop or completely pivot.")
        elif decision == "PIVOT":
            print("⚠️  YELLOW LIGHT: PIVOT REQUIRED")
            print(f"   {warnings} warnings triggered")
            print("   Adjust approach significantly or prepare to stop.")
        else:
            print("✅ GREEN LIGHT: CONTINUE")
            print("   All criteria passing. Keep going!")

        print("\n" + "="*70 + "\n")

        return {
            'project': project_criteria.project_name,
            'days_elapsed': days_elapsed,
            'results': results,
            'critical_triggered': critical_triggered,
            'warnings': warnings,
            'decision': decision
        }

    def _make_decision(self, critical: int, warnings: int, total: int) -> str:
        """Determine if project should stop, pivot, or continue"""
        if critical > 0:
            return "STOP"
        elif warnings >= 2:
            return "PIVOT"
        else:
            return "CONTINUE"

    def _print_summary(self, project_criteria: ProjectKillCriteria) -> None:
        """Print summary of kill criteria"""
        print("\n" + "="*70)
        print("📋 KILL CRITERIA SUMMARY")
        print("="*70)

        for i, criterion in enumerate(project_criteria.criteria, 1):
            print(f"\n{i}. {criterion.name}")
            print(f"   Metric: {criterion.metric}")
            print(f"   Condition: {criterion.metric} {criterion.operator} {criterion.threshold}")
            print(f"   Check after: Day {criterion.deadline_days}")
            print(f"   Severity: {'CRITICAL ☠️' if criterion.is_critical else 'WARNING ⚠️'}")
            print(f"   Why: {criterion.description}")

        print("\n" + "="*70)
        print("\n💡 Remember: Honor these criteria. Don't rationalize!")
        print("   The goal is to fail fast, not to fail slowly.\n")


def example_usage():
    """Show example usage"""
    print("\n" + "="*70)
    print("📚 EXAMPLE: How to use Kill Criteria Checker")
    print("="*70 + "\n")

    # Example project criteria
    example = ProjectKillCriteria(
        project_name="Stock Earnings Predictor",
        start_date="2025-11-21",
        hypothesis="QoQ growth >50% predicts 3-day returns >3%",
        criteria=[
            KillCriterion(
                name="Week 1: Correlation Check",
                metric="correlation",
                threshold=0.3,
                operator="<",
                description="If correlation < 0.3, hypothesis is weak",
                deadline_days=7,
                is_critical=True
            ),
            KillCriterion(
                name="Week 2: Win Rate Check",
                metric="win_rate",
                threshold=0.55,
                operator="<",
                description="Need >55% win rate to beat random",
                deadline_days=14,
                is_critical=True
            ),
            KillCriterion(
                name="Week 3: Sample Size Check",
                metric="sample_size",
                threshold=100,
                operator="<",
                description="Need 100+ samples for statistical power",
                deadline_days=21,
                is_critical=False
            )
        ],
        created_at=datetime.now().isoformat()
    )

    checker = KillCriteriaChecker()
    checker.save_criteria(example)

    print("✅ Example criteria created!")
    print("\nNow checking with sample metrics...\n")

    # Simulate checking after 14 days
    sample_metrics = {
        'correlation': 0.25,  # Below 0.3 threshold!
        'win_rate': 0.52,     # Below 0.55 threshold!
        'sample_size': 80     # Below 100 but not critical yet
    }

    result = checker.check_criteria(sample_metrics)

    print("\n📊 This example shows:")
    print("   - 2 critical criteria triggered → STOP decision")
    print("   - System caught the problem after Week 2")
    print("   - Saved you from wasting Weeks 3-12!\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python kill_criteria_checker.py setup    # Setup new project criteria")
        print("  python kill_criteria_checker.py check    # Check current project")
        print("  python kill_criteria_checker.py example  # Show example\n")
        sys.exit(1)

    command = sys.argv[1]

    checker = KillCriteriaChecker()

    if command == "setup":
        checker.setup_interactive()

    elif command == "check":
        print("\n📊 Enter current metric values:")
        project_criteria = checker.load_criteria()

        if not project_criteria:
            print("❌ No criteria found. Run 'setup' first.")
            sys.exit(1)

        metrics = {}
        for criterion in project_criteria.criteria:
            if criterion.metric not in metrics:
                value = float(input(f"  {criterion.metric}: ").strip())
                metrics[criterion.metric] = value

        checker.check_criteria(metrics)

    elif command == "example":
        example_usage()

    else:
        print(f"❌ Unknown command: {command}")
        print("   Valid commands: setup, check, example")
