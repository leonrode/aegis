from pathlib import Path
from gmail_api import init_gmail_service, send_email

# Configuration
client_file = 'client_secret.json'
email_identifier = 'hvm@umich.edu'  # Change this for each account

# Initialize Gmail API service for the specific email account
service = init_gmail_service(client_file, prefix=f'_{email_identifier}')

# Email details
to_address = 'harshavardhansai.career@gmail.com'
email_subject = 'MCP servers document'
email_body = 'This is a test email sent using the Gmail API.'

# Attachments
attachment_dir = Path('C:\\Users\\harsh\\Downloads\\MS projects\\MCP\\mcpdocs')
attachment_files = list(attachment_dir.glob('*'))  # Load all files from the attachments folder

# Send the email
response_email_sent = send_email(
    service=service,
    to=to_address,
    subject=email_subject,
    body=email_body, 
    body_type='plain',
    attachment_paths=attachment_files
)

# Output response
print(response_email_sent)

