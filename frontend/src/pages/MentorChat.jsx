import { useEffect, useRef, useState } from "react";

import { streamMentorReply } from "../services/mentorChat";

const MAX_LENGTH = 2000; // same limit as the backend (app/ai/schemas.py)

const WELCOME = {
  id: "welcome",
  role: "assistant",
  content: "Hi! I'm your Mentora AI mentor. Ask me anything about learning or your career.",
};

let nextId = 1;
const newId = () => nextId++;

// Chat with the AI mentor. The reply streams in token by token.
function MentorChat() {
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState("");
  // "idle" -> "waiting" (sent, no tokens yet) -> "streaming" -> "idle"
  const [phase, setPhase] = useState("idle");

  const abortRef = useRef(null);
  const listEndRef = useRef(null);
  const inputRef = useRef(null);

  const busy = phase !== "idle";

  // Keep the newest message in view as text arrives
  useEffect(() => {
    listEndRef.current?.scrollIntoView({ block: "end" });
  }, [messages, phase]);

  // Put the cursor back in the input once a reply is finished. This must run
  // after the re-render: a disabled textarea can't receive focus.
  useEffect(() => {
    if (phase === "idle") inputRef.current?.focus();
  }, [phase]);

  // Cancel a running stream if the user leaves the page
  useEffect(() => () => abortRef.current?.abort(), []);

  // Update one message by id (used while its reply streams in)
  const updateMessage = (id, changes) =>
    setMessages((current) =>
      current.map((m) => (m.id === id ? { ...m, ...(typeof changes === "function" ? changes(m) : changes) } : m))
    );

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || busy) return;

    const replyId = newId();
    setMessages((current) => [
      ...current,
      { id: newId(), role: "user", content: text },
      { id: replyId, role: "assistant", content: "" },
    ]);
    setInput("");
    setPhase("waiting");

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await streamMentorReply(text, {
        signal: controller.signal,
        onToken: (token) => {
          setPhase("streaming");
          updateMessage(replyId, (m) => ({ content: m.content + token }));
        },
      });
    } catch (err) {
      if (err.name === "AbortError") {
        updateMessage(replyId, { stopped: true });
      } else {
        updateMessage(replyId, { error: err.message });
      }
    } finally {
      abortRef.current = null;
      setPhase("idle");
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    sendMessage();
  };

  // Enter sends, Shift+Enter makes a new line
  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="d-flex flex-column chat-page">
      <h1 className="h3 mb-3">AI Mentor</h1>

      <div className="card flex-grow-1 overflow-hidden">
        {/* Message list */}
        <div className="card-body overflow-auto" aria-live="polite">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              isWaiting={phase === "waiting" && message.role === "assistant" && message.content === "" && !message.error}
            />
          ))}
          <div ref={listEndRef} />
        </div>

        {/* Input box */}
        <form className="card-footer bg-body" onSubmit={handleSubmit}>
          <div className="d-flex gap-2 align-items-end">
            <textarea
              ref={inputRef}
              className="form-control"
              rows={2}
              placeholder="Ask your mentor... (Enter to send, Shift+Enter for a new line)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              maxLength={MAX_LENGTH}
              disabled={busy}
              aria-label="Message"
              autoFocus
            />
            {busy ? (
              <button type="button" className="btn btn-outline-secondary" onClick={() => abortRef.current?.abort()}>
                Stop
              </button>
            ) : (
              <button type="submit" className="btn btn-primary" disabled={!input.trim()}>
                Send
              </button>
            )}
          </div>
          {input.length > MAX_LENGTH * 0.9 && (
            <div className="form-text text-end">
              {input.length} / {MAX_LENGTH}
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

function ChatMessage({ message, isWaiting }) {
  const isUser = message.role === "user";

  return (
    <div className={`d-flex mb-3 ${isUser ? "justify-content-end" : "justify-content-start"}`}>
      <div
        className={`chat-bubble rounded-3 px-3 py-2 ${isUser ? "bg-primary text-white" : "bg-body-tertiary border"}`}
        data-role={message.role}
      >
        {isWaiting ? (
          <span className="text-body-secondary">
            <span className="spinner-grow spinner-grow-sm me-2" role="status" />
            Thinking...
          </span>
        ) : (
          message.content
        )}

        {message.stopped && <div className="small text-body-secondary fst-italic mt-1">(stopped)</div>}
        {message.error && (
          <div className="alert alert-danger py-1 px-2 mb-0 mt-1 small" role="alert">
            {message.error}
          </div>
        )}
      </div>
    </div>
  );
}

export default MentorChat;
