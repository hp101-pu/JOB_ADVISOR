from gmail_context import get_gmail_service


USER_ID = "694faacfad6de1d647826618"

service = get_gmail_service(USER_ID)

results = service.users().messages().list(
    userId="me",
    maxResults=5
).execute()

print(results)
