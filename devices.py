import json
import os
from datetime import datetime

STATE_FILE = "device_state.json"
LOG_FILE = "action_log.txt"

def load_state():
    if not os.path.exists(STATE_FILE):
        raise FileNotFoundError("device_state.json not found")
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def log_action(action: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {action}\n")