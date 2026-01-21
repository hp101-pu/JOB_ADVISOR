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

        return {"final_score": final_score, "ats": ats_result, "llm_feedback": llm_feedback}