import React, { useState, useRef, useEffect } from "react";
import { Sparkles, SendHorizonal } from "lucide-react";
import { sendChatMessage } from "../../utils/api";

// Scoped to this browser session. Cleared on logout (TopHeader.jsx).
function getOrCreateConversationId() {
  let id = localStorage.getItem("seekr_conversation_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("seekr_conversation_id", id);
  }
  return id;
}

export default function AskSeekr() {
  const suggestions = ["Resume Tips", "Job Search Advice", "Interview Prep"];
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pendingConfirmation, setPendingConfirmation] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, pendingConfirmation]);

  const handleResponse = (data, userText) => {
    const reply =
      typeof data.response === "string"
        ? data.response
        : JSON.stringify(data.response);

    const status = data.metadata?.status;

    if (status === "NEEDS_CONFIRMATION") {
      setPendingConfirmation({ text: userText, reply });
      return;
    }

    setPendingConfirmation(null);

    if (status === "BLOCKED") {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: reply || "I need more information to do that." },
      ]);
      return;
    }

    const meta = data.metadata || {};
    let finalReply = reply;
    if (meta.google_synced === false && meta.event_created) {
      finalReply += "\n\n*Saved to your app calendar. Not synced to Google Calendar — connect your Google Calendar in Settings to sync.*";
    } else if (meta.google_synced === true && meta.event_created) {
      finalReply += "\n\n*Event saved and synced to Google Calendar.*";
    }

    setMessages((prev) => [...prev, { role: "assistant", content: finalReply }]);
  };

  const sendMessage = async (text, confirmed = false) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const conversationId = getOrCreateConversationId();

    if (!confirmed) {
      setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
      setInput("");
    }
    setLoading(true);

    try {
      const data = await sendChatMessage({
        text: trimmed,
        conversationId,
        confirmed,
      });
      handleResponse(data, trimmed);
    } catch (err) {
      setPendingConfirmation(null);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: err.message || "Something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    if (!pendingConfirmation) return;
    const text = pendingConfirmation.text;
    setPendingConfirmation(null);
    sendMessage(text, true);
  };

  const handleCancel = () => {
    setPendingConfirmation(null);
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "Action cancelled." },
    ]);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const isInputDisabled = loading || pendingConfirmation;

  return (
    <div className="card ask-seekr-card">
      <div className="ask-header" style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
        <div
          style={{
            width: 34, height: 34, borderRadius: 9,
            background: "var(--accent-soft)",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0, color: "var(--accent-primary)",
          }}
        >
          <Sparkles size={18} strokeWidth={2} />
        </div>
        <h3 style={{ margin: 0, borderBottom: "none", paddingBottom: 0 }}>Ask Seekr</h3>
      </div>

      {/* Chat history */}
      {messages.length > 0 && (
        <div
          style={{
            maxHeight: 220, overflowY: "auto", marginBottom: 10,
            display: "flex", flexDirection: "column", gap: 6,
          }}
        >
          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                background: m.role === "user" ? "var(--accent-primary)" : "var(--bg-secondary, #f1f5f9)",
                color: m.role === "user" ? "#fff" : "var(--text-primary, #1e293b)",
                borderRadius: 10,
                padding: "7px 12px",
                fontSize: 13,
                maxWidth: "85%",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                lineHeight: 1.5,
              }}
            >
              {m.content}
            </div>
          ))}
          {loading && (
            <div style={{ alignSelf: "flex-start", fontSize: 12, color: "var(--text-muted, #94a3b8)" }}>
              Seekr is thinking…
            </div>
          )}
          {pendingConfirmation && (
            <div
              style={{
                alignSelf: "flex-start",
                background: "var(--bg-secondary, #f1f5f9)",
                border: "1px solid var(--border-color)",
                borderRadius: 10,
                padding: "10px 12px",
                fontSize: 13,
                maxWidth: "90%",
              }}
            >
              <p style={{ margin: "0 0 8px" }}>{pendingConfirmation.reply}</p>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  onClick={handleConfirm}
                  style={{
                    padding: "4px 10px",
                    borderRadius: 6,
                    border: "none",
                    background: "var(--accent-primary)",
                    color: "#fff",
                    fontSize: 12,
                    cursor: "pointer",
                  }}
                >
                  Confirm
                </button>
                <button
                  onClick={handleCancel}
                  style={{
                    padding: "4px 10px",
                    borderRadius: 6,
                    border: "1px solid var(--border-color)",
                    background: "transparent",
                    color: "var(--text-primary)",
                    fontSize: 12,
                    cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      )}

      <div className="ask-input-wrapper" style={{ position: "relative" }}>
        <input
          type="text"
          placeholder={pendingConfirmation ? "Confirm or cancel the pending action…" : "Ask me anything…"}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isInputDisabled}
        />
        <button
          className="ask-send-btn"
          onClick={() => sendMessage(input)}
          disabled={isInputDisabled || !input.trim()}
          style={{
            position: "absolute", right: 10, top: "50%",
            transform: "translateY(-50%)",
            background: "var(--accent-gradient)",
            border: "none", borderRadius: 8,
            width: 30, height: 30,
            display: "flex", alignItems: "center", justifyContent: "center",
            cursor: isInputDisabled || !input.trim() ? "not-allowed" : "pointer",
            color: "#fff", opacity: isInputDisabled || !input.trim() ? 0.6 : 1,
          }}
        >
          <SendHorizonal size={15} strokeWidth={2.5} />
        </button>
      </div>

      {messages.length === 0 && !pendingConfirmation && (
        <div className="ask-suggestions">
          {suggestions.map((text) => (
            <button key={text} className="suggestion-pill" onClick={() => sendMessage(text)}>
              {text}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
