import { Cpu, Briefcase, Clock4 } from "lucide-react";

export default function ResumeOverview({
  skillsDetected,
  experienceYears,
  experienceMonths,
  lastUpdated,
}) {
  const expDisplay =
    experienceYears > 0
      ? `${experienceYears} yr${experienceYears > 1 ? "s" : ""}${experienceMonths > 0 ? ` ${experienceMonths} mo` : ""}`
      : experienceMonths > 0
      ? `${experienceMonths} mo`
      : "—";

  return (
    <div className="card resume-overview">
      <h3>Resume Overview</h3>

      <div className="meta-list compact">
        <div className="meta-row">
          <span className="meta-left">
            <Cpu size={15} strokeWidth={2} />
            Skills detected
          </span>
          <span className="meta-value">{skillsDetected ?? "—"}</span>
        </div>

        <div className="meta-row">
          <span className="meta-left">
            <Briefcase size={15} strokeWidth={2} />
            Experience
          </span>
          <span className="meta-value">{expDisplay}</span>
        </div>

        <div className="meta-row">
          <span className="meta-left">
            <Clock4 size={15} strokeWidth={2} />
            Last updated
          </span>
          <span className="meta-value">{lastUpdated ?? "—"}</span>
        </div>
      </div>
    </div>
  );
}
