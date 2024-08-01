import sys
from sqlite3 import connect
from math import floor
from os.path import join, dirname, abspath
from datetime import date, timedelta, datetime
stdscr = connection = cursor = None
task_history_column_names = ( 'date', 'all_task', 'completed_task' )
today_task_column_names = ( 'id', 'name', 'start_date', 'status', 'active_duration', 'description' )
upcoming_task_column_names = ( 'id', 'name', 'start_date', 'active_duration', 'recurrence_interval', 'remaining_recurrence', 'description' )
screen_data_path = None
def _start(_stdscr):
    global stdscr, connection, cursor, screen_data_path

    if getattr(sys, 'frozen', False): base_path = sys._MEIPASS
    else: base_path = abspath(join(dirname(abspath(__file__)), '..'))

    screen_data_path = join(base_path, 'screen_data')
    connection = connect(join(base_path, 'task.db'))
    cursor = connection.cursor()
    stdscr = _stdscr
    setup_database()
    sync_task()
def _end():
    connection.close()
def setup_database():
    cursor.execute('''CREATE TABLE IF NOT EXISTS task_history (
        date DATE UNIQUE DEFAULT CURRENT_DATE,
        all_task INTEGER NOT NULL DEFAULT 0,
        completed_task INTEGER DEFAULT 0
    );''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS today_task (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL DEFAULT '[NAME]',
        start_date DATE NOT NULL DEFAULT CURRENT_DATE,
        status INTEGER NOT NULL DEFAULT 0,
        active_duration INTEGER NOT NULL DEFAULT 1,
        description TEXT NOT NULL DEFAULT '[UNKNOWN]'
    );''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS upcoming_task (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL DEFAULT '[NAME]',
        start_date DATE NOT NULL DEFAULT CURRENT_DATE,
        active_duration INTEGER NOT NULL DEFAULT 1,
        recurrence_interval INTEGER NOT NULL DEFAULT 1,
        remaining_recurrence INTEGER DEFAULT 1,
        description TEXT NOT NULL DEFAULT '[UNKNOWN]'
    );''')
    connection.commit()
def sync_task():
    today = date.today()
    cursor.execute('SELECT * FROM today_task')
    today_tasks = cursor.fetchall()
    cursor.execute('SELECT * FROM upcoming_task')
    upcoming_tasks = cursor.fetchall()
    for upcoming_task in upcoming_tasks:
        upcoming_task = list(upcoming_task)
        if upcoming_task[5] == 0:
            cursor.execute("DELETE FROM upcoming_task WHERE id = ?", (upcoming_task[0],))
            continue
        if date.fromisoformat(upcoming_task[2]) > today: continue
        days_difference = (today - datetime.fromisoformat(upcoming_task[2]).date()).days
        passed_interval = int(floor(days_difference / upcoming_task[4]))
        upcoming_task[2] = (datetime.fromisoformat(upcoming_task[2]) + timedelta(days=passed_interval * upcoming_task[4])).date().isoformat()
        if upcoming_task[5] < 0:
            cursor.execute("INSERT INTO today_task (name, start_date, active_duration, description) VALUES (?, ?, ?, ?)", (upcoming_task[1], upcoming_task[2], upcoming_task[3], upcoming_task[6]))
            cursor.execute("UPDATE upcoming_task SET start_date = ? WHERE id = ?", ((datetime.fromisoformat(upcoming_task[2]) + timedelta(days=upcoming_task[4])).date().isoformat(), upcoming_task[0]))
            continue
        upcoming_task[5] -= passed_interval
        if upcoming_task[5] < 0: 
            cursor.execute("DELETE FROM upcoming_task WHERE id = ?", (upcoming_task[0],))
            continue
        cursor.execute("INSERT INTO today_task (name, start_date, active_duration, description) VALUES (?, ?, ?, ?)", (upcoming_task[1], upcoming_task[2], upcoming_task[3], upcoming_task[6]))
        if upcoming_task[5] == 0:
            cursor.execute("DELETE FROM upcoming_task WHERE id = ?", (upcoming_task[0],))
            continue
        cursor.execute("UPDATE upcoming_task SET start_date = ?, remaining_recurrence = ? WHERE id = ?", ((datetime.fromisoformat(upcoming_task[2]) + timedelta(days=upcoming_task[4])).date().isoformat(), upcoming_task[5], upcoming_task[0]))
    connection.commit()
    
    for today_task in today_tasks:
        if (datetime.fromisoformat(today_task[2]) + timedelta(days=today_task[4])).date() < today:
            cursor.execute("DELETE FROM today_task WHERE id = ?", (today_task[0],))
            cursor.execute("UPDATE task_history SET all_task = all_task + 1 WHERE date = ?" ,(today.isoformat(),))
            if today_task[3] == 2: cursor.execute("UPDATE task_history SET completed_task = completed_task + 1 WHERE date = ?", (today.isoformat(),))
    cursor.execute("INSERT OR IGNORE INTO task_history DEFAULT VALUES")
    connection.commit()