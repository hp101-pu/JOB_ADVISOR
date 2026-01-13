import React from "react";
import { useNavigate } from "react-router-dom";

export default function AskAIFab() {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate("/ask-ai")}
      aria-label="Ask Seekr AI"
      style={{
        position: "fixed",
        bottom: "28px",
        right: "28px",
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        gap: "8px",
        padding: "0 20px 0 14px",
        height: "48px",
        borderRadius: "24px",
        background: "var(--accent-primary)",
        color: "#fff",
        border: "none",
        cursor: "pointer",
        fontFamily: "inherit",
        fontSize: "14px",
        fontWeight: "700",
        boxShadow: "0 4px 20px rgba(37, 99, 235, 0.45)",
        transition: "transform 0.2s ease, box-shadow 0.2s ease",
      }}
      onMouseEnter={e => {
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.boxShadow = "0 8px 28px rgba(37, 99, 235, 0.55)";
      }}
      onMouseLeave={e => {
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow = "0 4px 20px rgba(37, 99, 235, 0.45)";
      }}
    >
      {/* Robot icon */}
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
      </svg>

      <span>Ask AI</span>

      {/* Green online dot */}
      <span style={{
        width: "7px",
        height: "7px",
        borderRadius: "50%",
        background: "#4ade80",
        animation: "wai-pulse 2s infinite",
        marginLeft: "2px",
      }} />

      <style>{`
        @keyframes wai-pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.8); }
        }
      `}</style>
    </button>
  );
}