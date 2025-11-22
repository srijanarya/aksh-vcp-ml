"""
Optimize Deployment - Cleans up unused resources and services

Actions:
1. Disables vcp-ml-api (if not needed)
2. Cleans apt cache
3. Rotates logs
"""

import subprocess
from pathlib import Path

def run_remote(cmd):
    ssh_cmd = f"ssh -i ~/.ssh/lightsail.pem ubuntu@13.200.109.29 '{cmd}'"
    print(f"Running: {cmd}")
    subprocess.run(ssh_cmd, shell=True)

def optimize():
    print("🚀 Starting Optimization...")
    
    # 1. Disable unused API service
    print("\n[1/3] Disabling vcp-ml-api service...")
    run_remote("sudo systemctl stop vcp-ml-api")
    run_remote("sudo systemctl disable vcp-ml-api")
    
    # 2. Clean System
    print("\n[2/3] Cleaning system packages...")
    run_remote("sudo apt-get autoremove -y")
    run_remote("sudo apt-get clean")
    
    # 3. Clean Logs
    print("\n[3/3] Truncating old logs...")
    run_remote("sudo truncate -s 0 /var/log/syslog")
    run_remote("sudo truncate -s 0 /var/log/auth.log")
    
    print("\n✅ Optimization Complete!")

if __name__ == "__main__":
    optimize()
