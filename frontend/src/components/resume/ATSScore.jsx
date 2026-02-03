import React from "react";

// ─── Helpers ───────────────────────────────────────────────────────────
const getText = (f) => (typeof f === "string" ? f : f?.text ?? "");

const severityClass = (severity) => {
  if (severity === "green")  return "feedback-good";
  if (severity === "red")    return "feedback-error";
  return "feedback-info";
};

const DEFAULT_RENDER_DATA = {
  profile: { key: null, label: "", description: "", color: "#10b981" },
  breakdown: [],
  flags: [],
  llm_feedback: [],
};

// ─── Component ───────────────────────────────────────────────────────────────
const ATSScore = ({ scoreData, uploadedFile, isCalculating, isLoadingResume, onCalculate }) => {
  const renderData = scoreData?.render_data || DEFAULT_RENDER_DATA;
  const profileConf = renderData.profile || DEFAULT_RENDER_DATA.profile;
  const scoreBadgeColor = scoreData ? (scoreData?.render_data?.profile?.color || "#10b981") : "#10b981";

  return (
    <div className="resume-column">
      <div className="resume-card">

        {/* ── Header ── */}
        <div className="resume-card-header">
          <h3>ATS Score</h3>
          {scoreData && (
            <span className="score-badge" style={{ backgroundColor: scoreBadgeColor }}>
              {renderData.score_label || "Score"}
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
            {profileConf?.key && (
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
            <div className="score-main" style={{ borderColor: scoreBadgeColor }}>
              <div className="score-number" style={{ color: scoreBadgeColor }}>
                {scoreData.final_score}
              </div>
              <div className="score-label">out of 100</div>
            </div>

            {/* Breakdown bars — rendered from backend render_data */}
            <div className="score-breakdown">
              <div className="breakdown-header">
                <h4>Score Breakdown</h4>
                {profileConf?.key && profileConf.key !== "professional" && (
                  <span className="breakdown-note">
                    {profileConf.key === "student" ? "Student-weighted" : "Junior-weighted"}
                  </span>
                )}
              </div>
              {renderData.breakdown?.length > 0 ? (
                renderData.breakdown.map((item, i) => (
                  <div key={item.key || i} className="breakdown-row">
                    <span className="breakdown-key">{item.label}</span>
                    <div className="breakdown-bar">
                      <div
                        className="breakdown-fill"
                        style={{ width: `${item.percentage}%`, backgroundColor: item.color }}
                      />
                    </div>
                    <span
                      className="breakdown-value"
                      style={{ color: item.color === "#94a3b8" ? "var(--color-text-secondary)" : undefined }}
                    >
                      {item.value}/{item.max}
                    </span>
                  </div>
                ))
              ) : (
                // Fallback for old cached scores without render_data
                Object.entries(scoreData.ats.breakdown).map(([key, value]) => (
                  <div key={key} className="breakdown-row">
                    <span className="breakdown-key">{key.charAt(0).toUpperCase() + key.slice(1)}</span>
                    <div className="breakdown-bar">
                      <div className="breakdown-fill" style={{ width: `${Math.min(value * 5, 100)}%` }} />
                    </div>
                    <span className="breakdown-value">{value}</span>
                  </div>
                ))
              )}
              {profileConf?.key === "student" && (
                <p className="breakdown-student-note">
                  Project Depth, Activity Score &amp; Internship Credit carry less weight for students — Technical Skills &amp; Resume Structure matter most.
                </p>
              )}
            </div>

            {/* Flags — rendered from backend render_data */}
            {renderData.flags?.length > 0 && (
              <div className="feedback-section">
                <h4>Flags</h4>
                {renderData.flags.map((flag, i) => (
                  <div key={i} className="feedback-item feedback-warning">
                    <span className="feedback-icon">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                        <line x1="12" y1="9" x2="12" y2="13" />
                        <line x1="12" y1="17" x2="12.01" y2="17" />
                      </svg>
                    </span>
                    <span className="feedback-text">{flag.text}</span>
                  </div>
                ))}
              </div>
            )}

            {/* LLM Feedback — rendered from backend render_data */}
            {renderData.llm_feedback?.length > 0 && (() => {
              const green  = renderData.llm_feedback.filter(f => f?.severity === "green");
              const yellow = renderData.llm_feedback.filter(f => !f?.severity || f?.severity === "yellow");
              const red    = renderData.llm_feedback.filter(f => f?.severity === "red");
              return (
                <>
                  {green.length > 0 && (
                    <div className="feedback-section">
                      <h4>What's strong</h4>
                      {green.map((f, i) => (
                        <div key={i} className={`feedback-item ${severityClass("green")}`}>
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
                        <div key={i} className={`feedback-item ${severityClass("yellow")}`}>
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
                        <div key={i} className={`feedback-item ${severityClass("red")}`}>
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