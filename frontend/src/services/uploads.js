// Upload files to the backend (POST /api/uploads) and build their URLs.
// Used for chat attachments and images in project write-ups.

import { API_BASE_URL, getErrorMessage } from "./api";

// Must match backend/app/services/upload_service.py
export const MAX_UPLOAD_MB = 20;
export const ACCEPTED_FILES = [
  "image/png",
  "image/jpeg",
  "image/webp",
  "image/gif",
  "application/pdf",
  ...[".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".toml", ".ini", ".xml", ".log"],
  ...[".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".sql", ".sh"],
  ...[".java", ".c", ".h", ".cpp", ".cs", ".go", ".rs", ".rb", ".php", ".kt", ".swift"],
].join(",");
export const ACCEPTED_IMAGES = "image/png,image/jpeg,image/webp,image/gif";
// Everything except images: PDFs and text/code files
export const ACCEPTED_DOCUMENTS = ACCEPTED_FILES.split(",")
  .filter((type) => !type.startsWith("image/"))
  .join(",");

/** Full URL of an uploaded file: "/api/uploads/<id>" -> "http://127.0.0.1:8002/api/uploads/<id>" */
export function fileUrl(path) {
  return path?.startsWith("/api/") ? `${API_BASE_URL}${path}` : path;
}

/** A client-side check before uploading. Returns an error message, or "" if OK. */
export function checkFile(file) {
  if (file.size === 0) return `"${file.name}" is empty.`;
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `"${file.name}" is larger than ${MAX_UPLOAD_MB} MB.`;
  return "";
}

/**
 * Upload one file. Resolves with { id, filename, content_type, size, url }.
 * onProgress(0..1) is called while it uploads. Uses XMLHttpRequest because
 * fetch() can't report upload progress.
 */
export function uploadFile(file, { onProgress, signal } = {}) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}/api/uploads`);
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.(event.loaded / event.total);
    };
    xhr.onload = () => {
      let data = null;
      try {
        data = JSON.parse(xhr.responseText);
      } catch {
        // not JSON
      }
      if (xhr.status >= 200 && xhr.status < 300) resolve(data);
      else reject(new Error(getErrorMessage(data, xhr.status)));
    };
    xhr.onerror = () => reject(new Error(`Cannot reach the backend at ${API_BASE_URL}. Is it running?`));
    xhr.onabort = () => reject(new DOMException("Upload cancelled", "AbortError"));
    signal?.addEventListener("abort", () => xhr.abort());

    const form = new FormData();
    form.append("file", file);
    xhr.send(form);
  });
}

/** Delete an uploaded file (e.g. an attachment removed before sending). Errors are ignored. */
export function deleteUpload(id) {
  return fetch(`${API_BASE_URL}/api/uploads/${id}`, { method: "DELETE" }).catch(() => {});
}

/** Bootstrap icon for a file type */
export function fileIcon(contentType) {
  if (contentType?.startsWith("image/")) return "bi-file-earmark-image";
  if (contentType === "application/pdf") return "bi-file-earmark-pdf";
  return "bi-file-earmark-code";
}

/** 1536 -> "1.5 KB" */
export function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
