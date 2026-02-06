import time
import json
import subprocess
import platform
from pynput import keyboard, mouse
from plyer import notification

# ================= CONFIG =================
CHECK_INTERVAL = 5          # seconds
IDLE_LIMIT = 300            # 5 minutes
STATE_FILE = "state.json"
LOG_FILE = "system.log"
# =========================================

last_input_time = time.time()
key_count = 0

focused_time = 0
idle_time = 0
total_time = 0

last_window = None
last_window_switch = time.time()

# ---------- INPUT TRACKING ----------
def on_input(*args):
    global last_input_time
    last_input_time = time.time()

def on_key(key):
    global key_count, last_input_time
    key_count += 1
    last_input_time = time.time()

mouse.Listener(
    on_move=on_input,
    on_click=on_input,
    on_scroll=on_input
).start()

keyboard.Listener(on_press=on_key).start()

# ---------- WINDOW NAME ----------
def get_active_window():
    try:
        if platform.system() == "Windows":
            import win32gui
            return win32gui.GetWindowText(win32gui.GetForegroundWindow())
        else:
            return subprocess.check_output(
                ["xdotool", "getactivewindow", "getwindowname"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
    except:
        return "UNKNOWN"

# ---------- NOTIFICATION ----------
def notify(title, message):
    try:
        notification.notify(
            title=title,
            message=message,
            timeout=5
        )
    except:
        pass

# ---------- MAIN LOOP ----------
while True:
    now = time.time()
    idle = now - last_input_time
    window = get_active_window()

    total_time += CHECK_INTERVAL

    if idle < CHECK_INTERVAL:
        focused_time += CHECK_INTERVAL
    else:
        idle_time += CHECK_INTERVAL

    focus_percent = (
        int((focused_time / total_time) * 100)
        if total_time > 0 else 0
    )

    # Notify on long idle
    if idle >= IDLE_LIMIT and idle < IDLE_LIMIT + CHECK_INTERVAL:
        notify(
            "😈 No Mercy",
            "Idle detected. Discipline slipping."
        )

    # Notify on Chrome abuse
    if "Chrome" in window and idle < CHECK_INTERVAL:
        notify(
            "😈 Focus Judge",
            "Too much Chrome. Build something."
        )

    # Save state
    state = {
        "time": now,
        "idle_seconds": int(idle),
        "keys_last_interval": key_count,
        "window": window,
        "focus_percent": focus_percent
    }

    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    with open(LOG_FILE, "a") as log:
        log.write(
            f"{now}, idle={int(idle)}s, "
            f"keys={key_count}, "
            f"focus={focus_percent}%, "
            f"window={window}\n"
        )

    key_count = 0
    time.sleep(CHECK_INTERVAL)
