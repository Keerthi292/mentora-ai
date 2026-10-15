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
