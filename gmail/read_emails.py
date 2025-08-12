from pathlib import Path
from gmail_api import init_gmail_service, get_email_messages, get_email_message_details, download_attachments_parent

client_file = 'client_secret.json'
email_identifier = 'harshavardhansai.career@gmail.com'  # Specify the email identifier

# Initialize Gmail API service
service = init_gmail_service(client_file, prefix=f'_{email_identifier}')

# Correctly unpack the messages and next_page_token
messages, _ = get_email_messages(service, max_results=5)

# Target directory to save attachments
attachment_dir = Path('./downloaded_attachments')  # Folder to save attachments
attachment_dir.mkdir(exist_ok=True)  # Create the folder if it doesn't exist

# Process Emails
for msg in messages:
    details = get_email_message_details(service, msg['id'])
    if details:
        print(f"Subject: {details['subject']}")
        print(f"From: {details['sender']}")
        print(f"Recipients: {details['recipients']}")
        print(f"Body: {details['body'][:100]}...")  # Print first 100 characters of the body
        print(f"Snippet: {details['snippet']}")
        print(f"Has Attachments: {details['has_attachments']}")
        print(f"Date: {details['date']}")
        print(f"Star: {details['star']}")
        print(f"Label: {details['label']}")
        print("-" * 50)

        # Download Attachments if present
        if details['has_attachments']:
            download_attachments_parent(service, user_id='me', msg_id=msg['id'], target_dir=str(attachment_dir))
