import json
from typing import Dict, Any, Optional
from client.mcp.client import get_mcp_client

# cached tool lookup — only populated once, cleared on error
_tools: Dict[str, Any] = {}


def _clear_tools_cache():
    global _tools
    _tools = {}


async def _get_tool(name: str):
    """
    Fetch tools from the 'resume' server only — avoids spawning gmail/job_search
    subprocesses when only resume tools are needed. Caches results.
    """
    global _tools
    if not _tools:
        print(f"[WRAPPER] _tools cache empty, calling get_mcp_client...", flush=True)
        mcp = await get_mcp_client()
        print(f"[WRAPPER] got mcp client, calling get_tools(server_name='resume')...", flush=True)
        all_tools = await mcp.get_tools(server_name="resume")
        print(f"[WRAPPER] got tools: {[t.name for t in all_tools]}", flush=True)
        _tools = {t.name: t for t in all_tools}

    tool = _tools.get(name)
    if not tool:
        _clear_tools_cache()
        raise RuntimeError(f"MCP tool '{name}' not found. Is resume_mcp running?")
    return tool


def _unwrap(result) -> dict:
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict) and item.get("type") == "text":
                return json.loads(item["text"])
        first = result[0] if result else {}
        return first if isinstance(first, dict) else {}
    raise ValueError(f"Unexpected MCP response type: {type(result)}")


async def parse_resume_pdf(file_b64: str) -> Dict[str, Any]:
    """Call resume_mcp:parse_resume."""
    try:
        print("[WRAPPER] getting tool: parse_resume...", flush=True)
        tool = await _get_tool("parse_resume")
        print("[WRAPPER] calling ainvoke on parse_resume...", flush=True)
        raw_result = await tool.ainvoke({"file_b64": file_b64})
        print(f"[WRAPPER] ainvoke returned: type={type(raw_result)}, val={repr(raw_result)[:300]}", flush=True)
        data = _unwrap(raw_result)
        print(f"[WRAPPER] unwrapped data: {repr(data)[:300]}", flush=True)
    except Exception as e:
        print(f"[WRAPPER] EXCEPTION in parse_resume_pdf: {e}", flush=True)
        _clear_tools_cache()
        return {"success": False, "error": f"MCP connection error: {str(e)}"}

    if data.get("status") != "ok":
        return {"success": False, "error": data.get("message") or "parse_resume failed"}

    return {"success": True, "parsed_resume": data.get("result", {})}


async def score_resume_ats(
    parsed_resume: dict,
    use_llm: bool = False,
    job_description: Optional[str] = None,
) -> Dict[str, Any]:
    """Call resume_mcp:ats_score."""
    try:
        print("[WRAPPER] getting tool: ats_score...", flush=True)
        tool = await _get_tool("ats_score")
        print("[WRAPPER] calling ainvoke on ats_score...", flush=True)

        args = {
            "parsed_resume": json.dumps(parsed_resume),
            "use_llm": use_llm,
        }
        if job_description is not None:
            args["job_description"] = job_description

        raw_result = await tool.ainvoke(args)
        print(f"[WRAPPER] ainvoke returned: type={type(raw_result)}, val={repr(raw_result)[:300]}", flush=True)
        data = _unwrap(raw_result)
        print(f"[WRAPPER] unwrapped data: {repr(data)[:300]}", flush=True)
    except Exception as e:
        print(f"[WRAPPER] EXCEPTION in score_resume_ats: {e}", flush=True)
        _clear_tools_cache()
        return {"success": False, "error": f"MCP connection error: {str(e)}"}

    if data.get("status") != "ok":
        return {"success": False, "error": data.get("message") or "ats_score failed"}

    return {"success": True, "score_result": data.get("result", {})}