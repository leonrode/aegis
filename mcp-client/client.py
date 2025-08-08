"""
Maintains several connections to MCP servers.
"""

import json
import subprocess
import threading
import time

class MCPClient:
    def __init__(self):
        # (server_name: process)
        self.clients = {}

    """
    Engages with an MCP server.

    Loads the manifest from aegis-manifest.json, starts the process, and sends initialization request.
    """
    def engage_mcp_server(self, server_name):
        # load the config from aegis-manifest.json

        try:
            with open("aegis-manifest.json", "r") as f:
                manifest = json.load(f)

            server_config = manifest["servers"][server_name]
        
        except Exception as e:
            print(f"Error loading manifest: {e}")
            return False

        try:
            # start the server
            print(f"Starting server {server_name}...")
            process = subprocess.Popen(
                server_config["startup"],
                cwd=server_config["cwd"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  
                universal_newlines=True
            )
            
            # Create the client dictionary with all components
            self.clients[server_name] = {
                "process": process,
                "stdout": None,
                "stderr": None,
                "req_id": 1,
                "stdout_callback": None,
                "stderr_callback": None,
                "messages": [],  # Store parsed JSON messages
                "stderr_logs": []  # Store stderr logs
            }

            def read_stdout(pipe, pipe_name):
                """Read and parse JSON messages from stdout"""
                for line in iter(pipe.readline, ""):
                    line = line.strip()
                    if line:
                        try:
                            # Parse the JSON message
                            message = json.loads(line)
                            # Store the message
                            self.clients[server_name]["messages"].append(message)
                        except json.JSONDecodeError as e:
                            print(f"{pipe_name} (invalid JSON): {line}")
                            print(f"JSON Error: {e}. This means the MCP server is not giving JSON responses.")
            
            def read_stderr(pipe, pipe_name):
                """Read stderr logs (usually debug info, not JSON)"""
                for line in iter(pipe.readline, ""):
                    line = line.strip()
                    if line:
                        # Store the log
                        self.clients[server_name]["stderr_logs"].append(line)
                        # Print the log
                        print(f"{pipe_name}: {line}")
            
            self.clients[server_name]["stdout_callback"] = read_stdout
            self.clients[server_name]["stderr_callback"] = read_stderr

            # Start the output reading threads
            self.clients[server_name]["stdout"] = threading.Thread(target=self.clients[server_name]["stdout_callback"], args=(process.stdout, f"{server_name}-stdout"), daemon=True)
            self.clients[server_name]["stdout"].start()
            self.clients[server_name]["stderr"] = threading.Thread(target=self.clients[server_name]["stderr_callback"], args=(process.stderr, f"{server_name}-stderr"), daemon=True)
            self.clients[server_name]["stderr"].start()


        except Exception as e:
            print(f"Error starting server {server_name}: {e}")
            return False

        init_request = {
            "jsonrpc": "2.0",
            "id": self.clients[server_name]["req_id"],
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "aegis",
                    "version": "0.1.0"
                }
            }
        }

        self.clients[server_name]["req_id"] += 1


        try:
            print(f"Sending initialization request to {server_name}...")
            self.clients[server_name]["process"].stdin.write(json.dumps(init_request) + "\n")
            self.clients[server_name]["process"].stdin.flush()
        except Exception as e:
            print(f"Error sending initialization request to {server_name}: {e}")
            return False

        time.sleep(1)

        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }

        print(f"Writing to stdin: {json.dumps(initialized_notification)}")
        self.clients[server_name]["process"].stdin.write(json.dumps(initialized_notification) + '\n')
        self.clients[server_name]["process"].stdin.flush()

        return True


    def build_request_caller(self, server_name):

        def sender(method, arguments):
            server_name = "google-calendar"
            request = {
                "jsonrpc": "2.0",
                "id": self.clients[server_name]["req_id"],
                "method": "tools/call",
                "params": {
                    "name": method,
                    "arguments": arguments
                }
            }

            self.clients[server_name]["process"].stdin.write(json.dumps(request) + "\n")
            self.clients[server_name]["process"].stdin.flush()
            self.clients[server_name]["req_id"] += 1

            time.sleep(1)
            return self.get_latest_message(server_name)
        
        return sender

    def send_request(self, server_name, method, arguments):
        request = {
            "jsonrpc": "2.0",
            "id": self.clients[server_name]["req_id"],
            "method": "tools/call",
            "params": {
                "name": method,
                "arguments": arguments
            }
        }
        self.clients[server_name]["process"].stdin.write(json.dumps(request) + "\n")
        self.clients[server_name]["process"].stdin.flush()
        self.clients[server_name]["req_id"] += 1

    def get_messages(self, server_name):
        """Get all stored JSON messages from a server"""
        if server_name in self.clients:
            return self.clients[server_name]["messages"]
        return []
    
    def get_latest_message(self, server_name):
        """Get the most recent JSON message from a server"""
        messages = self.get_messages(server_name)
        return messages[-1] if messages else None
    
    def get_stderr_logs(self, server_name):
        """Get all stderr logs from a server"""
        if server_name in self.clients:
            return self.clients[server_name]["stderr_logs"]
        return []

        
