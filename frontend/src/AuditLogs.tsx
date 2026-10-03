import { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

interface AuditLog {
  id: number;
  document_id: number;
  action: string;
  reviewer: string;
  comment: string | null;
  created_at: string;
}

interface AuditLogsResponse {
  count: number;
  logs: AuditLog[];
}

function AuditLogs() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadAuditLogs = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await axios.get<AuditLogsResponse>(
          `${API_URL}/api/documents/audit-logs`
        );

      setLogs(response.data.logs);
    } catch (err) {
      console.error(err);
      setError("Failed to load audit logs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, []);

  const goToDashboard = () => {
    window.location.href = "/";
  };

  const goToReviewQueue = () => {
    window.location.href = "/review-queue";
  };

  const goToAuditLogs = () => {
    window.location.href = "/audit-logs";
  };

  const openDocument = (documentId: number) => {
    window.location.href = `/review/${documentId}`;
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleString();
  };

  const getActionClass = (action: string) => {
    switch (action) {
      case "APPROVED":
        return "audit-action approved";

      case "CORRECTED":
        return "audit-action corrected";

      case "SENT_BACK":
        return "audit-action sent-back";

      case "RETRIED":
        return "audit-action retried";

      default:
        return "audit-action";
    }
  };

  if (loading) {
    return (
      <div className="app">

        <header className="header">

          <div className="logo">
            HealthFlow <span>AI</span>
          </div>

          <nav>
            <button onClick={goToDashboard}>
              Dashboard
            </button>

            <button>
              Documents
            </button>

            <button onClick={goToReviewQueue}>
              Review Queue
            </button>

            <button onClick={goToAuditLogs}>
              Audit Logs
            </button>
          </nav>

          <div className="user">
            Admin
          </div>

        </header>

        <main className="main">

          <div className="loading">
            Loading audit logs...
          </div>

        </main>

      </div>
    );
  }

  if (error) {
    return (
      <div className="app">

        <header className="header">

          <div className="logo">
            HealthFlow <span>AI</span>
          </div>

          <div className="user">
            Admin
          </div>

        </header>

        <main className="main">

          <div className="message error-message">
            {error}
          </div>

          <button
            className="queue-retry-button"
            onClick={loadAuditLogs}
          >
            Try Again
          </button>

        </main>

      </div>
    );
  }

  return (
    <div className="app">

      {/* HEADER */}

      <header className="header">

        <div className="logo">
          HealthFlow <span>AI</span>
        </div>

        <nav>

          <button onClick={goToDashboard}>
            Dashboard
          </button>

          <button>
            Documents
          </button>

          <button onClick={goToReviewQueue}>
            Review Queue
          </button>

          <button
            className="active-nav"
            onClick={goToAuditLogs}
          >
            Audit Logs
          </button>

        </nav>

        <div className="user">
          Admin
        </div>

      </header>

      {/* MAIN */}

      <main className="main">

        {/* PAGE HEADER */}

        <div className="page-header">

          <div>

            <h1>
              Audit Logs
            </h1>

            <p>
              Complete history of human review actions
            </p>

          </div>

          <div className="queue-count">

            <span>
              Total Events
            </span>

            <strong>
              {logs.length}
            </strong>

          </div>

        </div>

        {/* EMPTY STATE */}

        {logs.length === 0 ? (

          <div className="empty-queue">

            <div className="empty-queue-icon">
              ✓
            </div>

            <h2>
              No audit events
            </h2>

            <p>
              No review actions have been recorded yet.
            </p>

            <button
              className="queue-refresh-button"
              onClick={loadAuditLogs}
            >
              Refresh Logs
            </button>

          </div>

        ) : (

          /* AUDIT TABLE */

          <div className="queue-card">

            <div className="queue-table-wrapper">

              <table className="queue-table">

                <thead>

                  <tr>

                    <th>
                      ID
                    </th>

                    <th>
                      Document
                    </th>

                    <th>
                      Action
                    </th>

                    <th>
                      Reviewer
                    </th>

                    <th>
                      Comment
                    </th>

                    <th>
                      Date & Time
                    </th>

                  </tr>

                </thead>

                <tbody>

                  {logs.map((log) => (

                    <tr key={log.id}>

                      <td>
                        <strong>
                          #{log.id}
                        </strong>
                      </td>

                      <td>

                        <button
                          className="document-link"
                          onClick={() =>
                            openDocument(
                              log.document_id
                            )
                          }
                        >
                          Document #{log.document_id}
                        </button>

                      </td>

                      <td>

                        <span
                          className={getActionClass(
                            log.action
                          )}
                        >
                          {log.action.replaceAll(
                            "_",
                            " "
                          )}
                        </span>

                      </td>

                      <td>
                        {log.reviewer}
                      </td>

                      <td>

                        <div className="audit-comment">
                          {log.comment || "—"}
                        </div>

                      </td>

                      <td>
                        {formatDate(
                          log.created_at
                        )}
                      </td>

                    </tr>

                  ))}

                </tbody>

              </table>

            </div>

          </div>

        )}

      </main>

    </div>
  );
}

export default AuditLogs;