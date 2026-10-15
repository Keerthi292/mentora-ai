import CrudPage from "../components/CrudPage";
import StatusBadge, { statusOptions } from "../components/StatusBadge";
import { formatDate } from "../utils/format";

// Must match LearningGoalStatus in backend/app/schemas.py
const STATUSES = ["active", "paused", "completed", "abandoned"];

const FIELDS = [
  { name: "title", label: "Title", required: true, maxLength: 255, placeholder: "e.g. Learn FastAPI" },
  { name: "description", label: "Description", type: "textarea" },
  { name: "status", label: "Status", type: "select", options: statusOptions(STATUSES) },
  { name: "target_date", label: "Target date", type: "date" },
];

const COLUMNS = [
  {
    header: "Goal",
    render: (goal) => (
      <>
        <div className="fw-semibold">{goal.title}</div>
        {goal.description && <div className="small text-body-secondary">{goal.description}</div>}
      </>
    ),
  },
  { header: "Status", render: (goal) => <StatusBadge status={goal.status} /> },
  { header: "Target date", render: (goal) => formatDate(goal.target_date) },
];

function LearningGoals() {
  return (
    <CrudPage
      title="Learning Goals"
      itemName="goal"
      apiPath="/api/learning-goals"
      fields={FIELDS}
      columns={COLUMNS}
      getLabel={(goal) => goal.title}
      emptyText="No learning goals yet. What do you want to learn?"
    />
  );
}

export default LearningGoals;
