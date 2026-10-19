import { useEffect, useRef, useState } from "react";

import { api } from "../services/api";
import BotAvatar from "./BotAvatar";

// What each page's assistant can do, shown as examples in an empty chat
const PAGES = {
  skills: {
    title: "Skills",
    examples: ["Set my Docker level to advanced", "Add Kubernetes as a skill I want to learn", "Which skills have no level?"],
  },
  goals: {
    title: "Goals",
    examples: ["Add a goal to learn LangGraph by December", "I'm 60% done with my first goal", "Pause my oldest goal"],
  },
  career: {
    title: "Career",
    examples: ["Add Docker to my AI engineer role", "Add a target role: ML Engineer", "Set my target date to June 2027"],
  },
  projects: {
    title: "Projects",
    examples: ["Mark my website project as completed", "Add FastAPI to the technologies of my last project", "Add a project called Portfolio"],
  },
};

const MAX_HISTORY = 20;

/**
 * A small floating chat on a page that can change that page's data ("set Docker
 * to advanced"). `page` is "skills", "goals", "career" or "projects";
 * `onChanged()` is called after a change so the page reloads its list.
 * The chat itself is not saved: it starts fresh on every visit.
 */
function PageAssistant({ page, onChanged }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]); // { role, content, actions?, error? }
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const { title, examples } = PAGES[page];

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages, sending]);

  const send = async (message) => {
    message = message.trim();
    if (!message || sending) return;
    const history = messages
      .filter((m) => !m.error)
      .slice(-MAX_HISTORY)
      .map(({ role, content }) => ({ role, content }));
    setMessages((current) => [...current, { role: "user", content: message }]);
    setText("");
    setSending(true);
    try {
      const data = await api.post("/api/ai/assistant", { page, message, history });
      setMessages((current) => [...current, { role: "assistant", content: data.reply, actions: data.actions }]);
      if (data.changed) onChanged?.();
    } catch (err) {
      setMessages((current) => [...current, { role: "assistant", content: err.message, error: true }]);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  return (
    <>
      {open && (
        <section className="assistant-panel card shadow-lg" aria-label={`${title} assistant`}>
          <div className="assistant-header d-flex align-items-center gap-2">
            <BotAvatar size={30} thinking={sending} />
            <div className="flex-grow-1 lh-sm">
              <div className="fw-semibold">Mentora</div>
              <div className="small text-body-secondary">Changes things on the {title} page</div>
            </div>
            {messages.length > 0 && (
              <button
                type="button"
                className="btn btn-sm btn-link text-body-secondary p-1"
                title="Clear chat"
                aria-label="Clear chat"
                disabled={sending}
                onClick={() => setMessages([])}
              >
                <i className="bi bi-arrow-counterclockwise" aria-hidden="true" />
              </button>
            )}
            <button type="button" className="btn-close" aria-label="Close" onClick={() => setOpen(false)} />
          </div>

          <div className="assistant-messages" aria-live="polite">
            {messages.length === 0 && (
              <div className="text-center text-body-secondary small py-2">
                <p className="mb-2">Tell me what to change here. Try:</p>
                <div className="d-flex flex-column gap-2">
                  {examples.map((example) => (
                    <button key={example} type="button" className="btn btn-sm suggestion-chip" onClick={() => send(example)}>
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i} className={`d-flex mb-2 ${m.role === "user" ? "justify-content-end" : ""}`}>
                <div
                  className={`assistant-bubble ${m.role === "user" ? "chat-bubble-user" : "chat-bubble-bot"} ${
                    m.error ? "text-danger" : ""
                  }`}
                >
                  {m.content}
                  {m.actions?.length > 0 && (
                    <ul className="assistant-actions list-unstyled mb-0 mt-2">
                      {m.actions.map((action) => (
                        <li key={action}>
                          <i className="bi bi-check-circle-fill text-success me-1" aria-hidden="true" />
                          {action}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ))}

            {sending && (
              <div className="assistant-bubble chat-bubble-bot d-inline-block">
                <span className="typing-dots" aria-label="Mentora is working">
                  <span />
                  <span />
                  <span />
                </span>
              </div>
            )}
            <div ref={endRef} />
          </div>

          <form
            className="assistant-input d-flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              send(text);
            }}
          >
            <input
              ref={inputRef}
              className="form-control form-control-sm"
              placeholder={`Ask to change your ${title.toLowerCase()}...`}
              value={text}
              maxLength={2000}
              onChange={(e) => setText(e.target.value)}
              disabled={sending}
              aria-label="Message"
            />
            <button type="submit" className="btn btn-sm btn-gradient" disabled={sending || !text.trim()} aria-label="Send">
              <i className="bi bi-send" aria-hidden="true" />
            </button>
          </form>
        </section>
      )}

      <button
        type="button"
        className={`assistant-fab ${open ? "open" : ""}`}
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-label={open ? "Close Mentora" : `Ask Mentora to change your ${title.toLowerCase()}`}
        title={open ? "Close" : "Ask Mentora"}
      >
        {open ? <i className="bi bi-x-lg" aria-hidden="true" /> : <BotAvatar size={40} />}
      </button>
    </>
  );
}

export default PageAssistant;
