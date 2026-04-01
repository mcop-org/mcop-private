export function formatReservationKey(value: unknown): string {
  const text = String(value ?? "").trim();
  if (!text) {
    return "-";
  }

  if (/^-?\d+\.0+$/.test(text)) {
    return text.replace(/\.0+$/, "");
  }

  const numeric = Number(text);
  if (Number.isFinite(numeric) && Number.isInteger(numeric)) {
    return String(numeric);
  }

  return text;
}

export function getStatusTone(value: unknown): "warm" | "good" | "danger" | "neutral" {
  const normalized = String(value ?? "").trim().toLowerCase();

  if (
    normalized === "completed" ||
    normalized === "landed" ||
    normalized === "accepted" ||
    normalized === "build ready" ||
    normalized === "valid"
  ) {
    return "good";
  }

  if (
    normalized === "created" ||
    normalized === "incoming" ||
    normalized === "near expiry" ||
    normalized === "pending" ||
    normalized === "awaiting accepted file"
  ) {
    return "warm";
  }

  if (
    normalized === "breached" ||
    normalized === "landed not approved" ||
    normalized === "blocked" ||
    normalized === "rejected" ||
    normalized === "invalid" ||
    normalized.includes("unavailable") ||
    normalized.includes("missing")
  ) {
    return "danger";
  }

  return "neutral";
}

export function getStatusChipClass(value: unknown): string {
  return `status-chip tone-${getStatusTone(value)}`;
}
