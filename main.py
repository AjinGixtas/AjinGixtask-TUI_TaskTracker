from sqlite3 import DatabaseError
from curses import wrapper, curs_set, error
from time import sleep
from components import key_state_tracker, scene_manager, resources

def set_raw_mode_unix(fd):
    from termios import tcgetattr
    from tty import setraw
    old_settings = tcgetattr(fd)
    try:
        setraw(fd)
        return old_settings
    except Exception as e: return None
def restore_mode_unix(fd, old_settings):
    from termios import tcsetattr, TCSADRAIN
    if old_settings: tcsetattr(fd, TCSADRAIN, old_settings)
def set_raw_mode_windows():
    from win32console import GetStdHandle, STD_INPUT_HANDLE, ENABLE_LINE_INPUT, ENABLE_ECHO_INPUT
    hConsole = GetStdHandle(STD_INPUT_HANDLE)
    old_mode = hConsole.GetConsoleMode()
    hConsole.SetConsoleMode(old_mode & ~(ENABLE_LINE_INPUT | ENABLE_ECHO_INPUT))
    return old_mode
def restore_mode_windows(old_mode):
    from win32console import GetStdHandle, STD_INPUT_HANDLE
    hConsole = GetStdHandle(STD_INPUT_HANDLE)
    if old_mode is not None: hConsole.SetConsoleMode(old_mode)
def set_raw_mode():
    from sys import stdin
    from platform import system
    os_name = system()
    if os_name == 'Windows': return set_raw_mode_windows()
    else: return set_raw_mode_unix(fileno())
def restore_mode(old_settings):
    from sys import stdin
    from platform import system
    os_name = system()
    if os_name == 'Windows': restore_mode_windows(old_settings)
    else: restore_mode_unix(fileno(), old_settings)
old_settings = None
def _main(_stdscr):
    global old_settings
    old_settings = set_raw_mode()
    curs_set(0)
    key_state_tracker._start()
    resources._start(_stdscr)
    scene_manager._start()
    curs_set(0)
    production_mode = False
    while True:
        if not production_mode: scene_manager.current_page._update()
        else: 
            try: scene_manager.current_page._update()
            except error as e: 
                print("Error encountered! Maybe resizing the terminal window?")
                _end()
                return
            except DatabaseError as e:
                print("Save data corrupted! \nPlease send it to ajingixtascontact@gmail.com for the author to investigate. \nLook at the `Contact` section in the 'README.MD' file for more detail.")
            except Exception as e:
                print("Unexpected error encountered! \nIf the error persist, please report it at ajingixtascontact@gmail.com \nLook at the `Contact` section in the 'README.MD' file for more detail.")
                _end()
                return
        if key_state_tracker.get_key_state('ctrl', key_state_tracker.JUST_PRESSED) and key_state_tracker.get_key_state('q', key_state_tracker.JUST_PRESSED):
            _end()
            return
        key_state_tracker._update()
        sleep(.04166)
def _end():
    from sys import exit
    global old_settings
    resources._end()
    key_state_tracker._end()
    scene_manager._end()
    restore_mode(old_settings)
    exit()

if __name__ == "__main__":
    wrapper(_main)