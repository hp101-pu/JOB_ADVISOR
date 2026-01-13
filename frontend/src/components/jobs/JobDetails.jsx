import React from "react";

const JobDetails = ({
  job,
  isVisible,
  onClose,
  isSaved,
  onSaveJob,
  onUnsaveJob,
}) => {
  if (!job) {
    return (
      <div
        className={`job-details-panel ${isVisible ? "visible" : ""}`}
      >
        <div className="job-details-empty">
          <p>Select a job to view details</p>
        </div>
      </div>
    );
  }

  const formatSalary = (amount) => {
    if (!amount) return null;
    if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`;
    return `₹${amount.toLocaleString()}`;
  };

  const salaryRange =
    job.salary_min || job.salary_max
      ? `${formatSalary(job.salary_min) || "Not disclosed"} - ${
          formatSalary(job.salary_max) || "Not disclosed"
        }`
      : "Not disclosed";

  const cleanDescription = (html) => {
    if (!html) return "No description available";
    const text = html.replace(/<[^>]*>/g, " ");
    const textarea = document.createElement("textarea");
    textarea.innerHTML = text;
    return textarea.value.replace(/\s+/g, " ").trim();
  };

  const description = cleanDescription(job.description);

  const matchScore = job.match_score || job.matchScore;
  const matchReason = job.match_reason || job.matchReason;
  const matchedSkills = job.matched_skills || job.matchedSkills || [];

  const getMatchClass = (score) => {
    if (score >= 80) return "match-high";
    if (score >= 60) return "match-medium";
    return "match-low";
  };

  return (
    <div
      className={`job-details-panel ${isVisible ? "visible" : ""}`}
    >
      <button
        className="btn-close-details"
        onClick={onClose}
      >
        ✕
      </button>

      <div className="job-details-header">
        <div className="job-details-company">
          <div className="company-logo-large">
            {job.company?.charAt(0)?.toUpperCase() || "?"}
          </div>
          <div>
            <h2 className="job-details-title">
              {job.title}
            </h2>
            <p className="job-details-company-name">
              {job.company}
            </p>
            <p className="job-details-location">
              📍 {job.location}
            </p>
          </div>
        </div>

        <div className="job-details-actions">
          <button
            className={`btn-save-large ${isSaved ? "btn-save-active" : ""}`}
            onClick={() => (isSaved ? onUnsaveJob(job.id) : onSaveJob(job))}
          >
            {isSaved ? "❤️ Saved" : "♡ Save Job"}
          </button>

          {job.apply_url && (
            <a
              href={job.apply_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-apply"
            >
              Apply Now →
            </a>
          )}
        </div>
      </div>

      {matchScore > 0 && (
        <div
          className={`match-score-card ${getMatchClass(matchScore)}`}
        >
          <div className="match-card-top">
            <div className="match-donut">
              <span className="score-text">
                {matchScore}%
              </span>
            </div>
            <div className="match-summary">
              <h4>
                {matchScore >= 80
                  ? "Excellent Match"
                  : matchScore >= 60
                  ? "Good Match"
                  : "Potential Match"}
              </h4>
              <p>
                {matchReason || "This job aligns with your profile skills."}
              </p>
            </div>
          </div>

          {matchedSkills.length > 0 && (
            <div className="match-skills-list">
              <span className="label">
                Matched Skills:
              </span>
              <div className="skill-wrap">
                {matchedSkills.map((skill, i) => (
                  <span
                    key={i}
                    className="skill-pill-highlight"
                  >
                    ✓ {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="job-info-grid">
        <div className="job-info-item">
          <span className="job-info-label">
            Salary Range
          </span>
          <span className="job-info-value">
            {salaryRange}
          </span>
        </div>
        {job.contract_type && (
          <div className="job-info-item">
            <span className="job-info-label">
              Employment Type
            </span>
            <span className="job-info-value">
              {job.contract_type}
            </span>
          </div>
        )}
        {job.contract_time && (
          <div className="job-info-item">
            <span className="job-info-label">
              Work Schedule
            </span>
            <span className="job-info-value">
              {job.contract_time}
            </span>
          </div>
        )}
        {job.category && (
          <div className="job-info-item">
            <span className="job-info-label">
              Category
            </span>
            <span className="job-info-value">
              {job.category}
            </span>
          </div>
        )}
      </div>

      <div className="job-description-section">
        <h3 className="section-title">
          Job Description
        </h3>
        <div className="job-description-content">
          {description.split("\n\n").map((paragraph, index) => (
            <p key={index}>{paragraph}</p>
          ))}
        </div>
      </div>
    </div>
  );
};

export default JobDetails;