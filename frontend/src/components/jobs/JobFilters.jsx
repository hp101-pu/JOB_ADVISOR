import React from "react";

const JobFilters = ({
  filters,
  onFilterChange,
  onSearch,
  isOpen,
  onClose,
  isDisabled,
}) => {
  if (!filters) return null;

  const {
    keywords,
    location,
    category,
    jobType,
    minSalary,
    maxSalary,
  } = filters;

  return (
    <div
      className={`jobs-filters-col ${isOpen ? "mobile-open" : ""} ${
        isDisabled ? "filters-disabled" : ""
      }`}
    >
      <div className="mobile-filter-header">
        <span className="filter-title">Filter Jobs</span>
        <button
          className="btn-close-mobile"
          onClick={onClose}
        >
          ✕
        </button>
      </div>

      <div className="filter-header">
        <div
          className="filter-title"
          style={{ display: isOpen ? "none" : "flex" }}
        >
          Filter Jobs
        </div>
      </div>

      <div className="filter-group">
        <label className="filter-label">Keywords</label>
        <input
          type="text"
          className="job-input"
          placeholder="e.g. React, Python"
          value={keywords}
          onChange={(e) => onFilterChange("keywords", e.target.value)}
          disabled={isDisabled}
        />
      </div>

      <div className="filter-group">
        <label className="filter-label">Location</label>
        <input
          type="text"
          className="job-input"
          placeholder="e.g. Bangalore"
          value={location}
          onChange={(e) => onFilterChange("location", e.target.value)}
          disabled={isDisabled}
        />
      </div>

      <div className="filter-group">
        <label className="filter-label">Job Category</label>
        <select
          className="job-select"
          value={category}
          onChange={(e) => onFilterChange("category", e.target.value)}
          disabled={isDisabled}
        >
          <option value="">All Categories</option>
          <option value="IT Jobs">IT & Software</option>
          <option value="Accounting & Finance Jobs">Accounting & Finance</option>
          <option value="Engineering Jobs">Engineering</option>
          <option value="Sales Jobs">Sales & Marketing</option>
          <option value="HR Jobs">HR & Recruitment</option>
        </select>
      </div>

      <div className="filter-group">
        <label className="filter-label">Job Type</label>
        <select
          className="job-select"
          value={jobType}
          onChange={(e) => onFilterChange("jobType", e.target.value)}
          disabled={isDisabled}
        >
          <option value="full_time">Full-time</option>
          <option value="part_time">Part-time</option>
          <option value="contract">Contract</option>
        </select>
      </div>

      <div className="filter-group">
        <label className="filter-label">Salary Range (₹)</label>
        <div className="salary-range-inputs">
          <input
            type="number"
            className="job-input"
            placeholder="Min"
            value={minSalary}
            onChange={(e) => onFilterChange("minSalary", e.target.value)}
            disabled={isDisabled}
          />
          <input
            type="number"
            className="job-input"
            placeholder="Max"
            value={maxSalary}
            onChange={(e) => onFilterChange("maxSalary", e.target.value)}
            disabled={isDisabled}
          />
        </div>
      </div>

      <button
        className="btn-search-jobs"
        onClick={() => {
          onSearch();
          if (isOpen) onClose();
        }}
        disabled={isDisabled}
      >
        Search Jobs
      </button>
    </div>
  );
};

export default JobFilters;