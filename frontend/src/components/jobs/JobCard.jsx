import React from "react";

const JobCard = ({
  job,
  isSelected,
  isSaved,
  onClick,
  onSave,
  onUnsave,
  isSavedView,
}) => {
  const companyInitial = job.company?.charAt(0)?.toUpperCase() || "?";

  const formatSalary = (amount) => {
    if (!amount) return null;
    if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`;
    return `₹${amount.toLocaleString()}`;
  };

  const salaryText =
    job.salary_min || job.salary_max
      ? `${formatSalary(job.salary_min) || "?"} - ${
          formatSalary(job.salary_max) || "?"
        }`
      : "Salary not disclosed";

  const formatDate = (dateString) => {
    if (!dateString) return "Recently";
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffTime = Math.abs(now - date);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      if (diffDays === 0) return "Today";
      if (diffDays === 1) return "Yesterday";
      if (diffDays < 7) return `${diffDays} days ago`;
      if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
      return `${Math.floor(diffDays / 30)} months ago`;
    } catch {
      return "Recently";
    }
  };

  const postedText = formatDate(job.created);

  const matchScore = job.match_score || job.matchScore;
  const matchReason = job.match_reason || job.matchReason;
  const showMatchScore = matchScore && matchScore > 0;

  const getMatchClass = (score) => {
    if (score >= 80) return "match-high";
    if (score >= 60) return "match-medium";
    return "match-low";
  };

  return (
    <div
      className={`job-card ${isSelected ? "job-card-selected" : ""} ${
        showMatchScore ? "is-recommended" : ""
      }`}
      onClick={onClick}
    >
      {/* Match Badge (Top Right) */}
      {showMatchScore && (
        <div className={`match-score-badge-box ${getMatchClass(matchScore)}`}>
          <span className="match-percent-text">{matchScore}%</span>
          <span className="match-label-text">MATCH</span>
        </div>
      )}

      {/* Top Row: Logo + Job Details */}
      <div className="job-card-top-row">
        <div className="company-logo">{companyInitial}</div>

        <div className="job-details">
          <div className="job-role">{job.title}</div>

          <div className="job-company-loc">
            {job.company}
            <span className="dot-sep">•</span>
            {job.location}
          </div>

          {/* AI Insight Box */}
          {matchReason && (
            <div className={`match-reason-box ${getMatchClass(matchScore)}`}>
              <span className="reason-icon">✨</span>
              <span className="reason-text">{matchReason}</span>
            </div>
          )}

          <div className="job-badges">
            <span className="badge badge-salary">{salaryText}</span>

            {job.contract_type && (
              <span className="badge badge-type">
                {job.contract_type.replace("_", " ")}
              </span>
            )}

            {job.contract_time && (
              <span className="badge badge-time">{job.contract_time}</span>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Row: Posted Time + Action Button */}
      <div className="job-card-bottom-row">
        <span className="posted-time">{postedText}</span>

        {isSavedView ? (
          <button
            className="btn-card-action"
            onClick={(e) => {
              e.stopPropagation();
              onUnsave();
            }}
            title="Remove from saved"
          >
            ✕
          </button>
        ) : (
          <button
            className="btn-card-action"
            onClick={(e) => {
              e.stopPropagation();
              isSaved ? onUnsave() : onSave();
            }}
            title={isSaved ? "Unsave job" : "Save job"}
          >
            {isSaved ? "❤️" : "♡"}
          </button>
        )}
      </div>
    </div>
  );
};

export default JobCard;
