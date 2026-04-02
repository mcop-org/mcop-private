type TopBarProps = {
  currentPath: string;
  theme: "light" | "dark";
  onThemeChange: (theme: "light" | "dark") => void;
};

const titles: Record<string, string> = {
  "/data": "Data Upload / Contracts",
  "/product-references": "Product Reference Intelligence",
  "/reservations": "Reservation Intelligence",
  "/action-queue": "Reservation Risk / Action Queue",
  "/client-intelligence": "Client Intelligence",
  "/geography": "Client Geography",
  "/landed-stock": "Landed Stock Intelligence",
};

export function TopBar({ currentPath, theme, onThemeChange }: TopBarProps) {
  return (
    <header className="topbar">
      <div className="topbar-copy">
        <div className="topbar-eyebrow">MCOP Premium Application Layer</div>
        <h2>{titles[currentPath] ?? "MCOP Operations Workspace"}</h2>
        <p className="topbar-subcopy">
          Trusted module content preserved. Workspace presentation refined for faster operational scanning and a more productized shell.
        </p>
      </div>
      <div className="topbar-actions">
        <div className="theme-toggle" aria-label="Theme mode">
          <button
            className={`secondary-button theme-toggle-button${theme === "light" ? " active" : ""}`}
            type="button"
            aria-pressed={theme === "light"}
            onClick={() => onThemeChange("light")}
          >
            Light
          </button>
          <button
            className={`secondary-button theme-toggle-button${theme === "dark" ? " active" : ""}`}
            type="button"
            aria-pressed={theme === "dark"}
            onClick={() => onThemeChange("dark")}
          >
            Dark
          </button>
        </div>
        <div className="topbar-chip-wrap">
          <div className="topbar-chip">Reference workspace aligned</div>
          <div className="topbar-chip">Main MCOP dashboard untouched</div>
        </div>
      </div>
    </header>
  );
}
