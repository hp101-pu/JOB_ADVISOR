import React from "react";

// ─── Per-profile max weights ────────────────────────────────────────────────
// Must stay in sync with ats_scorer.py WEIGHTS dict.
const PROFILE_MAX = {
  student: {
    skills: 35, roles: 10, experience: 10, structure: 25, companies: 20,
  },
  early_career: {
    skills: 38, roles: 15, experience: 15, structure: 17, companies: 15,
  },
  professional: {
    skills: 40, roles: 20, experience: 20, structure: 10, companies: 10,
  },
};

// Fallback if meta.profile is missing (old cached scores)
const DEFAULT_MAX = PROFILE_MAX.professional;

// ─── Profile display config ──────────────────────────────────────────────────
const PROFILE_CONFIG = {
  student: {
    label: "Student Profile",
    color: "#6366f1",
    description: "Scored on skills, projects & education — not work experience.",
  },
  early_career: {
    label: "Early Career",
    color: "#f59e0b",
    description: "Scored with lighter experience requirements for junior candidates.",
  },
  professional: {
    label: "Professional",
    color: "#10b981",
    description: "Full scoring across all categories.",
  },
};

// ─── Flag → human readable labels (profile-aware) ────────────────────────────
const FLAG_LABELS = {
  // student flags
  missing_education_section:       "Add an Education section with your degree & institution",
  missing_experience_and_projects: "Add at least a Projects section to showcase your work",
  no_experience_signal:            "Add projects or internships to show real-world experience",
  // early career / professional flags
  missing_experience_section:      "Add a Work Experience section to strengthen your resume",
  low_experience:                  "Limited work experience detected — add internships or projects",
  intern_only_profile:             "Only intern-level roles found — consider adding projects or freelance work",
  no_company_signal:               "No company names detected — make sure employers are clearly listed",
  // student-specific
  low_skill_count:                 "List more technical skills — aim for at least 8-10 technologies",
  no_quantified_impact:            "Add numbers to your project bullets (e.g. '3 modules', '50% faster') to show impact",
  // all profiles
  missing_skills:                  "Add a Skills section listing your technical & soft skills",
};

const resolveFlag = (flag) =>
  FLAG_LABELS[flag] ?? flag.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

// ─── Score helpers ───────────────────────────────────────────────────────────
const scoreColor = (s) => s >= 80 ? "#10b981" : s >= 60 ? "#f59e0b" : "#ef4444";
const scoreLabel = (s) => s >= 80 ? "Excellent" : s >= 60 ? "Good" : "Needs Improvement";

// ─── Component ───────────────────────────────────────────────────────────────
const ATSScore = ({ scoreData, uploadedFile, isCalculating, isLoadingResume, onCalculate }) => {
  const profile     = scoreData?.ats?.meta?.profile ?? null;
  const profileConf = profile ? PROFILE_CONFIG[profile] : null;
  const maxMap      = profile ? (PROFILE_MAX[profile] ?? DEFAULT_MAX) : DEFAULT_MAX;

  return (
    <div className="resume-column">
      <div className="resume-card">

        {/* ── Header ── */}
        <div className="resume-card-header">
          <h3>ATS Score</h3>
          {scoreData && (
            <span className="score-badge" style={{ backgroundColor: scoreColor(scoreData.final_score) }}>
              {scoreLabel(scoreData.final_score)}
            </span>
          )}
        </div>

        {/* ── Loading ── */}
        {isLoadingResume ? (
          <div className="empty-state-with-button">
            <div className="empty-message"><p>Loading score...</p></div>
          </div>

        /* ── Empty / not yet scored ── */
        ) : scoreData?.final_score === undefined ? (
          <div className="empty-state-with-button">
            <div className="empty-message">
              <div className="empty-icon">
                <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
              </div>
              <p>Upload a resume to calculate the ATS score</p>
            </div>
            {uploadedFile && (
              <button onClick={onCalculate} className="btn-calculate-center" disabled={isCalculating}>
                {isCalculating ? "Analyzing Resume..." : "Calculate ATS Score"}
              </button>
            )}
          </div>

        /* ── Score result ── */
        ) : (
          <div className="score-content">

            {/* Profile badge */}
            {profileConf && (
              <div className="profile-badge" style={{ borderColor: profileConf.color }}>
                <span className="profile-badge__dot" style={{ background: profileConf.color }} />
                <div className="profile-badge__text">
                  <span className="profile-badge__label" style={{ color: profileConf.color }}>
                    {profileConf.label}
                  </span>
                  <span className="profile-badge__desc">{profileConf.description}</span>
                </div>
              </div>
            )}

            {/* Score number */}
            <div className="score-main" style={{ borderColor: scoreColor(scoreData.final_score) }}>
              <div className="score-number" style={{ color: scoreColor(scoreData.final_score) }}>
                {scoreData.final_score}
              </div>
              <div className="score-label">out of 100</div>
            </div>

            {/* Breakdown bars — profile-aware labels + weights */}
            <div className="score-breakdown">
              <div className="breakdown-header">
                <h4>Score Breakdown</h4>
                {profile && profile !== "professional" && (
                  <span className="breakdown-note">
                    {profile === "student" ? "Student-weighted" : "Junior-weighted"}
                  </span>
                )}
              </div>
              {Object.entries(scoreData.ats.breakdown).map(([key, value]) => {
                const max        = maxMap[key] ?? 20;
                const percentage = Math.min((value / max) * 100, 100);
                // For student profile, low-weight categories (roles/exp/companies)
                // are expected to be low — show them in neutral gray, not red
                const isLowWeightForStudent =
                  profile === "student" && ["roles", "experience", "companies"].includes(key);
                const color = isLowWeightForStudent
                  ? (percentage >= 60 ? "#10b981" : "#94a3b8")
                  : (percentage >= 75 ? "#10b981" : percentage >= 50 ? "#f59e0b" : "#ef4444");

                // Profile-aware labels
                const LABELS = {
                  student: {
                    skills:     "Technical Skills",
                    roles:      "Project Depth",
                    experience: "Activity Score",
                    structure:  "Resume Structure",
                    companies:  "Internship Credit",
                  },
                  early_career: {
                    skills:     "Technical Skills",
                    roles:      "Role Experience",
                    experience: "Work Duration",
                    structure:  "Resume Structure",
                    companies:  "Companies",
                  },
                };
                const label = LABELS[profile]?.[key] ?? (key.charAt(0).toUpperCase() + key.slice(1));

                return (
                  <div key={key} className="breakdown-row">
                    <span className="breakdown-key">{label}</span>
                    <div className="breakdown-bar">
                      <div className="breakdown-fill" style={{ width: `${percentage}%`, backgroundColor: color }} />
                    </div>
                    <span className="breakdown-value"
                      style={{ color: isLowWeightForStudent ? "var(--color-text-secondary)" : undefined }}>
                      {value}/{max}
                    </span>
                  </div>
                );
              })}
              {profile === "student" && (
                <p className="breakdown-student-note">
                  Project Depth, Activity Score &amp; Internship Credit carry less weight for students — Technical Skills &amp; Resume Structure matter most.
                </p>
              )}
            </div>

            {/* Flags */}
            {scoreData.ats.flags?.length > 0 && (
              <div className="feedback-section">
                <h4>Flags</h4>
                {scoreData.ats.flags.map((flag, i) => (
                  <div key={i} className="feedback-item feedback-warning">
                    <span className="feedback-icon">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                        <line x1="12" y1="9" x2="12" y2="13" />
                        <line x1="12" y1="17" x2="12.01" y2="17" />
                      </svg>
                    </span>
                    <span className="feedback-text">{resolveFlag(flag)}</span>
                  </div>
                ))}
              </div>
            )}

            {/* LLM Feedback — severity-based (green/yellow/red) */}
            {scoreData.llm_feedback?.length > 0 && (() => {
              const green  = scoreData.llm_feedback.filter(f => f?.severity === "green");
              const yellow = scoreData.llm_feedback.filter(f => !f?.severity || f?.severity === "yellow");
              const red    = scoreData.llm_feedback.filter(f => f?.severity === "red");
              const getText = (f) => (typeof f === "string" ? f : f?.text ?? "");
              return (
                <>
                  {green.length > 0 && (
                    <div className="feedback-section">
                      <h4>What's strong</h4>
                      {green.map((f, i) => (
                        <div key={i} className="feedback-item feedback-good">
                          <span className="feedback-icon">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                              <polyline points="22 4 12 14.01 9 11.01" />
                            </svg>
                          </span>
                          <span className="feedback-text">{getText(f)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {yellow.length > 0 && (
                    <div className="feedback-section">
                      <h4>Suggestions</h4>
                      {yellow.map((f, i) => (
                        <div key={i} className="feedback-item feedback-info">
                          <span className="feedback-icon">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <circle cx="12" cy="12" r="10" />
                              <line x1="12" y1="8" x2="12" y2="12" />
                              <line x1="12" y1="16" x2="12.01" y2="16" />
                            </svg>
                          </span>
                          <span className="feedback-text">{getText(f)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {red.length > 0 && (
                    <div className="feedback-section">
                      <h4>Critical issues</h4>
                      {red.map((f, i) => (
                        <div key={i} className="feedback-item feedback-error">
                          <span className="feedback-icon">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                              <line x1="12" y1="9" x2="12" y2="13" />
                              <line x1="12" y1="17" x2="12.01" y2="17" />
                            </svg>
                          </span>
                          <span className="feedback-text">{getText(f)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              );
            })()}

          </div>
        )}
      </div>
    </div>
  );
};

export default ATSScore;