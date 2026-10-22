
import {
  Camera,
  ClipboardCheck,
  FileText,
  CalendarClock,
  Users,
  ShieldCheck,
  LogOut,
  BookOpen,
} from "lucide-react";

const teacherModules = [
  {
    title: "Start Attendance",
    description: "Select an assigned subject and start an attendance session.",
    icon: Camera,
  },
  {
    title: "Attendance Records",
    description: "Review attendance sessions and student records.",
    icon: ClipboardCheck,
  },
  {
    title: "Leave Letters",
    description: "Upload leave documents and review extracted absence reasons.",
    icon: FileText,
  },
  {
    title: "Class & Teacher Availability",
    description: "View session status and teacher availability.",
    icon: CalendarClock,
  },
  {
    title: "Class Reports",
    description: "Review subject-wise attendance and student eligibility.",
    icon: Users,
  },
];

export default function TeacherDashboard({ user, onLogout }) {
  const isHod = user?.designation?.toUpperCase() === "HOD";

  return (
    <div className="dashboard-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon small">N</span>
          <span>NeuroFace</span>
        </div>

        <p className="sidebar-label">TEACHING WORKSPACE</p>
        <div className="sidebar-link active">
          <BookOpen size={19} /> Overview
        </div>
        <div className="sidebar-link">
          <Camera size={19} /> Attendance
        </div>
        <div className="sidebar-link">
          <FileText size={19} /> Leave Letters
        </div>
        <div className="sidebar-link">
          <ClipboardCheck size={19} /> Reports
        </div>

        {isHod && (
          <div className="sidebar-link">
            <ShieldCheck size={19} /> HOD Permissions
          </div>
        )}

        <button className="logout-button" onClick={onLogout}>
          <LogOut size={18} /> Sign out
        </button>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">
              {isHod ? "HOD WORKSPACE" : "TEACHER WORKSPACE"}
            </p>
            <h1>{isHod ? "HOD Dashboard" : "Teacher Dashboard"}</h1>
            <p className="muted">
              Manage classroom attendance, leave documents, and reports.
            </p>
          </div>
          <div className="profile-chip">
            <div className="avatar">T</div>
            <div>
              <strong>{user?.username || "Teacher"}</strong>
              <span>{isHod ? "Teacher · HOD" : "Teacher"}</span>
            </div>
          </div>
        </header>

        <section className="welcome-card">
          <div>
            <p className="welcome-label">CLASSROOM WORKSPACE</p>
            <h2>Welcome, {user?.username || "Teacher"}!</h2>
            <p>
              Start an attendance session for an assigned class and subject.
              Recognition and session controls will be connected to the backend.
            </p>
          </div>
          <div className="welcome-symbol">
            <Camera size={52} />
          </div>
        </section>

        {isHod && (
          <section className="hod-notice">
            <ShieldCheck size={21} />
            <div>
              <strong>HOD permissions</strong>
              <p>
                This account is intended to have additional report, eligibility,
                and medical-waiver permissions.
              </p>
            </div>
          </section>
        )}

        <section className="section-heading">
          <div>
            <h2>Teaching Modules</h2>
            <p className="muted">Your classroom management workspace.</p>
          </div>
        </section>

        <section className="module-grid">
          {teacherModules.map(({ title, description, icon: Icon }) => (
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
