"""GreenPES experiments module.

Benchmark and optimizer code archived — see archive/ARCHIVE_RATIONALE.md.
Active experiments: saturation analysis (saturation_benchmark.py, saturation_analysis.py).
"""

from .prompting_strategies import (
    PromptingStrategy,
    generate_prompt,
    TASK_CONFIGS,
    BENCHMARK_EXAMPLES,
)
