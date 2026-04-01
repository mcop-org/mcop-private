type TopBarProps = {
  currentPath: string;
};

const titles: Record<string, string> = {
  "/data": "Data Upload / Contracts",
  "/product-references": "Product Reference Intelligence",
  "/reservations": "Reservation Intelligence",
  "/action-queue": "Reservation Risk / Action Queue",
  "/geography": "Client Geography",
};

export function TopBar({ currentPath }: TopBarProps) {
  return (
    <header className="topbar">
      <div className="topbar-copy">
        <div className="topbar-eyebrow">Advanced UI First Slice</div>
        <h2>{titles[currentPath] ?? "MCOP Advanced UI"}</h2>
        <p className="topbar-subcopy">Trusted module content preserved. App-layer presentation refined for faster operational scanning.</p>
      </div>
      <div className="topbar-chip">Main MCOP dashboard untouched</div>
    </header>
  );
}
