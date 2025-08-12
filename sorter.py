from mcpcontroller import MCPController
import json
from llmcaller import LLMCaller
from dotenv import load_dotenv

load_dotenv()

class Sorter:
    """ Responsible for sorting the user query into the respective MCP Client"""

    def __init__(self):
        # service name -> MCPClient
        self.mcp_controllers = {}
        self._load_services_as_controllers()
        self.llm_caller = LLMCaller()

    def _load_services_as_controllers(self):
        with open("aegis-manifest.json", "r") as f:
            manifest = json.load(f)

            for service_name, server_config in manifest.get("servers", {}).items():
                self.mcp_controllers[service_name] = MCPController(service_name, server_config)

        

    def pull_all_data(self):
        data = {}
        for service_name in self.mcp_controllers:
            data[service_name] = self.mcp_controllers[service_name].pull_all_data()

        print("DATA PULLED")
        print(data)

        return data

    def accept_query(self, query):
        """Decides which MCP client to use to answer the query, and fowards the query to the appropriate MCP client"""

        # create LLM conversation with information about all the MCP servers
        # we can use

        prompt = f"""
        You are a helpful assistant with access to a wide variety of tools.
        The tools you have access to are:
        {json.dumps(list(self.mcp_controllers.keys()), indent=4)}

        Your job is to understand the user's query, and determine which service is best suited to answer the query.
        Your job is NOT to answer the query, only to determine the right service to use to answer the query.

        Your output should only be the name of the service derived from the JSON above.

        The user's query is: {query}
        """

        response = self.llm_caller.call_llm(prompt)
        print(response.text)

        service_name = response.text.strip()
        if service_name in self.mcp_controllers:
            return self.mcp_controllers[service_name].accept_query(query)
        else:
            return f"Error: Service {service_name} not found"







