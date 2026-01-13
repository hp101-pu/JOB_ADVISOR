import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { UserRound, Sun, Moon, LogOut } from "lucide-react";
import "../../styles/layout.css";
import { logoutUser } from "../../utils/api";

export default function TopHeader({ fullName = "Priyangshu Ghosh", title, hideGreeting = false }) {
  const [theme, setTheme] = useState(localStorage.getItem("seekr-theme") || "light");
  const [showMenu, setShowMenu] = useState(false);

  const navigate = useNavigate();
  const menuRef = useRef(null);

  const firstName = fullName ? fullName.split(" ")[0] : "User";

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("seekr-theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme((prev) => (prev === "light" ? "dark" : "light"));

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  const handleSignOut = async () => {
    try {
      const res = await logoutUser();
      if (res.success) {
        // Clear ALL chat state so the next user never sees this user's history
        localStorage.removeItem("seekr_conversation_id");
        localStorage.removeItem("seekr_ai_conv_id");
        localStorage.removeItem("seekr_ai_messages"); // remove old persisted messages if any
        navigate("/auth");
      }
    } catch {
      alert("Server error during logout");
    }
  };

  const handleGoToProfile = () => {
    navigate("/profile");
    setShowMenu(false);
  };

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setShowMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="top-header">
      <div className="top-header__left">
        {hideGreeting ? (
          <h1 className="greeting" style={{ fontSize: "24px" }}>{title}</h1>
        ) : (
          <>
            <div className="greeting-block">
              <p className="greeting-label">{getGreeting()},</p>
              <h1 className="greeting-name"><span>{firstName}</span></h1>
            </div>
            <p className="subtitle">Here's your job search snapshot</p>
          </>
        )}
      </div>

      <div className="top-header__right" ref={menuRef}>
        <span className="user-name">{fullName}</span>

        <div
          className="avatar"
          onClick={() => setShowMenu(!showMenu)}
          title="Open Menu"
        >
          {firstName.charAt(0)}
        </div>

        <div className={`profile-dropdown ${showMenu ? "active" : ""}`}>
          <div className="dropdown-header">
            <strong>{fullName}</strong>
            <span>Job Seeker</span>
          </div>

          <div className="dropdown-divider" />

          <button className="dropdown-item" onClick={handleGoToProfile}>
            <UserRound size={16} strokeWidth={2} />
            My Profile
          </button>

          <button className="dropdown-item" onClick={toggleTheme}>
            {theme === "light"
              ? <Moon size={16} strokeWidth={2} />
              : <Sun  size={16} strokeWidth={2} />}
            {theme === "light" ? "Dark Mode" : "Light Mode"}
          </button>

          <div className="dropdown-divider" />

          <button className="dropdown-item danger" onClick={handleSignOut}>
            <LogOut size={16} strokeWidth={2} />
            Sign Out
          </button>
        </div>
      </div>
    </header>
  );
}
