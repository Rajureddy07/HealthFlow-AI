import { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

// ==================================================
// Types
// ==================================================

interface ReviewQueueDocument {
  document_id: number;
  file_name: string;
  document_type: string;
  status: string;
  review_status: string;
  created_at: string;
}

interface ReviewQueueResponse {
  count: number;
  documents: ReviewQueueDocument[];
}

// ==================================================
// Review Queue
// ==================================================

function ReviewQueue() {
  const [documents, setDocuments] =
    useState<ReviewQueueDocument[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  // ==================================================
  // Load Queue
  // ==================================================

  const loadReviewQueue = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await axios.get<ReviewQueueResponse>(
          `${API_URL}/api/documents/review-queue`
        );

      setDocuments(
        response.data.documents
      );

    } catch (err) {
      console.error(err);

      setError(
        "Failed to load review queue."
      );

    } finally {
      setLoading(false);
    }
  };

  // ==================================================
  // Initial Load
  // ==================================================

  useEffect(() => {
    loadReviewQueue();
  }, []);

  // ==================================================
  // Open Review
  // ==================================================

  const openReview = (
    documentId: number
  ) => {
    window.location.href =
      `/review/${documentId}`;
  };

  // ==================================================
  // Dashboard
  // ==================================================

  const goToDashboard = () => {
    window.location.href = "/";
  };

  // ==================================================
  // Loading
  // ==================================================

  if (loading) {
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

          <div className="loading">
            Loading review queue...
          </div>

        </main>

      </div>
    );
  }

  // ==================================================
  // Error
  // ==================================================

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
            onClick={loadReviewQueue}
          >
            Try Again
          </button>

        </main>

      </div>
    );
  }

  // ==================================================
  // Render
  // ==================================================

  return (
    <div className="app">

      {/* ==========================================
          HEADER
      ========================================== */}

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
            onClick={() => {
              window.location.href =
                "/review-queue";
            }}
          >
            Review Queue
          </button>

        </nav>

        <div className="user">
          Admin
        </div>

      </header>

      {/* ==========================================
          MAIN
      ========================================== */}

      <main className="main">

        {/* ========================================
            PAGE HEADER
        ======================================== */}

        <div className="page-header">

          <div>

            <h1>
              Review Queue
            </h1>

            <p>
              Documents waiting for human review
            </p>

          </div>

          <div className="queue-count">

            <span>
              Pending
            </span>

            <strong>
              {documents.length}
            </strong>

          </div>

        </div>

        {/* ========================================
            EMPTY QUEUE
        ======================================== */}

        {documents.length === 0 ? (

          <div className="empty-queue">

            <div className="empty-queue-icon">
              ✓
            </div>

            <h2>
              No documents pending review
            </h2>

            <p>
              All documents have been reviewed.
            </p>

            <button
              className="queue-refresh-button"
              onClick={loadReviewQueue}
            >
              Refresh Queue
            </button>

          </div>

        ) : (

          /* ======================================
             QUEUE TABLE
          ====================================== */

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
                      Review Status
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

                        <td>
                          <strong>
                            #{document.document_id}
                          </strong>
                        </td>

                        <td>

                          <div className="queue-file-name">
                            {document.file_name}
                          </div>

                        </td>

                        <td>
                          {document.document_type}
                        </td>

                        <td>

                          <span className="queue-status ai">
                            {document.status.replaceAll(
                              "_",
                              " "
                            )}
                          </span>

                        </td>

                        <td>

                          <span className="queue-status pending">
                            {document.review_status.replaceAll(
                              "_",
                              " "
                            )}
                          </span>

                        </td>

                        <td>
                          {new Date(
                            document.created_at
                          ).toLocaleString()}
                        </td>

                        <td>

                          <button
                            className="review-button"
                            onClick={() =>
                              openReview(
                                document.document_id
                              )
                            }
                          >
                            Review →
                          </button>

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

export default ReviewQueue;