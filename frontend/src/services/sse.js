// Reads a Server-Sent Events (SSE) stream from a fetch() response body.
//
// The backend sends events like this, each ending with a blank line:
//   data: {"token": "Hello "}
//
//   data: [DONE]
//
// Network chunks don't line up with events: one read() can contain half an
// event or several events. So we keep a text buffer and only handle complete
// events (text up to a blank line); the rest waits for the next chunk.

/**
 * Call onData(payload) for every "data:" payload in the stream, in order.
 * Stops early (and returns true) if onData returns true.
 * Returns false if the stream ended without onData asking to stop.
 */
export async function readSseStream(body, onData) {
  const reader = body.getReader();
  // stream: true handles multi-byte characters (e.g. emoji) split across chunks
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      // Normalise Windows-style line endings so "\n\n" always marks an event end
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n?/g, "\n");

      let eventEnd;
      while ((eventEnd = buffer.indexOf("\n\n")) !== -1) {
        const rawEvent = buffer.slice(0, eventEnd);
        buffer = buffer.slice(eventEnd + 2);

        if (handleEvent(rawEvent, onData)) return true;
      }
    }
    // The stream closed; handle a last event that had no trailing blank line
    buffer += decoder.decode();
    return buffer.trim() ? handleEvent(buffer, onData) : false;
  } finally {
    reader.releaseLock();
  }
}

// One event can have several "data:" lines; SSE joins them with "\n"
function handleEvent(rawEvent, onData) {
  const dataLines = rawEvent
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).replace(/^ /, "")); // drop the optional single space

  if (dataLines.length === 0) return false; // e.g. a comment line like ": ping"
  return onData(dataLines.join("\n")) === true;
}
