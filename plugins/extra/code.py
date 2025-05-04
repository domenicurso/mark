from plugins.base import Plugin
from utils.types import PluginID, PluginStatus, PluginContext, PluginSettings
from utils.plugins import PluginHelpers

from utils.ascript import vscode_focused, get_app_title, running


class CodePlugin(Plugin):
    def __init__(self, settings: PluginSettings):
        super().__init__(PluginID("code"), settings)
        self.display_mode = self.pcfg.get("display", "file_project")

    def supports(self, context: PluginContext) -> bool:
        return context["_name"] in self.pcfg.get("apps", [""])

    def gather_context(self) -> PluginContext:
        apps = self.pcfg.get("apps", [])
        mapping = {
            "com.microsoft.vscode": (
                lambda: running("com.microsoft.vscode"),
                lambda: self._build_vscode_context(),
            ),
            "dev.zed.zed-preview": (
                lambda: running("dev.zed.zed-preview"),
                lambda: self._build_zed_preview_context(),
            ),
            "dev.zed.zed": (
                lambda: running("dev.zed.zed"),
                lambda: self._build_zed_context(),
            ),
        }
        return PluginHelpers.gather_context(apps, mapping)

    def _build_vscode_context(self) -> PluginContext:
        file_title, project_name = vscode_focused()
        return {"file_title": file_title, "project_name": project_name}

    def _build_zed_context(self) -> PluginContext:
        try:
            title = get_app_title("dev.zed.zed")
            if " — " in title:
                project_name, file_title = title.split(" — ", 1)
                return {"file_title": file_title, "project_name": project_name}
        except Exception:
            pass
        return {"file_title": "", "project_name": ""}

    def _build_zed_preview_context(self) -> PluginContext:
        try:
            title = get_app_title("dev.zed.zed-preview")
            if " — " in title:
                project_name, file_title = title.split(" — ", 1)
                return {"file_title": file_title, "project_name": project_name}
        except Exception:
            pass
        return {"file_title": "", "project_name": ""}

    def build_status(self, context: PluginContext) -> PluginStatus:
        sep = self._sep()
        current_time = self._time()
        app_name = context["_name"]
        emoji, default_text, default_type = self._status(app_name)

        data: dict[str, str] = PluginHelpers.prioritize_context(
            context, self.pcfg.get("apps", []), ["file_title", "project_name"]
        )
        file_title: str = data.get("file_title", "")
        project_name: str = data.get("project_name", "")

        text = self._format_text(
            self.pcfg.get("prefix", True),
            default_text,
            project_name,
            file_title,
            sep,
            current_time,
        )
        return (emoji, text, default_type)

    def _format_text(
        self,
        prefix_enabled: bool,
        prefix_text: str,
        project: str,
        file: str,
        sep: str,
        current_time: str,
    ) -> str:
        prefix_str = prefix_text + " in " if prefix_enabled else ""
        if self.display_mode == "project":
            return PluginHelpers.format_status(
                prefix_str, project or "[no project]", sep, current_time
            )
        elif self.display_mode == "file":
            return PluginHelpers.format_status(
                prefix_str, file or "[no file]", sep, current_time
            )
        elif self.display_mode == "both":
            return PluginHelpers.format_status(
                prefix_str,
                f"{file or '[no file]'} in {project or '[no project]'}",
                sep,
                current_time,
            )
        else:
            return f"{prefix_text}{current_time}"
