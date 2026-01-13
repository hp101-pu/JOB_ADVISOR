import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  BriefcaseBusiness,
  Mail,
  Sparkles,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import "../../styles/dashboard.css";

const NAV_ITEMS = [
  { to: "/dashboard", icon: LayoutDashboard,    label: "Dashboard" },
  { to: "/resume",    icon: FileText,            label: "Resume"    },
  { to: "/jobs",      icon: BriefcaseBusiness,   label: "Jobs"      },
  { to: "/emails",    icon: Mail,                label: "Emails"    },
  { to: "/ask-ai",    icon: Sparkles,            label: "Ask AI"    },
  { to: "/settings",  icon: Settings,            label: "Settings"  },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-top">
        <span className="sidebar-logo">Seekr</span>
        <button
          className="sidebar-toggle"
          onClick={() => setCollapsed(!collapsed)}
          aria-label="Toggle sidebar"
        >
          {collapsed
            ? <ChevronRight size={17} strokeWidth={2.5} />
            : <ChevronLeft  size={17} strokeWidth={2.5} />}
        </button>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => (isActive ? "active" : "")}
          >
            <span className="icon">
              <Icon size={18} strokeWidth={2} />
            </span>
            <span className="label">{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
