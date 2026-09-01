from tools import SENSITIVE_DEVICES

def requires_confirmation(tool_name: str, tool_args: dict) -> bool:
    """Determines whether an action requires human confirmation before execution."""
    if tool_name == "lock_unlock_door":
        return True
    return False

def check_permission(user_role: str, tool_name: str) -> bool:
    """Simple example of user permissions. Extend as needed."""
    restricted_tools = ["lock_unlock_door"]
    if user_role == "guest" and tool_name in restricted_tools:
        return False
    return True