// State management
let state = {
    selectedType: null,
    selectedTime: 'morning',
    selectedRecurrence: 'none',
    selectedWeekDay: null,
    selectedWeekNumbers: [],
    selectedMonthDay: null,
    tags: [],
    userId: 'user_' + Math.random().toString(36).substr(2, 9) // Simple user ID generation
};

// Helper functions
const addClass = (element, className) => element.classList.add(className);
const removeClass = (element, className) => element.classList.remove(className);

const toggleSelection = (button, type, value) => {
    document.querySelectorAll(`[data-${type}]`).forEach(btn => {
        removeClass(btn, 'bg-blue-500');
        removeClass(btn, 'text-white');
    });
    addClass(button, 'bg-blue-500');
    addClass(button, 'text-white');
    return value;
};

const toggleMultiSelection = (button) => {
    button.classList.toggle('bg-blue-500');
    button.classList.toggle('text-white');
};

// Event Listeners Setup
document.addEventListener('DOMContentLoaded', () => {
    setupTypeButtons();
    setupTimeButtons();
    setupRecurrenceButtons();
    setupWeekDayButtons();
    setupMonthlyPatternButtons();
    setupTagInput();
    setupSetReminderButton();
    loadReminders();
});

function setupTypeButtons() {
    document.getElementById('reminderTypes').addEventListener('click', (e) => {
        if (e.target.dataset.type) {
            state.selectedType = toggleSelection(e.target, 'type', e.target.dataset.type);
        }
    });
}

function setupTimeButtons() {
    document.getElementById('timePreferences').addEventListener('click', (e) => {
        if (e.target.dataset.time) {
            state.selectedTime = toggleSelection(e.target, 'time', e.target.dataset.time);
        }
    });
}

function setupRecurrenceButtons() {
    document.getElementById('recurrenceTypes').addEventListener('click', (e) => {
        if (e.target.dataset.recurrence) {
            state.selectedRecurrence = toggleSelection(e.target, 'recurrence', e.target.dataset.recurrence);
            document.getElementById('weeklyPattern').classList.add('hidden');
            document.getElementById('monthlyPattern').classList.add('hidden');

            if (state.selectedRecurrence === 'weekly') {
                document.getElementById('weeklyPattern').classList.remove('hidden');
            } else if (state.selectedRecurrence === 'monthly_weekday') {
                document.getElementById('monthlyPattern').classList.remove('hidden');
            }
        }
    });
}

function setupWeekDayButtons() {
    document.getElementById('weekDays').addEventListener('click', (e) => {
        if (e.target.dataset.day) {
            state.selectedWeekDay = toggleSelection(e.target, 'day', parseInt(e.target.dataset.day));
        }
    });
}

function setupMonthlyPatternButtons() {
    document.getElementById('weekNumbers').addEventListener('click', (e) => {
        if (e.target.dataset.week) {
            toggleMultiSelection(e.target);
            const weekNum = parseInt(e.target.dataset.week);
            const index = state.selectedWeekNumbers.indexOf(weekNum);
            if (index === -1) {
                state.selectedWeekNumbers.push(weekNum);
            } else {
                state.selectedWeekNumbers.splice(index, 1);
            }
        }
    });

    document.getElementById('monthlyWeekDays').addEventListener('click', (e) => {
        if (e.target.dataset.day) {
            state.selectedMonthDay = toggleSelection(e.target, 'day', parseInt(e.target.dataset.day));
        }
    });
}

function setupTagInput() {
    const tagInput = document.getElementById('tagInput');
    const activeTags = document.getElementById('activeTags');

    tagInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && e.target.value.trim()) {
            const tag = e.target.value.trim();
            if (!state.tags.includes(tag)) {
                state.tags.push(tag);
                const tagElement = createTagElement(tag);
                activeTags.appendChild(tagElement);
            }
            e.target.value = '';
        }
    });
}

function createTagElement(tag) {
    const div = document.createElement('div');
    div.className = 'bg-gray-200 px-2 py-1 rounded-lg flex items-center gap-2';
    div.innerHTML = `
        <span>${tag}</span>
        <button class="text-gray-500 hover:text-gray-700">×</button>
    `;
    div.querySelector('button').onclick = () => {
        div.remove();
        state.tags = state.tags.filter(t => t !== tag);
    };
    return div;
}

function setupSetReminderButton() {
    document.getElementById('setReminder').addEventListener('click', setReminder);
}

async function setReminder() {
    const reminderText = document.getElementById('reminderText').value;
    if (!reminderText) {
        alert('Please enter reminder text');
        return;
    }

    const data = {
        reminder_text: reminderText,
        time_preference: state.selectedTime,
        user_id: state.userId,
        recurrence_type: state.selectedRecurrence,
        recurrence_pattern: {},
        tags: state.tags
    };

    if (state.selectedRecurrence === 'weekly' && state.selectedWeekDay !== null) {
        data.recurrence_pattern = { weekday: state.selectedWeekDay };
    } else if (state.selectedRecurrence === 'monthly_weekday' && state.selectedMonthDay !== null) {
        data.recurrence_pattern = {
            weekday: state.selectedMonthDay,
            week_numbers: state.selectedWeekNumbers.length ? state.selectedWeekNumbers : [1]
        };
    }

    try {
        const response = await fetch('/set_reminder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Failed to set reminder');

        // Reset form
        document.getElementById('reminderText').value = '';
        state.tags = [];
        document.getElementById('activeTags').innerHTML = '';

        // Reload reminders
        loadReminders();
    } catch (error) {
        console.error('Error setting reminder:', error);
        alert('Failed to set reminder');
    }
}

async function loadReminders() {
    try {
        const response = await fetch(`/get_reminders/${state.userId}`);
        if (!response.ok) throw new Error('Failed to load reminders');

        const data = await response.json();
        displayReminders(data.reminders);
    } catch (error) {
        console.error('Error loading reminders:', error);
    }
}

function displayReminders(reminders) {
    const container = document.getElementById('reminders');
    container.innerHTML = '';

    reminders.forEach(reminder => {
        const div = document.createElement('div');
        div.className = 'bg-white p-4 rounded-lg shadow';

        const nextOccurrence = reminder.next_occurrence ?
            new Date(reminder.next_occurrence).toLocaleString() : 'No next occurrence';

        const tagsHtml = reminder.tags.map(tag =>
            `<span class="bg-gray-200 px-2 py-1 rounded-lg text-sm">${tag}</span>`
        ).join(' ');

        div.innerHTML = `
            <div class="flex justify-between items-start mb-2">
                <div class="flex-1">
                    <h3 class="font-semibold">${reminder.reminder_text}</h3>
                    <p class="text-sm text-gray-600">Next: ${nextOccurrence}</p>
                    ${reminder.recurrence_info ?
                `<p class="text-sm text-gray-600">Repeats: ${reminder.recurrence_info}</p>`
                : ''
            }
                    <p class="text-sm text-gray-600">Time: ${reminder.time_preference}</p>
                    ${reminder.tags.length ?
                `<div class="mt-2 flex flex-wrap gap-2">${tagsHtml}</div>`
                : ''
            }
                </div>
                <button
                    class="text-red-500 hover:text-red-700 ml-4"
                    onclick="deleteReminder('${reminder.reminder_id}')"
                >
                    ×
                </button>
            </div>
            ${reminder.status === 'failed' ?
                '<p class="text-red-500 text-sm">Failed to process - will retry</p>'
                : ''
            }
        `;
        container.appendChild(div);
    });
}

async function deleteReminder(reminderId) {
    if (!confirm('Are you sure you want to delete this reminder?')) {
        return;
    }

    try {
        const response = await fetch(`/delete_reminder/${reminderId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete reminder');

        // Reload reminders after successful deletion
        loadReminders();
    } catch (error) {
        console.error('Error deleting reminder:', error);
        alert('Failed to delete reminder');
    }
}

// Initial selection of morning time preference
window.onload = () => {
    const morningButton = document.querySelector('[data-time="morning"]');
    if (morningButton) {
        addClass(morningButton, 'bg-blue-500');
        addClass(morningButton, 'text-white');
    }
    loadReminders();
};

// Auto-refresh reminders every minute
setInterval(loadReminders, 60000);