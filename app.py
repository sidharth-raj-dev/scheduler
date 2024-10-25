import sys
import os
import logging
from dotenv import load_dotenv

sys.path.append(os.getcwd()+'/myenv/lib/python3.10/site-packages')
load_dotenv()
MACHINE = os.getenv('MACHINE', 'local')

from flask import Flask, request, jsonify, send_from_directory
from sqlalchemy import create_engine, Table, Column, String, DateTime, MetaData
from sqlalchemy.sql import select
import threading
import time
from datetime import datetime, timezone

# set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database setup
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'reminders.sqlite'))
engine = create_engine(f'sqlite:///{db_path}')
metadata = MetaData()

# Define reminders table
reminders = Table(
    'reminders', metadata,
    Column('id', String, primary_key=True),
    Column('reminder_text', String),
    Column('reminder_time', DateTime),
    Column('user_id', String),
    Column('status', String, default='pending')  # pending, completed, or failed
)

# Create tables
metadata.create_all(engine)

def check_reminders():
    """Background thread to check and trigger reminders"""
    while True:
        try:
            with engine.connect() as conn:
                # Get all pending reminders that are due
                now = datetime.now(timezone.utc)
                query = select(reminders).where(
                    reminders.c.status == 'pending',
                    reminders.c.reminder_time <= now
                )

                result = conn.execute(query)
                due_reminders = result.fetchall()
                
                for reminder in due_reminders:
                    logger.info(f"REMINDER for user {reminder.user_id}: {reminder.reminder_text}")
                    # Mark reminder as completed
                    conn.execute(
                        reminders.update()
                        .where(reminders.c.id == reminder.id)
                        .values(status='completed')
                    )
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Error checking reminders: {e}")
            
        time.sleep(10)  # Check every 10 seconds

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
        reminder_time_str = data.get('reminder_time').rstrip('Z')
        reminder_time = datetime.fromisoformat(reminder_time_str)
        user_id = data.get('user_id')

        if not all([reminder_text, reminder_time, user_id]):
            return jsonify({'error': 'Missing required fields'}), 400

        reminder_id = f"reminder_{user_id}_{datetime.now().timestamp()}"
        
        with engine.connect() as conn:
            conn.execute(reminders.insert().values(
                id=reminder_id,
                reminder_text=reminder_text,
                reminder_time=reminder_time,
                user_id=user_id,
                status='pending'
            ))
            conn.commit()

        return jsonify({
            'message': 'Reminder set successfully',
            'reminder_id': reminder_id,
            'reminder_time': reminder_time.isoformat()
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
                user_reminders.append({
                    'reminder_id': row.id,
                    'reminder_text': row.reminder_text,
                    'reminder_time': row.reminder_time.isoformat(),
                    'status': row.status
                })

        return jsonify({'reminders': user_reminders})
    except Exception as e:
        logger.error(f"Error getting reminders: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete_reminder/<reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    try:
        with engine.connect() as conn:
            conn.execute(
                reminders.delete().where(reminders.c.id == reminder_id)
            )
            conn.commit()
        return jsonify({'message': 'Reminder deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Start the background thread for checking reminders
reminder_thread = threading.Thread(target=check_reminders, daemon=True)
reminder_thread.start()

if __name__ == '__main__':
    app.run(debug=True)