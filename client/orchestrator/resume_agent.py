from typing import Dict, Any, Optional
from client.wrappers.resume_wrapper import parse_resume_pdf, score_resume_ats

SUPPORTED_MIMETYPES = {
    "application/pdf",
    "application/octet-stream",  # some browsers send this for .pdf downloads
}
SUPPORTED_EXTENSIONS = {".pdf"}


def _validate_file(filename: str, mimetype: str) -> Optional[str]:
    """Returns an error message if file type is unsupported, else None."""
    import os
    ext = os.path.splitext(filename)[1].lower()
    # Accept if EITHER the extension OR the mimetype is valid
    # This handles browsers that send application/octet-stream for PDFs
    if ext not in SUPPORTED_EXTENSIONS and mimetype not in SUPPORTED_MIMETYPES:
        return (
            f"Unsupported file type: '{filename}' ({mimetype}). "
            f"Only text-based PDF files are supported."
        )
    return None


async def rescore_resume_pipeline(
    user_id: str,
    parsed_resume: Dict[str, Any],
    use_llm: bool = True,
    job_description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Re-score only — skips the PDF parse step.
    Used when the scorer is updated and existing stored parsed_resume needs a fresh score.
    """
    print(f"🔄 Rescore pipeline | user={user_id}")

    scored = await score_resume_ats(
        parsed_resume=parsed_resume,
        use_llm=use_llm,
        job_description=job_description,
    )
    if not scored.get("success"):
        return {"success": False, "error": scored.get("error", "ATS scoring failed")}

    return {
        "success": True,
        "userId":  user_id,
        "score":   scored.get("score_result"),
    }


async def parse_resume_pipeline(
    user_id: str,
    jwt: str,
    file_b64: str,
    filename: str = "resume.pdf",
    mimetype: str = "application/pdf",
    use_llm: bool = True,
    job_description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Full resume pipeline: validate → parse → ATS score.

    Args:
        user_id:         ID of the user uploading the resume
        jwt:             Auth token (passed through for audit/logging)
        file_b64:        Base64-encoded PDF content
        filename:        Original filename (used for type validation)
        mimetype:        MIME type declared by the client
        use_llm:         Enable Groq LLM feedback on ATS score
        job_description: Optional JD text for aligned scoring
    """
    print(f"📄 Resume pipeline | user={user_id} file={filename} use_llm={use_llm}")

    # upfront file type check — fail fast before any API call
    err = _validate_file(filename, mimetype)
    if err:
        return {"success": False, "error": err}

    # Step 1: parse
    parsed = await parse_resume_pdf(file_b64=file_b64)
    if not parsed.get("success"):
        return {"success": False, "error": parsed.get("error", "Resume parsing failed")}

    parsed_resume = parsed.get("parsed_resume")
    if not parsed_resume:
        return {"success": False, "error": "parse_resume returned empty result"}

    # Step 2: ATS score
    scored = await score_resume_ats(
        parsed_resume=parsed_resume,
        use_llm=use_llm,
        job_description=job_description,
    )
    if not scored.get("success"):
        return {"success": False, "error": scored.get("error", "ATS scoring failed")}

    return {
        "success":       True,
        "userId":        user_id,
        "filename":      filename,
        "mimetype":      mimetype,
        "parsed_resume": parsed_resume,
        "score":         scored.get("score_result"),
    }