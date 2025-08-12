# aegis

## Introduction 

Aegis is designed to be a knowledgeable assistant that lives in your digital world. 

> Aegis is still under development

Most interaction that we humans make with AI is in the form of a chat conversation, where humans prompt the AI often for information, and, more frequently, to take action on the human's behalf. This way of communication is one-sided, in that the AI application only reads and changes data on demand.

Aegis aims to change that.

Aegis has access to a constantly evolving knowledge graph about your digital life. From this graph, Aegis can come up with many ways to determine how to, for example, resolve scheduling conflicts via Google Calendar, remind you to wish a happy birthday to a relative via your WhatsApp messages, or suggest any other way to relieve some cognitive load off a person's full plate.

## Technicals

Aegis is designed to communicate with third party services though the Model Context Protocol (MCP). MCP servers expose **tools**, stateful methods accessible to LLMs to use at their discretion. Aegis is designed to plug and play with any MCP server, after a call to its `tools/list` method and a meta-control prompt.

The `MCPClient` object is responsible for performing `send_request` calls to one MCP client given a `method` and arguments. It is the edge interface between Aegis and the MCP service. An `MCPClient` is controlled by an `MCPController`, which injects the service control prompt along with a user query into an `LLMCaller` which decides on the tool calls to make. The `MCPClient` is then used accordingly.

Aegis can perform a full data pull by dynamically extracting data nodes and their relationships, and generating Cypher queries suitable for a Neo4J AuraDB in the cloud.

User queries are converted to Cypher queries given knowledge graph metadata, and performed against the AuraDB itself (not routed into the `MCPClient`).

## Demo

After having data pulled from my email and calendar, I asked Aegis the following questions

```
> What's the latest in my email?

The latest email in your inbox is from LinkedIn, with the subject "New jobs similar to Software Developer Intern." It was sent on Tue, 12 Aug 2025 18:35:58 +0000 (UTC) to Leon Rode. The email is marked as unread, important, categorized as updates, and is in your inbox. It does not have any attachments.

> What events do I have?

The user has the following calendar events:

*   **X's Birthday**: A yearly recurring event with reminders set.
*   **Reservation at X**: A private event with no specified end time.
*   **Flight to New York**: A private flight with the location listed as X.
```

## Usage

Dependencies are best installed in a virtual environment. Once the virtual environment is created, install the dependencies with `pip install -r requirements.txt`

Set up a GCP account and create a project, and credentials. Copy the credentials into `credentials-web.json` at the project root. Ensure the scopes for Google Calendar and GMail are enabled, as well as VertexAI for LLM usage.

Set up a Neo4J AuraDB instance and copy the environment variables into a `.env` file at the root:

```
GCP_CLIENT_ID=
GCP_CLIENT_SECRET=
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_APPLICATION_CREDENTIALS_WEB=credentials-web.json
GOOGLE_APPLICATION_TOKENS=token.json
NEO4J_USERNAME=
NEO4J_PASSWORD=
NEO4J_INSTANCE_ID=
NEO4J_INSTANCE_URI=
```
