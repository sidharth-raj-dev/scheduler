from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
from datetime import datetime
import pytz

# Note: We need to add tasks API scope
SCOPES = ['https://www.googleapis.com/auth/tasks.readonly']

def get_tasks():
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

        # Build the Tasks service instead of Calendar
        service = build('tasks', 'v1', credentials=creds)

        # First, get all task lists
        results = service.tasklists().list().execute()
        task_lists = results.get('items', [])

        if not task_lists:
            print('No task lists found.')
            return

        print('\nYour Task Lists:')
        for task_list in task_lists:
            print(f"\nList: {task_list['title']}")
            
            # Get tasks in this list
            tasks = service.tasks().list(
                tasklist=task_list['id'],
                showCompleted=True,
                showHidden=True
            ).execute()
            
            # Print all tasks
            for task in tasks.get('items', []):
                due = task.get('due', 'No due date')
                if due != 'No due date':
                    # Convert UTC to IST
                    due_dt = datetime.fromisoformat(due.replace('Z', '+00:00'))
                    ist = pytz.timezone('Asia/Kolkata')
                    due_ist = due_dt.astimezone(ist)
                    due = due_ist.strftime('%I:%M %p')
                
                status = '✓' if task.get('status') == 'completed' else '☐'
                print(f"{status} {task.get('title', 'Untitled')} (Due: {due})")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    get_tasks()