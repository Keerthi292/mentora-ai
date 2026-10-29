import { useEffect, useState } from "react";

import BotAvatar from "./BotAvatar";

const DEFAULT_MESSAGES = ["Waking up your mentor", "Gathering your goals", "Polishing your dashboard", "Almost there"];

/**
 * Animated loading screen: the robot inside orbiting rings, a shimmering
 * wordmark and rotating status lines (the animations live in index.css).
 *
 *   fullscreen  covers the whole page with drifting glow blobs (app start);
 *               otherwise a compact block that fits inside a page
 *   messages    status lines shown one after another
 */
function LoadingScreen({ fullscreen = false, messages = DEFAULT_MESSAGES }) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (messages.length < 2) return;
    const timer = setInterval(() => setIndex((i) => (i + 1) % messages.length), 2500);
    return () => clearInterval(timer);
  }, [messages.length]);

  return (
    <div className={`loader ${fullscreen ? "loader-fullscreen" : ""}`} role="status" aria-live="polite">
      {fullscreen && (
        <div className="loader-blobs" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      )}

      <div className="loader-orbit" aria-hidden="true">
        <span className="loader-ring loader-ring-1" />
        <span className="loader-ring loader-ring-2" />
        <span className="loader-dot loader-dot-1" />
        <span className="loader-dot loader-dot-2" />
        <span className="loader-halo" />
        <BotAvatar size={fullscreen ? 84 : 56} float sparkles />
      </div>

      {fullscreen && (
        <>
          <h1 className="loader-title">Mentora AI</h1>
          <p className="loader-caption">Your personal learning and career companion</p>
        </>
      )}

      {/* key restarts the fade-in each time the line changes */}
      <p key={index} className="loader-message">
        {messages[index % messages.length]}
        <span className="loader-ellipsis" aria-hidden="true">
          <span>.</span>
          <span>.</span>
          <span>.</span>
        </span>
      </p>

      <div className="loader-bar" aria-hidden="true">
        <span />
      </div>
    </div>
  );
}

export default LoadingScreen;
