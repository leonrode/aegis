import subprocess
import json
import sys
import threading
import time
import os

def read_output(pipe, pipe_name):
    for line in iter(pipe.readline, ""):
        print(f"{pipe_name}: {line}", end="")
    pipe.close()

def run_client():
    # You need to specify the command to run
    # Replace this with the actual MCP server command you want to run
    cmd = ["python3", "-m", "mcp-google-calendar.mcp_server_google_calendar"]
    cwd = "local-mcp-test"  # Set working directory
    
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    threading.Thread(target=read_output, args=(process.stdout, "stdout"), daemon=True).start()
    threading.Thread(target=read_output, args=(process.stderr, "stderr"), daemon=True).start()

    time.sleep(2)
    
    # Step 1: Send initialization request
    init_request = {
        "jsonrpc": "2.0",
        "id": "init-1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "mcp-client",
                "version": "0.1.0"
            }
        }
    }
    
    print(f"Writing to stdin: {json.dumps(init_request)}")
    process.stdin.write(json.dumps(init_request) + '\n')
    process.stdin.flush()
    
    # Wait for initialization response
    time.sleep(1)
    
    # Step 2: Send initialized notification
    initialized_notification = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    
    print(f"Writing to stdin: {json.dumps(initialized_notification)}")
    process.stdin.write(json.dumps(initialized_notification) + '\n')
    process.stdin.flush()
    
    # Wait for server to be ready
    time.sleep(1)
    
    # Step 3: Now we can send tool calls
    query = {
        "jsonrpc": "2.0",
        "id": "request-1",
        "method": "tools/call",
        "params": {
            "name": "get-events",
            "arguments": {
                "calendarId": "leon.rode13@gmail.com"
            }
        }
    }

    # Send authentication request
    query_json_string = json.dumps(query) + '\n'
    print(f"Writing to stdin: {query_json_string.strip()}")
    
    try:
        process.stdin.write(query_json_string)
        process.stdin.flush()
    except BrokenPipeError:
        print("\nError: Could not write to the MCP server. It may have crashed on startup.")
        print("Check the [stderr] logs above for authentication or configuration errors.")
        return

    # Wait for OAuth flow to complete
    # print("Waiting for OAuth flow to complete...")
    # time.sleep(20)


    try:
        # Wait to allow time for the response to be printed by the reader threads
        time.sleep(10)
    finally:
        if process.poll() is None: # If the process is still running
            print("\nProcess is still running. Terminating.")
            process.terminate()
        else:
            print("\nProcess has terminated.")

    print("--- Script Finished ---")

if __name__ == "__main__":
    run_client()