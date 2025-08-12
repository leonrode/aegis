# aegis

## Introduction 

Aegis is designed to be a proactive personal assistant that lives in your digital world. 

> Aegis is still under development

Most interaction that we humans make with AI is in the form of a chat conversation, where humans prompt the AI often for information, and, more frequently, to take action on the human's behalf. This way of communication is one-sided, in that the AI application only reads and changes data on demand. This means that the cognitive load of *deciding* that a task must be done is still borne by the human. 

Aegis aims to change that.

Aegis has access to a constantly evolving knowledge graph about your digital life. From this graph, Aegis can come up with many ways to determine how to, for example, resolve scheduling conflicts via Google Calendar, remind you to wish a happy birthday to a relative via your WhatsApp messages, or suggest any other way to relieve some cognitive load off a person's full plate.

## Technicals

Aegis is designed to communicate with third party services though the Model Context Protocol (MCP). MCP servers expose **tools**, stateful methods accessible to LLMs to use at their discretion. Aegis is designed to plug and play with any MCP server, after a call to its `tools/list` method and a meta-control prompt.

The `MCPClient` object is responsible for performing `send_request` calls to one MCP client given a `method` and arguments. It is the edge interface between Aegis and the MCP service. An `MCPClient` is controlled by an `MCPController`, which injects the service control prompt along with a user query into an `LLMCaller` which decides on the tool calls to make. The `MCPClient` is then used accordingly.

Aegis performs a full data pull regularly in the background ny dynamically extracting data nodes and their relationships, and generating Cypher queries suitable for a Neo4J AuraDB in the cloud.

User queries are converted to Cypher queries given knowledge graph metadata, and performed against the AuraDB itself (not routed into the `MCPClient`).



