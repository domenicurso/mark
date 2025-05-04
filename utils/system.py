from .ascript import ascript


def get_frontmost_bundle() -> str:
    """
    Returns the name of the frontmost application on macOS using AppleScript.
    """
    script = """
    tell application "System Events"
        set frontApp to bundle identifier of first process whose frontmost is true
    end tell
    return frontApp
    """
    return str(ascript(script)).lower()


from Quartz import (
    CGEventSourceSecondsSinceLastEventType,
    kCGAnyInputEventType,
    kCGEventSourceStateCombinedSessionState,
)


def get_idle_time() -> float:
    return CGEventSourceSecondsSinceLastEventType(
        kCGEventSourceStateCombinedSessionState, kCGAnyInputEventType
    )
