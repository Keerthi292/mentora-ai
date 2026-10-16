import { useEffect, useRef, useState } from "react";

import BotAvatar from "../BotAvatar";
import { dateGroup } from "../../services/chatStorage";

// Bootstrap closes the slide-in panel (small screens) when these buttons are clicked
const closePanel = { "data-bs-dismiss": "offcanvas", "data-bs-target": "#chatHistory" };

/**
 * The list of saved chats, ChatGPT-style. A normal column on md+ screens and a
 * Bootstrap offcanvas panel (slides in from the left) on small screens.
 */
function ChatSidebar({ conversations, activeId, onHome, isHome, disabled, onNewChat, onSelect, onDelete, onRename }) {
  const [renamingId, setRenamingId] = useState(null);

  // Group by date, keeping the newest-first order: Today, Yesterday, ...
  const groups = [];
  for (const conversation of conversations) {
    const label = dateGroup(conversation.updatedAt);
    if (groups.at(-1)?.label !== label) groups.push({ label, items: [] });
    groups.at(-1).items.push(conversation);
  }

  return (
    <aside className="offcanvas-md offcanvas-start chat-sidebar" tabIndex="-1" id="chatHistory" aria-label="Chats">
      <div className="offcanvas-header d-md-none">
        <h2 className="offcanvas-title h5">Chats</h2>
        <button type="button" className="btn-close" aria-label="Close" {...closePanel} />
      </div>

      <div className="offcanvas-body d-flex flex-column gap-2 h-100">
        <button
          type="button"
          className={`btn chat-home-link d-flex align-items-center gap-2 text-start ${isHome ? "active" : ""}`}
          onClick={onHome}
          disabled={disabled}
          {...closePanel}
        >
          <BotAvatar size={26} />
          <span className="fw-semibold">Mentora home</span>
        </button>

        <button type="button" className="btn btn-gradient w-100" onClick={onNewChat} disabled={disabled} {...closePanel}>
          <i className="bi bi-plus-lg me-1" aria-hidden="true" /> New chat
        </button>

        <nav className="chat-list flex-grow-1 overflow-auto mt-2">
          {conversations.length === 0 && (
            <p className="small text-body-secondary px-2">
              <i className="bi bi-chat-dots me-1" aria-hidden="true" />
              Your chats will appear here.
            </p>
          )}

          {groups.map((group) => (
            <div key={group.label} className="mb-3">
              <div className="chat-group-label px-2 mb-1">{group.label}</div>
              {group.items.map((conversation) => (
                <div
                  key={conversation.id}
                  className={`chat-list-item d-flex align-items-center rounded-3 ${conversation.id === activeId ? "active" : ""}`}
                >
                  {renamingId === conversation.id ? (
                    <RenameInput
                      initial={conversation.title}
                      onSave={(title) => {
                        onRename(conversation.id, title);
                        setRenamingId(null);
                      }}
                      onCancel={() => setRenamingId(null)}
                    />
                  ) : (
                    <>
                      <button
                        type="button"
                        className="btn btn-sm text-start text-truncate flex-grow-1 border-0 d-flex align-items-center gap-2"
                        onClick={() => onSelect(conversation.id)}
                        onDoubleClick={() => !disabled && setRenamingId(conversation.id)}
                        disabled={disabled}
                        title={conversation.title}
                        aria-current={conversation.id === activeId ? "true" : undefined}
                        {...closePanel}
                      >
                        <i className="bi bi-chat-left-text text-body-secondary" aria-hidden="true" />
                        <span className="text-truncate">{conversation.title}</span>
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm border-0 text-body-secondary chat-delete"
                        onClick={() => setRenamingId(conversation.id)}
                        disabled={disabled}
                        aria-label={`Rename chat "${conversation.title}"`}
                        title="Rename chat"
                      >
                        <i className="bi bi-pencil" aria-hidden="true" />
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm border-0 text-body-secondary chat-delete"
                        onClick={() => onDelete(conversation)}
                        disabled={disabled}
                        aria-label={`Delete chat "${conversation.title}"`}
                        title="Delete chat"
                      >
                        <i className="bi bi-trash3" aria-hidden="true" />
                      </button>
                    </>
                  )}
                </div>
              ))}
            </div>
          ))}
        </nav>
      </div>
    </aside>
  );
}

// Inline title editor: Enter or clicking away saves, Escape cancels
function RenameInput({ initial, onSave, onCancel }) {
  const [title, setTitle] = useState(initial);
  const inputRef = useRef(null);
  const done = useRef(false); // Enter/Escape already handled; ignore the blur that follows

  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, []);

  const finish = (save) => {
    if (done.current) return;
    done.current = true;
    if (save && title.trim() && title.trim() !== initial) onSave(title);
    else onCancel();
  };

  return (
    <input
      ref={inputRef}
      className="form-control form-control-sm m-1"
      value={title}
      maxLength={80}
      onChange={(e) => setTitle(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === "Enter") finish(true);
        if (e.key === "Escape") finish(false);
      }}
      onBlur={() => finish(true)}
      aria-label="Chat name"
    />
  );
}

export default ChatSidebar;
