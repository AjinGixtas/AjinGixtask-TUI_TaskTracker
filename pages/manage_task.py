from curses import newpad, curs_set
from textwrap import wrap
from numpy import clip
from math import floor
from os.path import join
from datetime import datetime
from components import key_state_tracker, scene_manager, resources
KEY_MAP_DISPLAY_TABLE = [ True, True, True, True, True, True, True, True, True, True, False ]
pad = None
scroll_offset = 0
input_cell_char_limit = ( 96, 10, 3, 3, 3, 256 )
textbox_size = None
selection_cursor_x_position = ( 7, 43, 57, 69, 81, 94 )
selection_cursor_y_position = []
row_ids = []
column_widths = None
row_seperator = column_seperator = ''
origin_x = origin_y = columns = rows = 0
current_selection_cursor_position = [0, 0]
def _start():
    resources.sync_task()
    intial_render()
def intial_render():
    global pad, selection_cursor_y_position, columns, rows, origin_x, origin_y, column_widths, current_selection_cursor_position, row_seperator, column_seperator, row_ids, textbox_size
    columns, rows, origin_x, origin_y = scene_manager.get_drawable_screen_data()
    if pad != None: pad.clear()
    else: pad = newpad(1024, columns)
    row_ids = []
    selection_cursor_y_position = []
    column_widths = None
    current_selection_cursor_position = [0, 0]
    resources.cursor.execute('SELECT * FROM upcoming_task;')
    with open(join(resources.screen_data_path, 'manage_task.txt'), 'r', encoding='utf-8') as f:
        resources.stdscr.addstr(origin_y, origin_x, f.readline().rstrip())
        row_seperator = f.readline().rstrip() + '─' * (columns - 93)
        column_seperator = f.readline().rstrip()
        for i in range(1024):
            pad.addstr(i, 0, column_seperator);
        resources.stdscr.addstr(origin_y + 1, origin_x, row_seperator)
    resources.stdscr.refresh()
    entries = resources.cursor.fetchall()
    if len(entries) == 0: return
    used_row = 0
    column_widths = ( 32, 10, 10, 10, 10, columns - 97)
    textbox_size = (32, 10, 3, 3, 3, columns - 96)
    id = 0
    for entry in entries:
        selection_cursor_y_position.append(used_row)
        row_ids.append(entry[0])
        row_height = 1
        for i in range(len(selection_cursor_x_position)):
            cell_data = str(entry[i+1])
            if i == 2 or i == 3: cell_data = cell_data.ljust(4) + 'days'
            elif i == 4: 
                if cell_data[0] == '-': cell_data = 'inf times'
                else: cell_data = cell_data.ljust(4) + 'times'
            lines = wrap(cell_data, column_widths[i])
            for j in range(len(lines)):
                pad.addstr(used_row + j, selection_cursor_x_position[i] + 1, lines[j])
            row_height = max(row_height, len(lines))
        pad.addstr(used_row + row_height, 0, row_seperator)
        pad.addstr(used_row, 1, str(id))
        id += 1
        used_row += row_height + 1
    pad.refresh(0, 0, origin_y + 2, origin_x, origin_y + rows - 1, origin_x + columns)
current_input = ''
is_registering_input = False
def _update():
    global current_selection_cursor_position, current_input, is_registering_input, row_ids, scroll_offset
    if key_state_tracker.get_key_state('q', key_state_tracker.JUST_PRESSED) and not is_registering_input:
        scene_manager.change_page(scene_manager.MENU_INDEX)
        return
    elif key_state_tracker.get_key_state('ctrl') and key_state_tracker.get_key_state('n'):
        resources.cursor.execute('INSERT INTO upcoming_task DEFAULT VALUES')
        resources.connection.commit()
        intial_render()
    if len(selection_cursor_y_position) == 0: return
    if is_registering_input:
        if key_state_tracker.get_key_state('enter'):
            if (current_selection_cursor_position[1] == 1 and not date_validator(current_input)) or ((current_selection_cursor_position[1] == 2 or current_selection_cursor_position[1] == 3 or current_selection_cursor_position[1] == 4) and not int_validator(current_input)): 
                pad.refresh(0, 0, origin_y + 2, origin_x, origin_y + rows - 1, origin_x + columns)
                return
            is_registering_input = False
            resources.cursor.execute(f"UPDATE upcoming_task SET {resources.upcoming_task_column_names[current_selection_cursor_position[1] + 1]} = ? WHERE id = ?", (current_input, row_ids[current_selection_cursor_position[0]]))
            resources.connection.commit()
            current_input = ''
            curs_set(0)
            intial_render()
            return
        elif key_state_tracker.get_key_state('esc'):
            is_registering_input = False
            curs_set(0)
            intial_render()
            return
        elif len(current_input) < input_cell_char_limit[current_selection_cursor_position[1]]:
            for key in key_state_tracker.key_states[key_state_tracker.PRESSED]:
                if len(key.name) != 1: continue
                if key_state_tracker.get_key_state(key.name): current_input += key.name
            if key_state_tracker.get_key_state('space'): current_input += ' '
        if key_state_tracker.get_key_state('backspace'): 
            if len(current_input): current_input = current_input[:-1]
            else: current_input = ''
        wrapped_input_lines = wrap(current_input, textbox_size[current_selection_cursor_position[1]], drop_whitespace=False)
        if len(wrapped_input_lines) > 0:
            for i in range(len(wrapped_input_lines)):
                pad.addstr(selection_cursor_y_position[current_selection_cursor_position[0]] + i, 
                           selection_cursor_x_position[current_selection_cursor_position[1]] + 1, 
                           wrapped_input_lines[i].ljust(textbox_size[current_selection_cursor_position[1]]))
            pad.addstr(selection_cursor_y_position[current_selection_cursor_position[0]] + len(wrapped_input_lines), selection_cursor_x_position[current_selection_cursor_position[1]] + 1, ' ' * textbox_size[current_selection_cursor_position[1]])
            pad.move(selection_cursor_y_position[current_selection_cursor_position[0]] + len(wrapped_input_lines) - 1, selection_cursor_x_position[current_selection_cursor_position[1]] + len(wrapped_input_lines[-1]) + 1)
        else: 
            pad.addstr(selection_cursor_y_position[current_selection_cursor_position[0]] + len(wrapped_input_lines), selection_cursor_x_position[current_selection_cursor_position[1]] + 1, ' ')
            pad.move(selection_cursor_y_position[current_selection_cursor_position[0]], selection_cursor_x_position[current_selection_cursor_position[1]])
    else:
        if key_state_tracker.get_key_state('enter'): 
            is_registering_input = True
            resources.cursor.execute(f'SELECT {resources.upcoming_task_column_names[current_selection_cursor_position[1] + 1]} FROM upcoming_task WHERE id = ?', (row_ids[current_selection_cursor_position[0]],))
            current_input = str(resources.cursor.fetchall()[0][0])
            curs_set(1)
        elif key_state_tracker.get_key_state('ctrl', key_state_tracker.JUST_PRESSED) and key_state_tracker.get_key_state('delete', key_state_tracker.JUST_PRESSED):
            resources.cursor.execute(f'DELETE FROM upcoming_task WHERE id = ?', (row_ids[current_selection_cursor_position[0]],))
            resources.connection.commit()
            intial_render()
        else:
            cell_navigation()
            scroll_offset = int(floor(selection_cursor_y_position[current_selection_cursor_position[0]] / (rows - 2)) * (rows - 2))
    pad.refresh(scroll_offset, 0, origin_y + 2, origin_x, origin_y + rows - 1, origin_x + columns)
def cell_navigation():
    global current_selection_cursor_position
    pad.addstr(selection_cursor_y_position[current_selection_cursor_position[0]], selection_cursor_x_position[current_selection_cursor_position[1]], ' ')
    if key_state_tracker.get_key_state('a') or key_state_tracker.get_key_state('left'): current_selection_cursor_position[1] -= 1
    elif key_state_tracker.get_key_state('d') or key_state_tracker.get_key_state('right'): current_selection_cursor_position[1] += 1
    elif key_state_tracker.get_key_state('w') or key_state_tracker.get_key_state('up'): current_selection_cursor_position[0] -= 1
    elif key_state_tracker.get_key_state('s') or key_state_tracker.get_key_state('down'): current_selection_cursor_position[0] += 1
    current_selection_cursor_position = [ 
        int(clip(current_selection_cursor_position[0], 0, len(selection_cursor_y_position) - 1)), 
        int(clip(current_selection_cursor_position[1], 0, len(selection_cursor_x_position) - 1)) ]
    pad.addstr(selection_cursor_y_position[current_selection_cursor_position[0]], selection_cursor_x_position[current_selection_cursor_position[1]], '►')
def duration_validator():
    pass  
def int_validator(input):
    try:
        int(input)
        return True
    except ValueError: return False
def date_validator(input):
    try:
        datetime.strptime(input, '%Y-%m-%d')
        return True
    except ValueError: return False
def _end():
    global pad
    pad.clear()
    pad = None
