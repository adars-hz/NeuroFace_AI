
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Camera,
  Play,
  Square,
  RefreshCw,
  ClipboardCheck,
  AlertCircle,
  CheckCircle2,
  Clock,
  VideoOff,
} from "lucide-react";
import api from "../api";
import "../App.css";

export default function TeacherAttendance() {
  const [assignments, setAssignments] = useState([]);
  const [selectedAssignment, setSelectedAssignment] = useState("");
  const [duration, setDuration] = useState("60");
  const [activeSession, setActiveSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [cameraStream, setCameraStream] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [processingFrame, setProcessingFrame] = useState(false);
  const [recognitionResult, setRecognitionResult] = useState(null);
  const [presentStudents, setPresentStudents] = useState([]);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const processingRef = useRef(false);
  const scanningRef = useRef(false);

  async function loadAssignments() {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/teacher-assignments/mine");
      const data = Array.isArray(response.data)
        ? response.data
        : response.data.items || [];

      setAssignments(data);

      setSelectedAssignment((previous) => {
        if (data.some((item) => String(item.id) === previous)) {
          return previous;
        }
        return data.length ? String(data[0].id) : "";
      });
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not load your assignments. Please sign in again if your session has expired."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAssignments();
  }, []);

  const stopCamera = useCallback(() => {
    scanningRef.current = false;
    setScanning(false);
    setCameraStream((stream) => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
      return null;
    });
  }, []);

  useEffect(() => {
    if (videoRef.current && cameraStream) {
      videoRef.current.srcObject = cameraStream;
      videoRef.current.play().catch(() => {
        setError("Could not start video playback. Please try again.");
      });
    }
  }, [cameraStream]);

  useEffect(() => {
    return () => {
      scanningRef.current = false;
      if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [cameraStream]);

  useEffect(() => {
    if (!activeSession?.expires_at) return;

    const expiryTime = new Date(activeSession.expires_at).getTime();

    if (!Number.isFinite(expiryTime)) return;

    const remaining = expiryTime - Date.now();

    if (remaining <= 0) {
      stopCamera();
      setActiveSession(null);
      setMessage("The attendance session has expired.");
      return;
    }

    const timeout = window.setTimeout(() => {
      stopCamera();
      setActiveSession(null);
      setMessage("The attendance session has expired. Camera scanning stopped.");
    }, remaining);

    return () => window.clearTimeout(timeout);
  }, [activeSession, stopCamera]);

  async function startSession() {
    if (!selectedAssignment) {
      setError("Select an assigned subject and class first.");
      return;
    }

    setWorking(true);
    setError("");
    setMessage("");
    setRecognitionResult(null);
    setPresentStudents([]);

    try {
      const response = await api.post("/attendance-sessions/", {
        assignment_id: Number(selectedAssignment),
        duration_minutes: Number(duration),
      });

      setActiveSession(response.data);
      setMessage("Attendance session started successfully.");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not start the session.");
    } finally {
      setWorking(false);
    }
  }

  async function closeSession() {
    if (!activeSession?.id) {
      setError("There is no session to close.");
      return;
    }

    setWorking(true);
    setError("");
    setMessage("");

    try {
      const response = await api.patch(
        `/attendance-sessions/${activeSession.id}/close`
      );

      stopCamera();
      setActiveSession(null);
      setMessage(
        response.data.status === "EXPIRED"
          ? "This session had already expired."
          : "Attendance session closed successfully."
      );
    } catch (err) {
      setError(err.response?.data?.detail || "Could not close the session.");
    } finally {
      setWorking(false);
    }
  }

  async function startCamera() {
    setError("");
    setMessage("");
    setRecognitionResult(null);

    if (!activeSession?.id) {
      setError("Start an attendance session before opening the camera.");
      return;
    }

    if (
      activeSession.expires_at &&
      new Date(activeSession.expires_at).getTime() <= Date.now()
    ) {
      setActiveSession(null);
      setError("This session has expired. Start a new session.");
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Camera access is unavailable. Use a supported browser over HTTPS or localhost.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: { ideal: 640 },
          height: { ideal: 480 },
        },
        audio: false,
      });

      setCameraStream(stream);
      scanningRef.current = true;
      setScanning(true);
      setMessage("Camera started. Keep one student's face clearly visible.");
    } catch (err) {
      setError(
        err.name === "NotAllowedError"
          ? "Camera permission was denied. Allow camera access in your browser."
          : "Could not open the camera. Check that it is connected and not being used by another app."
      );
    }
  }

  const processFrame = useCallback(async () => {
    if (
      !scanningRef.current ||
      processingRef.current ||
      !videoRef.current ||
      !canvasRef.current ||
      !activeSession?.id
    ) {
      return;
    }

    const video = videoRef.current;

    if (video.readyState < 2 || !video.videoWidth || !video.videoHeight) {
      return;
    }

    processingRef.current = true;
    setProcessingFrame(true);

    try {
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const context = canvas.getContext("2d");
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      const blob = await new Promise((resolve) => {
        canvas.toBlob(resolve, "image/jpeg", 0.85);
      });

      if (!blob || !scanningRef.current) return;

      const formData = new FormData();
      formData.append("file", blob, "classroom-frame.jpg");

      const response = await api.post(
        `/face-recognition/mark-attendance?session_id=${activeSession.id}`,
        formData
      );

      if (!scanningRef.current) return;

      const result = response.data;
      setRecognitionResult(result);

      if (result.marked && result.student_id != null) {
        setPresentStudents((previous) => {
          if (previous.some((student) => student.id === result.student_id)) {
            return previous;
          }

          return [
            {
              id: result.student_id,
              name: result.student_name || `Student ${result.student_id}`,
              time: new Date().toLocaleTimeString(),
            },
            ...previous,
          ];
        });
      }
    } catch (err) {
      if (!scanningRef.current) return;

      const detail = err.response?.data?.detail;

      if (err.response?.status === 409) {
        stopCamera();
        setActiveSession(null);
        setError(detail || "The session is no longer active. Camera scanning stopped.");
      } else {
        setRecognitionResult({
          marked: false,
          message: detail || "Could not process this frame. Retrying shortly.",
        });
      }
    } finally {
      processingRef.current = false;
      setProcessingFrame(false);
    }
  }, [activeSession, stopCamera]);

  useEffect(() => {
    if (!scanning || !cameraStream || !activeSession) return;

    const interval = window.setInterval(() => {
      processFrame();
    }, 2000);

    return () => window.clearInterval(interval);
  }, [scanning, cameraStream, activeSession, processFrame]);

  const selected = assignments.find(
    (item) => String(item.id) === String(selectedAssignment)
  );

  return (
    <main className="dashboard-main teacher-attendance-page">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">TEACHER WORKSPACE</p>
          <h1>Take Attendance</h1>
          <p className="muted">
            Select your assigned class and subject to manage attendance.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={loadAssignments}
          disabled={loading || working || Boolean(activeSession)}
        >
          <RefreshCw size={15} />
          Refresh assignments
        </button>
      </header>

      {error && (
        <div className="error-message attendance-message">
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {message && (
        <div className="success-message attendance-message">
          <CheckCircle2 size={18} />
          {message}
        </div>
      )}

      <section className="attendance-setup-card">
        <div className="module-icon">
          <ClipboardCheck size={24} />
        </div>

        <h2>Session setup</h2>
        <p className="muted">
          Only assignments associated with your teacher account are available.
        </p>

        {loading ? (
          <p className="muted">Loading assignments...</p>
        ) : assignments.length === 0 ? (
          <p className="muted">
            No assignments found. Ask the administrator to assign you a class
            and subject.
          </p>
        ) : (
          <>
            <label htmlFor="assignment-select">
              Assigned class and subject
            </label>
            <select
              id="assignment-select"
              value={selectedAssignment}
              onChange={(event) => setSelectedAssignment(event.target.value)}
              disabled={Boolean(activeSession) || working}
            >
              <option value="">Select an assignment</option>
              {assignments.map((assignment) => (
                <option key={assignment.id} value={assignment.id}>
                  {assignment.subject_name || `Subject ${assignment.subject_id}`}
                  {" — "}
                  {assignment.class_name || `Class ${assignment.class_id}`}
                </option>
              ))}
            </select>

            <label htmlFor="session-duration">Session duration</label>
            <select
              id="session-duration"
              value={duration}
              onChange={(event) => setDuration(event.target.value)}
              disabled={Boolean(activeSession) || working}
            >
              <option value="30">30 minutes</option>
              <option value="45">45 minutes</option>
              <option value="60">60 minutes</option>
              <option value="90">90 minutes</option>
              <option value="120">120 minutes</option>
              <option value="180">180 minutes</option>
            </select>

            {selected && (
              <div className="assignment-details">
                <span>
                  Subject:{" "}
                  <strong>{selected.subject_name || selected.subject_id}</strong>
                </span>
                <span>
                  Class:{" "}
                  <strong>{selected.class_name || selected.class_id}</strong>
                </span>
              </div>
            )}
          </>
        )}

        {!activeSession ? (
          <button
            type="button"
            className="primary-button session-button"
            onClick={startSession}
            disabled={
              working || loading || !selectedAssignment || !assignments.length
            }
          >
            <Play size={17} />
            {working ? "Starting..." : "Start attendance session"}
          </button>
        ) : (
          <button
            type="button"
            className="danger-button session-button"
            onClick={closeSession}
            disabled={working}
          >
            <Square size={16} />
            {working ? "Closing..." : "Close attendance session"}
          </button>
        )}
      </section>

      <section className="attendance-setup-card session-status-card">
        <div className="module-icon">
          <Camera size={24} />
        </div>

        <h2>Live recognition</h2>

        {activeSession ? (
          <>
            <div className="session-status active-status">
              <span className="status-dot" />
              Session active
            </div>

            <p className="muted">Session ID: {activeSession.id}</p>
            <p className="muted">
              Expires at: {new Date(activeSession.expires_at).toLocaleString()}
            </p>

            <div style={{ marginTop: 16 }}>
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                aria-label="Classroom face recognition camera"
                style={{
                  display: cameraStream ? "block" : "none",
                  width: "100%",
                  maxWidth: 640,
                  borderRadius: 12,
                  background: "#111",
                }}
              />

              <canvas ref={canvasRef} style={{ display: "none" }} />

              {!cameraStream && (
                <div
                  style={{
                    padding: 24,
                    textAlign: "center",
                    border: "1px dashed #aaa",
                    borderRadius: 12,
                  }}
                >
                  <VideoOff size={30} />
                  <p className="muted">Camera is stopped.</p>
                </div>
              )}
            </div>

            {!scanning ? (
              <button
                type="button"
                className="primary-button session-button"
                onClick={startCamera}
              >
                <Camera size={17} />
                Start camera recognition
              </button>
            ) : (
              <button
                type="button"
                className="secondary-button session-button"
                onClick={stopCamera}
              >
                <VideoOff size={17} />
                Stop camera
              </button>
            )}

            {scanning && (
              <p className="muted">
                {processingFrame
                  ? "Checking the current frame..."
                  : "Camera is running. Checking approximately every two seconds."}
              </p>
            )}

            {recognitionResult && (
              <div
                className={
                  recognitionResult.marked
                    ? "success-message attendance-message"
                    : "attendance-message"
                }
                style={{ marginTop: 16 }}
                role="status"
              >
                {recognitionResult.marked ? (
                  <CheckCircle2 size={18} />
                ) : (
                  <AlertCircle size={18} />
                )}
                <span>
                  {recognitionResult.student_name
                    ? `${recognitionResult.student_name}: `
                    : ""}
                  {recognitionResult.message}
                  {typeof recognitionResult.similarity === "number" &&
                    ` (Similarity: ${(recognitionResult.similarity * 100).toFixed(1)}%)`}
                </span>
              </div>
            )}

            <h3 style={{ marginTop: 24 }}>Attendance marked this session</h3>
            <p className="muted">
              Recognized students recorded successfully: {presentStudents.length}
            </p>

            {presentStudents.length > 0 ? (
              <ul>
                {presentStudents.map((student) => (
                  <li key={student.id}>
                    <strong>{student.name}</strong> — {student.time}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">
                No students have been marked present in this browser session yet.
              </p>
            )}
          </>
        ) : (
          <>
            <div className="session-status inactive-status">
              <Clock size={16} />
              No active session
            </div>
            <p className="muted">
              Start a session before processing classroom attendance.
            </p>
          </>
        )}
      </section>
    </main>
  );
}
done
