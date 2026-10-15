import { useState } from "react";

import useResource from "../hooks/useResource";
import ConfirmDeleteModal from "./ConfirmDeleteModal";
import FormModal from "./FormModal";

/**
 * A full list + add / edit / delete page for one backend resource.
 *
 * Props:
 *   title       Page heading, e.g. "Skills"
 *   itemName    Singular name for buttons, e.g. "skill"
 *   apiPath     Backend path, e.g. "/api/skills"
 *   fields      Form fields (see FormModal)
 *   columns     Table columns: [{ header: "Name", render: (item) => item.name }]
 *   getLabel    Short text for an item in the delete dialog, e.g. (item) => item.name
 *   emptyText   Shown when the list is empty
 */
function CrudPage({ title, itemName, apiPath, fields, columns, getLabel, emptyText }) {
  const { items, loading, error, create, update, remove } = useResource(apiPath);

  // `editing` is null (modal closed), "new" (adding) or the item being edited
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);

  const isNew = editing === "new";

  return (
    <>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
        <h1 className="h3 mb-0">{title}</h1>
        <button type="button" className="btn btn-primary" onClick={() => setEditing("new")}>
          + Add {itemName}
        </button>
      </div>

      {error && <div className="alert alert-danger">Could not load {title.toLowerCase()}: {error}</div>}

      {loading && items.length === 0 ? (
        <div className="text-body-secondary">
          <span className="spinner-border spinner-border-sm me-2" role="status" />
          Loading...
        </div>
      ) : !error && items.length === 0 ? (
        <div className="card card-body text-center text-body-secondary">{emptyText}</div>
      ) : (
        items.length > 0 && (
          <div className="table-responsive">
            <table className="table table-hover align-middle">
              <thead>
                <tr>
                  {columns.map((column) => (
                    <th key={column.header} scope="col">
                      {column.header}
                    </th>
                  ))}
                  <th scope="col" className="text-end">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    {columns.map((column) => (
                      <td key={column.header}>{column.render(item)}</td>
                    ))}
                    <td className="text-end text-nowrap">
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-primary me-2"
                        onClick={() => setEditing(item)}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-danger"
                        onClick={() => setDeleting(item)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}

      {editing && (
        <FormModal
          // A new key resets the form when switching between items
          key={isNew ? "new" : editing.id}
          title={isNew ? `Add ${itemName}` : `Edit ${itemName}`}
          submitLabel={isNew ? "Add" : "Save changes"}
          fields={fields}
          initialValues={isNew ? {} : editing}
          onSubmit={(data) => (isNew ? create(data) : update(editing.id, data))}
          onClose={() => setEditing(null)}
        />
      )}

      {deleting && (
        <ConfirmDeleteModal
          itemLabel={getLabel(deleting)}
          onConfirm={() => remove(deleting.id)}
          onClose={() => setDeleting(null)}
        />
      )}
    </>
  );
}

export default CrudPage;
