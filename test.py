from mcpcontroller import MCPController
from dotenv import load_dotenv
import json

load_dotenv()


with open("aegis-manifest.json", "r") as f:
    manifest = json.load(f)

controller = MCPController("google-gmail", manifest["servers"]["google-gmail"])

print(controller.pull_all_data())