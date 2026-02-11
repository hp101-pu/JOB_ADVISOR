import React, { useState, useRef, useEffect } from "react";
import { BotMessageSquare, SendHorizonal, Trash2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import Sidebar from "../components/layout/Sidebar";
import { sendChatMessage } from "../utils/api";
import "../styles/dashboard.css";
import "../styles/askai.css";

const SUGGESTIONS = [
  "Summarize my recent rejection emails",
  "Any interview scheduled this week?",
  "Find me React developer jobs in Bangalore",
  "Draft a follow-up email for my last interview",
  "How is my job search going?",
];

// ─────────────────────────────────────────────
// conversation_id: stored in localStorage but
// NEVER shared across users — cleared on logout
// via TopHeader.jsx → localStorage.removeItem
// ─────────────────────────────────────────────
const CONV_ID_KEY = "seekr_ai_conv_id";

function getOrCreateConvId() {
  let id = localStorage.getItem(CONV_ID_KEY);
  if (!id) {
    id = `conv_${crypto.randomUUID()}`;
    localStorage.setItem(CONV_ID_KEY, id);
  }
  return id;
}

// ─────────────────────────────────────────────
// ❌ DO NOT persist messages in localStorage.
// Persisting means the next user who logs in on
// the same browser sees the previous user's chat
// history — the root cause of the hallucination.
// Messages are in-memory only (useState).
// ─────────────────────────────────────────────

function TypingDots() {
  return (
    <div className="ai-typing-indicator">
      <span /><span /><span />
    </div>
  );
}

function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  const content = typeof msg.content === "string"
    ? msg.content
    : JSON.stringify(msg.content, null, 2);

  return (
    <div className={`ai-message-row ${isUser ? "user" : "assistant"}`}>
      {!isUser && (
        <div className="ai-avatar">
          <BotMessageSquare size={15} strokeWidth={2} />
        </div>
      )}
      <div className={`ai-bubble ${isUser ? "user" : "assistant"}`}>
        {isUser ? (
          content
        ) : (
          <ReactMarkdown
            components={{
              a: ({ href, children }) => (
                <a href={href} target="_blank" rel="noopener noreferrer" className="ai-md-link">
                  {children}
                </a>
              ),
              p:      ({ children }) => <p className="ai-md-p">{children}</p>,
              strong: ({ children }) => <strong className="ai-md-bold">{children}</strong>,
              ul:     ({ children }) => <ul className="ai-md-ul">{children}</ul>,
              ol:     ({ children }) => <ol className="ai-md-ol">{children}</ol>,
              li:     ({ children }) => <li className="ai-md-li">{children}</li>,
              h1:     ({ children }) => <h1 className="ai-md-h">{children}</h1>,
              h2:     ({ children }) => <h2 className="ai-md-h">{children}</h2>,
              h3:     ({ children }) => <h3 className="ai-md-h3">{children}</h3>,
              code:   ({ children }) => <code className="ai-md-code">{children}</code>,
            }}
          >
            {content}
          </ReactMarkdown>
        )}
      </div>
      {isUser && <div className="ai-user-avatar">You</div>}
    </div>
  );
}

const DEFAULT_MSG = {
  role: "assistant",
  content: "Hey! I'm Seekr AI — ask me anything about your job search — emails, interviews, job listings, or career advice.",
};

export default function AskAI() {
  // ✅ In-memory only — never persisted to localStorage
  const [messages, setMessages] = useState([DEFAULT_MSG]);
  const [input, setInput]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [pendingConfirmation, setPendingConfirmation] = useState(null);
  const bottomRef  = useRef(null);
  const inputRef   = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, pendingConfirmation]);

  const sendMessage = async (text, confirmed = false) => {
    const trimmed = (text || input).trim();
    if (!trimmed || loading) return;

    const conversationId = getOrCreateConvId();

    if (!confirmed) {
      setInput("");
      setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    }
    setLoading(true);

    try {
      const data = await sendChatMessage({
        text: trimmed,
        conversationId,
        confirmed,
      });
      const reply =
        typeof data.response === "string"
          ? data.response
          : JSON.stringify(data.response, null, 2);

      if (data.metadata?.status === "NEEDS_CONFIRMATION") {
        setPendingConfirmation({ text: trimmed, reply });
      } else {
        setPendingConfirmation(null);

        // Check if the response includes Google Calendar sync info
        const meta = data.metadata || {};
        let finalReply = reply;

        if (meta.google_synced === false && meta.event_created) {
          finalReply = reply + "\n\n*Saved to your app calendar. Not synced to Google Calendar — connect your Google Calendar in Settings to sync.*";
        } else if (meta.google_synced === true && meta.event_created) {
          finalReply = reply + "\n\n*Event saved and synced to Google Calendar.*";
        }

        setMessages((prev) => [...prev, { role: "assistant", content: finalReply }]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: err.message || "Sorry, something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
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
      sendMessage();
    }
  };

  const handleClear = () => {
    setMessages([DEFAULT_MSG]);
    // Reset conversation so Python starts a fresh Redis context
    localStorage.removeItem(CONV_ID_KEY);
  };

  const showSuggestions = messages.length <= 1;

  return (
    <div className="dashboard-shell">
      <Sidebar />
      <main className="ai-page">

        {/* Header */}
        <div className="ai-header">
          <div className="ai-header-left">
            <div className="ai-header-icon">
              <BotMessageSquare size={20} strokeWidth={2} />
            </div>
            <div>
              <h1 className="ai-header-title">Ask Seekr</h1>
              <span className="ai-header-sub">Your AI job search assistant</span>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <button className="ai-clear-btn" title="Clear chat history" onClick={handleClear}>
              <Trash2 size={14} strokeWidth={2} />
              Clear
            </button>
            <div className="ai-status-pill">
              <span className="ai-status-dot" />
              Online
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="ai-thread">
          {messages.map((msg, i) => (
            <MessageBubble key={i} msg={msg} />
          ))}
          {loading && (
            <div className="ai-message-row assistant">
              <div className="ai-avatar">
                <BotMessageSquare size={15} strokeWidth={2} />
              </div>
              <div className="ai-bubble assistant">
                <TypingDots />
              </div>
            </div>
          )}
          {pendingConfirmation && (
            <div className="ai-confirmation-row">
              <div className="ai-confirmation-bubble">
                <p>{pendingConfirmation.reply}</p>
                <div className="ai-confirmation-actions">
                  <button className="ai-confirm-btn" onClick={handleConfirm}>
                    Confirm
                  </button>
                  <button className="ai-cancel-btn" onClick={handleCancel}>
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Suggestion Pills */}
        {showSuggestions && (
          <div className="ai-suggestions-bar">
            {SUGGESTIONS.map((s) => (
              <button key={s} className="ai-suggestion-pill" onClick={() => sendMessage(s)}>
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="ai-input-bar">
          <div className="ai-input-wrapper">
            <textarea
              ref={inputRef}
              className="ai-textarea"
              rows={1}
              placeholder={pendingConfirmation ? "Confirm or cancel the pending action…" : "Ask about your jobs, emails, interviews…"}
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = "auto";
                e.target.style.height = Math.min(e.target.scrollHeight, 140) + "px";
              }}
              onKeyDown={handleKeyDown}
              disabled={loading || pendingConfirmation}
            />
            <button
              className={`ai-send-btn ${loading || !input.trim() || pendingConfirmation ? "disabled" : ""}`}
              onClick={() => sendMessage()}
              disabled={loading || !input.trim() || pendingConfirmation}
            >
              <SendHorizonal size={16} strokeWidth={2.5} />
            </button>
          </div>
          <p className="ai-disclaimer">
            Seekr AI can make mistakes. Always verify important information.
          </p>
        </div>

      </main>
    </div>
  );
}
