#!/usr/bin/env python3

# Mark
# By @dombom

# Leave your mark behind

import json
import os
import re
import signal
import sys
import termios
import threading
import time
import tty
from pathlib import Path

# Third-party imports
import requests
from colorama import Fore, Style
from dotenv import load_dotenv

# Try to import macOS specific modules
try:
    from Cocoa import NSLog, NSWorkspace

    MACOS_SUPPORT = True
except ImportError:
    MACOS_SUPPORT = False
    raise ImportError("macOS support is required")

# Local imports
from zenif.cli import Applet

from plugins.manager import PluginManager
from utils.constants import FB_ICON, FB_TEXT, MIN_RATE_LIMIT, VERSION, l
from utils.system import get_frontmost_bundle, get_idle_time

# Initialize the CLI app
app = Applet(single=True)
app.install(os.path.abspath(__file__))

# Constants
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ENV_PATH = SCRIPT_DIR / ".env"
DEFAULT_SETTINGS_PATH = SCRIPT_DIR / "settings.jsonc"


class DiscordStatusManager:
    """Manages Discord custom status updates"""

    def __init__(self, settings, token):
        self.settings = settings
        self.token = token
        self.last_status = (None, None, None)
        self.last_status_time = 0

    def set_custom_status(self, emoji: str, text: str, status_type: str = "online"):
        """Set a custom status on Discord"""
        # Validate status type
        status_type = status_type.lower()
        if status_type not in ["online", "idle", "dnd", "invisible"]:
            status_type = "online"

        url = "https://discord.com/api/v9/users/@me/settings"
        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
        }
        payload = {
            "custom_status": {
                "text": text,
                "emoji_name": emoji,
            },
            "status": status_type,
        }

        resp = requests.patch(url, json=payload, headers=headers)
        if resp.status_code != 200:
            l.warning(f"Failed to set status. HTTP {resp.status_code}: {resp.text}")
            return False

        # Update last status information
        self.last_status = (emoji, text, status_type)
        self.last_status_time = time.time()

        # Print status update with color coded dots
        dot = "●"
        colorblind = self.settings.get("colorblind", False)
        if status_type == "online":
            dot = f"{Fore.GREEN}{dot if not colorblind else 'O'}{Style.RESET_ALL}"
        elif status_type == "idle":
            dot = f"{Fore.YELLOW}{dot if not colorblind else 'I'}{Style.RESET_ALL}"
        elif status_type == "dnd":
            dot = f"{Fore.RED}{dot if not colorblind else 'D'}{Style.RESET_ALL}"
        elif status_type == "invisible":
            dot = f"{Fore.BLUE}{dot if not colorblind else 'N'}{Style.RESET_ALL}"

        l.success(f"{dot} {Style.RESET_ALL}{Style.DIM}{emoji} {text}")
        return True

    def reset_to_default(self):
        """Reset status to the default defined in settings"""
        emoji, text, *maybe_type = self.settings["statuses"].get(
            "default", [FB_ICON(), FB_TEXT(), "online"]
        )
        status_type = maybe_type[0] if maybe_type else "online"
        return self.set_custom_status(emoji=emoji, text=text, status_type=status_type)


class ShutdownObserver(object):
    """Observer for macOS system shutdown events"""

    def __init__(self, shutdown_callback=None):
        self.shutdown_callback = shutdown_callback
        # Only call the NSObject init if we're on macOS
        if MACOS_SUPPORT:
            super(ShutdownObserver, self).__init__()

    def workspaceWillPowerOff_(self, notification):
        if MACOS_SUPPORT:
            NSLog(
                "Received NSWorkspaceWillPowerOffNotification. Initiating graceful shutdown."
            )
        else:
            print("Received power off notification. Initiating graceful shutdown.")

        if self.shutdown_callback:
            threading.Thread(target=self.shutdown_callback).start()


class MarkApp:
    """Main application class for Mark"""

    def __init__(self):
        self.settings = {}
        self.token = None
        self.status_manager = None
        self.plugin_manager = None
        self.update_interval = 5
        self.retry_interval = 5
        self.observer = None
        self.debug = False

    def load_settings(self, settings_path=None):
        """Load settings from the settings file"""
        settings_path = settings_path or DEFAULT_SETTINGS_PATH
        try:
            with open(settings_path, "r") as f:
                # Strip comments from JSON
                json_str = re.sub(r"/\*[\s\S]*?\*/", "", re.sub(r"//.*", "", f.read()))
                self.settings = json.loads(json_str)

            # Set intervals from settings
            self.update_interval = self.settings.get("update_interval", 5)
            self.retry_interval = max(
                MIN_RATE_LIMIT, self.settings.get("retry_interval", 0)
            )
            return True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            l.error(f"Failed to load settings: {e}")
            return False

    def load_env(self, env_path=None):
        """Load environment variables"""
        env_path = env_path or DEFAULT_ENV_PATH
        load_dotenv(env_path)
        self.token = os.getenv("DISCORD_TOKEN")
        if not self.token:
            l.error("DISCORD_TOKEN not found in environment variables")
            return False
        return True

    def setup(self, debug=False):
        """Set up the application"""
        self.debug = debug
        if debug:
            print("─" * os.get_terminal_size().columns)
            l.debug("Setting up application...")

        if not self.load_settings():
            l.error("Failed to load settings")
            return False

        if not self.load_env():
            l.error("Failed to load environment variables")
            return False

        self.status_manager = DiscordStatusManager(self.settings, self.token)
        self.plugin_manager = PluginManager(self.settings, debug=debug)

        # Set up shutdown handlers
        if debug:
            l.debug("Setting up shutdown handlers...")
        self.setup_shutdown_handlers()

        if debug:
            l.debug("Setup complete")
            print("─" * os.get_terminal_size().columns)

        return True

    def setup_shutdown_handlers(self):
        """Set up handlers for shutdown signals"""
        signal.signal(signal.SIGTERM, lambda sig, frame: self.graceful_shutdown())
        signal.signal(signal.SIGINT, lambda sig, frame: self.graceful_shutdown())

        # macOS specific shutdown observer
        if MACOS_SUPPORT:
            self.observer = ShutdownObserver(self.graceful_shutdown)
            notification_center = NSWorkspace.sharedWorkspace().notificationCenter()
            notification_center.addObserver_selector_name_object_(
                self.observer,
                b"workspaceWillPowerOff:",
                "NSWorkspaceWillPowerOffNotification",
                None,
            )
            l.success("Shutdown handlers set up.")
        else:
            l.info("macOS specific shutdown handlers not available on this platform.")

    def graceful_shutdown(self):
        """Handle graceful shutdown"""
        print("\nShutdown signal received. Cleaning up...")

        # Clear screen and show logo
        os.system("clear" if os.name == "posix" else "cls")
        print_logo()

        # Skip the rest if status_manager isn't initialized
        if not self.status_manager:
            l.info("Status manager not initialized, exiting immediately.")
            print("\033[?25h", end="")  # Show cursor
            sys.exit(0)

        # Check if we need to wait for rate limiting
        current_time = time.time()
        elapsed = current_time - self.status_manager.last_status_time
        remaining_time = max(0, MIN_RATE_LIMIT - elapsed)

        if remaining_time > 0:
            l.info(
                f"Waiting {remaining_time:.2f} seconds before final status reset to avoid rate limits..."
            )
            # Calculate fractional and whole parts of remaining_time
            whole = int(remaining_time)
            fractional = remaining_time - whole

            # First, wait the fractional part if any
            if fractional > 0:
                time.sleep(fractional)

            # Then, wait each whole second with per-second updates
            for seconds_remaining in range(whole, 0, -1):
                l.info(f"{seconds_remaining} seconds remaining...")
                time.sleep(1)

        # Reset to default status
        self.status_manager.reset_to_default()
        l.success("Final status reset. Exiting now.")

        # Show cursor
        print("\033[?25h", end="")
        sys.exit(0)

    def run(self, fast=False, debug=False):
        """Run the application"""
        # Clear screen
        os.system("clear" if os.name == "posix" else "cls")

        # Hide cursor
        print("\033[?25l", end="")

        try:
            if debug:
                l.debug(
                    "Verbose mode enabled... to turn off, run mark without the --verbose/-v flag"
                )

            if not self.setup(debug):
                l.error("Failed to set up application. Exiting.")
                return

            if not fast:
                self.show_startup_screen()

            print_logo()

            l.info(
                "Mark is ready and will start updating status soon\n"
                "You can leave this window in the background\n"
                "To exit, press Ctrl+C and wait for the final status reset",
            )

            if debug:
                l.debug("Entering main loop...")

            time.sleep(3)

            # Main loop
            self.status_update_loop(debug)

        except Exception as e:
            # Show cursor before exiting
            print("\033[?25h", end="")
            l.error(f"An error occurred: {e}")
            sys.exit(1)

    def status_update_loop(self, debug=False):
        """Main status update loop"""
        while True:
            # Skip if plugin_manager or status_manager aren't initialized
            if not self.plugin_manager or not self.status_manager:
                l.error(
                    "Plugin manager or status manager not initialized. Retrying in 5 seconds..."
                )
                time.sleep(5)
                continue

            try:
                # Get status from plugin manager
                context = {
                    "_name": get_frontmost_bundle(),
                    "_idle": get_idle_time(),
                    "_enabled": self.settings.get("statuses", {})
                    .get("plugins", {})
                    .get("_enabled", []),
                }

                emoji, text, status_type = self.plugin_manager.get_status(context)

                # Check if status has changed
                current_status = (emoji, text, status_type)
                now = time.time()

                if (
                    current_status != self.status_manager.last_status
                    and (now - self.status_manager.last_status_time)
                    > self.update_interval
                ):
                    if debug:
                        l.debug(
                            "Updating Discord status to: "
                            + emoji
                            + " "
                            + text
                            + " (type: "
                            + status_type
                            + ")"
                        )

                    self.status_manager.set_custom_status(emoji, text, status_type)

                    if debug:
                        l.success(
                            "Updated Discord status to: "
                            + emoji
                            + " "
                            + text
                            + " (type: "
                            + status_type
                            + ")"
                        )
                elif debug:
                    l.debug("Discord status is already up to date; skipping update.")
            except Exception as e:
                l.error("Error in status update loop: " + str(e))

            time.sleep(self.retry_interval)

    def show_startup_screen(self):
        """Show the startup screen with space to start prompt"""
        print_logo()

        # Calculate position for the start button
        button_width = 30
        lines = os.get_terminal_size().lines - 1
        columns = os.get_terminal_size().columns // 2 - button_width // 2

        # Display the button
        print(
            f"\033[{lines};{columns}H{Style.DIM}{'Press SPACE to start'.center(button_width)}{Style.RESET_ALL}",
            end="",
        )

        # Wait for spacebar press
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        ready = False

        while not ready:
            try:
                tty.setcbreak(sys.stdin.fileno())
                char = sys.stdin.read(1)
                if char == " ":
                    ready = True
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        os.system("clear" if os.name == "posix" else "cls")


def print_logo():
    """Print the Mark logo with styling"""
    logo = """
888b     d888        d8888 8888888b.  888    d8P
8888b   d8888       d88888 888   Y88b 888   d8P
88888b.d88888      d88P888 888    888 888  d8P
888Y88888P888     d88P 888 888   d88P 888d88K
888 Y888P 888    d88P  888 8888888P"  8888888b
888  Y8P  888   d88P   888 888 T88b   888  Y88b
888   "   888  d8888888888 888  T88b  888   Y88b
888       888 d88P     888 888   T88b 888    Y88b """

    columns = os.get_terminal_size().columns

    for line in logo.split("\n"):
        print(Fore.BLUE + line.ljust(50).center(columns))
    print()

    print(
        Fore.BLUE
        + Style.DIM
        + "Leave your mark behind\n".center(columns)
        + Style.RESET_ALL
    )


# CLI Commands
@app.single
@app.command
@app.flag("fast", help="Launch Mark without onboarding")
@app.flag("verbose", help="Enable verbose mode")
@app.flag("version", help="Get the version of Mark")
@app.flag("getbundle", help="Get the bundle ID of the active app")
@app.alias("fast", "f")
@app.alias("version", "v")
@app.alias("getbundle", "gb")
def run(fast: bool, verbose: bool, version: bool, getbundle: bool):
    """Initialize Mark"""
    if version:
        print(f"Mark v{VERSION}")
        sys.exit(0)
    elif getbundle:
        getbundle()
        sys.exit(0)

    mark = MarkApp()
    mark.run(fast=fast, debug=verbose)


def getbundle():
    """Get the bundle ID of the active app"""
    frontmost = None
    last_frontmost = None
    l.info("Focus an app to get its bundle ID")
    l.info("Press Ctrl+C to exit")
    try:
        while True:
            frontmost = get_frontmost_bundle()
            if frontmost != last_frontmost:
                last_frontmost = frontmost
                print(frontmost)
    except KeyboardInterrupt:
        pass
    sys.exit(0)


if __name__ == "__main__":
    app.run()
