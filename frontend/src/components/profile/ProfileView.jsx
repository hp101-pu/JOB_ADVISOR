import React from "react";

// Helper function to format URLs
const formatUrl = (url) => {
  if (!url) return '';
  return url.startsWith('http') ? url : `https://${url}`;
};

export default function ProfileView({ 
  user, 
  onEditExperience, 
  onEditEducation, 
  onEditSkills  // ✅ FIXED: Added missing prop
}) {
  return (
    <div className="profile-view-grid">
      {/* ================= LEFT COLUMN ================= */}
      <div className="profile-left-col">
        {/* ABOUT */}
        <div className="card profile-section">
          <h3>About Me</h3>
          <p className="profile-text">
            {user.about || "No bio added yet."}
          </p>
        </div>

        {/* SOCIALS */}
        <div className="card profile-section">
          <h3>Socials</h3>
          <div className="social-links-col">
            {user.socials?.linkedin && (
              <a
                href={formatUrl(user.socials.linkedin)}  // ✅ FIXED
                target="_blank"
                rel="noreferrer"
                className="social-link-item"
              >
                🔗 LinkedIn
              </a>
            )}

            {user.socials?.github && (
              <a
                href={formatUrl(user.socials.github)}  // ✅ FIXED
                target="_blank"
                rel="noreferrer"
                className="social-link-item"
              >
                🐙 GitHub
              </a>
            )}

            {user.socials?.website && (
              <a
                href={formatUrl(user.socials.website)}  // ✅ FIXED
                target="_blank"
                rel="noreferrer"
                className="social-link-item"
              >
                🌐 Portfolio
              </a>
            )}

            {!user.socials?.linkedin &&
              !user.socials?.github &&
              !user.socials?.website && (
                <span
                  className="text-muted"
                  style={{ fontSize: "13px" }}
                >
                  No social links added.
                </span>
              )}
          </div>
        </div>

        {/* CONTACT */}
        <div className="card profile-section">
          <h3>Contact</h3>
          <div className="contact-row">
            <span className="icon">📧</span> {user.email}
          </div>
        </div>

        {/* SKILLS */}
        <div className="card profile-section">
          <div
            className="section-header-row"
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              borderBottom: "1px solid var(--border-color)",
              paddingBottom: "12px",
              marginBottom: "16px",
            }}
          >
            <h3 style={{ margin: 0 }}>Skills</h3>
            <button
              className="btn-icon-add"
              onClick={onEditSkills}
            >
              ✎ Edit
            </button>
          </div>
          
          <div className="skills-wrapper">
            {user.skills.length > 0 ? (
              user.skills.map((skill, index) => (
                <span key={index} className="skill-pill">
                  {skill}
                </span>
              ))
            ) : (
              <span
                className="text-muted"
                style={{ fontSize: "13px" }}
              >
                No skills added yet. Click Edit to add skills.
              </span>
            )}
          </div>
        </div>
      </div>  {/* ✅ FIXED: Added missing closing tag for profile-left-col */}

      {/* ================= RIGHT COLUMN ================= */}
      <div className="profile-right-col">
        {/* EXPERIENCE */}
        <div className="card profile-section">
          <div
            className="section-header-row"
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              borderBottom: "1px solid var(--border-color)",
              paddingBottom: "12px",
              marginBottom: "16px",
            }}
          >
            <h3 style={{ margin: 0 }}>Experience</h3>
            <button
              className="btn-icon-add"
              onClick={() => onEditExperience(null)}
            >
              + Add
            </button>
          </div>

          <div className="timeline">
            {user.experience.length === 0 && (
              <span
                className="text-muted"
                style={{ fontSize: "13px" }}
              >
                No experience added yet.
              </span>
            )}

            {user.experience.map((exp) => (
              <div
                key={exp._id}
                className="timeline-item group"
              >
                <div className="timeline-dot"></div>
                <div className="timeline-content">
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                    }}
                  >
                    <h4 className="timeline-role">
                      {exp.title}
                    </h4>
                    <button
                      className="btn-icon-edit"
                      onClick={() =>
                        onEditExperience(exp)
                      }
                    >
                      ✎
                    </button>
                  </div>

                  <span className="timeline-company">
                    {exp.company} •{" "}
                    {exp.startDate
                      ? new Date(exp.startDate).toLocaleDateString(
                          "en-US",
                          {
                            month: "short",
                            year: "numeric",
                          }
                        )
                      : "—"}{" "}
                    -{" "}
                    {exp.isCurrent
                      ? "Present"
                      : exp.endDate
                      ? new Date(
                          exp.endDate
                        ).toLocaleDateString("en-US", {
                          month: "short",
                          year: "numeric",
                        })
                      : "—"}
                  </span>

                  {exp.description && (
                    <p className="timeline-desc">
                      {exp.description}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* EDUCATION */}
        <div className="card profile-section">
          <div
            className="section-header-row"
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              borderBottom: "1px solid var(--border-color)",
              paddingBottom: "12px",
              marginBottom: "16px",
            }}
          >
            <h3 style={{ margin: 0 }}>Education</h3>
            <button
              className="btn-icon-add"
              onClick={() => onEditEducation(null)}
            >
              + Add
            </button>
          </div>

          <div className="timeline">
            {user.education.length === 0 && (
              <span
                className="text-muted"
                style={{ fontSize: "13px" }}
              >
                No education added yet.
              </span>
            )}

            {user.education.map((edu) => (
              <div
                key={edu._id}
                className="timeline-item"
              >
                <div className="timeline-dot"></div>
                <div className="timeline-content">
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                    }}
                  >
                    <h4 className="timeline-role">
                      {edu.degree}
                      {edu.fieldOfStudy && ` in ${edu.fieldOfStudy}`}
                    </h4>
                    <button
                      className="btn-icon-edit"
                      onClick={() =>
                        onEditEducation(edu)
                      }
                    >
                      ✎
                    </button>
                  </div>

                  <span className="timeline-company">
                    {edu.institution} • {edu.year}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}