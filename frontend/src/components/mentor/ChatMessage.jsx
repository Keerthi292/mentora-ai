import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import BotAvatar from "../BotAvatar";
import { fileIcon, fileUrl, formatSize } from "../../services/uploads";

// How Markdown elements in the mentor's replies are rendered.
// Raw HTML in replies is ignored (react-markdown's default), so this is safe.
const MARKDOWN_COMPONENTS = {
  a: ({ node, ...props }) => <a {...props} target="_blank" rel="noreferrer" />,
  table: ({ node, ...props }) => (
    <div className="table-responsive">
      <table className="table table-sm table-bordered mb-2" {...props} />
    </div>
  ),
};

/**
 * One chat message with its avatar. The mentor's replies are rendered as Markdown
 * and get a copy button once finished.
 *
 *   isWaiting    sent, but no text has arrived yet (shows typing dots)
 *   isStreaming  text is still arriving (the bot jitters, a cursor blinks)
 *   canEdit      show an Edit button (your own messages, when no reply is running)
 *   onEdit(text) send the edited text; the mentor answers it again
 */
function ChatMessage({ message, isWaiting = false, isStreaming = false, canEdit = false, onEdit }) {
  const isUser = message.role === "user";
  const finished = !isWaiting && !isStreaming;
  const [editing, setEditing] = useState(false);

  return (
    <div className={`d-flex gap-2 mb-3 msg-enter ${isUser ? "flex-row-reverse" : ""}`}>
      <div className="flex-shrink-0 pt-1">
        {isUser ? (
          <span className="user-avatar" aria-hidden="true">
            <i className="bi bi-person-fill" />
          </span>
        ) : (
          <BotAvatar size={34} thinking={isWaiting || isStreaming} />
        )}
      </div>

      <div className={`d-flex flex-column chat-bubble-wrap ${isUser ? "align-items-end" : "align-items-start"}`}>
        {editing ? (
          <EditBox
            initial={message.content}
            allowEmpty={message.attachments?.length > 0}
            onCancel={() => setEditing(false)}
            onSave={(text) => {
              setEditing(false);
              onEdit(text);
            }}
          />
        ) : (
          <div className={`chat-bubble ${isUser ? "chat-bubble-user" : "chat-bubble-bot"}`} data-role={message.role}>
            {message.attachments?.length > 0 && <Attachments files={message.attachments} hasText={!!message.content} />}
            {isWaiting ? (
              <span className="typing-dots" role="status" aria-label="Mentora is thinking">
                <span />
                <span />
                <span />
              </span>
            ) : isUser ? (
              message.content || null
            ) : (
              <div className="markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={MARKDOWN_COMPONENTS}>
                  {message.content}
                </ReactMarkdown>
                {isStreaming && <span className="stream-caret" aria-hidden="true" />}
              </div>
            )}

            {message.stopped && <div className="small text-body-secondary fst-italic mt-1">(stopped)</div>}
            {message.error && (
              <div className="alert alert-danger py-1 px-2 mb-0 mt-2 small" role="alert">
                <i className="bi bi-exclamation-triangle me-1" aria-hidden="true" />
                {message.error}
              </div>
            )}
          </div>
        )}

        {!isUser && finished && message.content && <CopyButton text={message.content} />}
        {isUser && !editing && (canEdit || message.edited) && (
          <div className="d-flex align-items-center gap-2 mt-1 user-msg-actions">
            {message.edited && <span className="small text-body-secondary">(edited)</span>}
            {canEdit && (
              <button type="button" className="btn btn-sm msg-action" onClick={() => setEditing(true)} aria-label="Edit message">
                <i className="bi bi-pencil" aria-hidden="true" />
                <span className="ms-1">Edit</span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Files attached to a message: images as thumbnails, other files as chips
function Attachments({ files, hasText }) {
  const images = files.filter((f) => f.content_type.startsWith("image/"));
  const others = files.filter((f) => !f.content_type.startsWith("image/"));
  return (
    <div className={`d-flex flex-column gap-2 ${hasText ? "mb-2" : ""}`}>
      {images.length > 0 && (
        <div className="d-flex flex-wrap gap-2">
          {images.map((f) => (
            <a key={f.id} href={fileUrl(f.url)} target="_blank" rel="noreferrer" className="message-image" title={f.filename}>
              <img src={fileUrl(f.url)} alt={f.filename} loading="lazy" />
            </a>
          ))}
        </div>
      )}
      {others.map((f) => (
        <a key={f.id} href={fileUrl(f.url)} target="_blank" rel="noreferrer" className="message-file text-decoration-none">
          <i className={`bi ${fileIcon(f.content_type)} fs-5`} aria-hidden="true" />
          <span className="text-truncate">{f.filename}</span>
          <span className="small opacity-75 flex-shrink-0">{formatSize(f.size)}</span>
        </a>
      ))}
    </div>
  );
}

// Edit a sent message in place. Enter = save & send, Shift+Enter = new line, Escape = cancel.
function EditBox({ initial, allowEmpty, onSave, onCancel }) {
  const [text, setText] = useState(initial);
  const boxRef = useRef(null);
  const canSave = (text.trim() || allowEmpty) && text.trim() !== initial.trim();

  useEffect(() => {
    const box = boxRef.current;
    box.focus();
    box.setSelectionRange(box.value.length, box.value.length);
  }, []);

  // Grow with the text
  useEffect(() => {
    const box = boxRef.current;
    box.style.height = "auto";
    box.style.height = `${Math.min(box.scrollHeight, 240)}px`;
  }, [text]);

  return (
    <div className="edit-box">
      <textarea
        ref={boxRef}
        className="form-control border-0 bg-transparent shadow-none"
        value={text}
        maxLength={2000}
        rows={1}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Escape") onCancel();
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (canSave) onSave(text);
          }
        }}
        aria-label="Edit your message"
      />
      <div className="d-flex justify-content-between align-items-center gap-2 px-2 pb-2">
        <span className="small text-body-secondary">The replies after this message will be replaced.</span>
        <div className="d-flex gap-2 flex-shrink-0">
          <button type="button" className="btn btn-sm btn-outline-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button type="button" className="btn btn-sm btn-gradient" onClick={() => onSave(text)} disabled={!canSave}>
            Save &amp; send
          </button>
        </div>
      </div>
    </div>
  );
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard blocked (e.g. not a secure context): nothing to do
    }
  };

  return (
    <button type="button" className="btn btn-sm msg-action mt-1" onClick={copy} aria-label="Copy reply">
      <i className={`bi ${copied ? "bi-check2 text-success" : "bi-copy"}`} aria-hidden="true" />
      <span className="ms-1">{copied ? "Copied" : "Copy"}</span>
    </button>
  );
}

export default ChatMessage;
