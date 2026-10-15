import { useState } from "react";

import Modal from "./Modal";

/**
 * A modal with a form built from a list of field definitions.
 *
 * Each field looks like:
 *   { name: "title", label: "Title", type: "text" | "textarea" | "select" | "date",
 *     required: true, maxLength: 255, options: [{ value, label }] (for select),
 *     placeholder: "..." }
 *
 * `initialValues` fills the form (empty for "add", the item's values for "edit").
 * `onSubmit(data)` should save and throw an Error if saving fails; the
 * error message is then shown inside the modal.
 */
function FormModal({ title, fields, initialValues, submitLabel = "Save", onSubmit, onClose }) {
  const [values, setValues] = useState(() => toFormValues(fields, initialValues));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;
    setValues((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await onSubmit(toApiData(fields, values));
      onClose();
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  };

  return (
    <Modal title={title} onClose={onClose}>
      <form onSubmit={handleSubmit}>
        {error && <div className="alert alert-danger py-2">{error}</div>}

        {fields.map((field) => (
          <div className="mb-3" key={field.name}>
            <label className="form-label" htmlFor={`field-${field.name}`}>
              {field.label}
              {field.required && <span className="text-danger"> *</span>}
            </label>
            <FieldInput field={field} value={values[field.name]} onChange={handleChange} />
          </div>
        ))}

        <div className="d-flex justify-content-end gap-2">
          <button type="button" className="btn btn-outline-secondary" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Saving..." : submitLabel}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function FieldInput({ field, value, onChange }) {
  const common = {
    id: `field-${field.name}`,
    name: field.name,
    value,
    onChange,
    required: field.required,
  };

  if (field.type === "textarea") {
    return <textarea className="form-control" rows={3} placeholder={field.placeholder} {...common} />;
  }
  if (field.type === "select") {
    return (
      <select className="form-select" {...common}>
        {field.options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    );
  }
  return (
    <input
      className="form-control"
      type={field.type || "text"}
      maxLength={field.maxLength}
      placeholder={field.placeholder}
      {...common}
    />
  );
}

// Item from the API -> form values. Inputs need "" instead of null.
function toFormValues(fields, item = {}) {
  const values = {};
  for (const field of fields) {
    const fallback = field.type === "select" ? field.options[0].value : "";
    values[field.name] = item[field.name] ?? field.defaultValue ?? fallback;
  }
  return values;
}

// Form values -> data for the API. Trim text; empty optional fields become
// null, which also clears them when editing.
function toApiData(fields, values) {
  const data = {};
  for (const field of fields) {
    const value = typeof values[field.name] === "string" ? values[field.name].trim() : values[field.name];
    data[field.name] = value === "" && !field.required ? null : value;
  }
  return data;
}

export default FormModal;
