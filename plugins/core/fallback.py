from plugins.base import Plugin
from utils.types import PluginID, PluginStatus, PluginContext, PluginSettings
from utils.constants import FB_ICON, FB_TEXT


class FallbackPlugin(Plugin):

    def __init__(self, settings: PluginSettings) -> None:
        super().__init__(PluginID("fallback"), settings)
        self.default_emoji, self.default_text = settings["statuses"].get(
            "default", [FB_ICON(), FB_TEXT()]
        )

    def supports(self, context: PluginContext) -> bool:
        """
        Fallback is always true (lowest priority plugin).
        """
        return True

    def build_status(self, context: PluginContext) -> PluginStatus:
        """
        If there's no other plugin above us, build a fallback status:
          - Create a 'default' status with time appended
        """
        emoji, text, status_type = self._get_app_status(context)

        # Build the final fallback status
        return self._format_status(emoji, text, status_type)

    def _get_app_status(self, context: dict) -> tuple[str, str, str]:
        """
        Return [emoji, text, status_type] from the app config
        or fallback to the default if no specific app config is found.
        """
        emoji, text, *maybe_type = self.settings["statuses"]["apps"].get(
            context["_name"], [self.default_emoji, self.default_text, "online"]
        )
        type = maybe_type[0] if maybe_type else "online"
        return emoji, text, type

    def _format_status(
        self, emoji: str, text: str, status_type: str
    ) -> tuple[str, str, str]:
        """
        Append the current time to the text using the base class helpers.
        """
        current_time = self._time()
        sep = self._sep()

        return (emoji, f"{text}{sep}{current_time}", status_type)
