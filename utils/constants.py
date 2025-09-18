from zenif.log import Logger

l = Logger(  # noqa: E741
    {
        "log_line": {
            "format": [
                {
                    "type": "template",
                    "value": "level",
                    "parameters": [
                        {"color": {"foreground": "default"}},
                        {"truncate": {"width": 0, "marker": ""}},
                        {"affix": {"prefix": ">> "}},
                    ],
                }
            ]
        },
        "timestamps": {"always_show": True},
    }
)


VERSION = "1.0.0"

MIN_RATE_LIMIT = 2.9

DEFAULT_TIME_FORMAT = "%H:%M"
DEFAULT_SEPARATOR = ": "


def FB_ICON() -> str:
    """Return the fallback icon"""
    # l.warning("An icon could not be found; using fallback icon")
    return "❓"


def FB_TEXT() -> str:
    """Return the fallback text"""
    # l.warning("A status could not be found; using fallback status")
    return "No status"
