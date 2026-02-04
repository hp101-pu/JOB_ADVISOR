from services.ats_scorer import ATSScorer
from services.llm_scorer import LLMScorer
from services.groq_client import GroqClient


class ScorePipeline:
    def __init__(self, use_llm=False):
        self.ats = ATSScorer()
        self.llm = LLMScorer(GroqClient()) if use_llm else None

    def run(self, parsed_resume: dict, job_description=None) -> dict:
        ats_result   = self.ats.score(parsed_resume)
        final_score  = ats_result["total_score"]
        llm_feedback = []

        if self.llm:
            # Pass profile from ATS meta so LLM uses profile-aware instructions
            profile = ats_result.get("meta", {}).get("profile", "student")
            llm_result   = self.llm.evaluate(parsed_resume, ats_result, job_description, profile=profile)
            # score_adjustment is always 0 — final_score = pure ATS, LLM only provides feedback
            llm_feedback = llm_result["feedback"]  # list of {text, severity} dicts

        # Merge LLM feedback into the backend-owned render_data
        render_data = ats_result.get("render_data", {})
        render_data["llm_feedback"] = llm_feedback

        # Refresh focus areas now that LLM feedback is available
        flag_texts = [f.get("text", "") for f in render_data.get("flags", [])]
        llm_texts = [
            f.get("text", "") for f in llm_feedback
            if f.get("severity") in {"yellow", "red"}
        ]
        render_data["focus_areas"] = (flag_texts + llm_texts)[:3]

        return {
            "final_score":  final_score,
            "ats":          ats_result,
            "llm_feedback": llm_feedback,
            "render_data":  render_data,
        }