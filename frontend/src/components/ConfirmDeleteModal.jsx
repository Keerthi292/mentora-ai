import { useState } from "react";

import Modal from "./Modal";

/** Asks "are you sure?" before deleting. `onConfirm` should throw on failure. */
function ConfirmDeleteModal({ itemLabel, onConfirm, onClose }) {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  const handleDelete = async () => {
    setDeleting(true);
    setError("");
    try {
      await onConfirm();
      onClose();
    } catch (err) {
      setError(err.message);
      setDeleting(false);
    }
  };

  const footer = (
    <>
      <button type="button" className="btn btn-outline-secondary" onClick={onClose}>
        Cancel
      </button>
      <button type="button" className="btn btn-danger" onClick={handleDelete} disabled={deleting}>
        {deleting ? "Deleting..." : "Delete"}
      </button>
    </>
  );

  return (
    <Modal title="Delete item" onClose={onClose} footer={footer}>
      {error && <div className="alert alert-danger py-2">{error}</div>}
      <p className="mb-0">
        Delete <strong>{itemLabel}</strong>? This can't be undone.
      </p>
    </Modal>
  );
}

export default ConfirmDeleteModal;
