import { useEffect, useState } from "react";

import { api, API_BASE_URL } from "../services/api";

// Placeholder dashboard. For now it only checks that the backend is reachable.
function Dashboard() {
  // "checking" -> "online" or "offline"
  const [status, setStatus] = useState("checking");
  const [message, setMessage] = useState("");

  useEffect(() => {
    api
      .get("/")
      .then((data) => {
        setStatus("online");
        setMessage(data.message);
      })
      .catch((error) => {
        setStatus("offline");
        setMessage(error.message);
      });
  }, []);

  const badgeClass = {
    checking: "text-bg-secondary",
    online: "text-bg-success",
    offline: "text-bg-danger",
  }[status];

  return (
    <>
      <h1 className="h3 mb-3">Dashboard</h1>
      <p className="text-body-secondary">
        Your learning and career overview will appear here.
      </p>

      <div className="card">
        <div className="card-body">
          <h2 className="h6 card-title">
            Backend <span className={`badge ${badgeClass}`}>{status}</span>
          </h2>
          <p className="card-text small mb-0">
            <code>{API_BASE_URL}</code>
            {message && <> &middot; {message}</>}
          </p>
        </div>
      </div>
    </>
  );
}

export default Dashboard;
