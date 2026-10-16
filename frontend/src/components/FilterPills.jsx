import { formatStatus } from "./StatusBadge";

/** "All · Active · Paused ..." buttons with a count on each. */
function FilterPills({ statuses, items, value, onChange }) {
  const options = ["all", ...statuses];
  return (
    <div className="d-flex flex-wrap gap-2" role="group" aria-label="Filter by status">
      {options.map((status) => {
        const count = status === "all" ? items.length : items.filter((i) => i.status === status).length;
        return (
          <button
            key={status}
            type="button"
            className={`btn btn-sm filter-pill ${value === status ? "active" : ""}`}
            onClick={() => onChange(status)}
            aria-pressed={value === status}
          >
            {status === "all" ? "All" : formatStatus(status)}
            <span className="filter-count">{count}</span>
          </button>
        );
      })}
    </div>
  );
}

export default FilterPills;
