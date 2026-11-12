# DiscoveryBench Baseline Pilot

Low-cost ($10 budget) baseline pilot comparing 3 agent frameworks (ReAct, Smolagents Coder,
Asta DataVoyager) x 3 LLM backbones (GPT-5 Nano, Gemini 2.5 Flash-Lite, DeepSeek V4 Flash 0731),
all routed through OpenRouter, on the AstaBench implementation of DiscoveryBench
(https://github.com/allenai/asta-bench, https://github.com/allenai/agent-baselines).

This is an external-baseline-only pilot. It does not run or modify PerpetualMotion.

## Layout

- `pilot/task_ids.txt` — the 20 frozen DiscoveryBench validation sample IDs used across all arms.
- `pilot/datavoyager_configs/` — per-model OpenRouter-routed MagenticOne configs for the
  DataVoyager solver (its default config hardcodes `gpt-4o` and ignores Inspect's `--model` flag).
- `pilot/calib/` — the single shared calibration task used for the first cross-arm cost/compat check.
- `pilot/logs/` — raw Inspect `.eval` logs per run.
- `pilot/generate_datavoyager_configs.py` — script that generated the DataVoyager configs.

The upstream repos (`asta-bench`, `agent-baselines`) are cloned locally under `upstream/` but
not committed here (see `.gitignore`); clone them directly from Allen Institute for AI's GitHub
if reproducing this.
