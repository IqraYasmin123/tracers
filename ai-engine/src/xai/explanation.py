"""Explanation — the output of every explainer."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Explanation:
    """A structured, human-readable explanation of one image's forensic analysis.

    `summary` is a single headline sentence; `details` are supporting bullet points
    (detection reasoning, attack-type reasoning, attribution reasoning, reconstruction
    reasoning — whichever apply, in that order).
    """

    summary: str
    details: list[str] = field(default_factory=list)
    confidence_level: str = "low"

    def full_text(self) -> str:
        """Render as plain text — summary followed by bulleted details."""
        bullets = "\n".join(f"- {detail}" for detail in self.details)
        return f"{self.summary}\n\n{bullets}" if bullets else self.summary
