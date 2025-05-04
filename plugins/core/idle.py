from math import floor
from plugins.base import Plugin
from utils.types import PluginID, PluginStatus, PluginContext, PluginSettings

class IdlePlugin(Plugin):
    def __init__(self, settings: PluginSettings) -> None:
        super().__init__(PluginID("idle"), settings)

        self.idle_conf = settings["statuses"].get("idle", {})

        self.emoji, self.text = self.idle_conf.get("status", ["😴", "Away"])
        self.timeout = self.idle_conf.get("timeout", 5) * 60
        self.display_mode = self.idle_conf.get("display", "elapsed")

    def supports(self, context: PluginContext) -> bool:
        """
        Return True if the user's idle time is >= self.timeout.
        """
        return context["_idle"] >= self.timeout

    def build_status(self, context: PluginContext) -> PluginStatus:
        """
        Build an idle status using self.emoji, self.text, etc.
        """

        # Use the shared time & separator helpers
        current_time = self._time()
        sep = self._sep()
        idle_minutes = floor(context["_idle"] / 60)

        if self.display_mode == "elapsed":
            status_text = f"{self.text} ({idle_minutes}m){sep}{current_time}"
        else:  # e.g. "normal"
            status_text = f"{self.text}{sep}{current_time}"

        return (self.emoji, status_text, "idle")
