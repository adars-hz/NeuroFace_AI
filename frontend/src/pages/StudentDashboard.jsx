
import { useEffect, useState } from "react";
import {
  Camera,
  ClipboardCheck,
  FileText,
  GraduationCap,
  Percent,
  LogOut,
  BookOpen,
  Upload,
  RefreshCw,
} from "lucide-react";
import { getMyAttendanceSummary, registerMyFace } from "../api";

export default function StudentDashboard({ user, onLogout }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

  async function loadSummary() {
    setLoading(true);
    setError("");

    try {
      const data = await getMyAttendanceSummary();
      setSummary(data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not load attendance. Check that the backend is running."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSummary();
  }, []);

  async function handleFaceUpload(event) {
    event.preventDefault();
    setUploadMessage("");

    if (!selectedFile) {
      setUploadMessage("Please choose a face image first.");
      return;
    }

    setUploading(true);

    try {
      const result = await registerMyFace(selectedFile);
      setUploadMessage(
        result.status
          ? `Image submitted. Registration status: ${result.status}`
          : "Face image submitted successfully."
      );
      setSelectedFile(null);
      event.target.reset();
    } catch (err) {
      setUploadMessage(
        err.response?.data?.detail || "Face registration failed."
      );
    } finally {
      setUploading(false);
    }
  }

  const subjects = summary?.subjects || [];

  return (
    <div className="dashboard-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon small">N</span>
          <span>NeuroFace</span>
        </div>

        <p className="sidebar-label">STUDENT WORKSPACE</p>
        <div className="sidebar-link active">
          <BookOpen size={19} /> Overview
        </div>
        <div className="sidebar-link">
          <Camera size={19} /> Face Registration
        </div>
        <div className="sidebar-link">
          <ClipboardCheck size={19} /> My Attendance
        </div>
        <div className="sidebar-link">
          <GraduationCap size={19} /> Exam Eligibility
        </div>

        <button className="logout-button" onClick={onLogout}>
          <LogOut size={18} /> Sign out
        </button>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">STUDENT WORKSPACE</p>
            <h1>Student Dashboard</h1>
            <p className="muted">
              Your attendance and facial registration overview.
            </p>
          </div>

          <div className="profile-chip">
            <div className="avatar">S</div>
            <div>
              <strong>{summary?.student_name || user?.username || "Student"}</strong>
              <span>{summary?.class_name || "Student account"}</span>
            </div>
          </div>
        </header>

        <section className="welcome-card">
          <div>
            <p className="welcome-label">YOUR ACADEMIC OVERVIEW</p>
            <h2>Welcome, {summary?.student_name || user?.username || "Student"}!</h2>
            <p>
              Review your attendance for each subject and keep your face
              registration up to date.
            </p>
          </div>
          <div className="welcome-symbol">
            <GraduationCap size={54} />
          </div>
        </section>

        <section className="attendance-reminder">
          <Percent size={25} />
          <div>
            <strong>Minimum attendance requirement: 85%</strong>
            <p>
              Eligibility shown here is based on the attendance summary
              returned by the backend.
            </p>
          </div>
        </section>

        <section className="section-heading">
          <div>
            <h2>Subject-wise Attendance</h2>
            <p className="muted">Your latest attendance summary.</p>
          </div>
          <button className="secondary-button" onClick={loadSummary} disabled={loading}>
            <RefreshCw size={15} /> Refresh
          </button>
        </section>

        {loading && <p className="muted">Loading attendance...</p>}
        {error && <div className="error-message">{error}</div>}

        {!loading && !error && subjects.length === 0 && (
          <div className="empty-card">
            No subject attendance data is available yet. Your class and subject
            assignments may need to be configured by the administrator.
          </div>
        )}

        {!loading && !error && subjects.length > 0 && (
          <section className="attendance-list">
            {subjects.map((subject) => (
              <article className="attendance-card" key={subject.subject_id}>
                <div className="attendance-card-header">
                  <div>
                    <span className="subject-code">
                      {subject.subject_code}
                    </span>
                    <h3>{subject.subject_name}</h3>
                  </div>
                  <span
                    className={`eligibility-pill ${
                      subject.exam_eligible ? "eligible" : "not-eligible"
                    }`}
                  >
                    {subject.eligibility_status ||
                      (subject.exam_eligible ? "Eligible" : "Not eligible")}
                  </span>
                </div>

                <div className="attendance-percentage">
                  {Number(subject.attendance_percentage || 0).toFixed(2)}%
                </div>

                <div className="progress-track">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${Math.min(
                        100,
                        Math.max(0, Number(subject.attendance_percentage || 0))
                      )}%`,
                    }}
                  />
                </div>

                <div className="attendance-stats">
                  <span>
                    Classes held: <strong>{subject.total_sessions ?? 0}</strong>
                  </span>
                  <span>
                    Present: <strong>{subject.present_sessions ?? 0}</strong>
                  </span>
                  <span>
                    Absent: <strong>{subject.absent_sessions ?? 0}</strong>
                  </span>
                </div>
              </article>
            ))}
          </section>
        )}

        <section className="section-heading">
          <div>
            <h2>Face Registration</h2>
            <p className="muted">
              Upload a clear image containing only your face.
            </p>
          </div>
        </section>

        <section className="upload-card">
          <div className="upload-icon">
            <Camera size={25} />
          </div>
          <div className="upload-content">
            <h3>Register your face</h3>
            <p>
              Use a clear, front-facing JPEG, PNG, or WEBP image. The system
              checks for a detectable face before saving the registration.
            </p>

            <form onSubmit={handleFaceUpload}>
              <label className="file-input-label" htmlFor="face-image">
                Select face image
              </label>
              <input
                id="face-image"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(event) =>
                  setSelectedFile(event.target.files?.[0] || null)
                }
              />

              {selectedFile && (
                <p className="muted">Selected: {selectedFile.name}</p>
              )}

              <button
                className="primary-button upload-button"
                type="submit"
                disabled={uploading}
              >
                <Upload size={16} />
                {uploading ? "Uploading..." : "Submit face image"}
              </button>
            </form>

            {uploadMessage && (
              <p className="upload-message">{uploadMessage}</p>
            )}
          </div>
        </section>

        <section className="module-grid student-shortcuts">
          <article className="module-card">
            <div className="module-icon">
              <FileText size={23} />
            </div>
            <h3>Leave Status</h3>
            <p>Leave request status will be connected here in a later step.</p>
            <span className="module-status">Coming next</span>
          </article>

          <article className="module-card">
            <div className="module-icon">
              <GraduationCap size={23} />
            </div>
            <h3>Exam Eligibility</h3>
            <p>Eligibility is displayed above for each available subject.</p>
            <span className="module-status">Attendance-based</span>
          </article>
        </section>
      </main>
    </div>
  );
}
