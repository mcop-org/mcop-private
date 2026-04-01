import { NavLink } from "react-router-dom";

type SidebarNavProps = {
  currentPath: string;
};

const navItems = [
  { to: "/data", label: "Data Upload / Contracts" },
  { to: "/product-references", label: "Product Reference Intelligence" },
  { to: "/reservations", label: "Reservation Intelligence" },
  { to: "/action-queue", label: "Reservation Risk / Action Queue" },
  { to: "/geography", label: "Client Geography" },
];

export function SidebarNav(_props: SidebarNavProps) {
  return (
    <aside className="sidebar">
      <div className="brand-card">
        <div className="brand-eyebrow">MCOP Workspace</div>
        <h1>Advanced UI</h1>
        <p>Premium operational layer over trusted local MCOP outputs.</p>
        <div className="brand-meta">
          <span className="topbar-chip">Local only</span>
          <span className="topbar-chip">Reference logic preserved</span>
        </div>
      </div>
      <nav className="sidebar-nav" aria-label="Primary">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            to={item.to}
          >
            <span className="nav-link-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
