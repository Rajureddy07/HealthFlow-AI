import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

interface Extraction {
  medicine_name: string | null;
  active_ingredients: string[];
  strength: {
    value: string | null;
  } | null;
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

function App() {
  const [data, setData] = useState<ReviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
  const loadDocument = async () => {
    console.log("Starting request...");

    try {
      const response = await axios.get(
        "http://127.0.0.1:8000/api/documents/2/review"
      );

      console.log("Response received:");
      console.log(response.data);

      setData(response.data);

    } catch (error) {
      console.error("API ERROR:", error);
      setError("Failed to load document.");

    } finally {
      console.log("Request finished");
      setLoading(false);
    }
  };

  loadDocument();
}, []);

  if (loading) {
    return (
      <div className="loading">
        Loading document...
      </div>
    );
  }

  if (error) {
    return (
      <div className="loading error">
        {error}
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const extraction = data.extraction;

  const getEvidence = (fieldName: string) => {
    return data.evidence?.fields.find(
      (field) => field.field === fieldName
    );
  };

  const medicineEvidence = getEvidence("medicine_name");
  const strengthEvidence = getEvidence("strength");
  const dosageEvidence = getEvidence("dosage_form");
  const quantityEvidence = getEvidence("quantity");

  return (
    <div className="app">

      <header className="header">

        <div className="logo">
          HealthFlow <span>AI</span>
        </div>

        <nav>
          <button>Dashboard</button>
          <button>Documents</button>
          <button>Review Queue</button>
        </nav>

        <div className="user">
          Admin
        </div>

      </header>

      <main className="main">

        <div className="page-header">

          <div>
            <h1>Human Review</h1>

            <p>
              Document #{data.document_id} ·{" "}
              {data.file_name}
            </p>
          </div>

          <div className="status-badge">
            {data.status.replace("_", " ")}
          </div>

        </div>

        <section className="review-layout">

          {/* SOURCE DOCUMENT */}

          <div className="document-panel">

            <h2>Source Document</h2>

            <div className="document-preview">

              <img
                src={`http://127.0.0.1:8000/uploads/${encodeURIComponent(
                  data.file_name
                )}`}
                alt={data.file_name}
              />

            </div>

          </div>


          {/* EXTRACTION */}

          <div className="extraction-panel">

            <h2>Extracted Information</h2>

            {/* MEDICINE */}

            <div className="field">

              <label>
                Medicine Name
              </label>

              <div
                className={`field-value ${
                  medicineEvidence?.status === "LOW"
                    ? "warning"
                    : ""
                }`}
              >
                {extraction?.medicine_name ||
                  "Not extracted"}
              </div>

              <div
                className={`confidence ${
                  medicineEvidence?.status === "HIGH"
                    ? "high"
                    : "low"
                }`}
              >
                {medicineEvidence
                  ? `${medicineEvidence.status} CONFIDENCE · ${(
                      medicineEvidence.confidence * 100
                    ).toFixed(2)}%`
                  : "NO EVIDENCE"}
              </div>

            </div>


            {/* STRENGTH */}

            <div className="field">

              <label>
                Strength
              </label>

              <div className="field-value">

                {extraction?.strength?.value ||
                  "Not extracted"}

              </div>

              <div
                className={`confidence ${
                  strengthEvidence?.status === "HIGH"
                    ? "high"
                    : "low"
                }`}
              >
                {strengthEvidence
                  ? `${strengthEvidence.status} CONFIDENCE · ${(
                      strengthEvidence.confidence * 100
                    ).toFixed(2)}%`
                  : "NO EVIDENCE"}
              </div>

            </div>


            {/* DOSAGE FORM */}

            <div className="field">

              <label>
                Dosage Form
              </label>

              <div className="field-value">

                {extraction?.dosage_form ||
                  "Not extracted"}

              </div>

              <div
                className={`confidence ${
                  dosageEvidence?.status === "HIGH"
                    ? "high"
                    : "low"
                }`}
              >
                {dosageEvidence
                  ? `${dosageEvidence.status} CONFIDENCE · ${(
                      dosageEvidence.confidence * 100
                    ).toFixed(2)}%`
                  : "NO EVIDENCE"}
              </div>

            </div>


            {/* QUANTITY */}

            <div className="field">

              <label>
                Quantity
              </label>

              <div className="field-value missing">

                {extraction?.quantity ??
                  "Not extracted"}

              </div>

              {quantityEvidence && (
                <div className="confidence low">

                  {quantityEvidence.status} CONFIDENCE ·{" "}
                  {(
                    quantityEvidence.confidence * 100
                  ).toFixed(2)}
                  %

                </div>
              )}

            </div>


            {/* VALIDATION */}

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


            {/* ACTIONS */}

            <div className="actions">

              <button className="approve">
                Approve
              </button>

              <button className="send-back">
                Send Back
              </button>

            </div>

          </div>

        </section>

      </main>

    </div>
  );
}

export default App;