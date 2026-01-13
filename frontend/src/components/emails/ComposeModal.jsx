import React, { useState, useEffect } from "react";
import { X, Sparkles, SendHorizonal } from "lucide-react";

export default function ComposeModal({
  onClose,
  initialData,
  onAskAi,
  onSend,
  isAiLoading,
  isSending,
}) {
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  useEffect(() => {
    if (initialData) {
      setTo(initialData.to || "");
      setSubject(initialData.subject || "");
      setBody(initialData.body || "");
    }
  }, [initialData]);

  return (
    <div className="compose-overlay">
      <div className="compose-window">

        {/* ── Header ── */}
        <div className="compose-header">
          <span className="compose-title">New Message</span>
          <button className="icon-btn-close" onClick={onClose}>
            <X size={18} strokeWidth={2} />
          </button>
        </div>

        {/* ── To / Subject ── */}
        <div className="compose-inputs">
          <div className="input-row">
            <span className="input-label">To</span>
            <input
              className="clean-input"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              placeholder="recipient@example.com"
            />
          </div>
          <div className="input-row">
            <span className="input-label">Subject</span>
            <input
              className="clean-input"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Enter subject…"
            />
          </div>
        </div>

        {/* ── Body ── */}
        <textarea
          className="compose-body"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Start writing here…"
        />

        {/* ── Footer ── */}
        <div className="compose-footer">
          <button
            className="btn-ai-magic"
            onClick={onAskAi}
            disabled={isAiLoading}
          >
            <Sparkles size={14} strokeWidth={2.5} />
            {isAiLoading ? "Writing…" : "Ask AI to Write"}
          </button>

          <div style={{ display: "flex", gap: 10 }}>
            <button
              className="btn-secondary"
              onClick={onClose}
              style={{ padding: "9px 16px", fontSize: 13.5 }}
            >
              Discard
            </button>

            <button
              className="btn-send-primary"
              disabled={isSending}
              onClick={() =>
                onSend({
                  to,
                  subject,
                  body,
                  threadId: initialData?.threadId,
                  in_reply_to: initialData?.in_reply_to,
                })
              }
            >
              <SendHorizonal size={15} strokeWidth={2.5} />
              {isSending ? "Sending…" : "Send"}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
