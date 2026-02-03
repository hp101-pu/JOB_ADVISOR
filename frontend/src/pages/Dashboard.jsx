import { useState, useEffect } from "react";
import { getCurrentUser, startGmailSync, getGmailStatus, getEmailStats, getMyResume } from "../utils/api";
import "../styles/dashboard.css";

import TopHeader from "../components/layout/TopHeader";
import Sidebar from "../components/layout/Sidebar";

import ResumeOverview from "../components/dashboard/ResumeOverview";
import ResumePolishCard from "../components/dashboard/ResumePolishCard";
import StatusCard from "../components/dashboard/StatusCard";
import RecruiterActivity from "../components/dashboard/RecruiterActivity";
import UpcomingEvents from "../components/dashboard/UpcomingEvents";
import CalendarWidget from "../components/dashboard/CalendarWidget";

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [gmail, setGmail] = useState({
    isConnected: false,
    timestamp: "Not connected",
  });
  const [emailStats, setEmailStats] = useState({ interviews: 0, rejections: 0, assessments: 0 });
  const [resumeData, setResumeData] = useState(null);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const userRes = await getCurrentUser();
        const gmailRes = await getGmailStatus();
        const statsRes = await getEmailStats();
        const resumeRes = await getMyResume();

        setUser(userRes.user);
        setEmailStats(statsRes);
        setResumeData(resumeRes);

        setGmail({
          isConnected: gmailRes.connected,
          timestamp: gmailRes.connected
            ? `Synced ${new Date(gmailRes.lastSync).toLocaleString()}`
            : "Not connected",
        });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  const hasResume = resumeData?.data?.hasResume ?? false;
  const resumeTimestamp = hasResume && resumeData?.data?.resume?.uploadedAt
    ? `Updated ${new Date(resumeData.data.resume.uploadedAt).toLocaleString()}`
    : "No resume found";

  const parsed = resumeData?.data?.parsed_resume || {};
  const entities = parsed.entities || {};
  const skillsDetected = entities.skills?.length ?? 0;
  const experienceYears = entities.experience_years ?? 0;
  const experienceMonths = entities.experience_months ?? 0;

  if (loading) {
    return <div style={{ padding: "2rem" }}>Loading...</div>;
  }

  return (
    <div className="dashboard-shell">
      <Sidebar />

      <main className="dashboard-root">
        <TopHeader fullName={user?.fullname || "User"} />

        {/* ── 2-card status row ── */}
        <div className="dashboard-status-grid">
          <ResumeOverview
            skillsDetected={hasResume ? skillsDetected : null}
            experienceYears={hasResume ? experienceYears : null}
            experienceMonths={hasResume ? experienceMonths : null}
            lastUpdated={hasResume ? resumeTimestamp : "No resume uploaded"}
          />
          <StatusCard
            type="gmail"
            title="Gmail"
            statusText={gmail.isConnected ? "Connected" : "Not Connected"}
            lastUpdated={gmail.timestamp}
            state={gmail.isConnected ? "success" : "error"}
            onClick={!gmail.isConnected ? startGmailSync : undefined}
          />
        </div>

        {/* ── Polish + Recruiter side by side ── */}
        <div className="dashboard-main-grid">
          <ResumePolishCard resumeData={resumeData} />
          <RecruiterActivity
            interviews={emailStats.interviews}
            rejections={emailStats.rejections}
            assessments={emailStats.assessments}
          />
        </div>

        {/* ── Calendar + Events/AskSeekr ── */}
        <div className="dashboard-lower-grid">
          <CalendarWidget />
          <div className="lower-right-col">
            <UpcomingEvents />
          </div>
        </div>
      </main>
    </div>
  );
}
