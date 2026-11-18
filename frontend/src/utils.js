export const MAX_ENTRY_KG = 500;

const REASON_LABELS = {
  spoilage: "Spoilage",
  trimming: "Trimming",
  overproduction: "Overproduction",
  plate_waste: "Plate waste",
  other: "Other",
};

export const reasonLabel = (reason) => REASON_LABELS[reason] || reason;

// One fixed color per reason, so charts always match
export const REASON_COLORS = {
  spoilage: "#b8423a",
  trimming: "#e0a02e",
  overproduction: "#3b7bbf",
  plate_waste: "#7a6bc9",
  other: "#9aa59d",
};

// Colors for restaurants (assigned by position)
export const CHART_COLORS = ["#448699", "#d9822b", "#7a6bc9", "#b8527f", "#2f7d57", "#c9a227", "#3b6fbf", "#8a6a4f"];

// Today's date as YYYY-MM-DD in the user's own time zone
export const todayISO = () => new Date().toLocaleDateString("sv-SE");

export function daysAgoISO(days) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toLocaleDateString("sv-SE");
}

export function formatMoney(value) {
  return new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR" }).format(value);
}



export function formatKg(value) {
  return `${Number(Number(value).toFixed(3))} kg`;
}

// Label for a chart point: day, week or month
export function periodLabel(iso, interval) {
  if (interval === "month") return iso.slice(0, 7);
  if (interval === "week") return `Week of ${iso.slice(5)}`;
  return iso;
}

export function periodTick(iso, interval) {
  return interval === "month" ? iso.slice(0, 7) : iso.slice(5);
}

// Convert what the user typed into kilograms, or null if it isn't usable yet
export function toKg(amount, unit, gramsPerPiece) {
  const n = Number(amount);
  if (!Number.isFinite(n) || n <= 0) return null;
  if (unit === "kg") return n;
  if (unit === "g") return n / 1000;
  if (unit === "pcs") return gramsPerPiece ? (n * gramsPerPiece) / 1000 : null;
  return null;
}