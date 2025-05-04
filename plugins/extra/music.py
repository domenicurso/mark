from plugins.base import Plugin
from utils.types import PluginID, PluginStatus, PluginContext, PluginSettings
from utils.plugins import PluginHelpers

from utils.ascript import (
    spotify_track,
    apple_music_track,
    running,
)


class MusicPlugin(Plugin):
    def __init__(self, settings: PluginSettings) -> None:
        super().__init__(PluginID("music"), settings)
        self.display_mode: str = self.pcfg.get("display", "artist_title")

    def supports(self, context: PluginContext) -> bool:
        """
        Return True if the plugin should be active.

        When set to "focused", show the plugin when the app is focused.
        When set to "playing", show the plugin when the app is playing media.
        When set to "both", show the plugin when the app is focused and playing media.
        """
        focused_check: bool = False
        playing_check: bool = False

        if self.pcfg.get("when", "playing") in ["focused", "both"]:
            focused_check = context.get("_name", "") in self.pcfg.get("apps", [])

        if self.pcfg.get("when", "playing") in ["playing", "both"]:
            playing_check = any(
                context.get(app, {}).get("is_playing", False)
                for app in self.pcfg.get("apps", [])
            )

        return focused_check or playing_check

    def gather_context(self) -> PluginContext:
        def get_track_info(app_id: str) -> PluginContext:
            track_info: tuple[str, str, bool] | None = None
            source: str | None = None

            if app_id == "com.spotify.client":
                track_info = spotify_track()
                source = "spotify"
            elif app_id == "com.apple.music":
                track_info = apple_music_track()
                source = "music"
            else:
                return {}

            return {
                "track_title": track_info[0],
                "track_artist": track_info[1],
                "is_playing": track_info[2],
                "source": source,
            }

        apps = self.pcfg.get("apps", [])
        return PluginHelpers.gather_context(
            apps,
            {app: (lambda: running(app), lambda: get_track_info(app)) for app in apps},
        )

    def build_status(self, context: PluginContext) -> PluginStatus:
        # Look for a running track
        playing_data, playing_app = None, None
        for app in self.pcfg.get("apps", []):
            data = context.get(app, {})
            if data.get("is_playing", False):
                playing_data = data
                playing_app = app
                break

        if not playing_data:
            return self._build_paused()

        # Clean up track title and get artist name
        title = (
            PluginHelpers.clean(playing_data.get("track_title", ""))
            if self.pcfg.get("remove_extras", True)
            else playing_data.get("track_title", "")
        )
        artist = playing_data.get("track_artist", "")

        emoji, default_text, default_type = self._status(playing_app)
        formatted_text = self._format_text(default_text, title, artist)
        return (emoji, formatted_text, default_type)

    def _build_paused(self) -> PluginStatus:
        emoji, text, type_ = self._status(self.pcfg.get("apps", [""])[0])
        sep = self._sep()
        current_time = self._time()
        text = f"{text + ' ' if self.pcfg.get('prefix', True) else ''}paused{sep}{current_time}"
        return (emoji, text, type_)

    def _format_text(self, prefix_text: str, title: str, artist: str) -> str:
        prefix_str = prefix_text + " to " if self.pcfg.get("prefix", True) else ""
        sep = self._sep()
        current_time = self._time()
        if self.display_mode == "title":
            return PluginHelpers.format_status(
                prefix_str, title or "[no title]", sep, current_time
            )
        elif self.display_mode == "artist":
            return PluginHelpers.format_status(
                prefix_str, artist or "[no artist]", sep, current_time
            )
        elif self.display_mode == "both":
            return PluginHelpers.format_status(
                prefix_str,
                f"{title or '[no title]'} by {artist or '[no artist]'}",
                sep,
                current_time,
            )
        else:
            return f"{prefix_text}{current_time}"
