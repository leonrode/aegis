from dotenv import load_dotenv
import json
from neo4j_connector import Neo4JConnector
from sorter import Sorter
from llmcaller import LLMCaller
load_dotenv()

class AegisEngine:
    def __init__(self):
        self.sorter = Sorter()
        self.neo4j_connector = Neo4JConnector()
        self.llm_caller = LLMCaller()

        self.pull_data()

        self.graph_metadata = None
        self.graph_metadata_string = None
        self._get_graph_metadata()

        self.accept_query("Whats the latest in my email?")
    

    def pull_data(self):
        self.latest_data = self.sorter.pull_all_data()

        for service_name in self.latest_data.keys():
            graph = self.build_relationship_graph_from_data(self.latest_data[service_name], service_name)
            cyphers = self.build_cyphers_from_graph(graph)
            self.neo4j_connector.perform_cypher_query(cyphers)




    def _get_graph_metadata(self):
        schema, data = self.neo4j_connector.get_graph_metadata()

        # format the graph schema into a neat string
        nodes = []
        relationships = []
        
        # we go through the schema to understand the nodes
        # and the data to understand the relationships

        for entity in schema["value"].keys():
            if schema["value"][entity]["type"] == "node":
                properties = schema["value"][entity]["properties"]
                obj = {
                    "label": entity,
                    "properties": []
                }
                for property in properties.keys():
                    obj["properties"].append({
                        "name": property,
                        "type": properties[property]["type"]
                    })
                nodes.append(obj)
        


        for relationship in data["relationships"]:
            obj = {
                "source_label": relationship[0]["name"],
                "target_label": relationship[2]["name"],
                "type": relationship[1]
            }
            relationships.append(obj)

        self.graph_metadata_string = f"Nodes: {nodes}\nRelationships: {relationships}"

    def accept_query(self, query):

        print("GRAPH METADATA")
        print(self.graph_metadata_string)

        prompt = f"""
        You are an expert Neo4j data analyst who translates natural language questions into precise, read-only Cypher queries. Your task is to generate a single, valid Cypher query that answers the user's question, based only on the provided graph schema.

        ## Rules & Constraints
        Strict Schema Adherence: You MUST strictly adhere to the node names, relationship types, and property names defined in the schema. Do NOT invent any labels, relationships, or properties that are not explicitly listed.

        No Data Modification: You MUST NOT generate any queries that create, update, or delete data (e.g., no CREATE, SET, REMOVE, DELETE). Only generate queries that read data (e.g., MATCH, WHERE, RETURN).

        Handle Ambiguity: If the user's question is ambiguous, generate a query that returns broader results that can help clarify their intent.

        Output Format: Return ONLY the Cypher query text, with no explanations, preamble, or markdown formatting.

        ## Your Task
        Graph Schema:
        {self.graph_metadata_string}

        User's Question:
        {query}

        Cypher Query:
        """

        response = self.llm_caller.call_llm(prompt)

        text = response.candidates[0].content.parts[0].text

        if "```cypher" in text:
            text = text.replace("```cypher", "").replace("```", "")

        if "Unsupported" in text:
            text = text.replace("Unsupported", "")
            print("Unsupported query")

        text = text.strip()

        result = self.neo4j_connector.perform_cypher_query(text)

        if result and result[0]:
            prompt2 = f"""
            The user's question was: {query}

            The Cypher query was: {text}

            The result was: {result}

            From this result, please provide a summary of what was found as an answer to the user's question.

            Answer:
            """

            response2 = self.llm_caller.call_llm(prompt2)
            text2 = response2.candidates[0].content.parts[0].text

            print(text2)

        

    def build_relationship_graph_from_data(self, data, service_name):

        purposes = None
        with open("aegis-manifest.json", "r") as f:
            manifest = json.load(f)
            purposes = manifest["servers"][service_name]["data"]


        prompt = f"""
        You are a data architect. Your job is to convert the following text into a structured graph, adhering to a strict JSON schema. Identify all key entities as nodes and the connections between them as relationships. The provided 'purpose' tag describes the primary node.

        ## Output Specification
        You must return ONLY a single JSON object. This object must contain two keys: nodes and relationships.

        The nodes array: Each object in this array represents an entity and must contain the following keys:

        "id": A unique, temporary string you create for linking (e.g., "node1", "node2").


        "label": A general, one-word category for the entity (e.g., "person", "event", "email", "organization"). Use underscores for multi-word labels.

        "properties": An object of key-value pairs describing the entity.

        The relationships array: Each object in this array represents a connection and must contain the following keys:

        "source_id": The id of the node where the relationship starts.

        "target_id": The id of the node where the relationship ends.

        "type": An uppercase verb describing the relationship (e.g., "SENT", "ATTENDED", "ABOUT").

        ## Example
        Input Data: New email from alice@example.com about the 'Q3 Budget'.
        Purpose Tag: INTERACTION_LOG

        Correct JSON Output:

        ## Your Task
        Now, perform this task for the following data. Use the provided purpose tags to help determine the labels and properties of the nodes.

        Available Purpose Tags:
        {purposes}

        Input Data:
        {data}
        """


        response = self.llm_caller.call_llm(prompt)

        graph = {}
        for part in response.candidates[0].content.parts:
            if "```json" in part.text:
                text = part.text.replace("```json", "").replace("```", "")
                graph.update(json.loads(text))

        return graph
    
    def build_cyphers_from_graph(self, graph):
        cypher_parts = []
        node_vars = {}  # Maps temp JSON IDs to Cypher variable names

        # Create MERGE statements for nodes
        for i, node in enumerate(graph.get("nodes", [])):
            var = f"n{i}"
            node_vars[node['id']] = var
            # Escape single quotes in property values
            props = {k: str(v).replace("'", "\\'") for k, v in node['properties'].items()}
            prop_string = ", ".join([f"{k}: '{v}'" for k, v in props.items()])

            cypher_parts.append(f"MERGE ({var}:{node['label']} {{{prop_string}}})")

        # Create MERGE statements for relationships
        for rel in graph.get("relationships", []):
            source_var = node_vars.get(rel['source_id'])
            target_var = node_vars.get(rel['target_id'])
            if source_var and target_var:
                cypher_parts.append(f"MERGE ({source_var})-[:{rel['type']}]->({target_var})")

        return "\n".join(cypher_parts)
       
aegis = AegisEngine()
