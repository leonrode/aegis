import sys
sys.path.append('mcp-client')
from client import MCPClient
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

class AegisEngine:
    def __init__(self):
        self.client = MCPClient()
        self.client.engage_mcp_server("google-calendar")
        self.init_google_client()

    def init_google_client(self):
        self.google_client = genai.Client(vertexai=True, project=os.environ["GOOGLE_CLOUD_PROJECT"], location=os.environ["GOOGLE_CLOUD_LOCATION"])

        print("Generating content...")
        response = self.google_client.models.generate_content(
            model="gemini-2.0-flash-lite-001",
            contents="Tell me about the weather in Tokyo?",
        )
        # Print out the total tokens used from the response
        print("Total tokens used:", response.usage_metadata.total_token_count)
        print(response.text)

    def get_events(self, calendar_id, max_results):
        return self.client.send_request("google-calendar", "getEvents", {"calendarId": calendar_id, "maxResults": max_results})

aegis = AegisEngine()