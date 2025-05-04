import subprocess


def ascript(script: str) -> str:
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip()


def frontmost_title() -> str:
    """
    Returns the title of the focused window for the frontmost application.
    """
    script = """
    tell application "System Events"
        set frontApp to name of first process whose frontmost is true
        tell process frontApp
            if (count of windows) > 0 then
                return value of attribute "AXTitle" of window 1
            else
                return ""
            end if
        end tell
    end tell
    """
    return ascript(script)


def arc_tab_title() -> str:
    """
    Returns the title of the active tab in Arc using AppleScript.
    If there's an error or no valid tab is open, returns an empty string.
    """
    script = """
    tell application "Arc"
        if (count of windows) < 1 then return ""
        tell front window
            if (count of tabs) < 1 then return ""
            return title of active tab
        end tell
    end tell
    """
    return ascript(script)


def arc_tab_url() -> str:
    """
    Returns the URL of the active tab in Arc using AppleScript.
    If there's an error or Arc doesn't have a valid tab open, returns an empty string.
    """
    script = """
    tell application "Arc"
        if (count of windows) < 1 then
            return ""
        end if
        tell front window
            if (count of tabs) < 1 then
                return ""
            end if
            return URL of active tab
        end tell
    end tell
    """
    return ascript(script)


def vscode_focused() -> tuple[str, str]:
    """
    Returns a tuple containing the active file name and the project name from the front VS Code window.
    If no file is open, or an error occurs, returns ("", "").
    """
    script = """
    tell application "System Events"
        -- Adjust the process name if needed.
        -- On macOS the VS Code process is usually named "Code".
        tell process "Code"
            if (count of windows) > 0 then
                -- Retrieve the full title of the front window.
                set winTitle to value of attribute "AXTitle" of window 1
            else
                return "|||"
            end if
        end tell
    end tell

    return winTitle
    """
    result = ascript(script)
    if "—" in result:
        file_name, project_name = result.split(" — ")
        return (file_name, project_name)
    return ("", "")

def get_app_title(app: str) -> str:
    script = f"""
    set appBundleID to {app}
    tell application "System Events"
        set appName to name of every application process whose bundle identifier is appBundleID
        if (count of appName) > 0 then
            set appName to item 1 of appName
            tell process appName
                if (count of windows) > 0 then
                    set windowTitle to name of front window
                else
                    set windowTitle to "|||"
                end if
            end tell
        else
            set windowTitle to "|||"
        end if
    end tell

    return windowTitle
    """
    result = ascript(script).strip()

    if result == "|||":
        return ""

    return result

def running(bundle: str) -> bool:
    """
    Checks if an application with the given bundle identifier is running.
    """
    script = f"""
    tell application "System Events"
         set runningApps to bundle identifier of every process
         return runningApps contains "{bundle}"
    end tell
    """
    return ascript(script).strip().lower() == "true"


def spotify_track() -> tuple[str, str, bool]:
    """
    Returns (track_title, artist_name, is_playing) if Spotify is running and playing;
    otherwise returns ("", "", False).
    """
    script = """
    tell application "System Events"
        if exists process "Spotify" then
            tell application "Spotify"
                if player state is playing then
                    set trackTitle to name of current track
                    set artistName to artist of current track
                    return trackTitle & "|||" & artistName
                else
                    return "PAUSED|||"
                end if
            end tell
        end if
    end tell
    return ""
    """
    result = ascript(script)
    if result == "PAUSED|||" or result == "":
        return ("", "", False)
    if "|||" in result:
        parts = result.split("|||")
        if len(parts) == 2:
            title, artist = parts
            return (title, artist, True)
    return ("", "", False)


def apple_music_track() -> tuple[str, str, bool]:
    """
    Returns (track_title, artist_name, is_playing) if Apple Music is running and playing;
    otherwise returns ("", "", False).
    """
    script = """
    tell application "System Events"
        if exists process "Music" then
            tell application "Music"
                if player state is playing then
                    set trackTitle to name of current track -- use sort name for title if name doesn't work
                    set artistName to artist of current track
                    return trackTitle & "|||" & artistName
                else
                    return "PAUSED|||"
                end if
            end tell
        end if
    end tell
    return ""
    """
    result = ascript(script)
    if result == "PAUSED|||" or result == "":
        return ("", "", False)
    if "|||" in result:
        parts = result.split("|||")
        if len(parts) == 2:
            title, artist = parts
            # # remove anything inside parentheses from title (e.g., "(Explicit)")
            # title = re.sub(r"\s*\([^)]*\)", "", title)
            return (title, artist, True)
    return ("", "", False)
