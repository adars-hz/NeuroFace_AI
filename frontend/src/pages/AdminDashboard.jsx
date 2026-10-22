
import {
  Users,
  GraduationCap,
  BookOpen,
  ClipboardCheck,
  BarChart3,
  Settings,
  LogOut,
  Building2,
} from "lucide-react";

const sections = [
  {
    title: "User Management",
    description: "Manage student, teacher, and administrator accounts.",
    icon: Users,
  },
  {
    title: "Classes & Departments",
    description: "Organize departments, classes, and academic batches.",
    icon: Building2,
  },
  {
    title: "Subjects & Assignments",
    description: "Manage subjects and teacher-class assignments.",
    icon: BookOpen,
  },
  {
    title: "Attendance Monitoring",
    description: "Monitor attendance sessions and recorded attendance.",
    icon: ClipboardCheck,
  },
  {
    title: "Reports & Eligibility",
    description: "Review attendance percentages, eligibility, and fines.",
    icon: BarChart3,
  },
  {
    title: "System Management",
    description: "Review system configuration and administrative settings.",
    icon: Settings,
  },
];

export default function AdminDashboard({ user, onLogout }) {
  return (
    <div className="dashboard-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon small">N</span>
          <span>NeuroFace</span>
        </div>

        <p className="sidebar-label">ADMINISTRATION</p>
        <div className="sidebar-link active">
          <BarChart3 size={19} /> Overview
        </div>
        <div className="sidebar-link">
          <Users size={19} /> Users
        </div>
        <div className="sidebar-link">
          <GraduationCap size={19} /> Academics
        </div>
        <div className="sidebar-link">
          <ClipboardCheck size={19} /> Attendance
        </div>

        <button className="logout-button" onClick={onLogout}>
          <LogOut size={18} /> Sign out
        </button>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">ADMIN WORKSPACE</p>
            <h1>Admin Dashboard</h1>
            <p className="muted">
              Manage academic information and monitor the attendance system.
            </p>
          </div>
          <div className="profile-chip">
            <div className="avatar">A</div>
            <div>
              <strong>{user?.username || "Administrator"}</strong>
              <span>Administrator</span>
            </div>
          </div>
        </header>

        <section className="welcome-card">
          <div>
            <p className="welcome-label">NEUROFACE CONTROL CENTRE</p>
            <h2>Welcome back!</h2>
            <p>
              Manage users, academic structures, assignments, attendance, and
              reports from one workspace.
            </p>
          </div>
          <div className="welcome-symbol">
            <GraduationCap size={54} />
          </div>
        </section>

        <section className="section-heading">
          <div>
            <h2>Management Modules</h2>
            <p className="muted">Choose an area to manage.</p>
          </div>
        </section>

        <section className="module-grid">
          {sections.map(({ title, description, icon: Icon }) => (
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
