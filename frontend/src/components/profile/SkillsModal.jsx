import React, { useState } from "react";
import "../../styles/profile.css";

export default function SkillsModal({ initialSkills, onClose, onSave }) {
  const [skills, setSkills] = useState(initialSkills || []);
  const [inputValue, setInputValue] = useState("");

  const handleAddSkill = () => {
    const trimmedSkill = inputValue.trim();
    
    if (!trimmedSkill) {
      alert("Please enter a skill");
      return;
    }

    if (skills.includes(trimmedSkill)) {
      alert("This skill already exists");
      return;
    }

    setSkills([...skills, trimmedSkill]);
    setInputValue("");
  };

  const handleRemoveSkill = (skillToRemove) => {
    setSkills(skills.filter((skill) => skill !== skillToRemove));
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddSkill();
    }
  };

  return (
    <div className="modal-overlay">
      <div className="card modal-card">
        {/* HEADER */}
        <div className="modal-header">
          <h3>Edit Skills</h3>
          <button onClick={onClose} className="close-btn">
            ×
          </button>
        </div>

        {/* FORM */}
        <form
          className="modal-form"
          onSubmit={(e) => {
            e.preventDefault();
            onSave(skills);
          }}
        >
          {/* ADD SKILL INPUT */}
          <div className="form-group">
            <label>Add New Skill</label>
            <div style={{ display: "flex", gap: "8px" }}>
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                className="form-input"
                placeholder="e.g. JavaScript, Python, React..."
                style={{ flex: 1 }}
              />
              <button
                type="button"
                onClick={handleAddSkill}
                className="btn-primary"
                style={{ whiteSpace: "nowrap" }}
              >
                + Add
              </button>
            </div>
          </div>

          {/* CURRENT SKILLS */}
          <div className="form-group">
            <label>Your Skills ({skills.length})</label>
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "8px",
                minHeight: "100px",
                padding: "12px",
                background: "var(--bg-secondary)",
                borderRadius: "8px",
                border: "1px solid var(--border-color)",
              }}
            >
              {skills.length === 0 ? (
                <span
                  style={{
                    color: "var(--text-muted)",
                    fontSize: "14px",
                    margin: "auto",
                  }}
                >
                  No skills added yet. Add your first skill above!
                </span>
              ) : (
                skills.map((skill, index) => (
                  <div
                    key={index}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      padding: "6px 12px",
                      background: "var(--accent-primary)",
                      color: "white",
                      borderRadius: "20px",
                      fontSize: "14px",
                    }}
                  >
                    <span>{skill}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill(skill)}
                      style={{
                        background: "transparent",
                        border: "none",
                        color: "white",
                        cursor: "pointer",
                        fontSize: "16px",
                        padding: "0 4px",
                        lineHeight: "1",
                      }}
                      title="Remove skill"
                    >
                      ×
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* ACTIONS */}
          <div className="modal-actions">
            <button type="button" onClick={onClose} className="btn-social">
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}