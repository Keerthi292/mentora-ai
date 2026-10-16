/** A friendly "nothing here yet" card with an optional button. */
function EmptyState({ icon, text, action, onAction }) {
  return (
    <div className="card card-body text-center py-5 empty-state">
      <i className={`bi ${icon} display-5 text-gradient-icon`} aria-hidden="true" />
      <p className="text-body-secondary mt-2 mb-3">{text}</p>
      {action && (
        <div>
          <button type="button" className="btn btn-gradient" onClick={onAction}>
            <i className="bi bi-plus-lg me-1" aria-hidden="true" /> {action}
          </button>
        </div>
      )}
    </div>
  );
}

export default EmptyState;
