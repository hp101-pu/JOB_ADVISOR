from typing import Dict, Any
from client.ask_seekr.registry.pipeline_registry import PIPELINE_REGISTRY


def validate_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a planner decision before execution.
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
                f"Missing required information: "
                f"{', '.join(missing)}"
            )
        }

    
    if cfg.get("requires_confirmation", False):
        if not plan.get("confirmed", False):
            return {
                "status": "NEEDS_CONFIRMATION",
                "message": (
                    "Please confirm before I proceed."
                )
            }

    
    if cfg["risk"] == "HIGH" and not plan.get("confirmed", False):
        return {
            "status": "BLOCKED",
            "message": (
                "This action is considered high risk. "
                "Please confirm before I proceed."
            )
        }

    return {"status": "OK"}
