from gmail_api import init_gmail_service, get_email_message_details, search_emails, search_email_conversations

client_file = 'client_secret.json'
email_identifier = 'hvm@umich.edu'  # Specify the email identifier

# Initialize Gmail API service
service = init_gmail_service(client_file, prefix=f'_{email_identifier}')

query = 'from:me'
email_messages = search_emails(service, query, max_results=30)
email_messages += search_email_conversations(service, query, max_results=30)  # Combine both

for message in email_messages:
    email_detail = get_email_message_details(service, message['id'])
    
    if email_detail:  # Check if email details were fetched successfully
        print(message['id'])
        print(f"Subject: {email_detail.get('subject', 'No Subject')}")
        print(f"Date: {email_detail.get('date', 'No Date')}")
        print(f"Label: {email_detail.get('label', 'No Label')}")
        print('Snippet: ', email_detail.get('snippet', 'No Snippet'))
        print(f"Body: {email_detail.get('body', 'No Body')}")
        print('-' * 50)
    else:
        print(f"Skipping message ID {message['id']} as it couldn't be retrieved.")

