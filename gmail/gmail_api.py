import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from google_apis import create_service

def init_gmail_service(client_file, api_name='gmail', api_version='v1', scopes=['https://mail.google.com/'], prefix=''):
    return create_service(client_file, api_name, api_version, scopes, prefix=prefix)


def _extract_body(payload):
    body = '<text body not available>'
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'multipart/alternative':
                for subpart in part['parts']:
                    if subpart['mimeType'] == 'text/plain' and 'data' in subpart['body']:
                        body = base64.urlsafe_b64decode(subpart['body']['data']).decode('utf-8')
                        break
            elif part['body']['data']:
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                break
    return body

def get_email_messages(service, user_id='me', label_ids=None, folder_name='INBOX', max_results=5):
    messages = []
    next_page_token = None

    if folder_name:
        label_results = service.users().labels().list(userId=user_id).execute()
        labels = label_results.get('labels', [])
        folder_label_id = next((label['id'] for label in labels if label['name'].lower() == folder_name.lower()), None)

        if folder_label_id:
            message_response = service.users().messages().list(userId=user_id, labelIds=[folder_label_id], maxResults=max_results).execute()
            messages.extend(message_response.get('messages', []))
            next_page_token = message_response.get('nextPageToken', None)

    return messages, next_page_token

def get_email_message_details(service, msg_id):
    try:
        message = service.users().messages().get(userId='me', id=msg_id).execute()
        payload = message['payload']
        headers = payload.get('headers', [])
        
        subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No subject')
        
        sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'No sender')
        
        recipients = next((header['value'] for header in headers if header['name'].lower() == 'to'), 'No recipients')
        
        snippet = message.get('snippet', 'No snippet')
        
        has_attachments = any(part.get('filename') for part in payload.get('parts', []) if part.get('filename'))
        
        date = next((header['value'] for header in headers if header['name'].lower() == 'date'), 'No date')
        
        star = message.get('labelIds', []).count('STARRED') > 0
        
        label = ', '.join(message.get('labelIds', []))
        
        body = _extract_body(payload)
        
        return {
            'subject': subject,
            'sender': sender,
            'recipients': recipients,
            'body': body,
            'snippet': snippet,
            'has_attachments': has_attachments,
            'date': date,
            'star': star,
            'label': label
        }
    except Exception as e:
        print(f'Error getting email message details: {e}')
        return None
def send_email(service, to, subject, body, body_type='plain', attachment_paths=None):
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    import base64
    import os
    from pathlib import Path
    import mimetypes

    message = MIMEMultipart()
    message['to'] = to
    message['subject'] = subject

    message.attach(MIMEText(body, body_type))

    # Handle attachments
    if attachment_paths:
        for attachment_path in attachment_paths:
            attachment_path = Path(attachment_path)  # Ensure it's a Path object
            if not attachment_path.exists():
                raise FileNotFoundError(f"File not found - {attachment_path}")

            # Guess the MIME type based on file extension
            content_type, encoding = mimetypes.guess_type(attachment_path)
            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'

            main_type, sub_type = content_type.split('/', 1)

            with open(attachment_path, 'rb') as attachment_file:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(attachment_file.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{attachment_path.name}"'
                )
                message.attach(part)

    # Encode message and send
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    send_message = {'raw': raw_message}

    try:
        sent_message = service.users().messages().send(userId='me', body=send_message).execute()
        print(f"Email sent successfully to {to} with attachments.")
        return sent_message
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
def download_attachments_parent(service, user_id, msg_id, target_dir):
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    for part in message['payload']['parts']:
        if part['filename']:
            att_id = part['body']['attachmentId']
            att = service.users().messages().attachments().get(userId=user_id, messageId=msg_id, id=att_id).execute()
            data = att['data']
            file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
            file_path = os.path.join(target_dir, part['filename'])
            print('Saving attachment to:', file_path)
            with open(file_path, 'wb') as f:
                f.write(file_data)

def download_attachments_all(service, user_id, msg_id, target_dir):
    thread = service.users().threads().get(userId=user_id, id=msg_id).execute()
    for message in thread['messages']:
        for part in message['payload']['parts']:
            if part['filename']:
                att_id = part['body']['attachmentId']
                att = service.users().messages().attachments().get(userId=user_id, messageId=message['id'], id=att_id).execute()
                data = att['data']
                file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                file_path = os.path.join(target_dir, part['filename'])
                print('Saving attachment to:', file_path)
                with open(file_path, 'wb') as f:
                    f.write(file_data)
def search_emails(service, query, user_id='me', max_results=5):
    messages = []
    next_page_token = None

    while True:
        result = service.users().messages().list(
            userId=user_id,
            q=query,
            maxResults=min(500, max_results - len(messages)) if max_results else 500,
            pageToken=next_page_token
        ).execute()

        messages.extend(result.get('messages', []))

        next_page_token = result.get('nextPageToken')

        if not next_page_token or (max_results and len(messages) >= max_results):
            break

    return messages[:max_results] if max_results else messages

def search_email_conversations(service, query, user_id='me', max_results=5):
    conversations = []
    next_page_token = None

    while True:
        result = service.users().threads().list(
            userId=user_id,
            q=query,
            maxResults=min(500, max_results - len(conversations)) if max_results else 500,
            pageToken=next_page_token
        ).execute()

        conversations.extend(result.get('threads', []))

        next_page_token = result.get('nextPageToken')

        if not next_page_token or (max_results and len(conversations) >= max_results):
            break

    return conversations[:max_results] if max_results else conversations
