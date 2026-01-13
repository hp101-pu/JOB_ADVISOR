import { useState, useEffect } from "react";
import { getCurrentUser } from "../utils/api";

export function useCurrentUser() {
  const [fullName, setFullName] = useState("");

  useEffect(() => {
    getCurrentUser()
      .then((res) => setFullName(res?.user?.fullname || ""))
      .catch(() => {});
  }, []);

  return fullName;
}
