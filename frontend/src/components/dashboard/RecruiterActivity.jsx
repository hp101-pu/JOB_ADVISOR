import { Link } from "react-router-dom";
import { MessagesSquare, XCircle, ClipboardList, ArrowRight } from "lucide-react";

const STATS = [
  {
    key: "interviews",
    label: "Interviews",
    icon: MessagesSquare,
    color: "#1d4ed8",
    soft: "#eff6ff",
    border: "#bfdbfe",
  },
  {
    key: "rejections",
    label: "Rejections",
    icon: XCircle,
    color: "#dc2626",
    soft: "#fef2f2",
    border: "#fecaca",
  },
  {
    key: "assessments",
    label: "Assessments",
    icon: ClipboardList,
    color: "#7c3aed",
    soft: "#f5f3ff",
    border: "#ddd6fe",
  },
];

export default function RecruiterActivity({
  interviews = 3,
  rejections = 8,
  assessments = 2,
}) {
  const values = { interviews, rejections, assessments };

  return (
    <div className="card recruiter-activity">
      <h3>Recruiter Activity</h3>

      <div className="recruiter-stats-grid">
        {STATS.map(({ key, label, icon: Icon, color, soft, border }) => (
          <div
            key={key}
            className="recruiter-stat-card"
            style={{
              "--stat-color":  color,
              "--stat-soft":   soft,
              "--stat-border": border,
            }}
          >
            <div className="recruiter-stat-icon">
              <Icon size={18} strokeWidth={1.8} />
            </div>
            <div className="recruiter-stat-value">{values[key]}</div>
            <div className="recruiter-stat-label">{label}</div>
          </div>
        ))}
      </div>

      <Link to="/emails" className="recruiter-cta">
        View all emails
        <ArrowRight size={14} strokeWidth={2.5} />
      </Link>
    </div>
  );
}
