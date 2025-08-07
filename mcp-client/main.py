from client import MCPClient
import time

client = MCPClient()

print(client.engage_mcp_server("google-calendar"))

time.sleep(3)

while True:
    server = input("Server name: ")
    method = input("Method name: ")

    client.send_request(server, method, {"calendarId": "leon.rode13@gmail.com", "maxResults": 10})