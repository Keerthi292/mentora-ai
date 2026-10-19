import { useEffect, useState } from "react";

import useMe from "../../hooks/useMe";
import BotAvatar from "../BotAvatar";

// Quick-start ideas. Clicking one opens a new chat and sends the prompt.
export const SUGGESTIONS = [
  {
    icon: "bi-signpost-split",
    title: "Plan my next step",
    prompt: "Based on my skills and goals, what should I focus on next?",
  },
  {
    icon: "bi-calendar-check",
    title: "Build a study routine",
    prompt: "Help me build a realistic weekly study routine.",
  },
  {
    icon: "bi-lightbulb",
    title: "Project ideas",
    prompt: "Suggest a portfolio project that fits my skills.",
  },
  {
    icon: "bi-briefcase",
    title: "Career advice",
    prompt: "How can I prepare for the role I'm aiming for?",
  },
];

const TAGLINES = [
  "plan what to learn next",
  "stay consistent with your goals",
  "turn ideas into portfolio projects",
  "prepare for your dream role",
];

/** The Mentor landing screen, shown before a chat is opened. */
function MentorHome({ lastConversation, onNewChat, onOpen, onSuggestion }) {
  const [tagline, setTagline] = useState(0);
  const { name } = useMe();

  // Rotate the tagline every few seconds
  useEffect(() => {
    const timer = setInterval(() => setTagline((i) => (i + 1) % TAGLINES.length), 2800);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="mentor-home flex-grow-1 overflow-auto min-h-0">
      <div className="mentor-home-inner text-center mx-auto px-2 py-4 py-md-5">
        <div className="hero-bot mx-auto mb-3">
          <span className="hero-glow" aria-hidden="true" />
          <BotAvatar size={128} float sparkles />
        </div>

        <h1 className="h3 fw-bold mb-2">
          Hi{name && ` ${name}`}, I'm <span className="text-gradient">Mentora</span>
        </h1>
        <p className="text-body-secondary mb-4">
          Your personal AI mentor. I'm here to help you{" "}
          <span key={tagline} className="tagline fw-semibold text-body">
            {TAGLINES[tagline]}.
          </span>
        </p>

        <div className="d-flex flex-wrap justify-content-center gap-2 mb-5">
          <button type="button" className="btn btn-gradient px-4" onClick={onNewChat}>
            <i className="bi bi-chat-heart me-2" aria-hidden="true" />
            Start a new chat
          </button>
          {lastConversation && (
            <button
              type="button"
              className="btn btn-outline-secondary px-4 text-truncate continue-btn"
              onClick={() => onOpen(lastConversation.id)}
              title={lastConversation.title}
            >
              <i className="bi bi-clock-history me-2" aria-hidden="true" />
              Continue: {lastConversation.title}
            </button>
          )}
        </div>

        <div className="row g-3 text-start">
          {SUGGESTIONS.map((s, i) => (
            <div className="col-12 col-sm-6" key={s.title}>
              <button
                type="button"
                className="suggestion-card w-100 h-100 text-start"
                style={{ animationDelay: `${i * 80}ms` }}
                onClick={() => onSuggestion(s.prompt)}
              >
                <span className="suggestion-icon">
                  <i className={`bi ${s.icon}`} aria-hidden="true" />
                </span>
                <span className="d-block fw-semibold mt-2">{s.title}</span>
                <span className="d-block small text-body-secondary">{s.prompt}</span>
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default MentorHome;
