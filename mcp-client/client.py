"""
Maintains several connections to MCP servers.
"""

import json
import subprocess

class MCPClient:
    def __init__(self):
        # (server_name: process)
        self.clients = {}
        self.req_id = 1

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
            self.clients[server_name] = subprocess.Popen(
                server_config["startup"],
                cwd=server_config["cwd"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

        except Exception as e:
            print(f"Error starting server {server_name}: {e}")
            return False

        init_request = {
            "jsonrpc": "2.0",
            "id": self.req_id,
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

        self.req_id += 1


        try:
            print(f"Sending initialization request to {server_name}...")
            self.clients[server_name].stdin.write(json.dumps(init_request) + "\n")
            self.clients[server_name].stdin.flush()
        except Exception as e:
            print(f"Error sending initialization request to {server_name}: {e}")
            return False

        return True

        
    

        
        
