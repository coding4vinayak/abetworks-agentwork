"""Prompt template with safe variable substitution."""

from __future__ import annotations

import re
from typing import List


# Matches simple {variable_name} placeholders (no attribute access, indexing, or format specs)
_VARIABLE_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


class PromptTemplate:
    """A template for constructing prompts with safe variable substitution.

    Only simple {variable_name} placeholders are supported. Attribute access
    (e.g., {name.__class__}), indexing, and format specs are not allowed,
    preventing format-string injection attacks.

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
        names = []
        for match in _VARIABLE_PATTERN.finditer(self.template):
            name = match.group(1)
            if name not in names:
                names.append(name)
        return names

    def render(self, **kwargs: str) -> str:
        """Render the template with the given variables.

        Uses simple regex-based substitution that only allows plain variable
        names. Does NOT allow attribute access like {name.__class__}.

        Raises KeyError if a required variable is missing.
        """
        # Check all required variables are provided
        for var in self.variables:
            if var not in kwargs:
                raise KeyError(var)

        def _replace(match: re.Match) -> str:
            name = match.group(1)
            if name in kwargs:
                return str(kwargs[name])
            # Leave unmatched placeholders as-is (should not happen after check)
            return match.group(0)

        return _VARIABLE_PATTERN.sub(_replace, self.template)
