from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
from datetime import datetime
import pytz

# Combined scopes for both Calendar and Tasks
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/tasks.readonly'
]

def get_credentials():
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
    
    return creds

def get_calendar_events(service):
    print("\nFetching Calendar Events:")
    print("-" * 30)
    
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    events_result = service.events().list(
        calendarId='primary',
        timeMin=today_start.isoformat(),
        timeMax=today_end.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    if not events:
        print('No calendar events found for today.')
    else:
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            if 'T' in start:  # Time-specific event
                event_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                event_time = event_dt.astimezone(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p')
            else:
                event_time = 'All day'
            
            print(f"- {event_time}: {event.get('summary', 'No title')}")

def get_tasks(service):
    print("\nFetching Tasks:")
    print("-" * 30)
    
    results = service.tasklists().list().execute()
    task_lists = results.get('items', [])

    if not task_lists:
        print('No task lists found.')
        return

    for task_list in task_lists:
        print(f"\nList: {task_list['title']}")
        tasks = service.tasks().list(
            tasklist=task_list['id'],
            showCompleted=True,
            showHidden=True
        ).execute()
        
        for task in tasks.get('items', []):
            due = task.get('due', 'No due date')
            if due != 'No due date':
                due_dt = datetime.fromisoformat(due.replace('Z', '+00:00'))
                ist = pytz.timezone('Asia/Kolkata')
                due_ist = due_dt.astimezone(ist)
                due = due_ist.strftime('%I:%M %p')
            
            status = '✓' if task.get('status') == 'completed' else '☐'
            print(f"{status} {task.get('title', 'Untitled')} (Due: {due})")

def main():
    try:
        # Get credentials that work for both services
        creds = get_credentials()

        # Initialize both services
        calendar_service = build('calendar', 'v3', credentials=creds)
        tasks_service = build('tasks', 'v1', credentials=creds)

        # Get both calendar events and tasks
        get_calendar_events(calendar_service)
        get_tasks(tasks_service)

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()