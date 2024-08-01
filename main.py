from sqlite3 import DatabaseError
from curses import wrapper, curs_set, error
from time import sleep
from sys import stdin, exit
from platform import system
from components import key_state_tracker, scene_manager, resources

def set_raw_mode_unix(fd):
    import termios
    import tty
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return old_settings
    except Exception as e:
        return None
def restore_mode_unix(fd, old_settings):
    import termios
    if old_settings: termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
def set_raw_mode_windows():
    import win32console
    hConsole = win32console.GetStdHandle(win32console.STD_INPUT_HANDLE)
    old_mode = hConsole.GetConsoleMode()
    hConsole.SetConsoleMode(old_mode & ~(win32console.ENABLE_LINE_INPUT | win32console.ENABLE_ECHO_INPUT))
    return old_mode
def restore_mode_windows(old_mode):
    import win32console
    hConsole = win32console.GetStdHandle(win32console.STD_INPUT_HANDLE)
    if old_mode is not None: hConsole.SetConsoleMode(old_mode)
def set_raw_mode():
    os_name = system()
    if os_name == 'Windows': return set_raw_mode_windows()
    else: return set_raw_mode_unix(stdin.fileno())
def restore_mode(old_settings):
    os_name = system()
    if os_name == 'Windows': restore_mode_windows(old_settings)
    else: restore_mode_unix(stdin.fileno(), old_settings)
old_settings = None
def _main(_stdscr):
    global old_settings
    old_settings = set_raw_mode()
    curs_set(0)
    key_state_tracker._start()
    resources._start(_stdscr)
    scene_manager._start()
    curs_set(0)
    production_mode = True
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
    global old_settings
    resources._end()
    key_state_tracker._end()
    scene_manager._end()
    restore_mode(old_settings)
    exit()

if __name__ == "__main__":
    wrapper(_main)