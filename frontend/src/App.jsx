
import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { login, getCurrentUser, logout } from "./api";
import AdminDashboard from "./pages/AdminDashboard";
import TeacherDashboard from "./pages/TeacherDashboard";
import TeacherAttendance from "./pages/TeacherAttendance";
import StudentDashboard from "./pages/StudentDashboard";
import "./App.css";

function ProtectedRoute({ user, allowedRoles, children }) {
  if (!user) return <Navigate to="/" replace />;

  if (!allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
}

function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await onLogin(username, password);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to log in. Check your credentials and try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-brand">
        <div className="brand-icon">N</div>
        <h1>NeuroFace</h1>
        <p>AI-powered student attendance management</p>
        <div className="brand-bottom">
          Secure access. Smarter attendance.
        </div>
      </section>

      <section className="login-panel">
        <form className="login-form" onSubmit={handleSubmit}>
          <span className="eyebrow">WELCOME BACK</span>
          <h2>Sign in to NeuroFace</h2>
          <p className="muted">Enter your account details to continue.</p>

          <label htmlFor="username">Username</label>
          <input
            id="username"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Enter your username"
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter your password"
            required
          />

          {error && <div className="error-message">{error}</div>}

          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </button>

          <p className="login-note">
            Access is provided according to your assigned role.
          </p>
        </form>
      </section>
    </main>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    async function restoreSession() {
      if (!localStorage.getItem("neuroface_token")) {
        setChecking(false);
        return;
      }

      try {
        setUser(await getCurrentUser());
      } catch {
        logout();
      } finally {
        setChecking(false);
      }
    }

    restoreSession();
  }, []);

  async function handleLogin(username, password) {
    await login(username, password);
    setUser(await getCurrentUser());
  }

  function handleLogout() {
    logout();
    setUser(null);
  }

  if (checking) {
    return <div className="loading-screen">Loading NeuroFace...</div>;
  }

  const homePath = !user
    ? "/"
    : user.role === "ADMIN"
      ? "/admin"
      : user.role === "TEACHER"
        ? "/teacher"
        : "/student";

  return (
    <Routes>
      <Route
        path="/"
        element={
          user ? (
            <Navigate to={homePath} replace />
          ) : (
            <LoginPage onLogin={handleLogin} />
          )
        }
      />

      <Route
        path="/admin"
        element={
          <ProtectedRoute user={user} allowedRoles={["ADMIN"]}>
            <AdminDashboard user={user} onLogout={handleLogout} />
          </ProtectedRoute>
        }
      />

      <Route
        path="/teacher"
        element={
          <ProtectedRoute user={user} allowedRoles={["TEACHER"]}>
            <TeacherDashboard user={user} onLogout={handleLogout} />
          </ProtectedRoute>
        }
      />

      <Route
        path="/teacher/attendance"
        element={
          <ProtectedRoute user={user} allowedRoles={["TEACHER"]}>
            <TeacherAttendance />
          </ProtectedRoute>
        }
      />

      <Route
        path="/student"
        element={
          <ProtectedRoute user={user} allowedRoles={["STUDENT"]}>
            <StudentDashboard user={user} onLogout={handleLogout} />
          </ProtectedRoute>
        }
      />

      <Route
        path="/unauthorized"
        element={
          <main className="message-page">
            <h2>Access denied</h2>
            <p>Your account does not have permission to open this page.</p>
            <button
              className="primary-button"
              onClick={() => window.location.assign(homePath)}
            >
              Return to dashboard
            </button>
          </main>
        }
      />

      <Route path="*" element={<Navigate to={homePath} replace />} />
    </Routes>
  );
}

export default App;
