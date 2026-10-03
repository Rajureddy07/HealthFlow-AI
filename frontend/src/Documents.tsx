import { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

// ==================================================
// Types
// ==================================================

interface DocumentItem {
  document_id: number;
  file_name: string;
  document_type: string;
  status: string;
  review_status: string;
  created_at: string;
}

interface DocumentsResponse {
  count: number;
  documents: DocumentItem[];
}

// ==================================================
// Component
// ==================================================

function Documents() {
  // ==================================================
  // State
  // ==================================================

  const [documents, setDocuments] =
    useState<DocumentItem[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  // Stores the document ID currently being retried.
  // null = no retry operation running.
  const [actionLoading, setActionLoading] =
    useState<number | null>(null);

  // ==================================================
  // Load Documents
  // ==================================================

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await axios.get<DocumentsResponse>(
          `${API_URL}/api/documents/`
        );

      setDocuments(
        response.data.documents
      );

    } catch (err: any) {
      console.error(
        "Failed to load documents:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Failed to load documents."
      );

    } finally {
      setLoading(false);
    }
  };

  // ==================================================
  // Initial Load
  // ==================================================

  useEffect(() => {
    loadDocuments();
  }, []);

  // ==================================================
  // Navigation
  // ==================================================

  const goToDashboard = () => {
    window.location.href = "/";
  };

  const goToReviewQueue = () => {
    window.location.href =
      "/review-queue";
  };

  const goToAuditLogs = () => {
    window.location.href =
      "/audit-logs";
  };

  // ==================================================
  // Open Document
  // ==================================================

  const openDocument = (
    documentId: number
  ) => {
    window.location.href =
      `/review/${documentId}`;
  };

  // ==================================================
  // Retry Failed Document
  // ==================================================

  const retryDocument = async (
    documentId: number
  ) => {
    // Prevent duplicate retry requests.
    if (actionLoading !== null) {
      return;
    }

    try {
      setActionLoading(documentId);
      setError("");

      await axios.post(
        `${API_URL}/api/documents/${documentId}/retry`
      );

      // Reload the document list so the status
      // changes from PROCESSING_FAILED → QUEUED.
      await loadDocuments();

    } catch (err: any) {
      console.error(
        "Failed to retry document:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Failed to retry document."
      );

    } finally {
      setActionLoading(null);
    }
  };

  // ==================================================
  // Format Date
  // ==================================================

  const formatDate = (
    date: string
  ) => {
    return new Date(
      date
    ).toLocaleString();
  };

  // ==================================================
  // AI Status Class
  // ==================================================

  const getStatusClass = (
    status: string
  ) => {
    switch (status) {

      case "APPROVED":
        return "document-status approved";

      case "NEEDS_REVIEW":
        return "document-status needs-review";

      case "PROCESSING":
        return "document-status processing";

      case "QUEUED":
        return "document-status queued";

      case "PROCESSING_FAILED":
        return "document-status failed";

      default:
        return "document-status";
    }
  };

  // ==================================================
  // Human Review Class
  // ==================================================

  const getReviewClass = (
    status: string
  ) => {
    switch (status) {

      case "PENDING":
        return "document-review pending";

      case "APPROVED":
        return "document-review approved";

      case "SENT_BACK":
        return "document-review sent-back";

      default:
        return "document-review not-required";
    }
  };

  // ==================================================
  // Loading Screen
  // ==================================================

  if (loading) {
    return (
      <div className="app">

        <header className="header">

          <div className="logo">
            HealthFlow <span>AI</span>
          </div>

          <nav>

            <button
              onClick={goToDashboard}
            >
              Dashboard
            </button>

            <button className="active-nav">
              Documents
            </button>

            <button
              onClick={goToReviewQueue}
            >
              Review Queue
            </button>

            <button
              onClick={goToAuditLogs}
            >
              Audit Logs
            </button>

          </nav>

          <div className="user">
            Admin
          </div>

        </header>

        <main className="main">

          <div className="loading">
            Loading documents...
          </div>

        </main>

      </div>
    );
  }

  // ==================================================
  // Error Screen
  // ==================================================

  if (error && documents.length === 0) {
    return (
      <div className="app">

        <header className="header">

          <div className="logo">
            HealthFlow <span>AI</span>
          </div>

          <nav>

            <button
              onClick={goToDashboard}
            >
              Dashboard
            </button>

            <button className="active-nav">
              Documents
            </button>

            <button
              onClick={goToReviewQueue}
            >
              Review Queue
            </button>

            <button
              onClick={goToAuditLogs}
            >
              Audit Logs
            </button>

          </nav>

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
            onClick={loadDocuments}
          >
            Try Again
          </button>

        </main>

      </div>
    );
  }

  // ==================================================
  // Main Page
  // ==================================================

  return (
    <div className="app">

      {/* ============================================
          HEADER
      ============================================ */}

      <header className="header">

        <div className="logo">
          HealthFlow <span>AI</span>
        </div>

        <nav>

          <button
            onClick={goToDashboard}
          >
            Dashboard
          </button>

          <button
            className="active-nav"
          >
            Documents
          </button>

          <button
            onClick={goToReviewQueue}
          >
            Review Queue
          </button>

          <button
            onClick={goToAuditLogs}
          >
            Audit Logs
          </button>

        </nav>

        <div className="user">
          Admin
        </div>

      </header>

      {/* ============================================
          MAIN
      ============================================ */}

      <main className="main">

        {/* ==========================================
            PAGE HEADER
        ========================================== */}

        <div className="page-header">

          <div>

            <h1>
              Documents
            </h1>

            <p>
              Monitor document processing
              and workflow status
            </p>

          </div>

          <div className="queue-count">

            <span>
              Total Documents
            </span>

            <strong>
              {documents.length}
            </strong>

          </div>

        </div>

        {/* ==========================================
            ERROR MESSAGE
        ========================================== */}

        {error && (
          <div className="message error-message">
            {error}
          </div>
        )}

        {/* ==========================================
            EMPTY STATE
        ========================================== */}

        {documents.length === 0 ? (

          <div className="empty-queue">

            <div className="empty-queue-icon">
              ✓
            </div>

            <h2>
              No documents
            </h2>

            <p>
              No documents have been
              uploaded yet.
            </p>

            <button
              className="queue-refresh-button"
              onClick={loadDocuments}
            >
              Refresh
            </button>

          </div>

        ) : (

          /* ========================================
             DOCUMENT TABLE
          ======================================== */

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
                      Type
                    </th>

                    <th>
                      AI Status
                    </th>

                    <th>
                      Human Review
                    </th>

                    <th>
                      Created
                    </th>

                    <th>
                      Action
                    </th>

                  </tr>

                </thead>

                <tbody>

                  {documents.map(
                    (document) => (

                      <tr
                        key={
                          document.document_id
                        }
                      >

                        {/* ID */}

                        <td>

                          <strong>
                            #{document.document_id}
                          </strong>

                        </td>

                        {/* FILE NAME */}

                        <td>

                          <div
                            className="queue-file-name"
                            title={
                              document.file_name
                            }
                          >
                            {document.file_name}
                          </div>

                        </td>

                        {/* TYPE */}

                        <td>
                          {document.document_type}
                        </td>

                        {/* AI STATUS */}

                        <td>

                          <span
                            className={getStatusClass(
                              document.status
                            )}
                          >
                            {document.status.replaceAll(
                              "_",
                              " "
                            )}
                          </span>

                        </td>

                        {/* HUMAN REVIEW */}

                        <td>

                          <span
                            className={getReviewClass(
                              document.review_status
                            )}
                          >
                            {document.review_status.replaceAll(
                              "_",
                              " "
                            )}
                          </span>

                        </td>

                        {/* CREATED */}

                        <td>
                          {formatDate(
                            document.created_at
                          )}
                        </td>

                        {/* ACTIONS */}

                        <td>

                          <div className="document-actions">

                            {/* View */}

                            <button
                              className="review-button"
                              onClick={() =>
                                openDocument(
                                  document.document_id
                                )
                              }
                            >
                              View →
                            </button>

                            {/* Retry */}

                            {document.status ===
                              "PROCESSING_FAILED" && (

                              <button
                                className="retry-button"
                                onClick={() =>
                                  retryDocument(
                                    document.document_id
                                  )
                                }
                                disabled={
                                  actionLoading !==
                                    null
                                }
                              >
                                {actionLoading ===
                                document.document_id
                                  ? "Retrying..."
                                  : "Retry"}
                              </button>

                            )}

                          </div>

                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          </div>

        )}

      </main>

    </div>
  );
}

export default Documents;