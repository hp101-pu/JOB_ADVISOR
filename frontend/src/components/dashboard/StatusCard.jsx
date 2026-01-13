import React from "react";
import { FileCheck2, Mail, CheckCheck, X, ArrowRight } from "lucide-react";

const CONFIG = {
  resume: {
    icon: FileCheck2,
    label: "Resume Status",
    successDetail: "ATS-ready & fully parsed",
    errorDetail:   "Upload a resume to get started",
    accentColor:   "#16a34a",
    softColor:     "#dcfce7",
    borderColor:   "#a7f3d0",
    errorAccent:   "#dc2626",
    errorSoft:     "#fee2e2",
    errorBorder:   "#fecaca",
  },
  gmail: {
    icon: Mail,
    label: "Gmail Integration",
    successDetail: "Emails are being synced",
    errorDetail:   "Click to connect your inbox",
    accentColor:   "#1d4ed8",
    softColor:     "#eff6ff",
    borderColor:   "#bfdbfe",
    errorAccent:   "#dc2626",
    errorSoft:     "#fee2e2",
    errorBorder:   "#fecaca",
  },
};

export default function StatusCard({
  type = "resume",
  title = "Resume",
  statusText = "Parsed & Ready",
  lastUpdated = "Updated just now",
  state = "success",
  onClick,
}) {
  const cfg = CONFIG[type] || CONFIG.resume;
  const Icon = cfg.icon;

  const isSuccess = state === "success";

  const accentColor  = isSuccess ? cfg.accentColor  : cfg.errorAccent;
  const softColor    = isSuccess ? cfg.softColor     : cfg.errorSoft;
  const borderColor  = isSuccess ? cfg.borderColor   : cfg.errorBorder;
  const detail       = isSuccess ? cfg.successDetail : cfg.errorDetail;

  return (
    <div
      className="status-card-v2"
      onClick={onClick}
      tabIndex={onClick ? 0 : -1}
      role={onClick ? "button" : undefined}
      onKeyDown={(e) => {
        if (onClick && (e.key === "Enter" || e.key === " ")) onClick();
      }}
      style={{
        "--card-accent":  accentColor,
        "--card-soft":    softColor,
        "--card-border":  borderColor,
        cursor: onClick ? "pointer" : "default",
      }}
    >
      {/* Top accent bar */}
      <div className="scv2-accent-bar" />

      <div className="scv2-body">
        {/* Left: icon block */}
        <div className="scv2-icon-block">
          <Icon size={24} strokeWidth={1.8} />
        </div>

        {/* Middle: text */}
        <div className="scv2-text">
          <span className="scv2-label">{cfg.label}</span>
          <span className="scv2-value">{statusText}</span>
          <span className="scv2-detail">{detail}</span>
        </div>

        {/* Right: badge + optional cta */}
        <div className="scv2-right">
          <span className={`scv2-badge ${isSuccess ? "scv2-badge--ok" : "scv2-badge--err"}`}>
            {isSuccess
              ? <><CheckCheck size={12} strokeWidth={2.5} /> Active</>
              : <><X         size={12} strokeWidth={2.5} /> Inactive</>
            }
          </span>
          {onClick && !isSuccess && (
            <span className="scv2-cta">
              Connect <ArrowRight size={12} strokeWidth={2.5} />
            </span>
          )}
        </div>
      </div>

      {/* Bottom: last updated */}
      <div className="scv2-footer">
        <span className="scv2-timestamp">{lastUpdated}</span>
      </div>
    </div>
  );
}
