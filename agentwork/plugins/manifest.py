"""Plugin manifest model for metadata and configuration."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class PluginManifest(BaseModel):
    """Metadata describing a plugin and its entry point."""

    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    tools: List[str] = []
    dependencies: List[str] = []
    entry_point: str
