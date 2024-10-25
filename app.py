from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime
import os
from flask import Flask, request, jsonify
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure APScheduler
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}

executors = {
    'default': ThreadPoolExecutor(20)
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    timezone='UTC'
)

def init_scheduler():
    """Initialize the scheduler"""
    if not scheduler.running:
        try:
            scheduler.start()
            logger.info("Scheduler started successfully")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")

def send_reminder(reminder_text, user_id):
    """
    Function that gets called when a reminder is due
    """
    logger.info(f"REMINDER for user {user_id}: {reminder_text}")

@app.route('/')
def home():
    try:
        with open('/home/sidharthraj/mysite/index.html', 'r') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return "Error loading page", 500

@app.route('/set_reminder', methods=['POST'])
def set_reminder():
    try:
        data = request.json
        reminder_text = data.get('reminder_text')
        reminder_time = datetime.fromisoformat(data.get('reminder_time'))
        user_id = data.get('user_id')

        if not all([reminder_text, reminder_time, user_id]):
            return jsonify({'error': 'Missing required fields'}), 400

        job = scheduler.add_job(
            send_reminder,
            'date',
            run_date=reminder_time,
            args=[reminder_text, user_id],
            id=f"reminder_{user_id}_{datetime.now().timestamp()}"
        )

        return jsonify({
            'message': 'Reminder set successfully',
            'job_id': job.id,
            'reminder_time': reminder_time.isoformat()
        })

    except Exception as e:
        logger.error(f"Error setting reminder: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_reminders/<user_id>', methods=['GET'])
def get_reminders(user_id):
    jobs = scheduler.get_jobs()
    user_reminders = []

    for job in jobs:
        if job.args and job.args[1] == user_id:
            user_reminders.append({
                'job_id': job.id,
                'reminder_text': job.args[0],
                'reminder_time': job.next_run_time.isoformat()
            })

    return jsonify({'reminders': user_reminders})

@app.route('/delete_reminder/<job_id>', methods=['DELETE'])
def delete_reminder(job_id):
    try:
        scheduler.remove_job(job_id)
        return jsonify({'message': 'Reminder deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize scheduler when the app starts
init_scheduler()

if __name__ == '__main__':
    app.run(debug=True)