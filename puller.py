from neo4j_connector import Neo4JConnector
from llmcaller import LLMCaller

class Puller:
    """
    Pulls data from the MCP services and stores it in the Neo4J database.

    Each MCP service is queried for its data, which is converted to Cypher queries and executed
    via the Neo4J connector.

    The sorter is shared with the owner of Puller
    """
    def __init__(self, sorter):
        self.connector = Neo4JConnector()
        self.llmcaller = LLMCaller()
        self.sorter = sorter

    def pull_all_data(self):
        data = self.sorter.pull_all_data()

        return data

