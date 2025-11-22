"""
Debug Tools - Utilities for system diagnostics and remote verification

This module provides tools for:
1. Remote command execution via SSH
2. Log parsing and error extraction
3. Service status verification
4. HTTP endpoint health checks

Author: VCP Financial Research Team
Created: 2025-11-21
"""

import subprocess
import logging
import re
import json
import requests
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class RemoteShellExecutor:
    """Executes commands on a remote server via SSH"""
    
    def __init__(self, host: str, user: str = "ubuntu", key_path: str = "~/.ssh/lightsail.pem"):
        self.host = host
        self.user = user
        self.key_path = str(Path(key_path).expanduser())
        
    def run(self, command: str, timeout: int = 30) -> Dict[str, Union[str, int, bool]]:
        """
        Run a command on the remote server.
        
        Args:
            command: Shell command to execute
            timeout: Timeout in seconds
            
        Returns:
            Dict with 'stdout', 'stderr', 'exit_code', 'success'
        """
        ssh_cmd = [
            "ssh",
            "-i", self.key_path,
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=5",
            f"{self.user}@{self.host}",
            command
        ]
        
        try:
            logger.debug(f"Executing remote command: {command}")
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return {
                "stdout": "",
                "stderr": "Command timed out",
                "exit_code": -1,
                "success": False
            }
        except Exception as e:
            logger.error(f"SSH execution failed: {e}")
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "success": False
            }

    def check_connection(self) -> bool:
        """Verify SSH connection is working"""
        result = self.run("echo 'Connection OK'", timeout=10)
        return result["success"] and "Connection OK" in result["stdout"]


class ServiceStatusChecker:
    """Checks status of systemd services"""
    
    def __init__(self, executor: RemoteShellExecutor):
        self.executor = executor
        
    def check_service(self, service_name: str) -> Dict[str, str]:
        """
        Get detailed status of a systemd service.
        
        Returns:
            Dict with 'status', 'sub_status', 'uptime', 'logs'
        """
        # Check active status
        cmd = f"systemctl is-active {service_name}"
        result = self.executor.run(cmd)
        active_status = result["stdout"]
        
        # Get more details
        cmd = f"systemctl status {service_name} --no-pager -n 5"
        result = self.executor.run(cmd)
        full_status = result["stdout"]
        
        # Parse uptime (simplified)
        uptime = "Unknown"
        if "Active: active (running)" in full_status:
            match = re.search(r"since (.+?);", full_status)
            if match:
                uptime = match.group(1)
                
        return {
            "name": service_name,
            "active_status": active_status,
            "is_running": active_status == "active",
            "details": full_status,
            "uptime": uptime
        }


class LogParser:
    """Parses application logs for errors and patterns"""
    
    def __init__(self, executor: RemoteShellExecutor):
        self.executor = executor
        
    def get_recent_errors(self, log_path: str, lines: int = 100) -> List[str]:
        """Get recent error lines from a log file"""
        cmd = f"grep -i 'ERROR\\|CRITICAL\\|Exception' {log_path} | tail -n {lines}"
        result = self.executor.run(cmd)
        
        if not result["success"] or not result["stdout"]:
            return []
            
        return result["stdout"].split('\n')
        
    def tail_log(self, log_path: str, lines: int = 20) -> List[str]:
        """Get last N lines of a log file"""
        cmd = f"tail -n {lines} {log_path}"
        result = self.executor.run(cmd)
        
        if not result["success"]:
            return [f"Failed to read log: {result['stderr']}"]
            
        return result["stdout"].split('\n')


class EndpointValidator:
    """Checks HTTP endpoints"""
    
    @staticmethod
    def check_health(url: str, timeout: int = 5) -> Dict:
        """
        Check if an HTTP endpoint is healthy.
        """
        try:
            response = requests.get(url, timeout=timeout)
            return {
                "url": url,
                "status_code": response.status_code,
                "is_healthy": 200 <= response.status_code < 300,
                "latency_ms": int(response.elapsed.total_seconds() * 1000),
                "response": response.text[:500]  # Truncate
            }
        except Exception as e:
            return {
                "url": url,
                "status_code": 0,
                "is_healthy": False,
                "latency_ms": 0,
                "error": str(e)
            }

class NetworkValidator:
    """Low-level network diagnostics"""
    
    @staticmethod
    def check_ping(host: str) -> Dict[str, Union[bool, str]]:
        """Ping the host to check reachability"""
        try:
            # -c 1: count 1, -W 2000: wait 2000ms
            cmd = ["ping", "-c", "1", "-W", "2000", host]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {
                "reachable": result.returncode == 0,
                "output": result.stdout.strip() or result.stderr.strip()
            }
        except Exception as e:
            return {"reachable": False, "output": str(e)}

    @staticmethod
    def check_port(host: str, port: int, timeout: int = 3) -> bool:
        """Check if a TCP port is open"""
        import socket
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False
