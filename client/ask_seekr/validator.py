from typing import Dict, Any
from client.ask_seekr.registry.pipeline_registry import PIPELINE_REGISTRY, requires_confirmation


def _format_args_for_confirmation(args: Dict[str, Any]) -> str:
    """Format non-empty arguments as a markdown list for the confirmation prompt."""
    lines = []
    for key, value in args.items():
        if value is None or value == "":
            continue
        text = str(value)
        if len(text) > 120:
            text = text[:120] + "..."
        lines.append(f"- {key}: {text}")
    return "\n".join(lines) if lines else ""


def validate_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a planner decision before execution.

    Status semantics:
    - OK: plan is valid and can be executed.
    - NEEDS_CONFIRMATION: plan is valid but requires explicit user approval
      (e.g. HIGH risk actions). The frontend should resend with confirmed=True.
    - BLOCKED: plan is invalid or unrecoverable (unknown pipeline, missing
      required arguments). The user must rephrase or provide more info.
    """

    if plan["type"] != "ACTION":
        return {"status": "OK"}

    pipeline = plan.get("pipeline")

    if pipeline not in PIPELINE_REGISTRY:
        return {
            "status": "BLOCKED",
            "message": f"Unknown pipeline '{pipeline}'."
        }

    cfg = PIPELINE_REGISTRY[pipeline]

    missing = plan.get("missing", [])
    if missing:
        return {
            "status": "BLOCKED",
            "message": (
                f"Missing required information: {', '.join(missing)}"
            )
        }

    if requires_confirmation(cfg) and not plan.get("confirmed", False):
        action_description = cfg.get("description", pipeline)
        args_summary = _format_args_for_confirmation(plan.get("args", {}))

        message = f"This action is high risk: **{pipeline}** — {action_description}."
        if args_summary:
            message += f"\n\nDetails:\n{args_summary}"
        message += "\n\nPlease confirm before I proceed."

        return {
            "status": "NEEDS_CONFIRMATION",
            "message": message
        }

    return {"status": "OK"}
