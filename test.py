import requests
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def test_reminder_service():
    BASE_URL = "http://localhost:5000"
    
    # Helper function to convert IST to UTC
    def ist_to_utc(ist_datetime_str):
        # Parse IST time
        ist_time = datetime.fromisoformat(ist_datetime_str).replace(tzinfo=ZoneInfo("Asia/Kolkata"))
        # Convert to UTC and format for API
        return ist_time.astimezone(ZoneInfo("UTC")).isoformat()

    def set_reminder(reminder_text, reminder_time_ist, user_id):
        url = f"{BASE_URL}/set_reminder"
        reminder_time_utc = ist_to_utc(reminder_time_ist)
        
        payload = {
            "reminder_text": reminder_text,
            "reminder_time": reminder_time_utc,
            "user_id": user_id
        }
        
        response = requests.post(url, json=payload)
        print("\nSetting Reminder:")
        print(f"IST Time: {reminder_time_ist}")
        print(f"UTC Time: {reminder_time_utc}")
        print("Response:", json.dumps(response.json(), indent=2))
        return response.json()

    def get_reminders(user_id):
        url = f"{BASE_URL}/get_reminders/{user_id}"
        response = requests.get(url)
        print("\nGetting Reminders:")
        print("Response:", json.dumps(response.json(), indent=2))
        return response.json()

    def delete_reminder(reminder_id):
        url = f"{BASE_URL}/delete_reminder/{reminder_id}"
        response = requests.delete(url)
        print("\nDeleting Reminder:")
        print("Response:", json.dumps(response.json(), indent=2))
        return response.json()

    try:
        # Test 1: Set a reminder for 2 minutes from now
        current_time = datetime.now(ZoneInfo("Asia/Kolkata"))
        reminder_time = current_time + timedelta(minutes=2)
        reminder_time_str = reminder_time.strftime('%Y-%m-%dT%H:%M:%S')
        
        user_id = "test_user_1"
        
        # Set reminder
        set_result = set_reminder(
            "Test reminder - 2 minutes from now",
            reminder_time_str,
            user_id
        )
        
        # Get reminders
        get_result = get_reminders(user_id)
        
        # Test 2: Set a reminder for tomorrow
        tomorrow = current_time + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%Y-%m-%dT%H:%M:%S')
        
        set_result_2 = set_reminder(
            "Test reminder - tomorrow",
            tomorrow_str,
            user_id
        )
        
        # Get updated list
        get_result_2 = get_reminders(user_id)
        
        # Delete the first reminder
        if get_result_2['reminders']:
            delete_reminder(get_result_2['reminders'][0]['reminder_id'])
        
        # Final check
        final_reminders = get_reminders(user_id)

    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    test_reminder_service()