import time
import json
import subprocess as sp
from pynput import keyboard, mouse

STATE_FILE = "state.json"
LOG_FILE = "system.log"

CHECK_INTERVAL = 60          # seconds
IDLE_LIMIT = 300             # 5 minutes
LOW_FOCUS_LIMIT = 50         # %

# Apps that definitely steal attention
DISTRACT_APPS = [
    "Chrome", "YouTube", "Facebook", "X", "TikTok"
]

last_input_time = time.time()
key_count = 0

focused_time = 0
distracted_time = 0
idle_time = 0


def notify(title, message):
    try:
        sp.run(["notify-send", title, message])
    except:
        pass


def on_input(*args):
    global last_input_time
    last_input_time = time.time()


def on_key(key):
    global key_count, last_input_time
    key_count += 1
    last_input_time = time.time()


mouse.Listener(on_move=on_input, on_click=on_input, on_scroll=on_input).start()
keyboard.Listener(on_press=on_key).start()


def get_active_window():
    try:
        return sp.check_output(
            ["xdotool", "getactivewindow", "getwindowname"],
            stderr=sp.DEVNULL
        ).decode().strip()
    except:
        return "UNKNOWN"


def focus_percent():
    total = focused_time + distracted_time + idle_time
    if total == 0:
        return 100
    return int((focused_time / total) * 100)


while True:
    now = time.time()
    idle = now - last_input_time
    window = get_active_window()

    # SMART focus accounting
    if idle > CHECK_INTERVAL:
        idle_time += CHECK_INTERVAL
    else:
        if any(app in window for app in DISTRACT_APPS):
            distracted_time += CHECK_INTERVAL
        else:
            focused_time += CHECK_INTERVAL

    focus = focus_percent()

    # Notifications
    if idle > IDLE_LIMIT:
        notify(
            "😈 Wake up.",
            "You said you were building. Start typing."
        )

    if focus < LOW_FOCUS_LIMIT:
        notify(
            "⚠ Focus slipping",
            f"Focus at {focus}%. Discipline yourself."
        )

    # State snapshot
    state = {
        "time": int(now),
        "idle_seconds": int(idle),
        "keys_last_min": key_count,
        "window": window,
        "focus_percent": focus
    }

    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    with open(LOG_FILE, "a") as log:
        log.write(
            f"{now}, idle={int(idle)}s, "
            f"keys={key_count}, "
            f"focus={focus}%, "
            f"window={window}\n"
        )

    key_count = 0
    time.sleep(CHECK_INTERVAL)
