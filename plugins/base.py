from abc import ABC, abstractmethod
from datetime import datetime
from utils.constants import FB_ICON, DEFAULT_SEPARATOR, DEFAULT_TIME_FORMAT
from utils.types import PluginID, PluginStatus, PluginContext, PluginSettings


class Plugin(ABC):
    def __init__(self, id: PluginID, settings: PluginSettings):
        """
        Base class for all plugins.
        """
        self.id: PluginID = id
        self.settings: PluginSettings = settings
        self.pcfg: dict[str, any] = settings["statuses"]["plugins"].get(id, {})
        self.app_statuses: dict[str, any] = settings["statuses"].get("apps", {})

    def get_context(self, global_context: PluginContext) -> PluginContext:
        """
        Flatten context: include all global keys starting with '_' plus all keys
        returned by the plugin's gather_context().
        """
        flat_context = {k: v for k, v in global_context.items() if k.startswith("_")}
        flat_context.update(self.gather_context())
        return flat_context

    def supports(self, context: PluginContext) -> bool:
        """
        Return True if this plugin should be active.
        Default behavior: check if the plugin's name is in the global _enabled list.
        """
        return self.id in context.get("_enabled", [])

    @abstractmethod
    def build_status(self, context: PluginContext) -> PluginStatus:
        """
        Build and return the final status tuple: (emoji, text, status_type).
        """
        pass

    def gather_context(self) -> PluginContext:
        """
        Retrieve plugin-specific context.
        Override this method if your plugin needs extra data.
        """
        return {}

    def _time(self) -> str:
        tformat = self.settings["statuses"].get("time_format", DEFAULT_TIME_FORMAT)
        return (
            datetime.now().strftime(tformat)
            if self.settings["statuses"].get("show_time")
            else ""
        )

    def _sep(self) -> str:
        return (
            self.settings["statuses"].get("separator", DEFAULT_SEPARATOR)
            if self.settings["statuses"].get("show_time")
            else ""
        )

    def _status(self, app_name: str) -> list[str]:
        """
        Return the default [emoji, text, type] for a given app from the apps config,
        falling back to defaults if not found.
        """
        emoji, text, *maybe_type = self.app_statuses.get(
            app_name, [FB_ICON(), f"{app_name}", "online"]
        )
        status_type = maybe_type[0] if maybe_type else "online"
        return [emoji, text, status_type]
