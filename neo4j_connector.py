from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class Neo4JConnector:
    """
    Responsible for interfacing with the Neo4J database.
    """
    def __init__(self):
        self.driver = None
        self.connect_driver()

    def connect_driver(self):
        URI = os.getenv("NEO4J_INSTANCE_URI")
        USERNAME = os.getenv("NEO4J_USERNAME")
        PASSWORD = os.getenv("NEO4J_PASSWORD")

        self.driver = GraphDatabase.driver(
            URI,
            auth=(USERNAME, PASSWORD)
        )


    def perform_cypher_query(self, cypher_query):
        result = self.driver.execute_query(cypher_query)
        records, _, _ = result

        return records

    def get_graph_metadata(self):
        schema_result = self.driver.execute_query("CALL apoc.meta.schema()")
        data_result = self.driver.execute_query("CALL db.schema.visualization()")
        if schema_result.records:
            schema = schema_result.records[0].data()
        if data_result.records:
            data = data_result.records[0].data()
        return schema, data

    def close(self):
        self.driver.close()