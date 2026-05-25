"""Prompt template with variable substitution."""

from __future__ import annotations

import string
from typing import List


class PromptTemplate:
    """A template for constructing prompts with variable substitution.

    Usage:
        template = PromptTemplate("Hello, {name}! You are a {role}.")
        rendered = template.render(name="Alice", role="developer")
        # "Hello, Alice! You are a developer."
    """

    def __init__(self, template: str) -> None:
        self.template = template

    @property
    def variables(self) -> List[str]:
        """Extract variable names from the template."""
        formatter = string.Formatter()
        names = []
        for _, field_name, _, _ in formatter.parse(self.template):
            if field_name is not None and field_name not in names:
                names.append(field_name)
        return names

    def render(self, **kwargs: str) -> str:
        """Render the template with the given variables.

        Raises KeyError if a required variable is missing.
        """
        return self.template.format(**kwargs)
