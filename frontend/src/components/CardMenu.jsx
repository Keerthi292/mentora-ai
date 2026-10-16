// Edit / delete icons in a card's corner
function CardMenu({ onEdit, onDelete, label }) {
  return (
    <div className="d-flex gap-1 flex-shrink-0">
      <button type="button" className="btn btn-sm icon-btn" onClick={onEdit} aria-label={`Edit ${label}`} title="Edit">
        <i className="bi bi-pencil" aria-hidden="true" />
      </button>
      <button type="button" className="btn btn-sm icon-btn icon-btn-danger" onClick={onDelete} aria-label={`Delete ${label}`} title="Delete">
        <i className="bi bi-trash3" aria-hidden="true" />
      </button>
    </div>
  );
}

export default CardMenu;
