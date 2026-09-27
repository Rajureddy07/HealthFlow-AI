import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";
import ReviewQueue from "./ReviewQueue";

const API_URL = "http://127.0.0.1:8000";

// ==================================================
// Types
// ==================================================

interface Strength {
  value: string | null;
}

interface Extraction {
  medicine_name: string | null;
  active_ingredients: string[];
  strength: Strength | null;
  dosage_form: string | null;
  quantity: string | number | null;
  instructions: string | null;
  frequency: string | null;
}

interface EvidenceField {
  field: string;
  value: string | null;
  evidence: string[];
  confidence: number;
  status: string;
}

interface ValidationIssue {
  field: string;
  message: string;
  severity: string;
}

interface ReviewData {
  document_id: number;
  file_name: string;
  status: string;
  review_status: string;
  stage: string;

  extraction: Extraction | null;

  evidence: {
    fields: EvidenceField[];
  } | null;

  validation: {
    status: string;
    confidence: number;
    issues: ValidationIssue[];
  } | null;
}

interface ReviewActionResponse {
  message: string;
  document_id: number;
  status: string;
  review_status: string;
  extraction?: Extraction;
  action: string;
  reviewer: string;
  comment: string | null;
  review_action_id: number | null;
}

// ==================================================
// Get document ID from URL
// ==================================================

function getDocumentIdFromUrl(): number {
  const match = window.location.pathname.match(
    /\/review\/(\d+)/
  );

  if (!match) {
    return 1;
  }

  return Number(match[1]);
}

// ==================================================
// App
// ==================================================

function App() {
  const documentId = getDocumentIdFromUrl();

  const isReviewQueuePage =
    window.location.pathname === "/review-queue";

  // ==================================================
  // Main data
  // ==================================================

  const [data, setData] =
    useState<ReviewData | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [actionLoading, setActionLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [successMessage, setSuccessMessage] =
    useState("");

  // ==================================================
  // Unsaved changes
  // ==================================================

  const [hasUnsavedChanges, setHasUnsavedChanges] =
    useState(false);

  // ==================================================
  // Editable fields
  // ==================================================

  const [medicineName, setMedicineName] =
    useState("");

  const [activeIngredients, setActiveIngredients] =
    useState("");

  const [strength, setStrength] =
    useState("");

  const [dosageForm, setDosageForm] =
    useState("");

  const [quantity, setQuantity] =
    useState("");

  const [instructions, setInstructions] =
    useState("");

  const [frequency, setFrequency] =
    useState("");

  // ==================================================
  // Reviewer comment
  // ==================================================

  const [comment, setComment] =
    useState("");

  // ==================================================
  // Load document
  // ==================================================

  useEffect(() => {
    const loadDocument = async () => {

      // IMPORTANT:
      // Review Queue has its own API and does not
      // need to load document #1.
      if (isReviewQueuePage) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError("");
        setSuccessMessage("");
        setHasUnsavedChanges(false);

        const response =
          await axios.get<ReviewData>(
            `${API_URL}/api/documents/${documentId}/review`
          );

        const reviewData = response.data;

        setData(reviewData);

        const extraction =
          reviewData.extraction;

        setMedicineName(
          extraction?.medicine_name ?? ""
        );

        setActiveIngredients(
          extraction?.active_ingredients?.join(", ") ?? ""
        );

        setStrength(
          extraction?.strength?.value ?? ""
        );

        setDosageForm(
          extraction?.dosage_form ?? ""
        );

        setQuantity(
          extraction?.quantity?.toString() ?? ""
        );

        setInstructions(
          extraction?.instructions ?? ""
        );

        setFrequency(
          extraction?.frequency ?? ""
        );

        setComment("");

      } catch (err) {
        console.error(err);

        setError(
          "Failed to load document."
        );

      } finally {
        setLoading(false);
      }
    };

    loadDocument();

  }, [documentId, isReviewQueuePage]);

  // ==================================================
  // Get evidence
  // ==================================================

  const getEvidence = (
    fieldName: string
  ) => {
    return data?.evidence?.fields.find(
      (field) =>
        field.field === fieldName
    );
  };

  // ==================================================
  // Build extraction
  // ==================================================

  const buildExtraction = (): Extraction => {
    return {
      medicine_name:
        medicineName.trim() || null,

      active_ingredients:
        activeIngredients
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),

      strength: {
        value:
          strength.trim() || null
      },

      dosage_form:
        dosageForm.trim() || null,

      quantity:
        quantity.trim() || null,

      instructions:
        instructions.trim() || null,

      frequency:
        frequency.trim() || null
    };
  };

  // ==================================================
  // Save Correction
  // ==================================================

  const saveCorrection = async () => {
    if (!data) {
      return;
    }

    if (!hasUnsavedChanges) {
      return;
    }

    if (actionLoading) {
      return;
    }

    try {
      setActionLoading(true);
      setError("");
      setSuccessMessage("");

      const response =
        await axios.put<ReviewActionResponse>(
          `${API_URL}/api/documents/${data.document_id}/extraction`,
          {
            reviewer: "admin",

            comment:
              comment.trim() ||
              "Corrected extracted information after reviewing the source document.",

            extraction:
              buildExtraction()
          }
        );

      setData((previous) => {
        if (!previous) {
          return previous;
        }

        return {
          ...previous,

          extraction:
            response.data.extraction ??
            previous.extraction,

          review_status:
            response.data.review_status
        };
      });

      setHasUnsavedChanges(false);

      setSuccessMessage(
        response.data.action === "NO_CHANGE"
          ? "No extraction changes detected."
          : "Extraction correction saved successfully."
      );

    } catch (err: any) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
        "Failed to save correction."
      );

    } finally {
      setActionLoading(false);
    }
  };

  // ==================================================
  // Approve Document
  // ==================================================

  const approveDocument = async () => {
    if (!data) {
      return;
    }

    if (actionLoading) {
      return;
    }

    if (hasUnsavedChanges) {
      setError(
        "Please save your extraction correction before approving the document."
      );

      return;
    }

    try {
      setActionLoading(true);
      setError("");
      setSuccessMessage("");

      const response =
        await axios.post<ReviewActionResponse>(
          `${API_URL}/api/documents/${data.document_id}/approve`,
          {
            reviewer: "admin",

            comment:
              comment.trim() ||
              "Reviewed extracted information against source document."
          }
        );

      setData((previous) => {
        if (!previous) {
          return previous;
        }

        return {
          ...previous,

          review_status:
            response.data.review_status
        };
      });

      setSuccessMessage(
        "Document approved successfully."
      );

      setComment("");
      setHasUnsavedChanges(false);

    } catch (err: any) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
        "Failed to approve document."
      );

    } finally {
      setActionLoading(false);
    }
  };

  // ==================================================
  // Send Back
  // ==================================================

  const sendBackDocument = async () => {
    if (!data) {
      return;
    }

    if (actionLoading) {
      return;
    }

    if (!comment.trim()) {
      setError(
        "Please enter a comment before sending the document back."
      );

      return;
    }

    if (hasUnsavedChanges) {
      setError(
        "Please save your extraction correction before sending the document back."
      );

      return;
    }

    try {
      setActionLoading(true);
      setError("");
      setSuccessMessage("");

      const response =
        await axios.post<ReviewActionResponse>(
          `${API_URL}/api/documents/${data.document_id}/send-back`,
          {
            reviewer: "admin",
            comment: comment.trim()
          }
        );

      setData((previous) => {
        if (!previous) {
          return previous;
        }

        return {
          ...previous,

          review_status:
            response.data.review_status
        };
      });

      setSuccessMessage(
        "Document sent back successfully."
      );

      setComment("");
      setHasUnsavedChanges(false);

    } catch (err: any) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
        "Failed to send document back."
      );

    } finally {
      setActionLoading(false);
    }
  };

  // ==================================================
  // Review Queue Page
  // ==================================================

  if (isReviewQueuePage) {
    return <ReviewQueue />;
  }

  // ==================================================
  // Loading
  // ==================================================

  if (loading) {
    return (
      <div className="loading">
        Loading document...
      </div>
    );
  }

  // ==================================================
  // Error
  // ==================================================

  if (error && !data) {
    return (
      <div className="loading error">
        {error}
      </div>
    );
  }

  if (!data) {
    return null;
  }

  // ==================================================
  // Evidence
  // ==================================================

  const medicineEvidence =
    getEvidence("medicine_name");

  const strengthEvidence =
    getEvidence("strength");

  const dosageEvidence =
    getEvidence("dosage_form");

  const quantityEvidence =
    getEvidence("quantity");

  // ==================================================
  // Review state
  // ==================================================

  const isPending =
    data.review_status === "PENDING";

  // ==================================================
  // Render Human Review
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
            onClick={() => {
              window.location.href = "/";
            }}
          >
            Dashboard
          </button>

          <button>
            Documents
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
              Human Review
            </h1>

            <p>
              Document #{data.document_id}
              {" · "}
              {data.file_name}
            </p>

          </div>

          <div className="status-container">

            <div className="status-label">
              AI Status
            </div>

            <div className="status-badge">
              {data.status.replaceAll(
                "_",
                " "
              )}
            </div>

            <div className="status-label review-label">
              Human Review
            </div>

            <div
              className={`review-status-badge ${
                data.review_status.toLowerCase()
              }`}
            >
              {data.review_status.replaceAll(
                "_",
                " "
              )}
            </div>

          </div>

        </div>

        {/* ========================================
            MESSAGES
        ======================================== */}

        {error && (
          <div className="message error-message">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="message success-message">
            {successMessage}
          </div>
        )}

        {/* ========================================
            REVIEW LAYOUT
        ======================================== */}

        <section className="review-layout">

          {/* ======================================
              SOURCE DOCUMENT
          ====================================== */}

          <div className="document-panel">

            <h2>
              Source Document
            </h2>

            <div className="document-preview">

              <img
                src={`${API_URL}/uploads/${encodeURIComponent(
                  data.file_name
                )}`}
                alt={data.file_name}
              />

            </div>

          </div>

          {/* ======================================
              EXTRACTION PANEL
          ====================================== */}

          <div className="extraction-panel">

            <h2>
              Extracted Information
            </h2>

            {/* Medicine Name */}

            <div className="field">

              <label>
                Medicine Name
              </label>

              <input
                className="editable-field"
                value={medicineName}
                disabled={
                  !isPending ||
                  actionLoading
                }
                onChange={(event) => {
                  setMedicineName(
                    event.target.value
                  );

                  setHasUnsavedChanges(true);
                }}
              />

              <div
                className={`confidence ${
                  medicineEvidence?.status === "HIGH"
                    ? "high"
                    : "low"
                }`}
              >
                {medicineEvidence
                  ? `${medicineEvidence.status} CONFIDENCE · ${(medicineEvidence.confidence * 100).toFixed(2)}%`
                  : "NO EVIDENCE"}
              </div>

            </div>

            {/* Active Ingredients */}

            <div className="field">

              <label>
                Active Ingredients
              </label>

              <input
                className="editable-field"
                value={activeIngredients}
                disabled={
                  !isPending ||
                  actionLoading
                }
                onChange={(event) => {
                  setActiveIngredients(
                    event.target.value
                  );

                  setHasUnsavedChanges(true);
                }}
                placeholder="Separate multiple ingredients with commas"
              />

            </div>

            {/* Strength */}

            <div className="field">

              <label>
                Strength
              </label>

              <input
                className="editable-field"
                value={strength}
                disabled={
                  !isPending ||
                  actionLoading
                }
                onChange={(event) => {
                  setStrength(
                    event.target.value
                  );

                  setHasUnsavedChanges(true);
                }}
                placeholder="Example: 500 mg / 125 mg"
              />

              <div
                className={`confidence ${
                  strengthEvidence?.status === "HIGH"
                    ? "high"
                    : "low"
                }`}
              >
                {strengthEvidence
                  ? `${strengthEvidence.status} CONFIDENCE · ${(strengthEvidence.confidence * 100).toFixed(2)}%`
                  : "NO EVIDENCE"}
              </div>

            </div>

            {/* Dosage Form */}

            <div className="field">

              <label>
                Dosage Form
              </label>

              <input
                className="editable-field"
                value={dosageForm}
                disabled={
                  !isPending ||
                  actionLoading
                }
                onChange={(event) => {
                  setDosageForm(
                    event.target.value
                  );

                  setHasUnsavedChanges(true);
                }}
              />

              <div
                className={`confidence ${
                  dosageEvidence?.status === "HIGH"
                    ? "high"
                    : "low"
                }`}
              >
                {dosageEvidence
                  ? `${dosageEvidence.status} CONFIDENCE · ${(dosageEvidence.confidence * 100).toFixed(2)}%`
                  : "NO EVIDENCE"}
              </div>

            </div>

            {/* Quantity */}

            <div className="field">

              <label>
                Quantity
              </label>

              <input
                className="editable-field"
                value={quantity}
                disabled={
                  !isPending ||
                  actionLoading
                }
                onChange={(event) => {
                  setQuantity(
                    event.target.value
                  );

                  setHasUnsavedChanges(true);
                }}
                placeholder="Example: 10"
              />

              <div
                className={`confidence ${
                  quantityEvidence?.status === "HIGH"
                    ? "high"
                    : "low"
                }`}
              >
                {quantityEvidence
                  ? `${quantityEvidence.status} CONFIDENCE · ${(quantityEvidence.confidence * 100).toFixed(2)}%`
                  : "NO EVIDENCE"}
              </div>

            </div>

            {/* Instructions */}

            <div className="field">

              <label>
                Instructions
              </label>

              <textarea
                className="editable-field textarea-field"
                value={instructions}
                disabled={
                  !isPending ||
                  actionLoading
                }
                onChange={(event) => {
                  setInstructions(
                    event.target.value
                  );

                  setHasUnsavedChanges(true);
                }}
                rows={3}
              />

            </div>

            {/* Frequency */}

            <div className="field">

              <label>
                Frequency
              </label>

              <input
                className="editable-field"
                value={frequency}
                disabled={
                  !isPending ||
                  actionLoading
                }
                onChange={(event) => {
                  setFrequency(
                    event.target.value
                  );

                  setHasUnsavedChanges(true);
                }}
                placeholder="Example: Once daily"
              />

            </div>

            {/* Unsaved Changes */}

            {isPending &&
              hasUnsavedChanges && (
                <div className="message warning-message">
                  You have unsaved extraction changes.
                  Save them before approving or sending
                  the document back.
                </div>
              )}

            {/* Validation */}

            {data.validation &&
              data.validation.issues.length > 0 && (

              <div className="validation-box">

                <strong>
                  Validation Issues
                </strong>

                {data.validation.issues.map(
                  (issue, index) => (

                    <p key={index}>

                      <b>
                        {issue.severity}
                      </b>

                      {" — "}

                      {issue.message}

                    </p>

                  )
                )}

              </div>
            )}

            {/* Evidence */}

            {data.evidence && (

              <div className="evidence-section">

                <h3>
                  Evidence
                </h3>

                {data.evidence.fields.map(
                  (field) => (

                    <div
                      className="evidence-field"
                      key={field.field}
                    >

                      <div className="evidence-header">

                        <strong>
                          {field.field.replaceAll(
                            "_",
                            " "
                          )}
                        </strong>

                        <span>
                          {field.status}
                          {" · "}
                          {(field.confidence * 100).toFixed(2)}
                          %
                        </span>

                      </div>

                      {field.evidence.map(
                        (item, index) => (

                          <div
                            className="evidence-item"
                            key={index}
                          >
                            ✓ {item}
                          </div>

                        )
                      )}

                    </div>
                  )
                )}

              </div>
            )}

            {/* Save Correction */}

            {isPending && (

              <div className="correction-section">

                <button
                  className="save-correction"
                  onClick={saveCorrection}
                  disabled={
                    actionLoading ||
                    !hasUnsavedChanges
                  }
                >
                  {actionLoading
                    ? "Saving..."
                    : hasUnsavedChanges
                      ? "Save Correction"
                      : "No Changes to Save"}
                </button>

              </div>
            )}

            {/* Review Comment */}

            {isPending && (

              <div className="review-actions">

                <label>
                  Reviewer Comment
                </label>

                <textarea
                  value={comment}
                  disabled={actionLoading}
                  onChange={(event) =>
                    setComment(
                      event.target.value
                    )
                  }
                  placeholder="Enter review comment..."
                  rows={4}
                />

                {/* Action Buttons */}

                <div className="actions">

                  <button
                    className="approve"
                    onClick={approveDocument}
                    disabled={
                      actionLoading ||
                      hasUnsavedChanges
                    }
                  >
                    {actionLoading
                      ? "Processing..."
                      : "Approve"}
                  </button>

                  <button
                    className="send-back"
                    onClick={sendBackDocument}
                    disabled={
                      actionLoading ||
                      hasUnsavedChanges
                    }
                  >
                    {actionLoading
                      ? "Processing..."
                      : "Send Back"}
                  </button>

                </div>

              </div>
            )}

            {/* Completed Review */}

            {!isPending && (

              <div className="review-complete">

                Human review status:

                <strong>
                  {" "}
                  {data.review_status.replaceAll(
                    "_",
                    " "
                  )}
                </strong>

              </div>
            )}

          </div>

        </section>

      </main>

    </div>
  );
}

export default App;