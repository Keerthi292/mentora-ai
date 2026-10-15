import CrudPage from "../components/CrudPage";
import StatusBadge, { statusOptions } from "../components/StatusBadge";
import { formatDate } from "../utils/format";

// Must match CareerGoalStatus in backend/app/schemas.py
const STATUSES = ["active", "paused", "achieved", "abandoned"];

const FIELDS = [
  { name: "target_role", label: "Target role", required: true, maxLength: 255, placeholder: "e.g. Backend Developer" },
  { name: "description", label: "Description", type: "textarea" },
  { name: "status", label: "Status", type: "select", options: statusOptions(STATUSES) },
  { name: "target_date", label: "Target date", type: "date" },
];

const COLUMNS = [
  {
    header: "Target role",
    render: (goal) => (
      <>
        <div className="fw-semibold">{goal.target_role}</div>
        {goal.description && <div className="small text-body-secondary">{goal.description}</div>}
      </>
    ),
  },
  { header: "Status", render: (goal) => <StatusBadge status={goal.status} /> },
  { header: "Target date", render: (goal) => formatDate(goal.target_date) },
];

function CareerGoals() {
  return (
    <CrudPage
      title="Career Goals"
      itemName="career goal"
      apiPath="/api/career-goals"
      fields={FIELDS}
      columns={COLUMNS}
      getLabel={(goal) => goal.target_role}
      emptyText="No career goals yet. Which role are you aiming for?"
    />
  );
}

export default CareerGoals;
