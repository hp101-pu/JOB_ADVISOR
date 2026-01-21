from mcp.server.fastmcp import FastMCP
import base64, json, re, sys

from services.pdf_loader import extract_text_from_pdf
from pipelines.extract_pipeline import extract_resume
from pipelines.score_pipeline import ScorePipeline

mcp = FastMCP("resume-mcp")


@mcp.tool()
def parse_resume(file_b64: str):
    """Parse a base64-encoded resume PDF. Returns structured sections + entities."""
    print("[MCP SERVER] parse_resume called", flush=True, file=sys.stderr)

    if not file_b64 or not isinstance(file_b64, str):
        return {"status": "error", "error": "INVALID_INPUT", "message": "file_b64 must be a non-empty string"}

    try:
        raw = file_b64.strip()
        # unwrap {"file_b64": "..."} if client sends JSON by mistake
        if raw.startswith("{"):
            try:
                obj = json.loads(raw)
                raw = str(obj.get("file_b64", raw)).strip()
            except Exception:
                pass
        # strip data-URL prefix
        if raw.lower().startswith("data:"):
            raw = raw.split(",", 1)[1].strip()
        raw = re.sub(r"\s+", "", raw)
    except Exception as e:
        return {"status": "error", "error": "NORMALIZATION_FAILED", "message": str(e)}

    try:
        pdf_bytes = base64.b64decode(raw, validate=True)
    except Exception:
        return {"status": "error", "error": "INVALID_BASE64", "message": "Failed to decode base64"}

    print("[MCP SERVER] base64 decoded successfully", flush=True, file=sys.stderr)

    if not pdf_bytes.startswith(b"%PDF"):
        return {"status": "error", "error": "NOT_A_PDF", "message": "Input is not a valid PDF. Please upload a text-based PDF."}

    print("[MCP SERVER] PDF header valid, extracting text...", flush=True, file=sys.stderr)

    try:
        raw_text = extract_text_from_pdf(pdf_bytes)
    except RuntimeError as e:
        err = str(e)
        if "SCANNED_PDF" in err:
            return {"status": "error", "error": "SCANNED_PDF",
                    "message": "Scanned/image PDF — no extractable text. Please upload a text-based PDF."}
        return {"status": "error", "error": "PDF_EXTRACTION_FAILED", "message": err}
    except Exception as e:
        return {"status": "error", "error": "PDF_EXTRACTION_FAILED", "message": str(e)}

    print("[MCP SERVER] text extracted, running extract_resume...", flush=True, file=sys.stderr)

    try:
        result = extract_resume(raw_text)
        print("[MCP SERVER] extract_resume done, returning ok", flush=True, file=sys.stderr)
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "error": "PARSE_FAILED", "message": str(e)}


@mcp.tool()
def ats_score(parsed_resume, use_llm: bool = False, job_description: str = ""):
    """Score a parsed resume. Optionally use Groq LLM feedback and/or a job description."""
    print("[MCP SERVER] ats_score called", flush=True, file=sys.stderr)

    if isinstance(parsed_resume, str):
        try:
            parsed_resume = json.loads(parsed_resume)
        except Exception:
            return {"status": "error", "error": "INVALID_INPUT", "message": "Could not parse parsed_resume as JSON"}

    if not isinstance(parsed_resume, dict):
        return {"status": "error", "error": "INVALID_INPUT", "message": "parsed_resume must be a dict"}

    try:
        result = ScorePipeline(use_llm=use_llm).run(parsed_resume, job_description=job_description or None)
        print("[MCP SERVER] ats_score done, returning ok", flush=True, file=sys.stderr)
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "error": "SCORING_FAILED", "message": str(e)}


@mcp.tool()
def ping():
    """Health check."""
    return {"status": "ok", "message": "pong"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.streamable_http_app(), host="127.0.0.1", port=8001)