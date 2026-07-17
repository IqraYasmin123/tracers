"""
Abstract base interface for TRACER's explanation generators.

Same Dependency Inversion pattern as every prior module. Right now RuleBasedExplainer is the
only implementation, but this interface leaves room for e.g. an LLM-backed explainer later
without changing any calling code — see docs/module8_xai.md for why rule-based was chosen
as the actual implementation here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .context import ExplanationContext
from .explanation import Explanation


class BaseExplainer(ABC):
    """Abstract interface every TRACER explainer must implement."""

    @abstractmethod
    def explain(self, context: ExplanationContext) -> Explanation:
        raise NotImplementedError
