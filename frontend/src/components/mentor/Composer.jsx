import { useEffect, useImperativeHandle, useRef, useState } from "react";

import {
  ACCEPTED_DOCUMENTS,
  ACCEPTED_IMAGES,
  MAX_UPLOAD_MB,
  checkFile,
  deleteUpload,
  fileIcon,
  formatSize,
  uploadFile,
} from "../../services/uploads";

const MAX_LENGTH = 2000; // same limit as the backend (app/ai/schemas.py)
const MAX_ATTACHMENTS = 5; // per message, same as the backend
const MAX_INPUT_HEIGHT = 200; // px; the input grows with its text up to this

let nextKey = 1;

/**
 * The message box: text, attachments (button, drag & drop via ref.addFiles, or
 * paste), Send / Stop. Files upload as soon as they're added.
 *
 *   onSend(text, attachments)  attachments: [{ id, filename, content_type, size, url }]
 *   ref                        { addFiles(files), focus() } for the parent (drag & drop)
 */
function Composer({ busy, onSend, onStop, placeholder = "Message Mentora...", ref }) {
  const [text, setText] = useState("");
  // [{ key, name, type, size, preview, progress, upload, error, controller }]
  const [files, setFiles] = useState([]);
  const [notice, setNotice] = useState("");

  const inputRef = useRef(null);
  const filesRef = useRef(files);
  filesRef.current = files;

  const uploading = files.some((f) => !f.upload && !f.error);
  const ready = files.filter((f) => f.upload);
  const canSend = !busy && !uploading && (text.trim() || ready.length > 0);

  const updateFile = (key, changes) => setFiles((current) => current.map((f) => (f.key === key ? { ...f, ...changes } : f)));

  const addFiles = (fileList) => {
    setNotice("");
    const room = MAX_ATTACHMENTS - filesRef.current.length;
    const incoming = Array.from(fileList);
    if (incoming.length > room) setNotice(`You can attach up to ${MAX_ATTACHMENTS} files per message.`);

    for (const file of incoming.slice(0, Math.max(room, 0))) {
      const key = nextKey++;
      const error = checkFile(file);
      const controller = new AbortController();
      const item = {
        key,
        name: file.name,
        type: file.type,
        size: file.size,
        preview: file.type.startsWith("image/") ? URL.createObjectURL(file) : null,
        progress: 0,
        upload: null,
        error,
        controller,
      };
      setFiles((current) => [...current, item]);
      if (error) continue;

      uploadFile(file, { signal: controller.signal, onProgress: (progress) => updateFile(key, { progress }) })
        .then((upload) => updateFile(key, { upload, progress: 1 }))
        .catch((err) => {
          if (err.name !== "AbortError") updateFile(key, { error: err.message });
        });
    }
  };

  const removeFile = (item) => {
    item.controller.abort();
    if (item.upload) deleteUpload(item.upload.id); // never sent, so not needed on the server
    if (item.preview) URL.revokeObjectURL(item.preview);
    setFiles((current) => current.filter((f) => f.key !== item.key));
  };

  useImperativeHandle(ref, () => ({ addFiles, focus: () => inputRef.current?.focus() }));

  // Free image previews when the composer goes away
  useEffect(() => () => filesRef.current.forEach((f) => f.preview && URL.revokeObjectURL(f.preview)), []);

  // Focus the input when it's ready for typing. This must run after the re-render:
  // a disabled textarea can't receive focus.
  useEffect(() => {
    if (!busy) inputRef.current?.focus();
  }, [busy]);

  // Grow the input with its text (and shrink it back after sending)
  useEffect(() => {
    const box = inputRef.current;
    if (!box) return;
    box.style.height = "auto";
    box.style.height = `${Math.min(box.scrollHeight, MAX_INPUT_HEIGHT)}px`;
  }, [text]);

  const send = () => {
    if (!canSend) return;
    onSend(
      text.trim(),
      ready.map((f) => f.upload)
    );
    files.forEach((f) => f.preview && URL.revokeObjectURL(f.preview));
    setText("");
    setFiles([]);
    setNotice("");
  };

  const handleKeyDown = (event) => {
    // Enter sends, Shift+Enter makes a new line
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  };

  // Pasting an image (e.g. a screenshot) attaches it
  const handlePaste = (event) => {
    const pasted = Array.from(event.clipboardData?.files ?? []);
    if (pasted.length) {
      event.preventDefault();
      addFiles(pasted);
    }
  };

  return (
    <form
      className="card-footer bg-transparent border-0 pt-0"
      onSubmit={(event) => {
        event.preventDefault();
        send();
      }}
    >
      <div className="composer">
        {files.length > 0 && (
          <div className="d-flex flex-wrap gap-2 p-2 pb-1">
            {files.map((f) => (
              <AttachmentPreview key={f.key} item={f} onRemove={() => removeFile(f)} />
            ))}
          </div>
        )}

        <div className="d-flex gap-2 align-items-end">
          <AttachMenu
            disabled={busy || files.length >= MAX_ATTACHMENTS}
            onFiles={addFiles}
          />

          <textarea
            ref={inputRef}
            className="form-control border-0 bg-transparent shadow-none"
            rows={1}
            placeholder={placeholder}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            maxLength={MAX_LENGTH}
            disabled={busy}
            aria-label="Message"
          />

          {busy ? (
            <button type="button" className="btn btn-outline-secondary composer-btn" onClick={onStop} aria-label="Stop" title="Stop">
              <i className="bi bi-stop-fill" aria-hidden="true" />
            </button>
          ) : (
            <button
              type="submit"
              className="btn btn-gradient composer-btn"
              disabled={!canSend}
              aria-label="Send"
              title={uploading ? "Waiting for uploads to finish" : "Send"}
            >
              <i className="bi bi-send-fill" aria-hidden="true" />
            </button>
          )}
        </div>
      </div>

      <div className="d-flex justify-content-between form-text px-2">
        {notice ? (
          <span className="text-warning">{notice}</span>
        ) : (
          <span className="d-none d-sm-inline">Enter to send · Shift+Enter for a new line · drop or paste files to attach</span>
        )}
        {text.length > MAX_LENGTH * 0.9 && (
          <span className="ms-auto">
            {text.length} / {MAX_LENGTH}
          </span>
        )}
      </div>
    </form>
  );
}

// The "+" button: a small menu to upload images or other files
function AttachMenu({ disabled, onFiles }) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);
  const imageInputRef = useRef(null);
  const fileInputRef = useRef(null);

  // Close on a click outside or Escape
  useEffect(() => {
    if (!open) return;
    const onClick = (event) => !menuRef.current?.contains(event.target) && setOpen(false);
    const onKey = (event) => event.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const pick = (inputRef) => {
    setOpen(false);
    inputRef.current?.click();
  };

  const onChange = (event) => {
    onFiles(event.target.files);
    event.target.value = ""; // allow picking the same file again
  };

  return (
    <div className="attach-menu-wrap" ref={menuRef}>
      <button
        type="button"
        className={`btn composer-attach ${open ? "open" : ""}`}
        onClick={() => setOpen((o) => !o)}
        disabled={disabled}
        aria-label="Add images or files"
        aria-haspopup="menu"
        aria-expanded={open}
        title="Add images or files"
      >
        <i className="bi bi-plus-lg" aria-hidden="true" />
      </button>

      {open && (
        <div className="attach-menu" role="menu">
          <button type="button" role="menuitem" className="attach-menu-item" onClick={() => pick(imageInputRef)}>
            <span className="attach-menu-icon">
              <i className="bi bi-image" aria-hidden="true" />
            </span>
            <span>
              <span className="d-block fw-semibold">Upload images</span>
              <span className="d-block small text-body-secondary">PNG, JPEG, WebP, GIF</span>
            </span>
          </button>
          <button type="button" role="menuitem" className="attach-menu-item" onClick={() => pick(fileInputRef)}>
            <span className="attach-menu-icon">
              <i className="bi bi-file-earmark-text" aria-hidden="true" />
            </span>
            <span>
              <span className="d-block fw-semibold">Upload files</span>
              <span className="d-block small text-body-secondary">PDF, code, text, CSV, JSON</span>
            </span>
          </button>
          <div className="small text-body-secondary px-2 pt-1">
            Up to {MAX_ATTACHMENTS} files, {MAX_UPLOAD_MB} MB each. You can also drop or paste them.
          </div>
        </div>
      )}

      <input ref={imageInputRef} type="file" className="d-none" multiple accept={ACCEPTED_IMAGES} onChange={onChange} />
      <input ref={fileInputRef} type="file" className="d-none" multiple accept={ACCEPTED_DOCUMENTS} onChange={onChange} />
    </div>
  );
}

function AttachmentPreview({ item, onRemove }) {
  const done = !!item.upload;
  return (
    <div className={`attachment-preview ${item.error ? "has-error" : ""}`} title={item.error || item.name}>
      {item.preview ? (
        <img src={item.preview} alt="" className="attachment-thumb" />
      ) : (
        <span className="attachment-thumb">
          <i className={`bi ${fileIcon(item.type)} fs-4`} aria-hidden="true" />
        </span>
      )}
      <span className="attachment-meta">
        <span className="d-block text-truncate small fw-semibold">{item.name}</span>
        <span className={`d-block small ${item.error ? "text-danger" : "text-body-secondary"}`}>
          {item.error ? "Failed" : done ? formatSize(item.size) : `Uploading ${Math.round(item.progress * 100)}%`}
        </span>
      </span>
      {!done && !item.error && (
        <span className="attachment-progress" style={{ width: `${Math.round(item.progress * 100)}%` }} />
      )}
      <button type="button" className="btn-close attachment-remove" onClick={onRemove} aria-label={`Remove ${item.name}`} />
    </div>
  );
}

export default Composer;
