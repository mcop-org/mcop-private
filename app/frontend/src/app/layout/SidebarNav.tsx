import { NavLink } from "react-router-dom";
import logoDarkUrl from "../../../../../mcop/reference_workspace/assets/logo-dark.png";
import logoLightUrl from "../../../../../mcop/reference_workspace/assets/logo-light.png";

type SidebarNavProps = {
  currentPath: string;
  theme: "light" | "dark";
};

const navItems = [
  { to: "/data", label: "Data Upload / Contracts" },
  { to: "/product-references", label: "Product Reference Intelligence" },
  { to: "/reservations", label: "Reservation Intelligence" },
  { to: "/action-queue", label: "Reservation Risk / Action Queue" },
  { to: "/client-intelligence", label: "Client Intelligence" },
  { to: "/geography", label: "Client Geography" },
  { to: "/landed-stock", label: "Landed Stock Intelligence" },
];

export function SidebarNav({ theme }: SidebarNavProps) {
  const logoUrl = theme === "dark" ? logoDarkUrl : logoLightUrl;

  return (
    <aside className="sidebar">
      <div className="brand-card">
        <div className="brand-mark">
          <img alt="MCOP" className="brand-logo" src={logoUrl} />
        </div>
        <div className="brand-eyebrow">MCOP Reference Workspace</div>
        <h1>Operations Workspace</h1>
        <p>Premium operational application layer over trusted local MCOP outputs and reference modules.</p>
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
