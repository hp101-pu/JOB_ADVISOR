from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def build_gmail_service(access_token: str):
    creds = Credentials(
        token=access_token,
        scopes=["https://www.googleapis.com/auth/gmail.modify"]
    )
    return build("gmail", "v1", credentials=creds)
