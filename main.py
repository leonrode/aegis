import sys
sys.path.append('mcp-client')
from client import MCPClient
from google import genai
from google.genai import types
from google.genai.types import Part
from dotenv import load_dotenv
import os
import json
import time
load_dotenv()

class AegisEngine:
    def __init__(self):
        self.client = MCPClient()
        self.client.engage_mcp_server("google-calendar")
        self.client.engage_mcp_server("google-gmail")

        self.tools = []
        self.available_tools = {}
        self.load_manifest_into_functions()

        print(self.tools)
        print(self.available_tools)

        self.tool_config = None
        self.google_client = None
        self.init_google_client()



    def load_manifest_into_functions(self, path="aegis-manifest.json"):
        with open(path, "r") as f:
            manifest = json.load(f)

        # Build FunctionDeclaration objects from manifest tools and wrap them in a Tool
        function_declarations = []
        for _service_name, service_config in manifest.get("servers", {}).items():
            for tool in service_config.get("tools", []):
                fd = types.FunctionDeclaration(
                    name=tool.get("name"),
                    description=tool.get("description"),
                    # The SDK accepts a JSON Schema dict here; it will be parsed into types.Schema
                    parameters=tool.get("params", {"type": "object"}),
                )
                function_declarations.append(fd)
                
                self.available_tools[tool["name"]] = self.client.build_request_caller(_service_name)


        if function_declarations:
            self.tools = [types.Tool(function_declarations=function_declarations)]
        else:
            self.tools = []

    def init_google_client(self):
        self.tool_config = types.GenerateContentConfig(tools=self.tools)
        self.google_client = genai.Client(vertexai=True, project=os.environ["GOOGLE_CLOUD_PROJECT"], location=os.environ["GOOGLE_CLOUD_LOCATION"])


    def take_query(self, query):
        print(query)
        prompt = """
        You are a helpful assistant that can use a WIDE variety of tools from the calendar, Gmail, and other services.
        If a user asks for something related to the calendar, you should use the calendar tools available to you.
        If a user asks for something related to Gmail, you should use the Gmail tools available to you.
        Emails are given in the form of IDs. Once you have an email ID, you can use the appropriate Gmail tool to get the email content.


        All tools you need are probably available to you. Use them.

        You can use as many tools as you need to answer the user's query. Use them sequentially as you see fit. For example, to get the latest email,
        you use the get-unread-emails tool, get the first email ID, then use the read-email tool to get the email content, and finally use the open-email tool to open the email in the browser.
        """
        conversation_history = [Part.from_text(text=prompt), Part.from_text(text=query)]
    
        while True:
            print("\n--- Calling Gemini ---")
            
            # Make the API call with the current history and available tools
            response = self.google_client.models.generate_content(
                model="gemini-2.0-flash-lite-001",
                contents=conversation_history,
                config=self.tool_config
            )
            
            candidate = response.candidates[0]

            # Check if the model's response contains any function calls
            parts = candidate.content.parts or []
            has_function_calls = any(getattr(p, "function_call", None) for p in parts)
            if not has_function_calls:
                # EXIT CONDITION: The model provided a final text answer
                print("\n--- Final Answer from Gemini ---")
                print(response.text)
                break

            # --- The model wants to call one or more tools ---
            print("--- Gemini wants to call a tool ---")
            
            # Append the model's request to the history for the next turn
            conversation_history.append(candidate.content)

            # Prepare a list to hold the results of our tool calls
            function_responses = []

            # Execute all function calls requested by the model in this turn
            for part in parts:
                if not getattr(part, "function_call", None):
                    continue
                function_call = part.function_call
                function_name = function_call.name
                
                print(f"Executing function: {function_name} with args: {dict(function_call.args)}")
                
                if function_name in self.available_tools:
                    # Look up the function in our "toolbox" and call it
                    function_to_call = self.available_tools[function_name]
                    tool_result = function_to_call(function_name, function_call.args)
                    print(tool_result)
                    # Append the result to our list of responses
                    function_responses.append(Part.from_function_response(
                        name=function_name,
                        response={"result": tool_result}
                    ))
                else:
                    print(f"Error: Function '{function_name}' not found.")
            
            # Append the tool execution results to the conversation history
            print("Function responses: ", function_responses)
            conversation_history.extend(function_responses)
            # The loop will now continue, sending the tool results back to Gemini
            time.sleep(2)





aegis = AegisEngine()
aegis.take_query("Can you get me all unread emails in my inbox? When you get all the email IDs, take the first one and use the read-email tool to get the email content. Then use the open-email tool to open the email in the browser.")