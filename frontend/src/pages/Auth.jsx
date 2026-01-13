import React, { useState } from 'react';
import Login from '../components/auth/Login';
import Signin from '../components/auth/Signin';
import '../styles/auth.css';

export default function Auth() {
  const [isLoginView, setIsLoginView] = useState(true);

  return (
    <div className="auth-container">
      {/* Removed the Left Image Section.
         Now essentially a centered single-column layout.
      */}

      <div className="auth-right">
        {isLoginView ? (
          <Login onSwitchToSignup={() => setIsLoginView(false)} />
        ) : (
          <Signin onSwitchToLogin={() => setIsLoginView(true)} />
        )}
      </div>
    </div>
  );
}