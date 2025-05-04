from .core.fallback import FallbackPlugin
from .core.idle import IdlePlugin

from .extra.browser import BrowserPlugin
from .extra.code import CodePlugin
from .extra.music import MusicPlugin

from .base import Plugin
from typing import NewType

from utils.types import PluginContext, PluginStatus, PluginSettings

PluginID = NewType("PluginID", str)

PLUGINS: dict[PluginID, Plugin] = {
    PluginID("idle"): IdlePlugin,
    PluginID("fallback"): FallbackPlugin,
    PluginID("music"): MusicPlugin,
    PluginID("browser"): BrowserPlugin,
    PluginID("code"): CodePlugin,
}

from utils.constants import FB_ICON, FB_TEXT, l


class PluginManager:
    def __init__(self, settings: PluginSettings, debug: bool = False):
        self.settings: PluginSettings = settings
        self.debug: bool = debug

        if self.debug:
            l.debug("Initializing PluginManager with debug mode enabled.")

        plugins: list[Plugin] = []
        plugin_settings: dict = settings.get("statuses", {}).get("plugins", {})
        enabled_plugins: list[PluginID] = [
            PluginID(pid) for pid in plugin_settings.get("_enabled", [])
        ]

        # Always include IdlePlugin first.
        try:
            plugins.append(IdlePlugin(settings))
        except Exception as e:
            l.error(f"Failed to initialize IdlePlugin: {e}")

        for plugin_id in enabled_plugins:
            try:
                if plugin_id.strip():
                    if plugin_id in plugin_settings and plugin_id in PLUGINS:
                        if self.debug:
                            l.debug(f"Initializing plugin: {plugin_id}")
                        plugins.append(PLUGINS[plugin_id](settings))
                        if self.debug:
                            l.success(f"Plugin '{plugin_id}' initialized successfully.")
                    elif plugin_id not in PLUGINS:
                        l.warning(f"Plugin '{plugin_id}' not found.")
                    elif plugin_id not in plugin_settings:
                        l.warning(f"Plugin '{plugin_id}' has no settings object.")
            except Exception as e:
                l.error(f"Failed to initialize plugin '{plugin_id}': {e}")

        # Always add FallbackPlugin last.
        if self.debug:
            l.debug("Initializing FallbackPlugin.")
        try:
            plugins.append(FallbackPlugin(settings))
        except Exception as e:
            l.error(f"Failed to initialize FallbackPlugin: {e}")

        self.plugins: list[Plugin] = plugins

    def get_status(self, context: PluginContext) -> PluginStatus:
        """
        Iterate over plugins and for the first one that supports the current context,
        build a flattened context (global keys and plugin-specific keys) and return its status.
        """
        for plugin in self.plugins:
            flat_context = plugin.get_context(context)
            if self.debug:
                l.debug(
                    f"Checking plugin {plugin.__class__.__name__} with context:",
                    flat_context,
                )
            if plugin.supports(flat_context):
                if self.debug:
                    l.success(
                        f"Plugin {plugin.__class__.__name__} matched. Returning status:",
                        plugin.build_status(flat_context),
                    )
                return plugin.build_status(flat_context)
        emoji, text, *maybe_type = self.settings["statuses"].get(
            "default", [FB_ICON(), FB_TEXT(), "online"]
        )
        if self.debug:
            l.debug("No plugin matched context. Using default status.")
        status_type = maybe_type[0] if maybe_type else "online"
        return emoji, text, status_type
