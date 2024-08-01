from curses import newpad
from numpy import clip
from os.path import join
from datetime import datetime, timedelta
from components import key_state_tracker, scene_manager, resources
KEY_MAP_DISPLAY_TABLE = ( True, True, True, True, True, True, True, False, False, False, True )
MONTH_NAMES = ( 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec' )
FIRST_DAYS_OF_MONTH = ((1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335), (1, 32, 61, 92, 122, 153, 183, 214, 245, 275, 306, 336))
IS_LEAP_YEAR_FUNC = lambda year: year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
CALENDAR = 0
YEAR = 1
MAX_DAY = 0
FOCUS_CHAR_POSITION = ((0, 2), (11, 96))
OLDEST_YEAR = -1
ANCHOR = (0, 0)
current_focused_zone_index = CALENDAR
pad = None
columns = rows = origin_x = origin_y = 0
starting_weekday = 0
current_focused_zone_index = 0
date_cursor_position = 0
year_selection_position = 0
cell_origin = [0, 0]
PROGRESS_CHAR = ( '□', '░', '▒', '▓', '█' )
data = {}
def _start():
    resources.sync_task()
    intial_render()
def intial_render():
    global pad, columns, rows, origin_x, origin_y, OLDEST_YEAR, year_selection_position, date_cursor_position, starting_weekday, current_focused_zone_index, cell_origin, ANCHOR
    columns, rows, origin_x, origin_y = scene_manager.get_drawable_screen_data()
    ANCHOR = (max((rows - 17) // 2, 1), max((columns - 117) // 2, 1))
    starting_weekday = 0
    current_focused_zone_index = 0
    date_cursor_position = 0
    year_selection_position = 0
    cell_origin = [0, 0]
    if pad != None: pad.clear()
    else: pad = newpad(1024, columns)
    with open(join(resources.screen_data_path, 'past_task.txt'), 'r', encoding='utf-8') as f:
        for i in range(23):
            pad.addstr(i, 0, f.readline().rstrip())
    resources.cursor.execute('SELECT MIN(date) AS oldest_date FROM task_history;')
    OLDEST_YEAR = datetime.fromisoformat(resources.cursor.fetchone()[0]).year
    pad.addstr(15, 105, str(datetime.now().year))
    pad.addstr(16, 105, str(OLDEST_YEAR))
    render_year_board(datetime.now().year)
    if OLDEST_YEAR == datetime.now().year: pad.addstr(13, 101, ' ')
    pad.refresh(0, 0, ANCHOR[0], ANCHOR[1], 17, 117)
    updated_record_datas = data.get(date_cursor_position, [ (datetime(year_selection_position, 1, 1) + timedelta(days=date_cursor_position)).date(), 0, 0, '0.00 %'])
    for i in range(len(updated_record_datas)):
        pad.addstr(13 + i, 24, str(updated_record_datas[i]).ljust(20))
def _update():
    global current_focused_zone_index   
    if key_state_tracker.get_key_state('q', key_state_tracker.JUST_PRESSED):
        scene_manager.change_page(scene_manager.MENU_INDEX)
        return
    pad.addstr(FOCUS_CHAR_POSITION[current_focused_zone_index][0], FOCUS_CHAR_POSITION[current_focused_zone_index][1], ' ')
    if key_state_tracker.get_key_state('tab', key_state_tracker.JUST_PRESSED): current_focused_zone_index = (current_focused_zone_index + 1) % 2
    pad.addstr(FOCUS_CHAR_POSITION[current_focused_zone_index][0], FOCUS_CHAR_POSITION[current_focused_zone_index][1], '✶')
    if current_focused_zone_index == CALENDAR: handle_calendar_input()
    elif current_focused_zone_index == YEAR: handle_year_input()
    pad.refresh(0, 0, ANCHOR[0], ANCHOR[1], ANCHOR[0] + 17, ANCHOR[1] + 117)
def _end():
    global pad
    pad.clear()
    pad = None
def render_year_board(year):
    global starting_weekday, cell_origin, MAX_DAY, year_selection_position, date_cursor_position, current_month_index, data
    is_leap_year = 1 if IS_LEAP_YEAR_FUNC(year) else 0
    data = {}
    current_month_index = 0
    date_cursor_position = 0
    starting_weekday = datetime(year, 1, 1).weekday()
    cell_origin = [3 + starting_weekday, 8]
    pad.addstr(cell_origin[0], cell_origin[1]-1, '►')
    MAX_DAY = datetime(year, 12, 31).timetuple().tm_yday
    with open(join(resources.screen_data_path, 'past_task.txt'), 'r', encoding='utf-8') as f:
        for i in range(10): pad.addstr(i, 0, f.readline().strip('\n'))
    for i in range(MAX_DAY):
        pad.addstr(cell_origin[0], cell_origin[1], PROGRESS_CHAR[0])
        if cell_origin[0] == 4 and current_month_index < 12 and FIRST_DAYS_OF_MONTH[is_leap_year][current_month_index] <= i:
            pad.addstr(1, cell_origin[1], MONTH_NAMES[current_month_index])
            current_month_index += 1
        cell_origin[0] += 1
        if cell_origin[0] == 10:
            cell_origin[0] = 3
            cell_origin[1] += 2
    resources.cursor.execute("SELECT * FROM task_history WHERE strftime('%Y', date) = ?", (str(year),))
    records = resources.cursor.fetchall()
    for record in records:
        index = datetime.fromisoformat(record[0]).timetuple().tm_yday - 1
        if record[2] == 0 or record[1] == 0: continue
        completion_rate = record[2] / record[1]
        pad.addstr(3 + (index + starting_weekday) % 7, 8 + ((index + starting_weekday) // 7) * 2, PROGRESS_CHAR[0 if completion_rate == 0 else 1 if completion_rate < 1/3 else 2 if completion_rate < 2/3 else 3 if completion_rate < 1 else 4])
        data[index] = [ record[0], record[1], record[2], f"{completion_rate * 100.0:.2f} %" ]
    year_selection_position = year
    pad.addstr(13, 104, str(year))

def handle_calendar_input():
    global date_cursor_position
    pad.addstr(3 + (starting_weekday + date_cursor_position) % 7, 7 + ((starting_weekday + date_cursor_position) // 7) * 2, ' ')
    _ = date_cursor_position
    if key_state_tracker.get_key_state('w') or key_state_tracker.get_key_state('up'): date_cursor_position -= 1
    elif key_state_tracker.get_key_state('s') or key_state_tracker.get_key_state('down'): date_cursor_position += 1
    elif key_state_tracker.get_key_state('a') or key_state_tracker.get_key_state('left'): date_cursor_position -= 7
    elif key_state_tracker.get_key_state('d') or key_state_tracker.get_key_state('right'): date_cursor_position += 7
    date_cursor_position = int(clip(date_cursor_position, 0, MAX_DAY - 1))
    if _ != date_cursor_position:
        updated_record_datas = data.get(date_cursor_position, [ (datetime(year_selection_position, 1, 1) + timedelta(days=date_cursor_position)).date(), 0, 0, '0.00 %'])
        for i in range(len(updated_record_datas)):
            pad.addstr(13 + i, 24, str(updated_record_datas[i]).ljust(20))
    pad.addstr(3 + (starting_weekday + date_cursor_position) % 7, 7 + ((starting_weekday + date_cursor_position) // 7) * 2, '►')

def handle_year_input():
    global year_selection_position
    if key_state_tracker.get_key_state('a') or key_state_tracker.get_key_state('left'):    
        year_selection_position -= 1
        if year_selection_position <= OLDEST_YEAR: 
            pad.addstr(13, 101, ' ')
            year_selection_position = OLDEST_YEAR
        else: pad.addstr(13, 101, '<')
        pad.addstr(13, 110, '>')
        render_year_board(year_selection_position)
    elif key_state_tracker.get_key_state('d') or key_state_tracker.get_key_state('right'):
        year_selection_position += 1
        if year_selection_position >= datetime.now().year: 
            pad.addstr(13, 110, ' ')
            year_selection_position = datetime.now().year
        else: pad.addstr(13, 110, '>')
        pad.addstr(13, 101, '<')
        render_year_board(year_selection_position)
    pad.addstr(13, 104, str(year_selection_position))