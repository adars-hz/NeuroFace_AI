
import {
  Camera,
  ClipboardCheck,
  FileText,
  GraduationCap,
  Percent,
  LogOut,
  BookOpen,
} from "lucide-react";

const studentModules = [
  {
    title: "Face Registration",
    description: "Register your face using an authorized photograph.",
    icon: Camera,
  },
  {
    title: "My Attendance",
    description: "View your subject-wise attendance records.",
    icon: ClipboardCheck,
  },
  {
    title: "Attendance Percentage",
    description: "Check attendance percentages and the 85% requirement.",
    icon: Percent,
  },
  {
    title: "Leave Status",
    description: "Review the status of submitted leave documents.",
    icon: FileText,
  },
  {
    title: "Exam Eligibility",
    description: "Check eligibility for examinations by subject.",
    icon: GraduationCap,
  },
];

export default function StudentDashboard({ user, onLogout }) {
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
              View your attendance, registration, and academic status.
            </p>
          </div>
          <div className="profile-chip">
            <div className="avatar">S</div>
            <div>
              <strong>{user?.username || "Student"}</strong>
              <span>Student</span>
            </div>
          </div>
        </header>

        <section className="welcome-card">
          <div>
            <p className="welcome-label">YOUR ACADEMIC OVERVIEW</p>
            <h2>Welcome, {user?.username || "Student"}!</h2>
            <p>
              Keep track of your attendance and make sure you meet the
              minimum attendance requirement for each subject.
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
              Final eligibility will be calculated from your recorded attendance
              according to the system's academic rules.
            </p>
          </div>
        </section>

        <section className="section-heading">
          <div>
            <h2>My Modules</h2>
            <p className="muted">Your personal attendance workspace.</p>
          </div>
        </section>

        <section className="module-grid">
          {studentModules.map(({ title, description, icon: Icon }) => (
            <article className="module-card" key={title}>
              <div className="module-icon">
                <Icon size={23} />
              </div>
              <h3>{title}</h3>
              <p>{description}</p>
              <span className="module-status">Module planned</span>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}
