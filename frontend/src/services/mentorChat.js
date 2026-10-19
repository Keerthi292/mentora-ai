// Streams the AI mentor's reply from POST /api/ai/chat/stream.

import { API_BASE_URL, checkUnauthorized, getErrorMessage } from "./api";
import { readSseStream } from "./sse";

/**
 * Send a message and receive the reply piece by piece.
 *
 *   await streamMentorReply("How do I learn React?", {
 *     attachments,              // ids of files uploaded for this message (services/uploads.js)
 *     history,                  // earlier messages: [{ role, content, attachments }]
 *     onToken: (text) => ...,   // called for every new piece of the reply
 *     signal,                   // optional AbortController.signal to cancel
 *   });
 *
 * Resolves when the reply is complete ([DONE]); throws an Error otherwise.
 */
export async function streamMentorReply(message, { attachments = [], history = [], onToken, signal } = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/ai/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ message, attachments, history }),
      signal,
    });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw new Error("Cannot reach the backend. Is it running?");
  }

  // Errors before streaming starts (e.g. 422 for an empty message) come back as JSON
  if (!response.ok) {
    checkUnauthorized(response.status, "/api/ai/chat/stream");
    const data = await response.json().catch(() => null);
    throw new Error(getErrorMessage(data, response.status));
  }

  const finished = await readSseStream(response.body, (payload) => {
    if (payload === "[DONE]") return true; // stop reading

    const event = JSON.parse(payload);
    if (event.error) throw new Error(event.error);
    if (event.token) onToken(event.token);
    return false;
  });

  if (!finished) {
    throw new Error("The connection closed before the reply was finished.");
  }
}
