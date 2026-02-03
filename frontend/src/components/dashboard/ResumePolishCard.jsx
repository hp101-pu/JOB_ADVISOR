import { Sparkles, TrendingUp, Zap, Target, ArrowRight, Lock } from "lucide-react";
import { useNavigate } from "react-router-dom";
import polishIllustration from "../../assets/polish-resume.png";

function relativeTime(dateStr) {
  if (!dateStr) return "unknown";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1)  return "just now";
  if (mins < 60) return `${mins} minute${mins > 1 ? "s" : ""} ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)  return `${hrs} hour${hrs > 1 ? "s" : ""} ago`;
  const days = Math.floor(hrs / 24);
  return `${days} day${days > 1 ? "s" : ""} ago`;
}

const SCORE_METRICS = [
  { label: "ATS Readiness", key: "atsScore",      icon: Zap,        color: "#16a34a" },
  { label: "Impact",        key: "impactScore",    icon: TrendingUp, color: "#d97706" },
  { label: "Skill Match",   key: "skillAlignment", icon: Target,     color: "#1d4ed8" },
];

export default function ResumePolishCard({ resumeData }) {
  const navigate = useNavigate();

  const hasResume = resumeData?.data?.hasResume ?? false;
  const score     = resumeData?.data?.score ?? null;
  const meta      = resumeData?.data?.resume ?? null;

  // ── SVG ring calc ──────────────────────────────────────────────────────
  const r    = 28;
  const circ = 2 * Math.PI * r;

  // ── Derive values from real score ─────────────────────────────────────
  let resumeScore   = 0;
  let atsScore      = "—";
  let impactScore   = "—";
  let skillAlign    = "—";
  let focusAreas    = [];
  let lastAnalyzed  = "never";

  if (hasResume && score) {
    resumeScore = score.final_score ?? 0;
    const dashboard = score.render_data?.dashboard ?? {};

    atsScore     = dashboard.atsReadiness   || "—";
    impactScore  = dashboard.impact         || "—";
    skillAlign   = dashboard.skillAlignment || "—";
    focusAreas   = score.render_data?.focus_areas || [];
    lastAnalyzed = relativeTime(meta?.uploadedAt);
  }

  const dash = (resumeScore / 100) * circ;
  const vals = { atsScore, impactScore: impactScore, skillAlignment: skillAlign };

  return (
    <div className="card polish-card">

      {/* ── Top row: illustration + title + score ring ── */}
      <div className="polish-top">
        <img src={polishIllustration} alt="" className="polish-illustration" />

        <div className="polish-title-block">
          <div className="polish-eyebrow">
            <Sparkles size={13} strokeWidth={2.5} />
            AI-Powered Analysis
          </div>
          <h3 className="polish-title">Polish your resume</h3>
          <p className="polish-sub">
            {hasResume
              ? "Strengthen your profile for better shortlisting"
              : "Upload a resume to unlock insights"}
          </p>
        </div>

        {/* Score ring */}
        <div className="polish-score-ring">
          <svg width="72" height="72" viewBox="0 0 72 72">
            <circle cx="36" cy="36" r={r} fill="none" stroke="var(--border-color)" strokeWidth="5" />
            {hasResume && (
              <circle
                cx="36" cy="36" r={r} fill="none"
                stroke="var(--accent-primary)" strokeWidth="5"
                strokeLinecap="round"
                strokeDasharray={`${dash} ${circ}`}
                strokeDashoffset={circ * 0.25}
                style={{ transition: "stroke-dasharray 0.8s ease" }}
              />
            )}
          </svg>
          <div className="polish-score-label">
            {hasResume
              ? <><strong>{resumeScore}</strong><span>/100</span></>
              : <span style={{ color: "var(--text-secondary)", fontSize: "18px" }}>—</span>
            }
          </div>
        </div>
      </div>

      <div className="polish-divider" />

      {/* ── Metric pills ── */}
      <div className="polish-metrics">
        {SCORE_METRICS.map(({ label, key, icon, color }) => {
          const Icon = icon;
          return (
            <div
              key={key}
              className="polish-metric"
              style={{ "--metric-color": hasResume ? color : "var(--text-secondary)" }}
            >
              <div className="polish-metric__icon">
                <Icon size={14} strokeWidth={2} />
              </div>
              <div className="polish-metric__text">
                <span className="polish-metric__label">{label}</span>
                <span className="polish-metric__value">{vals[key]}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="polish-divider" />

      {/* ── Focus areas OR locked message ── */}
      {hasResume ? (
        <div className="polish-focus">
          <span className="focus-title">Focus areas</span>
          <ul className="focus-list">
            {focusAreas.length > 0
              ? focusAreas.map((item, i) => (
                  <li key={i} className="focus-item">
                    <span className="focus-dot" />
                    {item}
                  </li>
                ))
              : <li className="focus-item" style={{ color: "var(--text-secondary)" }}>No issues found — great resume!</li>
            }
          </ul>
        </div>
      ) : (
        <div className="polish-focus" style={{ textAlign: "center", padding: "12px 0 4px" }}>
          <Lock size={20} strokeWidth={1.5} style={{ color: "var(--text-secondary)", margin: "0 auto 8px" }} />
          <p style={{ fontSize: "13px", color: "var(--text-secondary)", margin: "0 0 4px" }}>
            No analysis available
          </p>
          <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: 0, lineHeight: 1.5 }}>
            Parse your resume to unlock AI-powered feedback and your ATS score.
          </p>
        </div>
      )}

      {/* ── CTA ── */}
      <div className="polish-footer">
        {hasResume ? (
          <>
            <button className="btn-primary polish-cta" onClick={() => navigate("/resume")}>
              Improve Resume
              <ArrowRight size={15} strokeWidth={2.5} />
            </button>
            <span className="polish-meta">Last analyzed {lastAnalyzed}</span>
          </>
        ) : (
          <button className="btn-primary polish-cta" onClick={() => navigate("/resume")}>
            Go to Resume
            <ArrowRight size={15} strokeWidth={2.5} />
          </button>
        )}
      </div>
    </div>
  );
}
