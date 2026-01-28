import React, { useState } from "react";
import { Star, Trash2, X, Sparkles, CalendarPlus, CalendarCheck, CalendarX, Loader2 } from "lucide-react";

export default function EmailDetail({
  email,
  onClose,
  onReply,
  onGenerateAiReply,
  isAiLoading,
  onDelete,
  onToggleStar,
  onAddToCalendar,
  onRemoveFromCalendar,
}) {
  const [calendarLoading, setCalendarLoading] = useState(false);

  if (!email) return null;

  if (email.isLoading) {
    return (
      <div className="email-content-col">
        <p style={{ padding: "28px", color: "var(--text-muted)", fontSize: 14 }}>
          Loading email…
        </p>
      </div>
    );
  }

  const isInterview = email.tag === "INTERVIEW";
  const isInCalendar = email.calendarEventCreated && !email.calendarEventDeleted;

  const handleAddToCalendar = async () => {
    if (!onAddToCalendar) return;
    setCalendarLoading(true);
    try {
      await onAddToCalendar(email);
    } finally {
      setCalendarLoading(false);
    }
  };

  const handleRemoveFromCalendar = async () => {
    if (!onRemoveFromCalendar) return;
    setCalendarLoading(true);
    try {
      await onRemoveFromCalendar(email);
    } finally {
      setCalendarLoading(false);
    }
  };

  return (
    <div className="email-content-col">

      {/* ── Header ── */}
      <div className="email-detail-header">
        <div className="detail-top-row">
          <button className="back-btn-mobile" onClick={onClose}>← Back</button>

          <div className="detail-badges">
            <span className="ai-status-pill">
              <Sparkles size={12} strokeWidth={2.5} />
              AI Ready
            </span>
          </div>

          <div className="detail-actions">
            <button
              className={`action-icon-btn ${email.isStarred ? "starred" : ""}`}
              onClick={() => onToggleStar(email)}
              title={email.isStarred ? "Unstar" : "Star"}
            >
              <Star
                size={15}
                strokeWidth={2}
                fill={email.isStarred ? "currentColor" : "none"}
              />
            </button>

            <button
              className="action-icon-btn danger"
              onClick={() => onDelete(email)}
              title="Delete"
            >
              <Trash2 size={15} strokeWidth={2} />
            </button>

            <button className="action-icon-btn" onClick={onClose} title="Close">
              <X size={15} strokeWidth={2.5} />
            </button>
          </div>
        </div>

        <h1 className="detail-subject">{email.subject || "(No subject)"}</h1>

        <div className="sender-card">
          <div className="sender-avatar">
            {email.sender ? email.sender.charAt(0) : "?"}
          </div>
          <div className="sender-meta">
            <span className="sender-name">
              {email.sender || "Unknown Sender"}
            </span>
            <span className="sender-email">
              &lt;recruiter@{email.company?.toLowerCase() || "company"}.com&gt;
            </span>
          </div>
        </div>

        {/* ── Calendar Button for INTERVIEW emails ── */}
        {isInterview && (
          <div style={{ marginTop: 14, display: "flex", alignItems: "center", gap: 10 }}>
            {calendarLoading ? (
              <button className="calendar-action-btn loading" disabled>
                <Loader2 size={14} strokeWidth={2} className="spin" />
                <span>Processing…</span>
              </button>
            ) : isInCalendar ? (
              <button
                className="calendar-action-btn added"
                onClick={handleRemoveFromCalendar}
                title="Click to remove from calendar"
              >
                <CalendarCheck size={14} strokeWidth={2} />
                <span>Added to Calendar</span>
                <span className="calendar-status-badge added">✓ Synced</span>
              </button>
            ) : (
              <button
                className="calendar-action-btn not-added"
                onClick={handleAddToCalendar}
                title="Click to add to calendar"
              >
                <CalendarPlus size={14} strokeWidth={2} />
                <span>Add to Calendar</span>
                <span className="calendar-status-badge not-added">Not synced</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* ── Body ── */}
      <div className="email-body-content">
        {(email.body || email.preview || "")
          .split("\n")
          .map((line, i) => <p key={i}>{line}</p>)}
      </div>

      {/* ── Footer ── */}
      <div className="email-detail-footer">
        <button
          className="btn-secondary"
          onClick={() => onGenerateAiReply(email)}
          disabled={isAiLoading}
          style={{ display: "flex", alignItems: "center", gap: 7 }}
        >
          <Sparkles size={14} strokeWidth={2} />
          {isAiLoading ? "Generating…" : "Generate AI Reply"}
        </button>

        <button className="btn-primary" onClick={() => onReply(email)}>
          Reply to {email.sender ? email.sender.split(" ")[0] : "Sender"}
        </button>
      </div>
    </div>
  );
}
