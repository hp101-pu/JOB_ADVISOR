import React, { useState, useEffect } from "react";
import Sidebar from "../components/layout/Sidebar";
import TopHeader from "../components/layout/TopHeader";
import { getGmailStatus, disconnectGmail, reconnectGmail } from "../utils/api";
import NotificationPrefsCard from "../components/settings/NotificationPrefsCard";
import { useCurrentUser } from "../hooks/useCurrentUser";
import "../styles/dashboard.css";

export default function Settings() {
  const [gmailStatus, setGmailStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [confirmDisconnect, setConfirmDisconnect] = useState(false);
  const fullName = useCurrentUser();

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getGmailStatus();
        setGmailStatus(data);
      } catch (err) {
        console.error("Failed to fetch Gmail status", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleDisconnect = async () => {
    try {
      setActionLoading(true);
      await disconnectGmail();
      setGmailStatus({ connected: false, lastSync: null });
      setConfirmDisconnect(false);
    } catch (err) {
      alert("Failed to disconnect Gmail. Please try again.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleConnect = () => {
    reconnectGmail(); // redirects to OAuth
  };

  return (
    <div className="dashboard-shell">
      <Sidebar />
      <main className="dashboard-root">
        <TopHeader title="Settings" hideGreeting={true} fullName={fullName} />

        <div style={{ maxWidth: 600 }}>

          {/* Gmail Integration Card */}
          <div style={{
            background: "var(--bg-card, #fff)",
            border: "1px solid var(--border-color, #e5e7eb)",
            borderRadius: 12,
            padding: "24px 28px",
            boxShadow: "0 1px 4px rgba(0,0,0,0.06)"
          }}>
            <h2 style={{ margin: "0 0 4px", fontSize: 17, fontWeight: 700 }}>
              Gmail Integration
            </h2>
            <p style={{ margin: "0 0 20px", color: "var(--text-secondary, #6b7280)", fontSize: 14 }}>
              Connect your Gmail account to sync job-related emails into Seekr.
            </p>

            {loading ? (
              <p style={{ color: "var(--text-secondary, #6b7280)", fontSize: 14 }}>
                Checking connection…
              </p>
            ) : gmailStatus?.connected ? (
              <>
                {/* Connected state */}
                <div style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "10px 14px",
                  background: "#f0fdf4",
                  border: "1px solid #bbf7d0",
                  borderRadius: 8,
                  marginBottom: 20
                }}>
                  <span style={{ fontSize: 18 }}>✅</span>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14, color: "#166534" }}>
                      Gmail Connected
                    </div>
                    {gmailStatus.lastSync && (
                      <div style={{ fontSize: 12, color: "#4ade80" }}>
                        Last synced: {new Date(gmailStatus.lastSync).toLocaleString()}
                      </div>
                    )}
                  </div>
                </div>

                <div style={{ display: "flex", gap: 10 }}>
                  {/* Switch Account = disconnect then reconnect */}
                  <button
                    onClick={handleConnect}
                    style={{
                      padding: "9px 18px",
                      background: "var(--accent-primary, #3b82f6)",
                      color: "#fff",
                      border: "none",
                      borderRadius: 8,
                      fontWeight: 600,
                      fontSize: 14,
                      cursor: "pointer"
                    }}
                  >
                    🔄 Switch Account
                  </button>

                  {!confirmDisconnect ? (
                    <button
                      onClick={() => setConfirmDisconnect(true)}
                      style={{
                        padding: "9px 18px",
                        background: "transparent",
                        color: "#ef4444",
                        border: "1px solid #ef4444",
                        borderRadius: 8,
                        fontWeight: 600,
                        fontSize: 14,
                        cursor: "pointer"
                      }}
                    >
                      Disconnect
                    </button>
                  ) : (
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <span style={{ fontSize: 13, color: "#ef4444" }}>
                        Are you sure?
                      </span>
                      <button
                        onClick={handleDisconnect}
                        disabled={actionLoading}
                        style={{
                          padding: "7px 14px",
                          background: "#ef4444",
                          color: "#fff",
                          border: "none",
                          borderRadius: 7,
                          fontWeight: 600,
                          fontSize: 13,
                          cursor: actionLoading ? "not-allowed" : "pointer",
                          opacity: actionLoading ? 0.7 : 1
                        }}
                      >
                        {actionLoading ? "Disconnecting…" : "Yes, Disconnect"}
                      </button>
                      <button
                        onClick={() => setConfirmDisconnect(false)}
                        style={{
                          padding: "7px 14px",
                          background: "transparent",
                          color: "var(--text-secondary, #6b7280)",
                          border: "1px solid var(--border-color, #e5e7eb)",
                          borderRadius: 7,
                          fontWeight: 600,
                          fontSize: 13,
                          cursor: "pointer"
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                {/* Disconnected state */}
                <div style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "10px 14px",
                  background: "#fafafa",
                  border: "1px solid var(--border-color, #e5e7eb)",
                  borderRadius: 8,
                  marginBottom: 20
                }}>
                  <span style={{ fontSize: 18 }}>🔌</span>
                  <div style={{ fontWeight: 600, fontSize: 14, color: "var(--text-secondary, #6b7280)" }}>
                    No Gmail account connected
                  </div>
                </div>

                <button
                  onClick={handleConnect}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "10px 20px",
                    background: "var(--accent-primary, #3b82f6)",
                    color: "#fff",
                    border: "none",
                    borderRadius: 8,
                    fontWeight: 600,
                    fontSize: 14,
                    cursor: "pointer"
                  }}
                >
                  <img
                    src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
                    alt="Google"
                    style={{ width: 18, height: 18, background: "#fff", borderRadius: 3, padding: 1 }}
                  />
                  Connect Gmail
                </button>
              </>
            )}
          </div>
          {/* Notification Preferences Card */}
          <NotificationPrefsCard />
        </div>
      </main>
    </div>
  );
}