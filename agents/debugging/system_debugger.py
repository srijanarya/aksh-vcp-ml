"""
System Debugger Agent - Orchestrates system health checks and diagnostics

This agent uses the debug tools and log analysis skills to:
1. Verify local and remote system health
2. Analyze logs for errors
3. Check service status
4. Verify deployment integrity

Author: VCP Financial Research Team
Created: 2025-11-21
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from tools.debug_tools import RemoteShellExecutor, ServiceStatusChecker, LogParser, EndpointValidator, NetworkValidator
from skills.log_analysis import LogAnalyzer

logger = logging.getLogger(__name__)

class SystemDebugger:
    """
    Agent responsible for debugging and verifying the system.
    """
    
    def __init__(self, host: str = "13.200.109.29", user: str = "ubuntu", key_path: str = "~/.ssh/lightsail.pem"):
        self.host = host
        self.executor = RemoteShellExecutor(host, user, key_path)
        self.service_checker = ServiceStatusChecker(self.executor)
        self.log_parser = LogParser(self.executor)
        self.log_analyzer = LogAnalyzer()
        self.network_validator = NetworkValidator()
        
    def diagnose_remote_health(self) -> Dict:
        """Run a full health check on the remote server"""
        logger.info(f"Starting remote health check for {self.host}...")
        
        report = {
            "ping": False,
            "ports": {},
            "connection": False,
            "services": {},
            "disk_usage": "Unknown",
            "memory_usage": "Unknown",
            "recent_errors": [],
            "status": "UNKNOWN"
        }
        
        # 0. Network Level Checks
        ping_result = self.network_validator.check_ping(self.host)
        report["ping"] = ping_result["reachable"]
        
        # Check critical ports
        for port in [22, 80, 8001, 8002]:
            report["ports"][port] = self.network_validator.check_port(self.host, port)
            
        if not report["ping"] and not any(report["ports"].values()):
            report["status"] = "CRITICAL: Host Unreachable (Down or Blocked)"
            return report

        # 1. Check SSH Connection
        if not self.executor.check_connection():
            report["status"] = "CRITICAL: SSH Failed (Auth or Timeout)"
            # If ping works but SSH fails, we might still be able to check HTTP ports externally
            if report["ports"].get(8001):
                 report["status"] += " - API Port 8001 is OPEN"
            return report
            
        report["connection"] = True
        
        # 2. Check Services (only if SSH works)
        services = ["vcp-intelligence", "vcp-ml-api"]
        for service in services:
            report["services"][service] = self.service_checker.check_service(service)
            
        # 3. Check Resources
        disk = self.executor.run("df -h /")
        if disk["success"]:
            report["disk_usage"] = disk["stdout"].split("\n")[1] if len(disk["stdout"].split("\n")) > 1 else "Unknown"
            
        mem = self.executor.run("free -h")
        if mem["success"]:
            report["memory_usage"] = mem["stdout"]
            
        # 4. Analyze Logs
        log_path = "/home/ubuntu/vcp-ml/announcement_intelligence.log"
        raw_errors = self.log_parser.get_recent_errors(log_path)
        report["recent_errors"] = raw_errors
        
        # Determine overall status
        failed_services = [s for s, info in report["services"].items() if not info["is_running"]]
        if failed_services:
            report["status"] = f"ERROR: Services failed: {', '.join(failed_services)}"
        elif raw_errors:
            report["status"] = "WARNING: Errors detected in logs"
        else:
            report["status"] = "HEALTHY"
            
        return report

    def verify_deployment(self) -> bool:
        """Verify that the deployment is active and correct"""
        health = self.diagnose_remote_health()
        
        print(f"\n=== Deployment Verification Report ===")
        print(f"Host: {self.host}")
        print(f"Status: {health['status']}")
        
        print(f"\n[Network]")
        print(f"Ping: {'✅' if health['ping'] else '❌'}")
        for port, is_open in health['ports'].items():
            print(f"Port {port}: {'✅ Open' if is_open else '❌ Closed'}")
            
        if not health["connection"]:
            print("\n⚠️ SSH Connection failed. Skipping internal checks.")
            return False
            
        print(f"\n[Services]")
        for name, info in health["services"].items():
            icon = "✅" if info["is_running"] else "❌"
            print(f"{icon} {name}: {info['active_status']} (Uptime: {info['uptime']})")
            
        print(f"\n[Resources]")
        print(f"Disk: {health['disk_usage']}")
        
        if health["recent_errors"]:
            print(f"\n[Recent Errors] ({len(health['recent_errors'])})")
            for err in health["recent_errors"][:5]:
                print(f"  - {err}")
        else:
            print("\n[Logs] No recent errors found.")
            
        return health["status"] == "HEALTHY"

if __name__ == "__main__":
    # Simple test run
    logging.basicConfig(level=logging.INFO)
    debugger = SystemDebugger()
    debugger.verify_deployment()
