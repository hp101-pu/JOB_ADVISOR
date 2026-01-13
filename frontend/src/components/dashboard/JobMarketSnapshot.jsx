import { PackageSearch, Timer } from "lucide-react";

export default function JobMarketSnapshot({
  totalJobs = 1200,
  lastSync = "1 hour ago",
}) {
  return (
    <div className="card job-market">
      <h3>Job Market Snapshot</h3>

      <div className="meta-grid compact">
        <div className="meta-row">
          <span className="meta-left">
            <PackageSearch size={15} strokeWidth={2} />
            Total jobs ingested
          </span>
          <span className="meta-value">{totalJobs}</span>
        </div>

        <div className="meta-row">
          <span className="meta-left">
            <Timer size={15} strokeWidth={2} />
            Last sync
          </span>
          <span className="meta-value">{lastSync}</span>
        </div>
      </div>
    </div>
  );
}
