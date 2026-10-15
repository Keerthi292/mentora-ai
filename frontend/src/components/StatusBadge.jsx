// Colour for each status value used by the backend
const STATUS_COLORS = {
  active: "primary",
  in_progress: "primary",
  planned: "secondary",
  paused: "warning",
  on_hold: "warning",
  completed: "success",
  achieved: "success",
  abandoned: "dark",
};

/** "in_progress" -> "In progress" */
export function formatStatus(status) {
  const text = status.replaceAll("_", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** A list of { value, label } for a status <select>. */
export function statusOptions(statuses) {
  return statuses.map((status) => ({ value: status, label: formatStatus(status) }));
}

function StatusBadge({ status }) {
  const color = STATUS_COLORS[status] || "secondary";
  return <span className={`badge text-bg-${color}`}>{formatStatus(status)}</span>;
}

export default StatusBadge;
