"""
Runs a single AstaBench discoverybench_validation sample through a given
agent-baselines solver, with ALL model calls (including the task's own
internal LLM-judge scorer, which hardcodes a direct OpenAI call) routed
through OpenRouter.

The discoverybench scorer (astabench.evals.discoverybench.lm_utils) calls
get_model(f"openai/{model}") with model="gpt-4o-2024-08-06" by default.
Inspect's native "openai" provider then sends the bare string
"gpt-4o-2024-08-06" to whatever OPENAI_BASE_URL is configured -- but
OpenRouter's catalog only recognizes the provider-prefixed ID
"openai/gpt-4o-2024-08-06". Rather than edit the installed package (an
irreversible change to third-party files), this monkey-patches the
module's DEFAULT_EVAL_OPENAI_MODEL and the two get_model() call sites
in-memory before running the eval, so the scorer calls
get_model("openrouter/openai/gpt-4o-2024-08-06") instead -- which
Inspect's openrouter provider forwards correctly as
model="openai/gpt-4o-2024-08-06" to OpenRouter.

It then re-invokes Inspect's own `eval` CLI command object directly
(inspect_ai._cli.main.eval_command) with the exact same argv a normal
`inspect eval ...` invocation would get, so all solver/model/sample-id
resolution semantics are identical to the CLI -- only the patch differs.

Usage: same flags as `inspect eval astabench/discoverybench_validation`,
e.g.:
  uv run --project solvers/<solver> --python 3.11 --frozen -- \
    python3 ../../pilot/run_discoverybench_openrouter.py \
      --solver <inspect solver ref> \
      --model openrouter/<provider>/<model-id> \
      --sample-id "<id>" \
      --max-connections 1 \
      --log-dir <dir> \
      [-S key=value ...]
"""

import sys


def patch_discoverybench_scorer_model() -> None:
    from astabench.evals.discoverybench import lm_utils

    judge_model = "openrouter/openai/gpt-4o-2024-08-06"

    async def patched_get_response(prompt, max_retry=5, model=judge_model, verbose=False):
        from inspect_ai.model import GenerateConfig, get_model

        model_obj = get_model(model, config=GenerateConfig(**lm_utils.OPENAI_GEN_HYP))
        n_try = 0
        while n_try < max_retry:
            response = await model_obj.generate(
                lm_utils.oaidicts_to_chatmessages(lm_utils.create_prompt(prompt))
            )
            output = response.choices[0].message.content.strip().strip("`json")
            try:
                import json

                return json.loads(output)
            except ValueError:
                n_try += 1
        return None

    async def patched_run_chatgpt_query_multi_turn(
        messages, model_name=judge_model, json_response=False
    ):
        from inspect_ai.model import GenerateConfig, get_model

        model_obj = get_model(
            model_name,
            config=GenerateConfig(
                response_schema=lm_utils.any_json_schema if json_response else None,
                **lm_utils.OPENAI_GEN_HYP,
            ),
        )
        return await model_obj.generate(lm_utils.oaidicts_to_chatmessages(messages))

    lm_utils.DEFAULT_EVAL_OPENAI_MODEL = judge_model
    lm_utils.get_response = patched_get_response
    lm_utils.run_chatgpt_query_multi_turn = patched_run_chatgpt_query_multi_turn

    from astabench.evals.discoverybench import eval_utils

    if hasattr(eval_utils, "get_response"):
        eval_utils.get_response = patched_get_response
    if hasattr(eval_utils, "run_chatgpt_query_multi_turn"):
        eval_utils.run_chatgpt_query_multi_turn = patched_run_chatgpt_query_multi_turn


def main() -> int:
    patch_discoverybench_scorer_model()

    import inspect_ai._cli.main as cli_main

    sys.argv = ["inspect", "eval", "astabench/discoverybench_validation"] + sys.argv[1:]
    try:
        cli_main.main()
    except SystemExit as e:
        return int(e.code or 0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
