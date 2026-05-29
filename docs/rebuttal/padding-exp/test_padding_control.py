"""
Dry-run test for the padding control experiment.

Verifies the full pipeline works end-to-end using MockProvider (no API keys needed).
Run with: python tests/test_padding_control.py
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greenprompt.llm import MockProvider, LLMResponse
from greenprompt.evaluators import LLMJudgeEvaluator
from experiments.rebuttal_padding_control import (
    build_padded_prompts,
    format_prompt,
    run_padding_control,
    analyze_padding_control,
    PADDING_TYPES,
    TARGET_TOKENS_BY_TASK,
    CURATED_EXAMPLE_INDICES,
    OUTPUT_PATH,
    ANALYSIS_PATH,
)
from experiments.prompting_strategies import BENCHMARK_EXAMPLES
from experiments.saturation_prompts import TASK_INPUT_KEY


class MockJudgeProvider(MockProvider):
    """Mock that returns valid judge JSON scores."""

    def __init__(self, **kwargs):
        # Accept and ignore any kwargs (api_key, model, etc.)
        super().__init__(response_text="mock", model="mock-judge")

    def generate(self, prompt: str, max_tokens: int = 500) -> LLMResponse:
        # Return a valid judge response
        input_tokens = int(len(prompt.split()) * 1.3)
        judge_response = '{"correctness": 4, "completeness": 4, "reasoning": 3, "conciseness": 4}'
        return LLMResponse(
            text=judge_response,
            input_tokens=input_tokens,
            output_tokens=15,
            latency_ms=5.0,
            model="mock-judge",
        )


def test_prompt_building():
    """Test that prompts are built correctly for all tasks and padding types."""
    print("=" * 60)
    print("TEST 1: Prompt Building")
    print("=" * 60)

    for task in ['classification', 'product_extraction']:
        for padding_type in PADDING_TYPES:
            templates = build_padded_prompts(task, padding_type)

            # Should have 7 levels
            assert len(templates) == 7, f"Expected 7 templates, got {len(templates)}"

            # L1 should be the bare prompt (no padding)
            assert '[Additional context:' not in templates[0], \
                f"L1 should not have padding for {task}/{padding_type}"

            # L2-L7 should have padding
            for i in range(1, 7):
                assert '[Additional context:' in templates[i], \
                    f"L{i+1} should have padding for {task}/{padding_type}"

            # Token counts should increase monotonically
            example = BENCHMARK_EXAMPLES[task][0]
            prev_words = 0
            for i, t in enumerate(templates):
                prompt = format_prompt(t, task, example)
                words = len(prompt.split())
                assert words > prev_words, \
                    f"L{i+1} ({words} words) should be longer than L{i} ({prev_words} words)"
                prev_words = words

            print(f"  ✓ {task}/{padding_type}: 7 levels, monotonically increasing")

    print("\n  All prompt building tests passed!\n")


def test_token_matching():
    """Test that padded prompts approximately match target token counts."""
    print("=" * 60)
    print("TEST 2: Token Count Matching")
    print("=" * 60)

    for task in ['classification', 'product_extraction']:
        templates = build_padded_prompts(task, 'irrelevant_facts')
        example = BENCHMARK_EXAMPLES[task][0]
        targets = TARGET_TOKENS_BY_TASK[task]

        print(f"\n  {task}:")
        print(f"  {'Level':<8} {'Words':<8} {'~Tokens':<10} {'Target':<10} {'Ratio':<8}")
        print(f"  {'-'*44}")

        for i, t in enumerate(templates):
            prompt = format_prompt(t, task, example)
            words = len(prompt.split())
            est_tokens = int(words * 1.3)
            target = targets[i + 1]
            ratio = est_tokens / target if target > 0 else 0
            print(f"  L{i+1:<6} {words:<8} {est_tokens:<10} {target:<10} {ratio:.2f}")

        # L7 should be within 50% of target (rough match is fine —
        # actual API tokenizer will differ anyway)
        prompt_l7 = format_prompt(templates[6], task, example)
        est_l7 = int(len(prompt_l7.split()) * 1.3)
        target_l7 = targets[7]
        assert est_l7 > target_l7 * 0.5, \
            f"L7 tokens ({est_l7}) too far below target ({target_l7})"

    print("\n  Token matching tests passed!\n")


def test_full_pipeline_mock():
    """Test the full run + analysis pipeline with mock providers."""
    print("=" * 60)
    print("TEST 3: Full Pipeline (Mock Providers)")
    print("=" * 60)

    # Use a temp directory for output
    import experiments.rebuttal_padding_control as module

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_output = os.path.join(tmpdir, 'padding_results.json')
        tmp_analysis = os.path.join(tmpdir, 'padding_analysis.json')

        # Monkey-patch the output paths
        original_output = module.OUTPUT_PATH
        original_analysis = module.ANALYSIS_PATH
        module.OUTPUT_PATH = tmp_output
        module.ANALYSIS_PATH = tmp_analysis

        # Monkey-patch get_provider to return mock
        import experiments.saturation_benchmark as bench_module
        original_get_provider = bench_module.get_provider

        def mock_get_provider(model_name):
            mock = MockProvider(
                response_text="positive",  # valid classification response
                model=model_name,
            )
            return model_name, mock

        bench_module.get_provider = mock_get_provider

        # Monkey-patch GeminiProvider in the module to use MockJudgeProvider
        import greenprompt.llm as llm_module
        original_gemini = llm_module.GeminiProvider
        llm_module.GeminiProvider = MockJudgeProvider

        # Also need to set a fake env var so the judge check passes
        os.environ.setdefault('GEMINI_API_KEY', 'fake-key-for-testing')

        try:
            # Run with minimal scope: 1 model, 1 task, 1 padding type
            print("\n  Running experiment (mock, minimal scope)...")
            results = run_padding_control(
                model_names=['mock'],
                tasks=['classification'],
                padding_types=['irrelevant_facts'],
                delay=0,  # no delay for testing
                resume=False,
            )

            # Check results
            assert len(results) > 0, "No results produced"
            successful = [r for r in results if 'error' not in r]
            expected = 7 * len(CURATED_EXAMPLE_INDICES['classification'])  # 7 levels × 7 examples
            print(f"  Generated {len(successful)} successful records (expected {expected})")
            assert len(successful) == expected, \
                f"Expected {expected} records, got {len(successful)}"

            # Check record structure
            r = successful[0]
            required_fields = [
                'model', 'task', 'padding_type', 'level', 'example_id',
                'prompt_tokens', 'output_tokens', 'response_text',
                'quality', 'completed', 'timestamp',
            ]
            for field in required_fields:
                assert field in r, f"Missing field: {field}"
            print(f"  ✓ Record structure correct ({len(required_fields)} fields)")

            # Check that results were saved
            assert os.path.exists(tmp_output), "Results file not created"
            with open(tmp_output) as f:
                saved = json.load(f)
            assert len(saved) == len(results), "Saved results don't match"
            print(f"  ✓ Results saved to disk ({len(saved)} records)")

            # Run analysis
            print("\n  Running analysis...")
            analysis = analyze_padding_control(
                results_path=tmp_output,
                compare_with_real=False,
            )

            assert 'summary' in analysis, "Analysis missing 'summary'"
            assert 'per_task' in analysis, "Analysis missing 'per_task'"
            assert 'classification' in analysis['per_task'], "Missing classification in analysis"
            assert 'mock' in analysis['per_task']['classification'], "Missing mock model"

            entry = analysis['per_task']['classification']['mock']['irrelevant_facts']
            assert 'quality_by_level' in entry, "Missing quality_by_level"
            assert 'spearman_r' in entry, "Missing spearman_r"
            assert 'quality_delta_l1_l7' in entry, "Missing quality_delta_l1_l7"
            print(f"  ✓ Analysis structure correct")
            print(f"    Quality by level: {entry['quality_by_level']}")
            print(f"    L1→L7 delta: {entry['quality_delta_l1_l7']}")
            print(f"    Spearman r: {entry['spearman_r']}, p: {entry['spearman_p']}")
            print(f"    Trend significant: {entry['trend_significant']}")

            # With mock (constant response), quality should be flat
            delta = entry['quality_delta_l1_l7']
            assert delta is None or abs(delta) < 0.01, \
                f"Mock should produce flat quality (constant response), got delta={delta}"
            print(f"  ✓ Mock produces flat quality (as expected)")

        finally:
            # Restore originals
            module.OUTPUT_PATH = original_output
            module.ANALYSIS_PATH = original_analysis
            bench_module.get_provider = original_get_provider
            llm_module.GeminiProvider = original_gemini

    print("\n  Full pipeline test passed!\n")


def test_resume_logic():
    """Test that --resume correctly skips completed experiments."""
    print("=" * 60)
    print("TEST 4: Resume Logic")
    print("=" * 60)

    import experiments.rebuttal_padding_control as module
    import experiments.saturation_benchmark as bench_module
    import greenprompt.llm as llm_module

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_output = os.path.join(tmpdir, 'padding_results.json')
        tmp_analysis = os.path.join(tmpdir, 'padding_analysis.json')

        module.OUTPUT_PATH = tmp_output
        module.ANALYSIS_PATH = tmp_analysis

        original_get_provider = bench_module.get_provider
        original_gemini = llm_module.GeminiProvider

        call_count = [0]

        class CountingMock(MockProvider):
            def generate(self, prompt, max_tokens=500):
                call_count[0] += 1
                return super().generate(prompt, max_tokens)

        def mock_get_provider(model_name):
            mock = CountingMock(response_text="positive", model=model_name)
            return model_name, mock

        bench_module.get_provider = mock_get_provider
        llm_module.GeminiProvider = MockJudgeProvider
        os.environ.setdefault('GEMINI_API_KEY', 'fake-key-for-testing')

        try:
            # First run
            call_count[0] = 0
            run_padding_control(
                model_names=['mock'],
                tasks=['classification'],
                padding_types=['irrelevant_facts'],
                delay=0,
                resume=False,
            )
            first_run_calls = call_count[0]
            print(f"  First run: {first_run_calls} provider calls")

            # Second run with resume — should make 0 new calls
            call_count[0] = 0
            run_padding_control(
                model_names=['mock'],
                tasks=['classification'],
                padding_types=['irrelevant_facts'],
                delay=0,
                resume=True,
            )
            second_run_calls = call_count[0]
            print(f"  Resume run: {second_run_calls} provider calls (should be 0)")
            assert second_run_calls == 0, \
                f"Resume should skip all, but made {second_run_calls} calls"
            print(f"  ✓ Resume correctly skips completed experiments")

        finally:
            module.OUTPUT_PATH = OUTPUT_PATH
            module.ANALYSIS_PATH = ANALYSIS_PATH
            bench_module.get_provider = original_get_provider
            llm_module.GeminiProvider = original_gemini

    print("\n  Resume logic test passed!\n")


def test_padding_content_differs():
    """Test that different padding types produce different content."""
    print("=" * 60)
    print("TEST 5: Padding Content Diversity")
    print("=" * 60)

    task = 'classification'
    example = BENCHMARK_EXAMPLES[task][0]

    prompts_by_type = {}
    for pt in PADDING_TYPES:
        templates = build_padded_prompts(task, pt)
        # Check L4 (middle level with substantial padding)
        prompt = format_prompt(templates[3], task, example)
        prompts_by_type[pt] = prompt

    # All three should be different
    assert prompts_by_type['irrelevant_facts'] != prompts_by_type['repeated_filler']
    assert prompts_by_type['irrelevant_facts'] != prompts_by_type['random_words']
    assert prompts_by_type['repeated_filler'] != prompts_by_type['random_words']
    print("  ✓ All three padding types produce different prompts")

    # But all should start with the same bare task instruction
    for pt, prompt in prompts_by_type.items():
        assert prompt.startswith("Classify:"), \
            f"{pt} doesn't start with bare instruction"
    print("  ✓ All start with the same bare task instruction")

    # Show samples
    for pt, prompt in prompts_by_type.items():
        # Extract just the padding part
        padding_start = prompt.find('[Additional context:')
        if padding_start >= 0:
            padding = prompt[padding_start:padding_start + 100]
            print(f"  {pt}: ...{padding}...")

    print("\n  Padding diversity test passed!\n")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  PADDING CONTROL EXPERIMENT — DRY RUN TESTS")
    print("  (No API keys required)")
    print("=" * 60 + "\n")

    test_prompt_building()
    test_token_matching()
    test_full_pipeline_mock()
    test_resume_logic()
    test_padding_content_differs()

    print("=" * 60)
    print("  ALL TESTS PASSED ✓")
    print("=" * 60)
    print("\n  The experiment code is verified and ready to run with real API keys.")
    print("  See docs/rebuttal/RUNNING_INSTRUCTIONS.md for next steps.\n")
