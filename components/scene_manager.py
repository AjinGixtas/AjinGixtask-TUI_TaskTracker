from pages import menu, today_task, manage_task, past_task
from components import resources
current_index = -1
current_page = menu
MENU_INDEX = -1
TODAY_TASK_INDEX = 0
MANAGE_TASK_INDEX = 1
PAST_TASK_INDEX = 2
def _start():
    draw_screen_bone(menu.KEY_MAP_DISPLAY_TABLE)
    current_page._start()
def change_page(index):
    global current_page
    current_page._end()
    current_index = index
    if current_index == MENU_INDEX: current_page = menu
    elif current_index == TODAY_TASK_INDEX: current_page = today_task
    elif current_index == MANAGE_TASK_INDEX: current_page = manage_task
    elif current_index == PAST_TASK_INDEX: current_page = past_task
    draw_screen_bone(current_page.KEY_MAP_DISPLAY_TABLE)
    current_page._start()

columns = 0
rows = 0
origin_x = 0
origin_y = 0
def draw_screen_bone(key_map_display_table):
    from shutil import get_terminal_size
    from curses import newpad
    global columns, rows, origin_x, origin_y
    columns, rows = get_terminal_size()
    resources.stdscr.clear()
    resources.stdscr.refresh()
    resources.stdscr.addstr(0, 0, '┌' + '─' * (columns - 2) + '┐')
    for i in range(rows - 3): resources.stdscr.addstr(i + 1, 0, '│' + ' ' * (columns - 2) + '│')
    resources.stdscr.refresh()
    with open(resources.screen_data_path + '/key_lookup_table.txt', 'r') as f:
        input = f.readline()
        y, padding = map(int, input.split())
        pad = newpad(12, columns)
        pad.addstr(0, 0, '├' + '─' * (columns - 2) + '┤')
        pad.addstr(1, 0, '│' + ' ' * (columns - 2) + '│')
        cursor_x = 2
        cursor_y = 1
        for i in range(y):
            key_info = f.readline().rstrip()
            if not key_map_display_table[i]: continue
            pad.addstr(cursor_y, cursor_x, key_info)
            cursor_x += padding
            if cursor_x + padding >= columns: 
                cursor_x = 2
                cursor_y += 1
                pad.addstr(cursor_y, 0, '│' + ' ' * (columns - 2) + '│')
        pad.refresh(0, 0, rows - cursor_y - 1, 0, rows - 1, columns - 1)
    columns -= 2
    rows -= 2 + cursor_y
    origin_x = origin_y = 1
def get_drawable_screen_data():
    return (columns, rows, origin_x, origin_y)
def _end():
    pass