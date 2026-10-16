import Image from "@tiptap/extension-image";
import { Placeholder } from "@tiptap/extensions";
import { EditorContent, useEditor, useEditorState } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useEffect, useRef, useState } from "react";

import { API_BASE_URL } from "../services/api";
import { ACCEPTED_IMAGES, checkFile, fileUrl, uploadFile } from "../services/uploads";

// Images are saved as "/api/uploads/<id>" (so the content doesn't depend on the
// backend's address) and shown with the full backend URL.
const UploadedImage = Image.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      src: {
        default: null,
        parseHTML: (element) => toStoredSrc(element.getAttribute("src")),
        renderHTML: (attributes) => ({ src: fileUrl(attributes.src) }),
      },
    };
  },
});

function toStoredSrc(src) {
  return src?.startsWith(`${API_BASE_URL}/api/uploads/`) ? src.slice(API_BASE_URL.length) : src;
}

/** The editor's HTML with image URLs back in their stored "/api/uploads/<id>" form. */
export function storedHtml(editor) {
  return editor.getHTML().replaceAll(`${API_BASE_URL}/api/uploads/`, "/api/uploads/");
}

/**
 * A Word-like editor for project write-ups (TipTap). With editable=false it just
 * displays the content; only the editor's known elements are rendered, so stored
 * HTML can't inject scripts. Images upload to /api/uploads via the toolbar, paste
 * or drag & drop.
 *
 *   onChange(html)  called with the stored HTML whenever the content changes
 */
function RichEditor({ content, editable = true, onChange, placeholder = "Start writing..." }) {
  const [uploads, setUploads] = useState(0);
  const [error, setError] = useState("");
  const editorRef = useRef(null);

  // Upload image files and insert them at `pos` (or at the cursor)
  const insertImages = async (files, pos) => {
    setError("");
    for (const file of files) {
      const problem = !file.type.startsWith("image/") ? `"${file.name}" is not an image.` : checkFile(file);
      if (problem) {
        setError(problem);
        continue;
      }
      setUploads((n) => n + 1);
      try {
        const upload = await uploadFile(file);
        const chain = editorRef.current.chain().focus();
        (pos == null ? chain : chain.setTextSelection(pos)).setImage({ src: upload.url, alt: file.name }).run();
      } catch (err) {
        setError(err.message);
      } finally {
        setUploads((n) => n - 1);
      }
    }
  };

  const editor = useEditor({
    editable,
    content: content || "",
    extensions: [
      StarterKit.configure({
        heading: { levels: [2, 3] },
        link: { openOnClick: !editable, autolink: true, HTMLAttributes: { target: "_blank", rel: "noreferrer" } },
      }),
      UploadedImage,
      Placeholder.configure({ placeholder }),
    ],
    editorProps: {
      attributes: { class: "rich-content", "aria-label": "Project write-up" },
      handlePaste: (view, event) => {
        const images = Array.from(event.clipboardData?.files ?? []).filter((f) => f.type.startsWith("image/"));
        if (!images.length) return false;
        insertImages(images);
        return true;
      },
      handleDrop: (view, event, slice, moved) => {
        const files = Array.from(event.dataTransfer?.files ?? []);
        if (moved || !files.length) return false;
        event.preventDefault();
        const pos = view.posAtCoords({ left: event.clientX, top: event.clientY })?.pos;
        insertImages(files, pos);
        return true;
      },
    },
    onUpdate: ({ editor }) => onChange?.(storedHtml(editor)),
  });
  editorRef.current = editor;

  // Switch between viewing and editing without recreating the editor
  useEffect(() => {
    if (editor && editor.isEditable !== editable) editor.setEditable(editable);
  }, [editor, editable]);

  if (!editor) return null;

  return (
    <div className={`rich-editor ${editable ? "is-editing" : ""}`}>
      {editable && <Toolbar editor={editor} onImages={insertImages} uploading={uploads > 0} />}
      {error && (
        <div className="alert alert-danger py-1 px-2 small m-2">
          <i className="bi bi-exclamation-triangle me-1" aria-hidden="true" />
          {error}
        </div>
      )}
      <EditorContent editor={editor} />
    </div>
  );
}

function Toolbar({ editor, onImages, uploading }) {
  const fileInputRef = useRef(null);
  // Re-render the toolbar when the selection's formatting changes
  const state = useEditorState({
    editor,
    selector: ({ editor: e }) => ({
      bold: e.isActive("bold"),
      italic: e.isActive("italic"),
      underline: e.isActive("underline"),
      strike: e.isActive("strike"),
      h2: e.isActive("heading", { level: 2 }),
      h3: e.isActive("heading", { level: 3 }),
      bullet: e.isActive("bulletList"),
      ordered: e.isActive("orderedList"),
      quote: e.isActive("blockquote"),
      code: e.isActive("codeBlock"),
      link: e.isActive("link"),
      canUndo: e.can().undo(),
      canRedo: e.can().redo(),
    }),
  });

  const run = (command) => () => command(editor.chain().focus()).run();

  const setLink = () => {
    const previous = editor.getAttributes("link").href || "";
    const url = window.prompt("Link URL (leave empty to remove):", previous);
    if (url === null) return;
    if (url.trim() === "") editor.chain().focus().extendMarkRange("link").unsetLink().run();
    else editor.chain().focus().extendMarkRange("link").setLink({ href: url.trim() }).run();
  };

  const buttons = [
    ["bi-type-bold", "Bold", state.bold, run((c) => c.toggleBold())],
    ["bi-type-italic", "Italic", state.italic, run((c) => c.toggleItalic())],
    ["bi-type-underline", "Underline", state.underline, run((c) => c.toggleUnderline())],
    ["bi-type-strikethrough", "Strikethrough", state.strike, run((c) => c.toggleStrike())],
    "|",
    ["bi-type-h2", "Heading", state.h2, run((c) => c.toggleHeading({ level: 2 }))],
    ["bi-type-h3", "Subheading", state.h3, run((c) => c.toggleHeading({ level: 3 }))],
    ["bi-list-ul", "Bullet list", state.bullet, run((c) => c.toggleBulletList())],
    ["bi-list-ol", "Numbered list", state.ordered, run((c) => c.toggleOrderedList())],
    ["bi-quote", "Quote", state.quote, run((c) => c.toggleBlockquote())],
    ["bi-code-square", "Code block", state.code, run((c) => c.toggleCodeBlock())],
    "|",
    ["bi-link-45deg", "Link", state.link, setLink],
  ];

  return (
    // preventDefault on mousedown keeps the focus (and cursor, and pending bold/italic)
    // in the text while a toolbar button is clicked
    <div className="editor-toolbar" role="toolbar" aria-label="Formatting" onMouseDown={(e) => e.preventDefault()}>
      {buttons.map((button, i) =>
        button === "|" ? (
          <span key={i} className="toolbar-divider" aria-hidden="true" />
        ) : (
          <button
            key={button[1]}
            type="button"
            className={`toolbar-btn ${button[2] ? "active" : ""}`}
            onClick={button[3]}
            aria-label={button[1]}
            aria-pressed={button[2]}
            title={button[1]}
          >
            <i className={`bi ${button[0]}`} aria-hidden="true" />
          </button>
        )
      )}
      <button
        type="button"
        className="toolbar-btn"
        onClick={() => fileInputRef.current?.click()}
        disabled={uploading}
        aria-label="Add image"
        title="Add image (or paste / drop one)"
      >
        <i className={`bi ${uploading ? "bi-hourglass-split spin" : "bi-image"}`} aria-hidden="true" />
      </button>
      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_IMAGES}
        multiple
        className="d-none"
        onChange={(event) => {
          onImages(Array.from(event.target.files));
          event.target.value = "";
        }}
      />
      <span className="toolbar-divider" aria-hidden="true" />
      <button type="button" className="toolbar-btn" onClick={run((c) => c.undo())} disabled={!state.canUndo} aria-label="Undo" title="Undo">
        <i className="bi bi-arrow-counterclockwise" aria-hidden="true" />
      </button>
      <button type="button" className="toolbar-btn" onClick={run((c) => c.redo())} disabled={!state.canRedo} aria-label="Redo" title="Redo">
        <i className="bi bi-arrow-clockwise" aria-hidden="true" />
      </button>
      {uploading && <span className="small text-body-secondary ms-2">Uploading image...</span>}
    </div>
  );
}

export default RichEditor;
