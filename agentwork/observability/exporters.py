"""Metric and trace exporters: Console, File, and OpenTelemetry-compatible."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import List


class Exporter(ABC):
    """Abstract base class for data exporters."""

    @abstractmethod
    def export(self, data: List[dict]) -> None:
        """Export a batch of data entries."""
        ...


class ConsoleExporter(Exporter):
    """Exports data entries as JSON to stdout."""

    def export(self, data: List[dict]) -> None:
        """Print each entry as a JSON string."""
        for entry in data:
            print(json.dumps(entry))


class FileExporter(Exporter):
    """Exports data entries as JSON lines to a file."""

    def __init__(self, file_path: str) -> None:
        self._file_path = file_path

    def export(self, data: List[dict]) -> None:
        """Append each entry as a JSON line to the file."""
        with open(self._file_path, "a") as f:
            for entry in data:
                f.write(json.dumps(entry) + "\n")


class OTELExporter(Exporter):
    """Exports data in OpenTelemetry-compatible JSON structure (stub)."""

    def export(self, data: List[dict]) -> None:
        """Format and print data in OTEL-compatible structure."""
        otel_payload = {
            "resourceSpans": [
                {
                    "resource": {"attributes": []},
                    "scopeSpans": [
                        {
                            "scope": {"name": "agentwork"},
                            "spans": data,
                        }
                    ],
                }
            ]
        }
        print(json.dumps(otel_payload))
