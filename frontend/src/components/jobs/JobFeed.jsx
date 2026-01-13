import React, { useMemo } from "react";
import JobCard from "./JobCard";

const JobFeed = ({
  jobs = [],
  loading,
  selectedJob,
  onSelectJob,
  onToggleFilters,
  savedJobIds,
  onSaveJob,
  onUnsaveJob,
  sortBy,
  onSortChange,
  viewMode,
  onViewChange,
  user,
}) => {
  const isSavedView = viewMode === "saved";

  const sortedJobs = useMemo(() => {
    if (sortBy === "salary") {
      return [...jobs].sort((a, b) => {
        const salA = a.salary_max || 0;
        const salB = b.salary_max || 0;
        return salB - salA;
      });
    }
    if (sortBy === "date") {
      return [...jobs].sort((a, b) => new Date(b.created) - new Date(a.created));
    }
    if (viewMode === "recommended") {
      return [...jobs].sort((a, b) => (b.match_score || 0) - (a.match_score || 0));
    }
    return jobs;
  }, [jobs, sortBy, viewMode]);

  return (
    <div className="jobs-feed-col">
      <div className="jobs-feed-header">
        <div className="feed-tabs-wrapper">
          <div className="feed-tabs">
            <button
              className={`feed-tab ${viewMode === "search" ? "active" : ""}`}
              onClick={() => onViewChange("search")}
            >
              All Jobs
            </button>
            <button
              className={`feed-tab ${viewMode === "recommended" ? "active" : ""}`}
              onClick={() => onViewChange("recommended")}
            >
              Recommended
            </button>
            <button
              className={`feed-tab ${viewMode === "saved" ? "active" : ""}`}
              onClick={() => onViewChange("saved")}
            >
              Saved
            </button>
          </div>
        </div>

        <div className="feed-controls-row">
          <div className="feed-count">
            {loading ? (
              "Loading..."
            ) : (
              <>
                <span>{jobs.length}</span> {jobs.length === 1 ? "job" : "jobs"} found
              </>
            )}
          </div>

          <div className="feed-actions">
            {jobs.length > 0 && (
              <select
                className="job-select sort-select-feed"
                value={sortBy}
                onChange={(e) => onSortChange(e.target.value)}
              >
                <option value="relevance" disabled={!user}>
                  {user ? "Relevance" : "Relevance (Login Required)"}
                </option>
                <option value="date">Date (Newest)</option>
                <option value="salary">Salary (High to Low)</option>
              </select>
            )}

            {viewMode === "search" && (
              <button
                className="btn-filter-trigger"
                onClick={onToggleFilters}
                title="Open Filters"
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  width="20"
                  height="20"
                >
                  <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      <div
        className="jobs-scroll-area"
        key={viewMode}
      >
        {loading ? (
          <div className="jobs-empty-state">
            <div className="spinner"></div>
            <p>
              {viewMode === "recommended"
                ? "Curating matches..."
                : "Finding jobs..."}
            </p>
          </div>
        ) : sortedJobs.length > 0 ? (
          sortedJobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              isSelected={selectedJob?.id === job.id}
              isSaved={savedJobIds?.has(job.id)}
              isSavedView={isSavedView}
              onClick={() => onSelectJob(job)}
              onSave={() => onSaveJob(job)}
              onUnsave={() => onUnsaveJob(job.id)}
            />
          ))
        ) : (
          <div className="jobs-empty-state">
            <p>
              {viewMode === "saved"
                ? "No saved jobs."
                : "No jobs found."}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobFeed;