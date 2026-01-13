import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { getCurrentUser } from "../../utils/api";

export default function ProtectedRoute({ children }) {
  const [loading, setLoading] = useState(true);
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    getCurrentUser()
      .then((res) => {
        setAuthorized(res.success === true);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Checking authentication...</p>;

  if (!authorized) return <Navigate to="/auth" replace />;

  return children;
}
