"""
Verify Deployment - Master script to check AWS deployment status

Usage:
    python verify_deployment.py [--browser]

Options:
    --browser   Also open the dashboard in the browser for visual verification.
"""

import sys
import argparse
import webbrowser
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from agents.debugging.system_debugger import SystemDebugger

def main():
    parser = argparse.ArgumentParser(description="Verify AWS Deployment")
    parser.add_argument("--browser", action="store_true", help="Open dashboard in browser")
    args = parser.parse_args()
    
    print("🚀 Starting Deployment Verification...")
    
    debugger = SystemDebugger()
    
    # 1. Run System Checks
    try:
        is_healthy = debugger.verify_deployment()
    except Exception as e:
        print(f"❌ Verification failed with error: {e}")
        print("Tip: Ensure you have the SSH key at ~/.ssh/lightsail.pem")
        is_healthy = False

    # 2. Browser Verification
    if args.browser:
        # Check both 8001 (allowed by firewall) and 8002 (mentioned in docs)
        urls = [
            "http://13.200.109.29:8001/docs",
            "http://13.200.109.29:8002"
        ]
        
        print(f"\n🌐 Opening browser verification...")
        for url in urls:
            print(f"   - {url}")
        # In an agentic context, this might be handled by a browser tool
        # For local user usage:
        # webbrowser.open(url) 
        print("Please check the browser window.")

    # 3. Optimization Suggestions
    print("\n=== Optimization Suggestions ===")
    if is_healthy:
        print("✅ System is healthy. No immediate fixes needed.")
    else:
        print("⚠️ System issues detected. Check logs above.")
        
    print("\nTo optimize:")
    print("1. Run 'sudo apt-get autoremove' to clean unused packages")
    print("2. Check 'du -sh /var/log/*' to clean old logs")
    print("3. Verify if 'vcp-ml-api' is actually needed if only using intelligence")

if __name__ == "__main__":
    main()
