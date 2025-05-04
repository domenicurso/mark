import re
from collections.abc import Callable

ContextData = dict[str, any]
PluginContext = dict[str, ContextData]


class PluginHelpers:
    """
    PluginHelpers provides helper functions for gathering context and building status messages.
    This API abstracts common patterns so that individual plugins only need to provide the app-specific details.
    """

    @staticmethod
    def gather_context(
        apps: list[str],
        mapping: dict[str, tuple[Callable[[], bool], Callable[[], PluginContext]]],
    ) -> PluginContext:
        """
        Iterates over apps and, using the mapping, checks if each app is running.
        Calls the info function for running apps and returns a context dictionary.
        """
        context: dict[str, dict[str, any]] = {}
        for app in apps:
            if app in mapping:
                check_func, info_func = mapping[app]
                if check_func():
                    context[app] = info_func()
        return context

    @staticmethod
    def prioritize_context(
        context: PluginContext, apps: list[str], keys: list[str]
    ) -> ContextData:
        """
        Returns the first dictionary (by app order) that contains at least one of the given keys.
        """
        for app in apps:
            data = context.get(app, {})
            if any(data.get(key) for key in keys):
                return data
        return {}

    @staticmethod
    def format_status(prefix: str, main_text: str, sep: str, current_time: str) -> str:
        """
        Combines prefix, main text, separator, and current time into a status string.
        """
        return f"{prefix}{main_text}{sep}{current_time}"

    @staticmethod
    def clean(text: str) -> str:
        """
        Cleans text by removing content within brackets or parentheses.
        """
        return re.sub(r"\[.*?\]|\(.*?\)", "", text).strip()
