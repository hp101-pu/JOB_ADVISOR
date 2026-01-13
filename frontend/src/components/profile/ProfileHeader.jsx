import React from "react";

export default function ProfileHeader({ user, isEditing, toggleEdit, onAvatarClick, defaultAvatar }) {
  const avatarSrc = user.avatar || defaultAvatar;

  return (
    <div className="card profile-header-card">
      <div className="profile-cover"></div>

      <div className="profile-identity">
        {/* Clickable Avatar Wrapper */}
        <div className="profile-avatar-wrapper" onClick={onAvatarClick} title="Change Profile Picture">
          <img src={avatarSrc} alt="Profile" className="profile-avatar-img" />
          <div className="avatar-overlay">
            📷
          </div>
        </div>

        <div className="profile-info">
          <h2 className="profile-name">{user.fullname}</h2>
          <p className="profile-role">{user.headline}</p>
          <div className="profile-meta">
            <span>📍 {user.location?.city && user.location?.country
              ? `${user.location.city}, ${user.location.country}`
              : "Add location"}</span>
            {user.openToWork && (
              <span className="badge-open">Open to Work</span>
            )}
          </div>
        </div>

        <div className="profile-actions">
          <button className={`btn-edit ${isEditing ? 'active' : ''}`} onClick={toggleEdit}>
            {isEditing ? "Cancel" : "Edit Profile"}
          </button>
        </div>
      </div>
    </div>
  );
}