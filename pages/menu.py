from components import key_state_tracker, scene_manager, resources
KEY_MAP_DISPLAY_TABLE = [ True, True, False, False, True, True, True, False, False, False, False ]
ANCHOR = None
cursor_origin_x = 16
cursor_origin_y = 4
columns = rows = origin_x = origin_y = 0
index = 0
pad = None
def _start():
    from curses import newpad
    global cursor_origin_x, cursor_origin_y, columns, rows, max_index, pad, ANCHOR
    columns, rows, origin_x, origin_y = scene_manager.get_drawable_screen_data()
    with open(resources.screen_data_path + '/menu.txt', 'r', encoding='utf-8') as f:
        input = f.readline()
        y, x = map(int, input.split())
        pad = newpad(y, x)
        for i in range(y):
            pad.addstr(i, 0, f.readline().rstrip())
        ANCHOR = ((rows - y) // 2, (columns - x) // 2)
        pad.refresh(0, 0, ANCHOR[0], ANCHOR[1], rows, columns)
def _update():
    global index, max_index, cursor_origin_x, cursor_origin_y
    pad.addstr(cursor_origin_y + index, cursor_origin_x, ' ')
    if key_state_tracker.get_key_state('enter', key_state_tracker.JUST_PRESSED): 
        scene_manager.change_page(index)
        return
    elif key_state_tracker.get_key_state('s', key_state_tracker.JUST_PRESSED) or key_state_tracker.get_key_state('down', key_state_tracker.JUST_PRESSED): index += 1
    elif key_state_tracker.get_key_state('w', key_state_tracker.JUST_PRESSED) or key_state_tracker.get_key_state('up', key_state_tracker.JUST_PRESSED): index -= 1
    index = 0 if index < 0 else 2 if index > 2 else index
    pad.addstr(cursor_origin_y + index, cursor_origin_x, '✶')
    pad.refresh(0, 0, ANCHOR[0], ANCHOR[1], rows, columns)

def _end():
    global pad
    pad.clear()
    pad = None
