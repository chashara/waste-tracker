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

const toISO = (date) => date.toLocaleDateString("sv-SE");

// The last N months as dropdown options, newest first: { value: "2026-11", label: "November 2026" }
export function recentMonths(count = 24) {
  const now = new Date();
  const months = [];
  for (let i = 0; i < count; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    months.push({
      value: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`,
      label: d.toLocaleDateString("en-GB", { month: "long", year: "numeric" }),
    });
  }
  return months;
}

// "2026-11" -> first and last day of that month (the last day is capped at today)
export function monthRange(yearMonth) {
  const [year, month] = yearMonth.split("-").map(Number);
  const first = toISO(new Date(year, month - 1, 1));
  const last = toISO(new Date(year, month, 0));
  const today = todayISO();
  return { date_from: first, date_to: last > today ? today : last };
}

// The previous calendar month, cut to the same day of the month as `endISO`,
// so an unfinished month is compared with the same number of days
export function previousMonthRange(yearMonth, endISO) {
  const [year, month] = yearMonth.split("-").map(Number);
  const prevFirst = new Date(year, month - 2, 1);
  const daysInPrevMonth = new Date(year, month - 1, 0).getDate();
  const endDay = Math.min(Number(endISO.slice(8, 10)), daysInPrevMonth);
  const prevEnd = new Date(prevFirst.getFullYear(), prevFirst.getMonth(), endDay);
  return { compare_from: toISO(prevFirst), compare_to: toISO(prevEnd) };
}