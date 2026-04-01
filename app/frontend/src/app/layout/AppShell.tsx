import { Outlet, useLocation } from "react-router-dom";
import { SidebarNav } from "./SidebarNav";
import { TopBar } from "./TopBar";

export function AppShell() {
  const location = useLocation();

  return (
    <div className="app-shell">
      <SidebarNav currentPath={location.pathname} />
      <main className="app-main">
        <TopBar currentPath={location.pathname} />
        <Outlet />
      </main>
    </div>
  );
}
