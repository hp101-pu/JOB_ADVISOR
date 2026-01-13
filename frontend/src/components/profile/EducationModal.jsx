import React, { useState } from "react";
import "../../styles/profile.css";

export default function EducationModal({
  initialData,
  onClose,
  onSave,
  onDelete,
}) {
  const [form, setForm] = useState(
    initialData || {
      degree: "",
      fieldOfStudy: "",
      institution: "",
      year: "",
    }
  );

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  return (
    <div className="modal-overlay">
      <div className="card modal-card">
        <div className="modal-header">
          <h3>{initialData ? "Edit Education" : "Add Education"}</h3>
          <button onClick={onClose} className="close-btn">×</button>
        </div>

        <form
          className="modal-form"
          onSubmit={(e) => {
            e.preventDefault();
            onSave(form);
          }}
        >
          {/* DEGREE + FIELD OF STUDY */}
          <div className="form-row">
            <div className="form-group">
              <label>Degree</label>
              <input
                type="text"
                name="degree"
                value={form.degree}
                onChange={handleChange}
                className="form-input"
                required
                placeholder="e.g. B.Tech, M.Sc, MBA"
              />
            </div>

            <div className="form-group">
              <label>Field of Study</label>
              <input
                type="text"
                name="fieldOfStudy"
                value={form.fieldOfStudy}
                onChange={handleChange}
                className="form-input"
                required
                placeholder="e.g. Computer Science"
              />
            </div>
          </div>

          {/* INSTITUTION */}
          <div className="form-group">
            <label>School / University</label>
            <input
              type="text"
              name="institution"
              value={form.institution}
              onChange={handleChange}
              className="form-input"
              required
              placeholder="e.g. MIT, Stanford University"
            />
          </div>

          {/* YEAR */}
          <div className="form-group">
            <label>Year of Passing</label>
            <input
              type="text"
              name="year"
              value={form.year}
              onChange={handleChange}
              className="form-input"
              placeholder="e.g. 2021"
            />
          </div>

          {/* ACTIONS */}
          <div
            className="modal-actions"
            style={{ justifyContent: "space-between" }}
          >
            {initialData && (
              <button
                type="button"
                onClick={() => onDelete(initialData._id)}
                style={{
                  color: "#ef4444",
                  background: "transparent",
                  border: "none",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Delete
              </button>
            )}

            <div style={{ display: "flex", gap: "8px" }}>
              <button type="button" onClick={onClose} className="btn-social">
                Cancel
              </button>
              <button type="submit" className="btn-primary">
                Save
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}