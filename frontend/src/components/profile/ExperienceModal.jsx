import React, { useState } from "react";
import "../../styles/profile.css";

// Helper function to convert ISO date to YYYY-MM format
const formatDateForInput = (dateString) => {
  if (!dateString) return "";
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
};

export default function ExperienceModal({
  initialData,
  onClose,
  onSave,
  onDelete,
}) {
  const [form, setForm] = useState(
    initialData
      ? {
          ...initialData,
          startDate: formatDateForInput(initialData.startDate),
          endDate: formatDateForInput(initialData.endDate),
        }
      : {
          title: "",
          company: "",
          startDate: "",
          endDate: "",
          isCurrent: false,
          description: "",
        }
  );

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <div className="modal-overlay">
      <div className="card modal-card">
        {/* HEADER */}
        <div className="modal-header">
          <h3>{initialData ? "Edit Experience" : "Add Experience"}</h3>
          <button onClick={onClose} className="close-btn">
            ×
          </button>
        </div>

        {/* FORM */}
        <form
          className="modal-form"
          onSubmit={(e) => {
            e.preventDefault();
            onSave(form);
          }}
        >
          {/* TITLE */}
          <div className="form-group">
            <label>Role / Title</label>
            <input
              type="text"
              name="title"
              value={form.title}
              onChange={handleChange}
              className="form-input"
              required
              placeholder="e.g. Senior Developer"
            />
          </div>

          {/* COMPANY */}
          <div className="form-group">
            <label>Company</label>
            <input
              type="text"
              name="company"
              value={form.company}
              onChange={handleChange}
              className="form-input"
              required
              placeholder="e.g. Google"
            />
          </div>

          {/* DATES */}
          <div className="form-row">
            <div className="form-group">
              <label>Start Date</label>
              <input
                type="month"
                name="startDate"
                value={form.startDate}
                onChange={handleChange}
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label>End Date</label>
              <input
                type="month"
                name="endDate"
                value={form.endDate}
                onChange={handleChange}
                className="form-input"
                disabled={form.isCurrent}
              />
            </div>
          </div>

          {/* CURRENT */}
          <div className="form-group">
            <label style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              <input
                type="checkbox"
                checked={form.isCurrent}
                onChange={(e) =>
                  setForm({
                    ...form,
                    isCurrent: e.target.checked,
                    endDate: "",
                  })
                }
              />
              Currently working here
            </label>
          </div>

          {/* DESCRIPTION */}
          <div className="form-group">
            <label>Description</label>
            <textarea
              name="description"
              value={form.description}
              onChange={handleChange}
              className="form-input textarea"
              rows="3"
              placeholder="Describe your work and impact"
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
              <button
                type="button"
                onClick={onClose}
                className="btn-social"
              >
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