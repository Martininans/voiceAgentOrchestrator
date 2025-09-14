from typing import Dict, Callable


def booking_tool(text: str, context: Dict) -> str:
    return "Booking created (stub)."


def information_tool(text: str, context: Dict) -> str:
    return "Here is the information you requested (stub)."


def fallback_tool(text: str, context: Dict) -> str:
    return "I'm not sure I understood. Could you rephrase?"


INTENT_TO_TOOL: Dict[str, Callable[[str, Dict], str]] = {
    "room_booking": booking_tool,
    "information": information_tool,
}


def route_to_tool(intent: str, text: str, context: Dict) -> str:
    tool = INTENT_TO_TOOL.get(intent, fallback_tool)
    return tool(text, context) 