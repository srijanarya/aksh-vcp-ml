import sys
import os

# Add project root to path
sys.path.append("/Users/srijan/Desktop/aksh")

from agents.ml.ml_master_orchestrator import MLMasterOrchestrator

def verify_system():
    print("Initializing MLMasterOrchestrator...")
    orchestrator = MLMasterOrchestrator()
    
    # Trigger lazy loading of all agents
    print("Loading agents...")
    _ = orchestrator.data_collector
    _ = orchestrator.feature_engineer
    _ = orchestrator.training_agent
    _ = orchestrator.inference_agent
    _ = orchestrator.monitoring_agent
    _ = orchestrator.backtesting_agent
    _ = orchestrator.alert_agent
    
    status = orchestrator.get_system_status()
    
    print("\nSystem Status Report:")
    print(f"Version: {status['orchestrator_version']}")
    print("Agents Loaded:")
    for agent, loaded in status['agents_loaded'].items():
        print(f"  - {agent}: {'✅' if loaded else '❌'}")
        
    if all(status['agents_loaded'].values()):
        print("\nSUCCESS: All agents loaded correctly.")
    else:
        print("\nFAILURE: Some agents failed to load.")

if __name__ == "__main__":
    verify_system()
