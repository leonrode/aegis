#!/usr/bin/env python3
"""Utility script to clean up OAuth ports."""

import sys
import time
import subprocess
import platform

def kill_processes_on_ports(ports):
    """Kill any processes running on the specified ports."""
    system = platform.system().lower()
    
    for port in ports:
        try:
            if system == "darwin":  # macOS
                # Find processes using the port
                cmd = f"lsof -ti:{port}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid:
                            print(f"Killing process {pid} on port {port}...")
                            subprocess.run(f"kill -9 {pid}", shell=True, capture_output=True)
                            time.sleep(0.5)  # Give it time to die
                else:
                    print(f"No processes found on port {port}")
            elif system == "linux":
                # Find processes using the port
                cmd = f"fuser -k {port}/tcp"
                subprocess.run(cmd, shell=True, capture_output=True)
                print(f"Killed processes on port {port}")
            elif system == "windows":
                # Find processes using the port
                cmd = f"netstat -ano | findstr :{port}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            parts = line.split()
                            if len(parts) > 4:
                                pid = parts[-1]
                                print(f"Killing process {pid} on port {port}...")
                                subprocess.run(f"taskkill /PID {pid} /F", shell=True, capture_output=True)
                else:
                    print(f"No processes found on port {port}")
        except Exception as e:
            print(f"Warning: Could not kill processes on port {port}: {e}")

def main():
    """Main function to clean up OAuth ports."""
    oauth_ports = [8080, 8081, 8082, 8083, 8084, 8085]
    
    print("Cleaning up OAuth ports...")
    kill_processes_on_ports(oauth_ports)
    print("Cleanup complete!")

if __name__ == "__main__":
    main() 