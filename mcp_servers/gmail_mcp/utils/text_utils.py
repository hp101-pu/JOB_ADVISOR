JOB_KEYWORDS = [
    "interview", "recruiter", "hiring",
    "resume", "offer", "job"
]

def email_to_text(subject, body):
    return f"Subject: {subject}\n\n{body}"

def is_job_related(text: str) -> bool:
    text = text.lower()
    return any(k in text for k in JOB_KEYWORDS)
