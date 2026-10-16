import { useId } from "react";

/**
 * Mentora's animated robot (inline SVG; the animations live in index.css).
 *
 *   size      width/height in px
 *   thinking  jitters and looks around (while a reply is being written)
 *   float     gently bobs up and down
 *   sparkles  twinkling stars around it
 */
function BotAvatar({ size = 40, thinking = false, float = false, sparkles = false, className = "" }) {
  // Unique gradient ids, so several bots on one page don't clash
  const id = useId().replace(/:/g, "");
  const classes = ["bot", thinking && "bot-thinking", float && "bot-float", className].filter(Boolean).join(" ");

  return (
    <svg className={classes} width={size} height={size} viewBox="0 0 120 120" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id={`${id}-head`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#a78bfa" />
          <stop offset="100%" stopColor="#22d3ee" />
        </linearGradient>
        <radialGradient id={`${id}-glow`}>
          <stop offset="0%" stopColor="#fde68a" />
          <stop offset="100%" stopColor="#f59e0b" />
        </radialGradient>
      </defs>

      <g className="bot-body">
        {/* Antenna with a glowing tip */}
        <line x1="60" y1="24" x2="60" y2="12" stroke="#a78bfa" strokeWidth="4" strokeLinecap="round" />
        <circle className="bot-antenna" cx="60" cy="9" r="6" fill={`url(#${id}-glow)`} />

        {/* Ears */}
        <rect x="14" y="44" width="10" height="20" rx="4" fill="#7c3aed" />
        <rect x="96" y="44" width="10" height="20" rx="4" fill="#7c3aed" />

        {/* Head and face screen */}
        <rect x="22" y="24" width="76" height="62" rx="22" fill={`url(#${id}-head)`} />
        <rect x="31" y="35" width="58" height="40" rx="15" fill="#0b1020" />

        {/* Eyes (they blink, and dart around while thinking) */}
        <g className="bot-eyes">
          <rect className="bot-eye" x="42" y="47" width="11" height="14" rx="5.5" fill="#67e8f9" />
          <rect className="bot-eye" x="67" y="47" width="11" height="14" rx="5.5" fill="#67e8f9" />
        </g>
        <path d="M51 67 Q60 73 69 67" stroke="#67e8f9" strokeWidth="3" fill="none" strokeLinecap="round" />

        {/* Shoulders */}
        <rect x="40" y="88" width="40" height="20" rx="10" fill="#7c3aed" />
        <circle cx="60" cy="98" r="4" fill="#67e8f9" className="bot-heart" />
      </g>

      {sparkles && (
        <g fill="#fde68a">
          {[
            [12, 18, 1],
            [104, 14, 0.8],
            [108, 92, 0.9],
            [8, 96, 0.7],
          ].map(([x, y, scale], i) => (
            <path
              key={i}
              className="bot-sparkle"
              style={{ animationDelay: `${i * 0.45}s` }}
              transform={`translate(${x} ${y}) scale(${scale})`}
              d="M0 -9 C1 -2 2 -1 9 0 C2 1 1 2 0 9 C-1 2 -2 1 -9 0 C-2 -1 -1 -2 0 -9 Z"
            />
          ))}
        </g>
      )}
    </svg>
  );
}

export default BotAvatar;
