"""
GreenPES: Prompt Saturation Analysis Framework

A framework for studying LLM prompt efficiency and quality saturation.
GreenPES metric code archived — see archive/ARCHIVE_RATIONALE.md.
"""

from .evaluators import QualityEvaluator, QAEvaluator, SummarizationEvaluator, get_evaluator, MathReasoningEvaluator, ProductExtractionEvaluator
from .llm import (
    LLMProvider, GeminiProvider, GroqProvider, OpenAIProvider,
    AnthropicProvider, TogetherProvider, MockProvider, LLMResponse
)

__version__ = "0.2.0"

__all__ = [
    # Evaluators
    "QualityEvaluator",
    "QAEvaluator",
    "SummarizationEvaluator",
    "MathReasoningEvaluator",
    "ProductExtractionEvaluator",
    "get_evaluator",
    # LLM Providers
    "LLMProvider",
    "GeminiProvider",
    "GroqProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "TogetherProvider",
    "MockProvider",
    "LLMResponse",
]
