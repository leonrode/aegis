import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from mcp.server.fastmcp import FastMCP, Context

from gmail_api import (
    init_gmail_service,
    get_email_message_details,
    search_emails,
    search_email_conversations,
    send_email,
    get_email_messages,
    download_attachments_parent,
    download_attachments_all
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gmail_mcp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('gmail_mcp')

# Initialize MCP Server
mcp = FastMCP(
    "Gmail MCP Server",
    dependencies=["google-api-python-client", "google-auth-oauthlib"]
)

# Gmail Service Initialization
CLIENT_FILE = '../credentials-web.json'

def get_gmail_service(email_identifier: str):
    try:
        service = init_gmail_service(CLIENT_FILE, prefix=f'_{email_identifier}')
        if not service:
            raise ValueError(f"Failed to initialize Gmail service for {email_identifier}")
        return service
    except Exception as e:
        logger.error(f"Error initializing Gmail service: {str(e)}")
        raise

# Resources
@mcp.tool()
async def get_inbox(email_identifier: str) -> Dict[str, Any]:
    """Get latest emails from inbox"""
    try:
        logger.info(f"Fetching inbox for {email_identifier}")
        service = get_gmail_service(email_identifier)
        messages, next_page = get_email_messages(service, max_results=10)
        emails = []
        for msg in messages:
            details = get_email_message_details(service, msg['id'])
            if details:
                emails.append(details)
        return {
            "success": True,
            "emails": emails,
            "has_more": bool(next_page)
        }
    except Exception as e:
        logger.error(f"Error fetching inbox: {str(e)}")
        return {"success": False, "message": str(e)}

@mcp.tool()
async def get_email_details(email_identifier: str, msg_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific email"""
    try:
        logger.info(f"Fetching email details for ID {msg_id}")
        service = get_gmail_service(email_identifier)
        details = get_email_message_details(service, msg_id)
        if details:
            return {"success": True, "email": details}
        return {"success": False, "message": "Email not found"}
    except Exception as e:
        logger.error(f"Error fetching email details: {str(e)}")
        return {"success": False, "message": str(e)}

@mcp.tool()
async def list_attachments(email_identifier: str, msg_id: str) -> Dict[str, Any]:
    """List attachments for a specific email"""
    try:
        logger.info(f"Listing attachments for email {msg_id}")
        service = get_gmail_service(email_identifier)
        details = get_email_message_details(service, msg_id)
        if details and details.get('has_attachments'):
            return {
                "success": True,
                "has_attachments": True,
                "message_id": msg_id
            }
        return {
            "success": True,
            "has_attachments": False
        }
    except Exception as e:
        logger.error(f"Error listing attachments: {str(e)}")
        return {"success": False, "message": str(e)}

# Tools
@mcp.tool()
async def send_gmail(
    email_identifier: str, 
    to: str, 
    subject: str, 
    body: str, 
    attachment_paths: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Send an email with optional attachments"""
    try:
        logger.info(f"Sending email to {to} from {email_identifier}")
        service = get_gmail_service(email_identifier)
        
        # Validate attachment paths
        if attachment_paths:
            for path in attachment_paths:
                if not os.path.exists(path):
                    return {
                        "success": False,
                        "message": f"Attachment not found: {path}"
                    }
        
        response = send_email(
            service=service,
            to=to,
            subject=subject,
            body=body,
            body_type='plain',
            attachment_paths=attachment_paths
        )
        
        if response:
            return {
                "success": True,
                "message": f"Email sent successfully to {to}",
                "message_id": response.get('id', 'unknown')
            }
        return {
            "success": False,
            "message": "Failed to send email"
        }
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return {"success": False, "message": str(e)}

@mcp.tool()
async def search_email_tool(
    email_identifier: str,
    query: str = '',
    max_results: int = 30,
    include_conversations: bool = True
) -> Dict[str, Any]:
    """Search emails with optional conversation inclusion"""
    try:
        logger.info(f"Searching emails for {email_identifier} with query: {query}")
        service = get_gmail_service(email_identifier)
        
        emails = []
        # Search regular emails
        messages = search_emails(service, query, max_results=max_results)
        for msg in messages:
            details = get_email_message_details(service, msg['id'])
            if details:
                emails.append(details)
                
        # Search conversations if requested
        if include_conversations:
            conversations = search_email_conversations(service, query, max_results=max_results)
            for conv in conversations:
                details = get_email_message_details(service, conv['id'])
                if details:
                    emails.append(details)
                    
        return {
            "success": True,
            "message": f"Found {len(emails)} emails",
            "emails": emails
        }
    except Exception as e:
        logger.error(f"Error searching emails: {str(e)}")
        return {"success": False, "message": str(e), "emails": []}

@mcp.tool()
async def read_latest_emails(
    email_identifier: str,
    max_results: int = 5,
    download_attachments: bool = False
) -> Dict[str, Any]:
    """Read latest emails with optional attachment download"""
    try:
        logger.info(f"Reading latest {max_results} emails for {email_identifier}")
        service = get_gmail_service(email_identifier)
        
        messages, _ = get_email_messages(service, max_results=max_results)
        emails = []
        
        attachment_dir = Path('./downloaded_attachments')
        if download_attachments:
            attachment_dir.mkdir(exist_ok=True)
            
        for msg in messages:
            details = get_email_message_details(service, msg['id'])
            if details:
                if download_attachments and details.get('has_attachments'):
                    download_attachments_parent(
                        service, 
                        user_id='me',
                        msg_id=msg['id'],
                        target_dir=str(attachment_dir)
                    )
                    details['attachments_downloaded'] = True
                    details['attachment_dir'] = str(attachment_dir)
                emails.append(details)
        
        return {
            "success": True,
            "message": f"Retrieved {len(emails)} latest emails",
            "emails": emails,
            "attachment_downloads": download_attachments
        }
    except Exception as e:
        logger.error(f"Error reading latest emails: {str(e)}")
        return {"success": False, "message": str(e), "emails": []}

@mcp.tool()
async def download_email_attachments(
    email_identifier: str,
    msg_id: str,
    download_all_in_thread: bool = False
) -> Dict[str, Any]:
    """Download attachments for a specific email or its entire thread"""
    try:
        logger.info(f"Downloading attachments for email {msg_id}")
        service = get_gmail_service(email_identifier)
        
        attachment_dir = Path('./downloaded_attachments')
        attachment_dir.mkdir(exist_ok=True)
        
        if download_all_in_thread:
            download_attachments_all(
                service,
                user_id='me',
                msg_id=msg_id,
                target_dir=str(attachment_dir)
            )
        else:
            download_attachments_parent(
                service,
                user_id='me',
                msg_id=msg_id,
                target_dir=str(attachment_dir)
            )
            
        return {
            "success": True,
            "message": "Attachments downloaded successfully",
            "directory": str(attachment_dir),
            "thread_downloaded": download_all_in_thread
        }
    except Exception as e:
        logger.error(f"Error downloading attachments: {str(e)}")
        return {"success": False, "message": str(e)}

# Prompts
@mcp.prompt()
def compose_email_prompt() -> Dict[str, Any]:
    """Guide for composing and sending an email"""
    return {
        "description": "Guide for composing and sending an email",
        "messages": [
            {
                "role": "system",
                "content": """You're helping the user compose and send an email. Make sure to collect:
1. Email identifier (the account sending the email)
2. Recipient's email address
3. Subject line
4. Email body content
5. Any attachments (optional) - provide full file paths"""
            },
            {
                "role": "user",
                "content": "I need to send an email."
            },
            {
                "role": "assistant",
                "content": """I'll help you compose and send an email. Please provide:

1. Which email account should send this? (email identifier)
2. Who are you sending it to? (recipient's email)
3. What's the subject of your email?
4. What would you like to say in the email?
5. Do you need to attach any files? If yes, please provide the file paths."""
            }
        ]
    }

@mcp.prompt()
def search_email_prompt() -> Dict[str, Any]:
    """Guide for searching emails with various criteria"""
    return {
        "description": "Guide for searching emails",
        "messages": [
            {
                "role": "system",
                "content": """You're helping the user search through their emails. Collect:
1. Email identifier (which account to search)
2. Search criteria (from, to, subject, date range, etc.)
3. Maximum number of results needed
4. Whether to include conversation threads"""
            },
            {
                "role": "user",
                "content": "I want to search my emails."
            },
            {
                "role": "assistant",
                "content": """I'll help you search your emails. Please specify:

1. Which email account do you want to search? (email identifier)
2. What are you looking for? You can search by:
   - Sender (from:someone@example.com)
   - Subject (subject:meeting)
   - Date range (after:2024/01/01 before:2024/02/01)
   - Has attachment (has:attachment)
   Or combine these criteria.
3. How many results would you like to see? (default is 30)
4. Should I include conversation threads in the search? (yes/no)"""
            }
        ]
    }

@mcp.prompt()
def read_latest_emails_prompt() -> Dict[str, Any]:
    """Guide for reading recent emails with optional attachment handling"""
    return {
        "description": "Guide for reading latest emails",
        "messages": [
            {
                "role": "system",
                "content": """You're helping the user read their recent emails. Collect:
1. Email identifier (which account to read)
2. Number of emails to retrieve
3. Whether to automatically download attachments"""
            },
            {
                "role": "user",
                "content": "I want to check my recent emails."
            },
            {
                "role": "assistant",
                "content": """I'll help you check your recent emails. Please specify:

1. Which email account do you want to check? (email identifier)
2. How many recent emails would you like to see? (default is 5)
3. Should I automatically download any attachments found? (yes/no)
   Note: Attachments will be saved to a 'downloaded_attachments' folder."""
            }
        ]
    }

@mcp.prompt()
def download_attachments_prompt() -> Dict[str, Any]:
    """Guide for downloading email attachments"""
    return {
        "description": "Guide for downloading email attachments",
        "messages": [
            {
                "role": "system",
                "content": """You're helping the user download email attachments. Collect:
1. Email identifier (which account to use)
2. Message ID of the email
3. Whether to download attachments from the entire conversation thread"""
            },
            {
                "role": "user",
                "content": "I want to download attachments from an email."
            },
            {
                "role": "assistant",
                "content": """I'll help you download email attachments. Please provide:

1. Which email account has the attachments? (email identifier)
2. What's the Message ID of the email? (You can get this from search results)
3. Do you want to download attachments from the entire conversation thread? (yes/no)
   Note: Files will be saved to a 'downloaded_attachments' folder."""
            }
        ]
    }

if __name__ == "__main__":
    try:
        logger.info("Starting Gmail MCP server...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal server error: {str(e)}")
