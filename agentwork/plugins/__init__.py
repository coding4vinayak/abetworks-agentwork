"""Plugin system for loading custom tools from external packages at runtime."""

from agentwork.plugins.manifest import PluginManifest
from agentwork.plugins.plugin import Plugin
from agentwork.plugins.manager import PluginManager

__all__ = ["PluginManifest", "Plugin", "PluginManager"]
