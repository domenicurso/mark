from typing import NewType

PluginID = NewType("PluginID", str)
ContextData = dict[str, any]
PluginContext = dict[str, ContextData]
PluginStatus = tuple[str, str, str]
PluginSettings = dict[str, any]
