import CrudPage from "../components/CrudPage";

// The shared skill catalog (e.g. "Python", "SQL"). Names must be unique.
const FIELDS = [
  { name: "name", label: "Name", required: true, maxLength: 100, placeholder: "e.g. Python" },
  { name: "category", label: "Category", maxLength: 100, placeholder: "e.g. Programming" },
];

const COLUMNS = [
  { header: "Name", render: (skill) => <span className="fw-semibold">{skill.name}</span> },
  { header: "Category", render: (skill) => skill.category || <span className="text-body-secondary">-</span> },
];

function Skills() {
  return (
    <CrudPage
      title="Skills"
      itemName="skill"
      apiPath="/api/skills"
      fields={FIELDS}
      columns={COLUMNS}
      getLabel={(skill) => skill.name}
      emptyText="No skills yet. Add your first one!"
    />
  );
}

export default Skills;
