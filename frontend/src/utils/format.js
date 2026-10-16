// Small display helpers shared by pages

/** "2026-12-31" -> "Dec 31, 2026" (or "-" when empty) */
export function formatDate(isoDate) {
  if (!isoDate) return "-";
  // Build the date from its parts so it isn't shifted by the user's time zone
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** Days from today to an ISO date: { text: "in 12 days" | "due today" | "3 days overdue", tone } */
export function dueText(isoDate) {
  if (!isoDate) return null;
  const [y, m, d] = isoDate.split("-").map(Number);
  const today = new Date();
  const days = Math.round(
    (new Date(y, m - 1, d) - new Date(today.getFullYear(), today.getMonth(), today.getDate())) / 86400000
  );
  if (days === 0) return { text: "due today", tone: "warning" };
  if (days < 0) return { text: `${-days} day${days === -1 ? "" : "s"} overdue`, tone: "danger" };
  return { text: `in ${days} day${days === 1 ? "" : "s"}`, tone: days <= 7 ? "warning" : "secondary" };
}

/** "React, FastAPI ,  SQL" -> ["React", "FastAPI", "SQL"] */
export function splitList(text) {
  return (text || "")
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}
