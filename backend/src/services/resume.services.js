/**
 * Resume Service
 * --------------
 * Node Backend → Orchestrator (FastAPI :9000) → resume_mcp
 */

import { callMCP } from "./mcp.service.js";

class ResumeService {
  async rescoreResume({ userId, jwt, parsed_resume }) {
    console.log(`🔄 Rescoring resume for user: ${userId}`);

    if (!parsed_resume) throw new Error("parsed_resume is required");

    let result;
    try {
      result = await callMCP({
        endpoint: "/pipelines/resume-recalculate",
        args: { parsed_resume },
        userId,
        jwt,
      });
    } catch (error) {
      console.error("❌ Rescore MCP call failed:", error.message);
      throw new Error(`Resume rescore failed: ${error.message}`);
    }

    if (!result?.success) {
      const reason = result?.error || "Resume rescore pipeline returned failure";
      console.error("❌ Rescore pipeline failure:", reason);
      throw new Error(reason);
    }

    return result;
  }

  async parseResumePdf({ userId, jwt, file_b64, filename, mimetype }) {
    console.log(`📄 Parsing resume PDF for user: ${userId}`);

    if (!file_b64) throw new Error("file_b64 is required");

    let result;
    try {
      result = await callMCP({
        endpoint: "/pipelines/resume-parse",
        args: {
          file_b64,
          filename: filename || "resume.pdf",
          mimetype: mimetype || "application/pdf",
        },
        userId,
        jwt,
      });
    } catch (error) {
      // callMCP throws if HTTP response is not ok
      console.error("❌ MCP call failed:", error.message);
      throw new Error(`Resume pipeline failed: ${error.message}`);
    }

    // callMCP returns the parsed JSON — if the Python orchestrator returned
    // {success: false, error: "..."} with HTTP 200, we catch it here
    if (!result?.success) {
      const reason = result?.error || "Resume parsing pipeline returned failure";
      console.error("❌ Pipeline returned failure:", reason);
      throw new Error(reason);
    }

    return result;
  }
}

export const resumeService = new ResumeService();