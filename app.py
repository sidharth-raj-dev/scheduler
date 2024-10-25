import sys
import os
import logging
from dotenv import load_dotenv
import json
from datetime import datetime, timezone, timedelta
import threading
import time

sys.path.append(os.getcwd()+'/myenv/lib/python3.10/site-packages')
load_dotenv()
MACHINE = os.getenv('MACHINE', 'local')

from flask import Flask, request, jsonify, send_from_directory
from sqlalchemy import create_engine, Table, Column, String, DateTime, MetaData, JSON
from sqlalchemy.sql import select

# Add time preferences constants
TIME_PREFERENCES = {
    'morning': '08:00',
    'afternoon': '14:00',
    'evening': '19:00'
}

# Initialize Flask and logging
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'reminders.sqlite'))
engine = create_engine(f'sqlite:///{db_path}')
metadata = MetaData()

# Updated reminders table with new columns
reminders = Table(
    'reminders', metadata,
    Column('id', String, primary_key=True),
    Column('reminder_text', String),
    Column('reminder_time', DateTime),
    Column('user_id', String),
    Column('status', String, default='pending'),
    Column('recurrence_type', String, default='none'),  # none, daily, weekly, monthly, monthly_weekday
    Column('recurrence_pattern', String),  # JSON string
    Column('time_preference', String),  # morning, afternoon, evening
    Column('next_occurrence', DateTime),
    Column('tags', String)  # JSON string array
)

# Create tables
metadata.create_all(engine)

def calculate_next_occurrence(reminder_time, recurrence_type, recurrence_pattern, time_preference):
    """Calculate next occurrence based on recurrence pattern"""
    if recurrence_type == 'none':
        return None
        
    base_time = datetime.now(timezone.utc)
    pattern = json.loads(recurrence_pattern) if recurrence_pattern else {}
    time_of_day = TIME_PREFERENCES[time_preference]
    hour, minute = map(int, time_of_day.split(':'))
    
    if recurrence_type == 'daily':
        next_date = base_time + timedelta(days=1)
        return next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
    elif recurrence_type == 'weekly':
        target_weekday = pattern.get('weekday', 0)
        days_ahead = target_weekday - base_time.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_date = base_time + timedelta(days=days_ahead)
        return next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
    elif recurrence_type == 'monthly_weekday':
        weekday = pattern.get('weekday', 0)
        week_numbers = pattern.get('week_numbers', [1])
        
        # Get next month's dates
        next_month = base_time.replace(day=1) + timedelta(days=32)
        next_month = next_month.replace(day=1)
        
        # Find all occurrences of the weekday
        weekday_dates = []
        current = next_month
        while current.month == next_month.month:
            if current.weekday() == weekday:
                week_num = (current.day - 1) // 7 + 1
                if week_num in week_numbers or (-1 in week_numbers and current.month != (current + timedelta(days=7)).month):
                    weekday_dates.append(current)
            current += timedelta(days=1)
            
        if weekday_dates:
            next_date = min(weekday_dates)
            return next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
    return None

def check_reminders():
    """Background thread to check and trigger reminders"""
    while True:
        try:
            with engine.connect() as conn:
                now = datetime.now(timezone.utc)
                query = select(reminders).where(
                    reminders.c.status == 'pending',
                    reminders.c.reminder_time <= now
                )
                
                result = conn.execute(query)
                due_reminders = result.fetchall()
                
                for reminder in due_reminders:
                    logger.info(f"REMINDER for user {reminder.user_id}: {reminder.reminder_text}")
                    
                    if reminder.recurrence_type != 'none':
                        # Calculate next occurrence for recurring reminders
                        next_time = calculate_next_occurrence(
                            reminder.reminder_time,
                            reminder.recurrence_type,
                            reminder.recurrence_pattern,
                            reminder.time_preference
                        )
                        
                        if next_time:
                            conn.execute(
                                reminders.update()
                                .where(reminders.c.id == reminder.id)
                                .values(
                                    reminder_time=next_time,
                                    next_occurrence=next_time
                                )
                            )
                    else:
                        # Mark one-time reminder as completed
                        conn.execute(
                            reminders.update()
                            .where(reminders.c.id == reminder.id)
                            .values(status='completed')
                        )
                    
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Error checking reminders: {e}")
            
        time.sleep(10)

@app.route('/')
def index():
    try:
        if MACHINE == 'local':
            return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')
        else:
            return send_from_directory('/home/sidharthraj/mysite/index.html', 'index.html')
    except Exception as e:
        logger.error(f"Error serving index page: {e}")
        return jsonify({'error': 'Could not load the page'}), 500

@app.route('/set_reminder', methods=['POST'])
def set_reminder():
    try:
        data = request.json
        reminder_text = data.get('reminder_text')
        time_preference = data.get('time_preference', 'morning')
        user_id = data.get('user_id')
        recurrence_type = data.get('recurrence_type', 'none')
        recurrence_pattern = json.dumps(data.get('recurrence_pattern', {}))
        tags = json.dumps(data.get('tags', []))

        if not all([reminder_text, user_id]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Calculate initial reminder time
        hour, minute = map(int, TIME_PREFERENCES[time_preference].split(':'))
        reminder_time = datetime.now(timezone.utc).replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
        
        # For recurring reminders, calculate next occurrence
        next_occurrence = calculate_next_occurrence(
            reminder_time, recurrence_type, recurrence_pattern, time_preference
        ) if recurrence_type != 'none' else reminder_time

        reminder_id = f"reminder_{user_id}_{datetime.now().timestamp()}"
        
        with engine.connect() as conn:
            conn.execute(reminders.insert().values(
                id=reminder_id,
                reminder_text=reminder_text,
                reminder_time=next_occurrence or reminder_time,
                user_id=user_id,
                status='pending',
                recurrence_type=recurrence_type,
                recurrence_pattern=recurrence_pattern,
                time_preference=time_preference,
                next_occurrence=next_occurrence,
                tags=tags
            ))
            conn.commit()

        return jsonify({
            'message': 'Reminder set successfully',
            'reminder_id': reminder_id,
            'next_occurrence': next_occurrence.isoformat() if next_occurrence else None
        })

    except Exception as e:
        logger.error(f"Error setting reminder: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_reminders/<user_id>', methods=['GET'])
def get_reminders(user_id):
    try:
        with engine.connect() as conn:
            query = select(reminders).where(reminders.c.user_id == user_id)
            result = conn.execute(query)
            user_reminders = []
            
            for row in result:
                recurrence_info = ''
                if row.recurrence_type != 'none':
                    pattern = json.loads(row.recurrence_pattern)
                    if row.recurrence_type == 'monthly_weekday':
                        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        week_numbers = pattern.get('week_numbers', [])
                        week_desc = 'Last' if -1 in week_numbers else '/'.join([str(n) + 'st' for n in week_numbers])
                        weekday = weekday_names[pattern.get('weekday', 0)]
                        recurrence_info = f"Every {week_desc} {weekday}"
                    elif row.recurrence_type == 'daily':
                        recurrence_info = 'Every day'
                    elif row.recurrence_type == 'weekly':
                        weekday = weekday_names[pattern.get('weekday', 0)]
                        recurrence_info = f'Every {weekday}'
                
                user_reminders.append({
                    'reminder_id': row.id,
                    'reminder_text': row.reminder_text,
                    'next_occurrence': row.next_occurrence.isoformat() if row.next_occurrence else None,
                    'status': row.status,
                    'recurrence_info': recurrence_info,
                    'time_preference': row.time_preference,
                    'tags': json.loads(row.tags) if row.tags else []
                })

        return jsonify({'reminders': user_reminders})
    except Exception as e:
        logger.error(f"Error getting reminders: {e}")
        return jsonify({'error': str(e)}), 500

# Start the background thread
reminder_thread = threading.Thread(target=check_reminders, daemon=True)
reminder_thread.start()

if __name__ == '__main__':
    app.run(debug=True)