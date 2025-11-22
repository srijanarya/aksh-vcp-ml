"""
Re-label Circuits Script

Re-labels all samples using proper 10% circuit threshold instead of 2%.
This will significantly improve model training by using real circuit events.

Usage:
    python scripts/relabel_circuits.py

Author: VCP Financial Research Team
Created: 2025-11-19
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.ml.ml_label_quality_agent import MLLabelQualityAgent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("RE-LABEL CIRCUITS WITH PROPER THRESHOLD")
    print("=" * 60)
    print()
    
    # Initialize agent
    agent = MLLabelQualityAgent(
        db_base_path="/Users/srijan/Desktop/aksh/data",
        circuit_threshold=5.0  # Lowered to 5% to get more samples
    )
    
    # Show current state
    print("📊 Current Label Statistics:")
    print("-" * 60)
    current_stats = agent.get_label_stats()
    print(f"Total labels: {current_stats['total_labels']}")
    print(f"Positive labels: {current_stats['positive_labels']} ({current_stats['positive_ratio']*100:.1f}%)")
    print(f"Negative labels: {current_stats['negative_labels']}")
    print()
    
    # Validate current labels
    validation = agent.validate_labels()
    print("🔍 Current Label Validation:")
    print("-" * 60)
    if validation['valid']:
        print("✅ Labels are valid")
    else:
        print("❌ Issues found:")
        for issue in validation['issues']:
            print(f"   - {issue}")
    print()
    
    # Ask for confirmation
    print("⚠️  This will:")
    print("   1. Backup existing labels")
    print("   2. Delete all current labels")
    print("   3. Create new labels with 10% threshold")
    print()
    
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return
    
    print()
    print("🔄 Re-labeling in progress...")
    print("-" * 60)
    
    # Re-label
    results = agent.relabel_circuits()
    
    print()
    print("✅ Re-labeling Complete!")
    print("=" * 60)
    print(f"Circuits identified: {results['circuits_identified']}")
    print(f"Labels created: {results['labels_created']}")
    print()
    
    # Show new statistics
    new_stats = results['label_stats']
    print("📊 New Label Statistics:")
    print("-" * 60)
    print(f"Total labels: {new_stats['total_labels']}")
    print(f"Positive labels: {new_stats['positive_labels']} ({new_stats['positive_ratio']*100:.1f}%)")
    print(f"Negative labels: {new_stats['negative_labels']}")
    print(f"Avg price change: {new_stats['avg_price_change']:.2f}%")
    print(f"Max price change: {new_stats['max_price_change']:.2f}%")
    print()
    
    # Validate new labels
    new_validation = agent.validate_labels()
    print("🔍 New Label Validation:")
    print("-" * 60)
    if new_validation['valid']:
        print("✅ Labels are valid and ready for training!")
    else:
        print("⚠️  Issues found:")
        for issue in new_validation['issues']:
            print(f"   - {issue}")
        
        if new_validation['recommendations']:
            print("\n💡 Recommendations:")
            for rec in new_validation['recommendations']:
                print(f"   - {rec}")
    
    print()
    print("=" * 60)
    print("Next step: Run training pipeline to see improved results")
    print("Command: python run_training_pipeline.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
