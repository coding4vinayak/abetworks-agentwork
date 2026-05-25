"""Plugin manager for discovering, loading, and managing plugins."""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

from agentwork.plugins.manifest import PluginManifest
from agentwork.plugins.plugin import Plugin
from agentwork.tools.base import Tool

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages plugin discovery, loading, and lifecycle.

    Discovers plugins by scanning directories for plugin.json manifest files,
    loads them, and provides access to all tools from loaded plugins.
    """

    def __init__(self) -> None:
        self._plugins: Dict[str, Plugin] = {}

    def discover(self, directory: str) -> List[PluginManifest]:
        """Scan directory for plugin.json files and parse them as PluginManifest.

        Uses os.walk to find nested plugin.json files.

        Args:
            directory: Root directory to scan for plugins.

        Returns:
            List of discovered PluginManifest instances.
        """
        manifests: List[PluginManifest] = []

        if not os.path.isdir(directory):
            logger.warning("Plugin directory does not exist: %s", directory)
            return manifests

        for root, _dirs, files in os.walk(directory):
            if "plugin.json" in files:
                manifest_path = os.path.join(root, "plugin.json")
                try:
                    with open(manifest_path, "r") as f:
                        data = json.load(f)
                    manifest = PluginManifest(**data)
                    manifests.append(manifest)
                    logger.debug("Discovered plugin: %s at %s", manifest.name, manifest_path)
                except Exception as e:
                    logger.warning(
                        "Failed to parse plugin manifest at %s: %s",
                        manifest_path,
                        str(e),
                    )

        return manifests

    def load_plugin(self, manifest: PluginManifest) -> Plugin:
        """Create a Plugin from a manifest, load it, and track it.

        Args:
            manifest: The plugin manifest to load.

        Returns:
            The loaded Plugin instance.
        """
        plugin = Plugin(manifest)
        plugin.load()
        self._plugins[manifest.name] = plugin
        return plugin

    def unload_plugin(self, name: str) -> None:
        """Unload a plugin and remove it from tracking.

        Args:
            name: The name of the plugin to unload.
        """
        plugin = self._plugins.get(name)
        if plugin is not None:
            plugin.unload()
            del self._plugins[name]
        else:
            logger.warning("Cannot unload plugin '%s': not found", name)

    def reload_plugin(self, name: str) -> Plugin:
        """Reload a plugin by name.

        Args:
            name: The name of the plugin to reload.

        Returns:
            The reloaded Plugin instance.

        Raises:
            KeyError: If plugin is not found.
        """
        plugin = self._plugins.get(name)
        if plugin is None:
            raise KeyError(f"Plugin '{name}' not found")
        plugin.reload()
        return plugin

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name.

        Args:
            name: The plugin name.

        Returns:
            The Plugin instance, or None if not found.
        """
        return self._plugins.get(name)

    def list_plugins(self) -> List[Plugin]:
        """Return all tracked plugins.

        Returns:
            List of all Plugin instances.
        """
        return list(self._plugins.values())

    def get_all_tools(self) -> List[Tool]:
        """Aggregate tools from all loaded plugins.

        Returns:
            List of Tool instances from all loaded plugins.
        """
        tools: List[Tool] = []
        for plugin in self._plugins.values():
            if plugin.loaded:
                tools.extend(plugin.tools)
        return tools
