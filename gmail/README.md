# Gmail MCP Server
[![smithery badge](https://smithery.ai/badge/@Quantum-369/Gmail-mcp-server)](https://smithery.ai/server/@Quantum-369/Gmail-mcp-server)

A powerful and flexible Gmail integration server built using the MCP (Message Control Protocol) framework. This server provides a robust interface to interact with Gmail APIs, offering functionality for reading, sending, and managing emails programmatically.

## Features

- Read emails from multiple Gmail accounts
- Send emails with attachments
- Search emails with advanced query options
- Download email attachments
- Handle email conversations and threads
- Real-time email monitoring
- Support for multiple Gmail accounts

## Prerequisites

Before running the Gmail MCP server, ensure you have the following:

1. Python 3.12 or higher
2. Google Cloud Project with Gmail API enabled
3. OAuth 2.0 Client ID credentials
4. Required Python packages (specified in pyproject.toml)

## Installation

### Installing via Smithery

To install Gmail Integration Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@Quantum-369/Gmail-mcp-server):

```bash
npx -y @smithery/cli install @Quantum-369/Gmail-mcp-server --client claude
```

1. Clone the repository:
```bash
git clone <your-repository-url>
cd gmail-mcp-server
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix/MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install .
```

## Running on Ubuntu

1. Install Python 3.12 and create a virtual environment if you haven't already:
   ```bash
   sudo apt install python3.12 python3.12-venv -y
   python3.12 -m venv venv
   source venv/bin/activate
   ```
2. Place your downloaded `client_secret.json` in the project root.
3. Generate an OAuth token for the Gmail account you want to use. Copy the URL
   printed by the script into a web browser and complete the sign-in process:
   ```bash
   python gmail_token_creator.py
   ```
4. Start the server:
   ```bash
   python gmail_server.py
   ```

## Setup Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API for your project
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the client configuration file
5. Rename the downloaded file to `client_secret.json` and place it in the project root directory

## Configuration

1. Set up email identifiers in `gmail_token_creator.py`:
```python
email_identifier = 'your.email@gmail.com'  # Change this for each account
```

2. Run the token creator to authenticate your Gmail accounts:
```bash
python gmail_token_creator.py
```
The script prints an authorization URL. Copy this URL into your web browser,
complete the Google consent flow, and copy the verification code back into the
terminal if prompted. A token file will be created inside `token_files/` for
future use.

3. Repeat the process for each Gmail account you want to integrate

## Server Structure

- `gmail_server.py`: Main MCP server implementation
- `gmail_api.py`: Gmail API interaction functions
- `google_apis.py`: Google API authentication utilities
- Supporting files:
  - `read_emails.py`: Email reading functionality
  - `search_emails.py`: Email search functionality
  - `send_emails.py`: Email sending functionality

## Usage

### Starting the Server

```bash
python gmail_server.py
```

### Running with Docker

You can also build a container image using the provided `Dockerfile`:

```bash
docker build -t gmail-mcp-server .
docker run -v $(pwd)/client_secret.json:/app/client_secret.json \
           -v $(pwd)/token_files:/app/token_files gmail-mcp-server
```

The container runs the same server and stores authentication tokens in the
`token_files` directory on the host so they persist between runs.

### Available Tools

1. Send Email:
```python
await send_gmail(
    email_identifier="your.email@gmail.com",
    to="recipient@example.com",
    subject="Test Subject",
    body="Email body content",
    attachment_paths=["path/to/attachment"]
)
```

2. Search Emails:
```python
await search_email_tool(
    email_identifier="your.email@gmail.com",
    query="from:someone@example.com",
    max_results=30,
    include_conversations=True
)
```

3. Read Latest Emails:
```python
await read_latest_emails(
    email_identifier="your.email@gmail.com",
    max_results=5,
    download_attachments=False
)
```

4. Download Attachments:
```python
await download_email_attachments(
    email_identifier="your.email@gmail.com",
    msg_id="message_id",
    download_all_in_thread=False
)
```

## Security Considerations

- Store `client_secret.json` securely and never commit it to version control
- Keep token files secure and add them to `.gitignore`
- Use environment variables for sensitive information
- Regularly rotate OAuth credentials
- Monitor API usage and set appropriate quotas

## Error Handling

The server includes comprehensive error handling and logging:
- Logs are written to `gmail_mcp.log`
- Both file and console logging are enabled
- Detailed error messages for debugging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

Apachelicense2.0

## Support

For issues and feature requests, please use the GitHub issue tracker.
