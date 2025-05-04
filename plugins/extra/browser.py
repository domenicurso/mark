from plugins.base import Plugin
from utils.types import PluginID, PluginStatus, PluginContext, PluginSettings
from utils.plugins import PluginHelpers

from urllib.parse import urlparse
from utils.ascript import arc_tab_url, arc_tab_title, running


class BrowserPlugin(Plugin):
    def __init__(self, settings: PluginSettings):
        super().__init__(PluginID("browser"), settings)

    def supports(self, context: PluginContext) -> bool:
        return context["_name"] in self.pcfg.get("apps", [""])

    def gather_context(self) -> PluginContext:
        apps = self.pcfg.get("apps", [])
        mapping = {
            "company.thebrowser.browser": (
                lambda: running("company.thebrowser.browser"),
                lambda: self._build_browser_context(),
            )
        }
        return PluginHelpers.gather_context(apps, mapping)

    def _build_browser_context(self) -> PluginContext:
        return {"url": arc_tab_url(), "title": arc_tab_title()}

    def build_status(self, context: PluginContext) -> PluginStatus:
        sep = self._sep()
        current_time = self._time()
        app_name = context["_name"]
        emoji, default_text, default_type = self._status(app_name)

        prefix_text = f"{default_text} " if self.pcfg.get("prefix", True) else ""

        data = PluginHelpers.prioritize_context(
            context, self.pcfg.get("apps", []), ["url", "title"]
        )
        url = data.get("url", "")
        title = data.get("title", "")

        # Special handling for known domains
        if url and self.pcfg.get("use_special", True):
            parsed = urlparse(url)
            domain = parsed.netloc.lower().removeprefix("www.")
            special_urls = self.pcfg.get("special_statuses", {})
            if domain in special_urls:
                sp_emoji, sp_text, *maybe_type = special_urls[domain]
                sp_type = maybe_type[0] if maybe_type else "online"
                return (
                    sp_emoji,
                    PluginHelpers.format_status(
                        prefix_text, sp_text, sep, current_time
                    ),
                    sp_type,
                )

        # Fallback to display title or URL
        if self.pcfg.get("display", "none") == "title" and title:
            text = PluginHelpers.format_status(prefix_text, title, sep, current_time)
        elif self.pcfg.get("display", "none") == "url" and url:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().removeprefix("www.")
            text = PluginHelpers.format_status(prefix_text, domain, sep, current_time)
        else:
            text = PluginHelpers.format_status(default_text, "", sep, current_time)

        return (emoji, text, default_type)
