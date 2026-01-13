import React, { useState } from "react";

export default function ProfileEdit({ user, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    fullname: user.fullname,
    headline: user.headline,
    location: {
      city: user.location?.city || "",
      country: user.location?.country || "India",
    },
    about: user.about,
    socials: {
      linkedin: user.socials?.linkedin || "",
      github: user.socials?.github || "",
      website: user.socials?.website || ""
    }
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleLocationChange = (e) => {
    setFormData({
      ...formData,
      location: {
        ...formData.location,
        [e.target.name]: e.target.value,
      },
    });
  };

  // Handle nested social object changes
  const handleSocialChange = (e) => {
    setFormData({
      ...formData,
      socials: { ...formData.socials, [e.target.name]: e.target.value }
    });
  };

  return (
    <div className="card profile-edit-card">
      <h3 className="edit-title">Edit Profile Details</h3>

      <form className="edit-form" onSubmit={(e) => { e.preventDefault(); onSave(formData); }}>
        <div className="form-row">
          <div className="form-group">
            <label>Full Name</label>
            <input type="text" name="fullname" value={formData.fullname} onChange={handleChange} className="form-input" required />
          </div>
          <div className="form-group">
            <label>Headline</label>
            <input type="text" name="headline" value={formData.headline} onChange={handleChange} className="form-input" />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>City</label>
            <input
              type="text"
              name="city"
              value={formData.location.city}
              onChange={handleLocationChange}
              className="form-input"
              placeholder="City"
            />
          </div>

          <div className="form-group">
            <label>Country</label>
            <input
              type="text"
              name="country"
              value={formData.location.country}
              onChange={handleLocationChange}
              className="form-input"
              placeholder="Country"
            />
          </div>

          {/* ✅ Email Field Preserved (Locked) */}
          <div className="form-group">
            <label>Email (Locked)</label>
            <input type="email" value={user.email} disabled className="form-input disabled" />
          </div>
        </div>

        {/* ✅ Social Links Section */}
        <div style={{ marginTop: '16px', marginBottom: '16px', padding: '16px', background: 'var(--bg-primary)', borderRadius: '8px' }}>
          <label className="form-label" style={{ marginBottom: '12px', display: 'block', color: 'var(--accent-primary)' }}>Social Profiles</label>

          <div className="form-row">
            <div className="form-group">
              <label style={{ fontSize: '12px' }}>LinkedIn URL</label>
              <input type="text" name="linkedin" value={formData.socials.linkedin} onChange={handleSocialChange} className="form-input" placeholder="linkedin.com/in/username" />
            </div>
            <div className="form-group">
              <label style={{ fontSize: '12px' }}>GitHub URL</label>
              <input type="text" name="github" value={formData.socials.github} onChange={handleSocialChange} className="form-input" placeholder="github.com/username" />
            </div>
          </div>

          <div className="form-group" style={{ marginTop: '12px' }}>
            <label style={{ fontSize: '12px' }}>Portfolio Website</label>
            <input type="text" name="website" value={formData.socials.website} onChange={handleSocialChange} className="form-input" placeholder="yourname.dev" />
          </div>
        </div>

        <div className="form-group">
          <label>About Me</label>
          <textarea name="about" value={formData.about} onChange={handleChange} className="form-input textarea" rows="4"></textarea>
        </div>

        <div className="form-actions" style={{ gap: '10px' }}>
          <button type="button" className="btn-social" onClick={onCancel}>Cancel</button>
          <button type="submit" className="btn-primary">Save Changes</button>
        </div>
      </form>
    </div>
  );
}