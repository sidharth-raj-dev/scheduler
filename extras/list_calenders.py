from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def list_calendars():
    try:
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=8080)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        print("\nFetching all calendars...\n")
        calendar_list = service.calendarList().list().execute()
        
        for calendar in calendar_list['items']:
            print(f"Calendar: {calendar['summary']}")
            print(f"ID: {calendar['id']}")
            print(f"Access Role: {calendar.get('accessRole', 'N/A')}")
            print(f"Primary: {calendar.get('primary', False)}")
            print(f"Selected: {calendar.get('selected', False)}")
            print(f"Time Zone: {calendar.get('timeZone', 'N/A')}")
            print("-" * 50)

    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == '__main__':
    list_calendars()