from curses import newpad
from textwrap import wrap
from numpy import clip
from math import floor
from os.path import join
from datetime import date, timedelta, datetime

from components import key_state_tracker, scene_manager, resources
STATUS_STRING = ['[--PENDING--]', '[IN-PROGRESS]', '[-COMPLETED-]']
KEY_MAP_DISPLAY_TABLE = [ True, True, False, False, True, True, True, False, True, False, False ]
current_selected_index = 0
selection_cursor_y_position = []
selection_cursor_x_position = (55, 69)
origin_x = origin_y = columns = rows = 0
task_state_table = []
scroll_offset = 0
def _start():
    resources.sync_task()
    intial_render()

pad = None
def intial_render():
    global pad, current_selected_index, selection_cursor_y_position, columns, rows, origin_x, origin_y, task_state_table
    columns, rows, origin_x, origin_y = scene_manager.get_drawable_screen_data()
    row_seperator = column_seperator = ''
    resources.cursor.execute('SELECT * FROM today_task;')
    entries = resources.cursor.fetchall()
    pad = newpad(1024, columns)
    selection_cursor_y_position = []
    task_state_table = []
    current_selected_index = 0

    with open(join(resources.screen_data_path, 'today_task.txt'), 'r', encoding='utf-8') as f:
        resources.stdscr.addstr(origin_y, origin_x, f.readline().rstrip())
        row_seperator = f.readline().rstrip() + '─' * (columns - 85)
        column_seperator = f.readline().rstrip()
        resources.stdscr.addstr(origin_y + 1, origin_x, row_seperator)
        resources.stdscr.refresh()
    if len(entries) == 0: 
        pad.addstr(6, (columns - 63) // 2, 'No task here yet! Try adding some in the manage task section ^^')
        return
    used_row = 0
    column_width = (32, 10, 13, 10, columns - 88)
    starting_cursor_position = (7, 42, 56, 73, 87)
    for i in range(1024):
        pad.addstr(i, 0, column_seperator)
    task_state_table = []
    x = 0
    for entry in entries:
        pad.addstr(used_row, 1, str(x))
        row_height = 1
        task_state_table.append([entry[0], entry[3]])
        for i in range(len(starting_cursor_position)):
            lines = ''
            if i == 2:
                lines = wrap(STATUS_STRING[entry[3]], column_width[i])
            elif i == 3:
                lines = wrap(str((datetime.strptime(entry[2], '%Y-%m-%d') + timedelta(days=entry[i + 1])).strftime('%Y-%m-%d')), column_width[i])
            else:
                lines = wrap(str(entry[i+1]), column_width[i])
            row_height = max(row_height, len(lines))
            for j in range(len(lines)):
                pad.addstr(used_row + j, starting_cursor_position[i], lines[j])
        selection_cursor_y_position.append(used_row)
        used_row += row_height
        pad.addstr(used_row, 0, row_seperator)
        used_row += 1
        x += 1
    pad.addstr(selection_cursor_y_position[current_selected_index], selection_cursor_x_position[0], '►')
    pad.addstr(selection_cursor_y_position[current_selected_index], selection_cursor_x_position[1], '◄')
    pad.refresh(0, 0, origin_y + 2, origin_x, origin_y + rows - 1, origin_x + columns)

def _update():
    global current_selected_index, task_state_table, scroll_offset
    if key_state_tracker.get_key_state('q', key_state_tracker.JUST_PRESSED):
        scene_manager.change_page(scene_manager.MENU_INDEX)
        return
    if len(selection_cursor_y_position) > 0:
        pad.addstr(selection_cursor_y_position[current_selected_index], selection_cursor_x_position[0], ' ')
        pad.addstr(selection_cursor_y_position[current_selected_index], selection_cursor_x_position[1], ' ')
        
        if key_state_tracker.get_key_state('w', key_state_tracker.PRESSED) or key_state_tracker.get_key_state('up', key_state_tracker.PRESSED): current_selected_index -= 1
        elif key_state_tracker.get_key_state('s', key_state_tracker.PRESSED) or key_state_tracker.get_key_state('down', key_state_tracker.PRESSED): current_selected_index += 1
        elif key_state_tracker.get_key_state('enter', key_state_tracker.PRESSED):
            task_state_table[current_selected_index][1] = (task_state_table[current_selected_index][1] + 1) % 3
            pad.addstr(selection_cursor_y_position[current_selected_index], 56, STATUS_STRING[task_state_table[current_selected_index][1]])
            resources.cursor.execute('UPDATE today_task SET status = ? WHERE id = ? ;', (int(task_state_table[current_selected_index][1]), int(task_state_table[current_selected_index][0])))
            resources.connection.commit()
        elif key_state_tracker.get_key_state('ctrl', key_state_tracker.JUST_PRESSED) and key_state_tracker.get_key_state('delete', key_state_tracker.JUST_PRESSED):
            resources.cursor.execute('DELETE FROM today_task WHERE id = ?', (int(task_state_table[current_selected_index][0]),))
            current_selection_cursor_position[1] -= 1
            resources.connection.commit()
            intial_render()
            return
        current_selected_index = clip(current_selected_index, 0, len(selection_cursor_y_position) - 1)
        pad.addstr(selection_cursor_y_position[current_selected_index], selection_cursor_x_position[0], '►')
        pad.addstr(selection_cursor_y_position[current_selected_index], selection_cursor_x_position[1], '◄')
        
        scroll_offset = int(floor(selection_cursor_y_position[current_selected_index] / (rows - 2)) * (rows - 2))
        resources.stdscr.refresh()
    pad.refresh(scroll_offset, 0, origin_y + 2, origin_x, origin_y + rows - 1, origin_x + columns)
def _end():
    global pad
    pad.clear()
    pad = None
