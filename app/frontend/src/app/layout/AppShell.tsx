import { Outlet, useLocation } from "react-router-dom";
import { useSessionStorageState } from "../../lib/sessionState";
import { SidebarNav } from "./SidebarNav";
import { TopBar } from "./TopBar";

type AppThemeMode = "light" | "dark";

const APP_THEME_STATE_KEY = "mcop-advanced-ui:theme";

export function AppShell() {
  const location = useLocation();
  const { state: theme, setState: setTheme } = useSessionStorageState<AppThemeMode>(
    APP_THEME_STATE_KEY,
    "light",
  );

  return (
    <div className="app-shell" data-theme={theme}>
      <SidebarNav currentPath={location.pathname} theme={theme} />
      <main className="app-main">
        <TopBar
          currentPath={location.pathname}
          theme={theme}
          onThemeChange={(nextTheme) => setTheme(nextTheme)}
        />
        <Outlet />
      </main>
    </div>
  );
}
