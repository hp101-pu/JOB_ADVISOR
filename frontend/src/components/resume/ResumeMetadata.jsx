import React from "react";

// ─── SVG icon helpers ──────────────────────────────────────────────────────────
const CalendarIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
    <line x1="16" y1="2" x2="16" y2="6" />
    <line x1="8" y1="2" x2="8" y2="6" />
    <line x1="3" y1="10" x2="21" y2="10" />
  </svg>
);
const CompanyIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
);
const StarIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
  </svg>
);
const RoleIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M20 7H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z" />
    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
  </svg>
);
const ProjectIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="16 18 22 12 16 6" />
    <polyline points="8 6 2 12 8 18" />
  </svg>
);
const EducationIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
    <path d="M6 12v5c3 3 9 3 12 0v-5" />
  </svg>
);
const BuildingIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
  </svg>
);

// ─── Stat box ───────────────────────────────────────────────────────────────
const StatBox = ({ icon, value, label }) => (
  <div className="stat-box">
    <div className="stat-icon">{icon}</div>
    <div className="stat-value">{value}</div>
    <div className="stat-label">{label}</div>
  </div>
);

// ─── Component ───────────────────────────────────────────────────────────────
const ResumeMetadata = ({ metadataData, scoreData }) => {
  if (!metadataData) {
    return (
      <div className="resume-column">
        <div className="resume-card">
          <div className="resume-card-header"><h3>Key Insights</h3></div>
          <div className="empty-message">
            <div className="empty-icon">
              <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <p>Key insights will appear here after analysis</p>
          </div>
        </div>
      </div>
    );
  }

  const entities  = metadataData.entities  || {};
  const structured = metadataData.structured || {};
  const profile   = scoreData?.render_data?.profile?.key || "student";

  const skills    = entities.skills    || [];
  const companies = entities.companies || [];
  const roles     = entities.roles     || [];
  const expYears  = entities.experience_years  ?? 0;
  const expMonths = entities.experience_months ?? 0;

  const expDisplay =
    expYears > 0
      ? `${expYears}yr${expMonths > 0 ? ` ${expMonths}mo` : ""}`.trim()
      : `${expMonths}mo`;

  const projects       = structured.projects       || [];
  const experience     = structured.experience     || [];
  const volunteer      = structured.volunteer      || [];
  const education      = structured.education      || [];
  const achievements   = structured.achievements   || [];
  const certifications = structured.certifications || [];

  const projectCount = projects.length;
  const hasEducation  = education.length > 0;
  const hasProjects   = projects.length > 0;
  const hasAchiev     = achievements.length > 0;
  const hasCerts      = certifications.length > 0;
  const hasVolunteer  = volunteer.length > 0;
  const hasExperience = experience.length > 0;

  const isStudent = profile === "student";
  const isEarly   = profile === "early_career";

  return (
    <div className="resume-column">
      <div className="resume-card">
        <div className="resume-card-header"><h3>Key Insights</h3></div>

        <div className="metadata-content">

          {/* STAT BOXES */}
          <div className="metadata-stats">
            {isStudent ? (
              <>
                <StatBox icon={<ProjectIcon />}  value={hasProjects ? projectCount || "✓" : "0"} label="Projects" />
                <StatBox icon={<EducationIcon />} value={hasEducation ? "✓" : "–"} label="Education" />
                <StatBox icon={<StarIcon />}      value={skills.length}  label="Skills" />
                <StatBox icon={<RoleIcon />}      value={roles.length}   label="Roles" />
              </>
            ) : isEarly ? (
              <>
                <StatBox icon={<CalendarIcon />} value={expDisplay}       label="Experience" />
                <StatBox icon={<CompanyIcon />}  value={companies.length} label="Companies" />
                <StatBox icon={<StarIcon />}     value={skills.length}    label="Skills" />
                <StatBox icon={<RoleIcon />}     value={roles.length}     label="Roles" />
              </>
            ) : (
              <>
                <StatBox icon={<CalendarIcon />} value={expDisplay}       label="Experience" />
                <StatBox icon={<CompanyIcon />}  value={companies.length} label="Companies" />
                <StatBox icon={<StarIcon />}     value={skills.length}    label="Skills Listed" />
                <StatBox icon={<RoleIcon />}     value={roles.length}     label="Roles Detected" />
              </>
            )}
          </div>

          {/* TOP SKILLS */}
          {skills.length > 0 && (
            <div className="metadata-section">
              <h4>Top Skills</h4>
              <div className="skills-list">
                {skills.slice(0, 8).map((skill, i) => (
                  <span key={i} className="skill-item">{skill}</span>
                ))}
                {skills.length > 8 && (
                  <span className="skill-item skill-more">+{skills.length - 8} more</span>
                )}
              </div>
            </div>
          )}

          {/* PROJECTS */}
          {(isStudent || isEarly) && hasProjects && (
            <div className="metadata-section">
              <h4>Projects ({projects.length})</h4>
              <div className="projects-preview">
                {projects.slice(0, 4).map((proj, i) => (
                  <div key={i} className="project-entry">
                    <div className="project-line">
                      <span className="project-bullet" />
                      <span className="project-name">{proj.name}</span>
                    </div>
                    {proj.date && <div className="project-detail">{proj.date}</div>}
                    {proj.tech_stack?.length > 0 && (
                      <div className="project-tech">{proj.tech_stack.join(", ")}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* EDUCATION */}
          {hasEducation && (
            <div className="metadata-section">
              <h4>Education</h4>
              <div className="education-preview">
                {education.slice(0, 2).map((edu, i) => (
                  <div key={i} className="education-entry">
                    <div className="education-institute">{edu.institution}</div>
                    {edu.degree && <div className="education-degree">{edu.degree}</div>}
                    <div className="education-meta">
                      {edu.date  && <span className="education-year">{edu.date}</span>}
                      {edu.details && <span className="education-score">{edu.details}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* WORK HISTORY / EXPERIENCE */}
          {!isStudent && hasExperience && (
            <div className="metadata-section">
              <h4>Work History</h4>
              <div className="companies-list">
                {experience.map((exp, i) => (
                  <div key={i} className="company-item">
                    <BuildingIcon />
                    {exp.company || exp.role}
                    {exp.date && <span className="project-detail"> — {exp.date}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* INTERNSHIPS — from structured experience */}
          {isStudent && hasExperience && (
            <div className="metadata-section">
              <h4>Internships</h4>
              <div className="companies-list">
                {experience.map((exp, i) => (
                  <div key={i} className="company-item">
                    <BuildingIcon />
                    {exp.company || exp.role}
                    {exp.date && <span className="project-detail"> — {exp.date}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* POSITIONS OF RESPONSIBILITY — from structured volunteer */}
          {isStudent && hasVolunteer && (
            <div className="metadata-section">
              <h4>Positions of Responsibility</h4>
              <div className="projects-preview">
                {volunteer.slice(0, 4).map((vol, i) => (
                  <div key={i} className="project-entry">
                    <div className="project-line">
                      <span className="project-bullet" />
                      <span className="project-name">{vol.role}</span>
                    </div>
                    {vol.date && <div className="project-detail">{vol.date}</div>}
                    {vol.organization && <div className="project-detail">{vol.organization}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* DETECTED ROLES */}
          {roles.length > 0 && (
            <div className="metadata-section">
              <h4>Detected Roles</h4>
              <div className="skills-list">
                {roles.map((role, i) => (
                  <span key={i} className="skill-item">{role}</span>
                ))}
              </div>
            </div>
          )}

          {/* ACHIEVEMENTS */}
          {(isStudent || isEarly) && hasAchiev && (
            <div className="metadata-section">
              <h4>Achievements</h4>
              <div className="projects-preview">
                {achievements.map((ach, i) => (
                  <div key={i} className="project-line">
                    <span className="project-bullet" />
                    <span className="project-name">{ach.title}</span>
                    {ach.date && <span className="project-detail"> — {ach.date}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CERTIFICATIONS */}
          {(isStudent || isEarly) && hasCerts && (
            <div className="metadata-section">
              <h4>Certifications</h4>
              <div className="education-preview">
                {certifications.map((cert, i) => (
                  <div key={i} className="education-line">
                    {cert.title}
                    {cert.issuer && <span className="project-detail"> — {cert.issuer}</span>}
                    {cert.date && <span className="project-detail"> — {cert.date}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default ResumeMetadata;