from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os.path
import pickle
import sys
from google.auth.exceptions import RefreshError
import pytz

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_events():
    try:
        # Setup IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        
        creds = None
        if os.path.exists('token.pickle'):
            print("Found existing token, attempting to load...")
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
            print("Token loaded successfully")
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing expired credentials...")
                try:
                    creds.refresh(Request())
                    print("Credentials refreshed successfully")
                except RefreshError as e:
                    print(f"Error refreshing credentials: {e}")
                    if os.path.exists('token.pickle'):
                        os.remove('token.pickle')
                    creds = None
            
            if not creds:
                print("No valid credentials found. Starting new OAuth flow...")
                if not os.path.exists('credentials.json'):
                    print("Error: credentials.json not found!")
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', 
                    SCOPES,
                    redirect_uri='http://localhost:8080'
                )
                creds = flow.run_local_server(port=8080)
                print("New credentials obtained successfully")
                
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
                print("New credentials saved to token.pickle")

        print("Building Calendar service...")
        service = build('calendar', 'v3', credentials=creds)

        # Get today's start and end time in IST
        now = datetime.now(ist)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        print(f"\nFetching events for {now.strftime('%Y-%m-%d')} (IST)...")
        print(f"Time range: {today_start.strftime('%I:%M %p')} - {today_end.strftime('%I:%M %p')} IST")
        
        events_result = service.events().list(
            calendarId='primary',
            singleEvents=True,  # This expands recurring events
            maxResults=2500,    # Increased to get more events
            orderBy='startTime',
            timeZone='Asia/Kolkata'  # Explicitly set timezone to IST
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            print('\nNo events found for today.')
            
            # List calendars for debugging
            calendar_list = service.calendarList().list().execute()
            print("\nAvailable calendars:")
            for calendar in calendar_list['items']:
                print(f"- {calendar['summary']} (ID: {calendar['id']})")
                print(f"  Access Role: {calendar.get('accessRole', 'N/A')}")
                print(f"  Primary: {calendar.get('primary', False)}")
        else:
            print('\nToday\'s events:')
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                if 'T' in start:  # This is a time-specific event
                    event_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    event_time = event_dt.astimezone(ist).strftime('%I:%M %p')
                else:  # This is an all-day event
                    event_time = 'All day'
                
                summary = event.get('summary', 'No title')
                recurrence = "🔄 " if event.get('recurringEventId') else ""
                print(f"- {event_time}: {recurrence}{summary}")

                # Debug: Print raw event data
                print(f"  Debug - Raw event data: {event}\n")

    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print("\nDebug information:")
        import traceback
        traceback.print_exc()
        print(f"\nPython version: {sys.version}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Files in current directory: {os.listdir('.')}")
        if os.path.exists('credentials.json'):
            print("credentials.json exists")
        if os.path.exists('token.pickle'):
            print("token.pickle exists")

if __name__ == '__main__':
    get_calendar_events()