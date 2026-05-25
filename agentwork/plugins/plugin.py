"""Plugin class for loading and managing tool modules."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from typing import List, Optional

from agentwork.plugins.manifest import PluginManifest
from agentwork.tools.base import Tool

logger = logging.getLogger(__name__)


class Plugin:
    """A loaded plugin that provides Tool instances.

    Wraps a PluginManifest and manages the lifecycle of loading/unloading
    the module specified by the manifest's entry_point.
    """

    def __init__(self, manifest: PluginManifest) -> None:
        self._manifest = manifest
        self._loaded = False
        self._tools: List[Tool] = []
        self._error: Optional[str] = None
        self._module = None

    @property
    def name(self) -> str:
        return self._manifest.name

    @property
    def version(self) -> str:
        return self._manifest.version

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def tools(self) -> List[Tool]:
        return list(self._tools)

    @property
    def error(self) -> Optional[str]:
        return self._error

    @property
    def manifest(self) -> PluginManifest:
        return self._manifest

    def load(self) -> "Plugin":
        """Import the module from entry_point and collect Tool instances.

        Uses importlib.import_module for dotted paths and
        importlib.util.spec_from_file_location for file paths.
        Errors are captured in the error property rather than raised.

        Returns self for chaining.
        """
        self._error = None
        self._tools = []

        try:
            entry_point = self._manifest.entry_point
            module = self._import_module(entry_point)
            self._module = module

            # Scan module attributes for Tool instances
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, Tool):
                    self._tools.append(attr)

            self._loaded = True
            logger.info(
                "Plugin '%s' loaded with %d tools", self.name, len(self._tools)
            )

        except Exception as e:
            self._error = str(e)
            self._loaded = False
            logger.error("Failed to load plugin '%s': %s", self.name, str(e))

        return self

    def unload(self) -> None:
        """Clear tools and mark as unloaded."""
        self._tools = []
        self._loaded = False
        self._error = None
        self._module = None
        logger.info("Plugin '%s' unloaded", self.name)

    def reload(self) -> "Plugin":
        """Unload then load the plugin (hot-reload).

        For dotted-path plugins, uses importlib.reload() on the cached module
        to pick up file changes. For file-path plugins, re-executes the file.
        """
        cached_module = self._module
        entry_point = self._manifest.entry_point
        self.unload()

        # For dotted-path imports, reload the cached module so changes are picked up
        is_file_path = "/" in entry_point or "\\" in entry_point or entry_point.endswith(".py")
        if not is_file_path and cached_module is not None:
            try:
                importlib.reload(cached_module)
            except Exception:
                pass

        return self.load()

    def _import_module(self, entry_point: str):
        """Import a module from a dotted path or file path."""
        # Determine if this is a file path (contains / or \ or ends with .py)
        if "/" in entry_point or "\\" in entry_point or entry_point.endswith(".py"):
            return self._import_from_file(entry_point)
        else:
            return importlib.import_module(entry_point)

    def _import_from_file(self, file_path: str):
        """Import a module from a file path."""
        spec = importlib.util.spec_from_file_location("_plugin_module", file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from path: {file_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
