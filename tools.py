from langchain_core.tools import tool
from devices import load_state, save_state, log_action

# List of sensitive devices that require human confirmation
SENSITIVE_DEVICES = ["front_door", "back_door"]
@tool
def get_all_devices_status() -> str:
    """Returns the current status of all devices in the house."""
    state = load_state()
    return str(state)

@tool
def control_light(device_id: str, action: str, brightness: int = 100) -> str:
    """
    Controls a light device.
    device_id: name of the light, e.g. living_room_light or bedroom_light
    action: 'on' or 'off'
    brightness: brightness percentage from 0 to 100 (optional)
    """
    state = load_state()
    if device_id not in state:
        return f"Device {device_id} not found"

    state[device_id]["status"] = action
    state[device_id]["brightness"] = brightness if action == "on" else 0
    save_state(state)
    log_action(f"control_light: {device_id} -> {action} ({brightness}%)")
    return f"Done: {device_id} is now {action} at {brightness}% brightness"

@tool
def set_thermostat(temp: int, mode: str) -> str:
    """
    Sets the thermostat (AC/heating).
    temp: desired temperature
    mode: 'cooling', 'heating', or 'off'
    """
    state = load_state()
    state["thermostat"]["temp"] = temp
    state["thermostat"]["mode"] = mode
    save_state(state)
    log_action(f"set_thermostat: {temp}°C mode={mode}")
    return f"Thermostat set to {temp}°C, mode: {mode}"

@tool
def lock_unlock_door(door_id: str, action: str) -> str:
    """
    Locks or unlocks a door. This action is sensitive and requires
    user confirmation before execution.
    door_id: front_door or back_door
    action: 'lock' or 'unlock'
    """
    state = load_state()
    if door_id not in state:
        return f"Door {door_id} not found"

    state[door_id]["locked"] = (action == "lock")
    save_state(state)
    log_action(f"lock_unlock_door: {door_id} -> {action}")
    return f"Done: {door_id} is now {'locked' if action == 'lock' else 'unlocked'}"


ALL_TOOLS = [get_all_devices_status, control_light, set_thermostat, lock_unlock_door]