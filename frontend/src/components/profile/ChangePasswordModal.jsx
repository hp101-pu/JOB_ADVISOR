import React, { useState } from "react";
import { changePassword } from "../../utils/api";
import "../../styles/profile.css";

export default function ChangePasswordModal({ onClose }) {
  const [passwords, setPasswords] = useState({
    current: "",
    new: "",
    confirm: ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  });

  const handleChange = (e) => {
    setPasswords({ ...passwords, [e.target.name]: e.target.value });
    setError(""); // Clear error when user types
  };

  const togglePasswordVisibility = (field) => {
    setShowPasswords({
      ...showPasswords,
      [field]: !showPasswords[field]
    });
  };

  const validateForm = () => {
    if (!passwords.current || !passwords.new || !passwords.confirm) {
      setError("All fields are required");
      return false;
    }

    if (passwords.new.length < 6) {
      setError("New password must be at least 6 characters long");
      return false;
    }

    if (passwords.new !== passwords.confirm) {
      setError("New passwords do not match");
      return false;
    }

    if (passwords.current === passwords.new) {
      setError("New password must be different from current password");
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setLoading(true);
    setError("");

    try {
      const response = await changePassword(passwords.current, passwords.new);
      
      if (response.success) {
        alert(response.message || "Password changed successfully!");
        onClose();
      }
    } catch (err) {
      setError(err.message || "Failed to change password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="card modal-card">
        <div className="modal-header">
          <h3>Change Password</h3>
          <button onClick={onClose} className="close-btn">×</button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          {/* Current Password */}
          <div className="form-group">
            <label>Current Password</label>
            <div style={{ position: 'relative' }}>
              <input 
                type={showPasswords.current ? "text" : "password"}
                name="current" 
                className="form-input" 
                value={passwords.current}
                onChange={handleChange}
                disabled={loading}
                required 
              />
              <button
                type="button"
                onClick={() => togglePasswordVisibility('current')}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '18px'
                }}
              >
                {showPasswords.current ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
          </div>
          
          {/* New Password */}
          <div className="form-group">
            <label>New Password</label>
            <div style={{ position: 'relative' }}>
              <input 
                type={showPasswords.new ? "text" : "password"}
                name="new" 
                className="form-input" 
                value={passwords.new}
                onChange={handleChange}
                disabled={loading}
                required 
              />
              <button
                type="button"
                onClick={() => togglePasswordVisibility('new')}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '18px'
                }}
              >
                {showPasswords.new ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
            <small style={{ color: '#666', fontSize: '12px' }}>
              Minimum 6 characters
            </small>
          </div>

          {/* Confirm New Password */}
          <div className="form-group">
            <label>Confirm New Password</label>
            <div style={{ position: 'relative' }}>
              <input 
                type={showPasswords.confirm ? "text" : "password"}
                name="confirm" 
                className="form-input" 
                value={passwords.confirm}
                onChange={handleChange}
                disabled={loading}
                required 
              />
              <button
                type="button"
                onClick={() => togglePasswordVisibility('confirm')}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '18px'
                }}
              >
                {showPasswords.confirm ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div style={{
              padding: '10px',
              backgroundColor: '#fee',
              border: '1px solid #fcc',
              borderRadius: '4px',
              color: '#c00',
              marginBottom: '15px'
            }}>
              {error}
            </div>
          )}

          <div className="modal-actions">
            <button 
              type="button" 
              onClick={onClose} 
              className="btn-social"
              disabled={loading}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="btn-primary"
              disabled={loading}
            >
              {loading ? "Updating..." : "Update Password"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}