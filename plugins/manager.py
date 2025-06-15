from typing import NewType
import os

from .core.fallback import FallbackPlugin
from .core.idle import IdlePlugin

from .extra.browser import BrowserPlugin
from .extra.code import CodePlugin
from .extra.music import MusicPlugin

from .base import Plugin

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

        plugins: list[Plugin] = []
        plugin_settings: dict = settings.get("statuses", {}).get("plugins", {})
        enabled_plugins: list[PluginID] = [
            PluginID(pid) for pid in plugin_settings.get("_enabled", [])
        ]

        # Always include IdlePlugin first.
        try:
            plugins.append(IdlePlugin(settings))
            self._log_successfully_initialized('idle', len(plugins), len(enabled_plugins))
        except Exception as e:
            self._log_failed_to_initialize('idle', len(plugins), len(enabled_plugins), e)

        for plugin_id in enabled_plugins:
            try:
                if plugin_id.strip():
                    if plugin_id in plugin_settings and plugin_id in PLUGINS:
                        plugins.append(PLUGINS[plugin_id](settings))
                        self._log_successfully_initialized(plugin_id, len(plugins), len(enabled_plugins))
                    elif plugin_id not in PLUGINS:
                        self._log_warning(plugin_id, len(plugins), len(enabled_plugins), "not found in library")
                    elif plugin_id not in plugin_settings:
                        self._log_warning(plugin_id, len(plugins), len(enabled_plugins), "has no settings object")
            except Exception as e:
                self._log_failed_to_initialize(plugin_id, len(plugins), len(enabled_plugins), e)

        # Always add FallbackPlugin last.
        try:
            plugins.append(FallbackPlugin(settings))
            self._log_successfully_initialized('fallback', len(plugins), len(enabled_plugins))
        except Exception as e:
            self._log_failed_to_initialize('fallback', len(plugins), len(enabled_plugins), e)


        if debug:
            l.debug(f"Successfully initialized {len(plugins)} plugins")


        self.plugins: list[Plugin] = plugins

    def _log_successfully_initialized(self, plugin_id: str, current: int, total: int):
        if self.debug:
            l.success(f"Plugin \033[0;32m{plugin_id.upper()}\033[0m initialized successfully")

    def _log_failed_to_initialize(self, plugin_id: str, current: int, total: int, error: Exception):
        if self.debug:
            l.error(f"Plugin \033[0;31m{plugin_id.upper()}\033[0m failed to initialize: {str(error).upper()}")

    def _log_warning(self, plugin_id: str, current: int, total: int, warning: str):
        if self.debug:
            l.warning(f"Plugin \033[0;33m{plugin_id.upper()}\033[0m warning: {warning.upper()}")

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
