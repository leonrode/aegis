"""
Maintains several connections to MCP servers.
"""

import json
import subprocess
import threading
import time
import os
from google.genai.types import FunctionDeclaration, Tool, Schema

class MCPClient:
    def __init__(self, server_name, server_config):
        # (server_name: process)
        self.server_name = server_name
        self.server_config = server_config

        self.req_id = 1
        self.process = None
        self.stdout = None # thread
        self.stderr = None # thread
        self.messages = []
        self.stderr_logs = []

        self.engage_mcp_server()



    """
    Engages with an MCP server.

    Loads the manifest from aegis-manifest.json, starts the process, and sends initialization request.
    """
    def engage_mcp_server(self):


        try:
            # start the server
            print(f"Starting server {self.server_name}...")
            print(self.server_config["startup"])
            self.process = subprocess.Popen(
                self.server_config["startup"],
                cwd=self.server_config["cwd"] if self.server_config["cwd"] else os.getcwd(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  
                universal_newlines=True
            )
            

            def read_stdout(pipe, pipe_name):
                """Read and parse JSON messages from stdout"""
                print(f"Reading stdout from {pipe_name}...")
                for line in iter(pipe.readline, ""):
                    line = line.strip()
                    if line:
                        try:
                            # Parse the JSON message
                            message = json.loads(line)
                            # Store the message
                            self.messages.append(message)
                        except json.JSONDecodeError as e:
                            print(f"{pipe_name} (invalid JSON): {line}")
                            print(f"JSON Error: {e}. This means the MCP server is not giving JSON responses.")
            
            def read_stderr(pipe, pipe_name):
                """Read stderr logs (usually debug info, not JSON)"""
                print(f"Reading stderr from {pipe_name}...")
                for line in iter(pipe.readline, ""):
                    line = line.strip()
                    if line:
                        # Store the log
                        self.stderr_logs.append(line)
                        # Print the log
                        print(f"{pipe_name}: {line}")
            
            self.stdout_callback = read_stdout
            self.stderr_callback = read_stderr

            # Start the output reading threads
            self.stdout = threading.Thread(target=self.stdout_callback, args=(self.process.stdout, f"{self.server_name}-stdout"), daemon=True)
            self.stdout.start()
            self.stderr = threading.Thread(target=self.stderr_callback, args=(self.process.stderr, f"{self.server_name}-stderr"), daemon=True)
            self.stderr.start()


        except Exception as e:
            print(f"Error starting server {self.server_name}: {e}")
            return False


        init_request = {
            "jsonrpc": "2.0",
            "id": self.req_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "aegis",
                    "version": "0.1.0"
                }
            }
        }

        self.req_id += 1

        self.process.stdin.write(json.dumps(init_request) + "\n")
        self.process.stdin.flush()
        
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        time.sleep(3)

        print(f"Writing to stdin: {json.dumps(initialized_notification)}")
        self.process.stdin.write(json.dumps(initialized_notification) + '\n')
        self.process.stdin.flush()


        return True




    def send_request(self, method, arguments):
        request = {
            "jsonrpc": "2.0",
            "id": self.req_id,
            "method": "tools/call",
            "params": {
                "name": method,
                "arguments": arguments
            }
        }
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        self.req_id += 1

        time.sleep(5)

        return self.messages[-1]

        
