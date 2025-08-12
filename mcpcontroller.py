import sys
sys.path.append('mcp-client')
from client import MCPClient
from google.genai.types import FunctionDeclaration, Tool, Schema, Part, GenerateContentConfig
import time
from llmcaller import LLMCaller
import json

class MCPController:
    """
    Responsible for one MCPClient. Contains the prompt of how to use the MCP service.
    Accepts a query from the Sorter and starts the Gemini Tool Calling loop with the prompt
    and associated function.

    Additionally enables the owner of the MCP service to pull all data from the MCP service.
    
    """

    def __init__(self, server_name, server_config):
        self.server_name = server_name
        self.server_config = server_config
        self.mcp_client = MCPClient(server_name, server_config)
        self.tools = []
        self.available_tools = {}
        self._load_config_into_functions()

        print(f"Available tools: {self.available_tools}")

        self.tool_config = GenerateContentConfig(tools=self.tools)

        self.llm_caller = LLMCaller(tools_config=self.tool_config)


    def _load_config_into_functions(self):

        function_declarations = []
        for tool in self.server_config.get("tools", []):
            fd = FunctionDeclaration(
                name=tool.get("name"),
                description=tool.get("description"),
                # The SDK accepts a JSON Schema dict here; it will be parsed into types.Schema
                parameters=tool.get("params", {"type": "object"}),
            )
            function_declarations.append(fd)

            self.available_tools[tool["name"]] = (lambda method, arguments: self.mcp_client.send_request(method, arguments))

        self.mcp_client.tools = [Tool(function_declarations=function_declarations)]
        # Also populate self.tools for the tool_config
        self.tools = [Tool(function_declarations=function_declarations)]
    

    def pull_all_data(self):
        """
        Pulls all data from the MCP service.
        """

        query = f"""
        You are the Sync Strategist for the Aegis AI assistant. Your goal is to generate a plan to keep the user's knowledge graph up-to-date.
        This is done by pulling all data from the {self.server_name} via the tools provided.

        Below is a complete list of all tools available from {self.server_name}.

        Use all tools that start with get- or list- or search-

        If relevant, use 'primary' for an ID or 'leon.rode13@gmail.com' for an email address.
        If relevant, start any time range with the current date minus 1 month.

        **Available Tools:**
        {json.dumps(self.server_config["tools"], indent=4)}

        **Your Task:**
        Based ONLY on the tools provided, generate a JSON array of ALL of the essential, non-destructive, read-only tool calls that should be run to get a complete overview of the user's recent activity.

        Remember the principles of the MCP service. If a tool returns a reference, you NEED to use the tool that retrieves the resource by ID, and add that tool to the list.

        **Output Format**

        [
            {{
                "tool_name": "name of the tool",
                "params": {{ "params for the tool" }}
            }}
            ...
        ]

        """

        result = self.llm_caller.call_llm(query)

        text = result.candidates[0].content.parts[0].text


        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]



        text = json.loads(text)

        # print(text)

        data = []

        for tool in text:
            print(f"Calling tool: {tool['tool_name']} with params: {tool['params']}")
            response = self.available_tools[tool["tool_name"]](tool["tool_name"], tool["params"])
            print(f"Response: {response}")
            obj = response["result"]

            if response["result"]:
                obj = response["result"]
                if "content" in obj:
                    obj = obj["content"][0]

                    if obj["type"] == "text":
                        obj = json.loads(obj["text"])
            
            if tool["tool_name"] == "get-events":
                return obj


            data.append(obj)

        return data


    def accept_query(self, query, prompt="control_prompt"):
        conversation_history = [Part.from_text(text=self.server_config[prompt]), Part.from_text(text=query)]
    
        answered_once = False
        while True:
            print("\n--- Calling Gemini ---")
            
            # Make the API call with the current history and available tools
            response = self.llm_caller.call_llm(
                prompt="", # prompt is in the conversation_history
                conversation_history=conversation_history,
            )

            #print(response)
            print(f"Tokens used: {response.usage_metadata.total_token_count}")

            candidate = response.candidates[0]

            # Check if the model's response contains any function calls
            parts = candidate.content.parts or []
            has_function_calls = any(getattr(p, "function_call", None) for p in parts)
            if not has_function_calls and answered_once:
                # EXIT CONDITION: The model provided a final text answer
                print("\n--- Final Answer from Gemini ---")
                print(response.text)
                return conversation_history

            answered_once = True

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

                    if "result" in tool_result:
                        
                        sliced_tool_result = json.dumps(tool_result["result"]["content"])
                    else:
                        sliced_tool_result = tool_result
                    # Append the result to our list of responses
                    function_responses.append(Part.from_function_response(
                        name=function_name,
                        response={"result": sliced_tool_result}
                    ))
                else:
                    print(f"Error: Function '{function_name}' not found.")
            
            # Append the tool execution results to the conversation history
            print("Function responses: ", function_responses)
            conversation_history.extend(function_responses)
            # The loop will now continue, sending the tool results back to Gemini
            time.sleep(2)
