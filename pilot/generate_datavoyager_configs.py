import copy
import yaml

BASE = "../upstream/agent-baselines/agent_baselines/solvers/datavoyager/dv_core/config/datavoyager_modal_deployment_magentic_one_config_20250617.yaml"

TARGETS = {
    "gpt5nano": "openai/gpt-5-nano",
    "gemini25flashlite": "google/gemini-2.5-flash-lite",
    "deepseekv4flash0731": "deepseek/deepseek-v4-flash-0731",
}

MODEL_INFO = {
    "vision": False,
    "function_calling": True,
    "json_output": True,
    "family": "unknown",
    "structured_output": True,
}

with open(BASE) as f:
    base_cfg = yaml.safe_load(f)

for label, model_id in TARGETS.items():
    cfg = copy.deepcopy(base_cfg)
    for agent_name, agent_cfg in cfg["agents"].items():
        if "model_client" in agent_cfg:
            agent_cfg["model_client"]["model"] = model_id
            agent_cfg["model_client"]["base_url"] = "https://openrouter.ai/api/v1"
            agent_cfg["model_client"]["model_info"] = MODEL_INFO
            agent_cfg["model_client"].pop("seed", None)
    cfg["orchestrator"]["model_client"]["model"] = model_id
    cfg["orchestrator"]["model_client"]["base_url"] = "https://openrouter.ai/api/v1"
    cfg["orchestrator"]["model_client"]["model_info"] = MODEL_INFO
    cfg["orchestrator"]["model_client"].pop("seed", None)

    out_path = f"datavoyager_configs/{label}.yaml"
    with open(out_path, "w") as f:
        yaml.dump(cfg, f, sort_keys=False, allow_unicode=True)
    print("wrote", out_path, "-> model:", model_id)
