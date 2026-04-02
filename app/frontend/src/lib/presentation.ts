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

function asFiniteNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

type NumberFormatOptions = {
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
};

export function formatNumber(
  value: unknown,
  {
    minimumFractionDigits = 0,
    maximumFractionDigits = 0,
  }: NumberFormatOptions = {},
): string {
  const number = asFiniteNumber(value);
  if (number === null) {
    return "-";
  }

  return new Intl.NumberFormat("en-GB", {
    minimumFractionDigits,
    maximumFractionDigits,
  }).format(number);
}

export function formatCount(value: unknown, maximumFractionDigits = 0): string {
  return formatNumber(value, { maximumFractionDigits });
}

export function formatMoney(value: unknown): string {
  const number = asFiniteNumber(value);
  if (number === null) {
    return "-";
  }

  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(number);
}

export function formatCompactMoney(value: unknown): string {
  const number = asFiniteNumber(value);
  if (number === null) {
    return "-";
  }

  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    notation: "compact",
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  }).format(number);
}

export function formatPercent(value: unknown, maximumFractionDigits = 0): string {
  const number = asFiniteNumber(value);
  if (number === null) {
    return "-";
  }

  return new Intl.NumberFormat("en-GB", {
    style: "percent",
    minimumFractionDigits: 0,
    maximumFractionDigits,
  }).format(number);
}

export function formatBags(value: unknown): string {
  const number = asFiniteNumber(value);
  if (number === null) {
    return "Unavailable";
  }

  return `${formatNumber(number, { maximumFractionDigits: 2 })} bags`;
}

export function formatKg(value: unknown): string {
  const number = asFiniteNumber(value);
  if (number === null) {
    return "-";
  }

  return `${formatNumber(number, { maximumFractionDigits: 2 })} kg`;
}

export function formatIsoDate(value: unknown): string {
  const text = String(value ?? "").trim();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(text)) {
    return "-";
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${text}T00:00:00Z`));
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
