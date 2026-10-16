import { useId } from "react";

/** A circular progress indicator with the percentage in the middle. */
function ProgressRing({ percent, size = 64, stroke = 7, label }) {
  const id = useId().replace(/:/g, "");
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const value = Math.max(0, Math.min(100, percent));

  return (
    <div className="progress-ring" style={{ width: size, height: size }} role="img" aria-label={label ?? `${value}% done`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
        <defs>
          <linearGradient id={`${id}-ring`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#22d3ee" />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={radius} className="progress-ring-track" strokeWidth={stroke} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={`url(#${id}-ring)`}
          strokeWidth={stroke}
          strokeLinecap="round"
          fill="none"
          className="progress-ring-value"
          style={{ "--circumference": circumference, "--offset": circumference * (1 - value / 100) }}
          strokeDasharray={circumference}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <span className="progress-ring-label" style={{ fontSize: size * 0.24 }}>
        {value}%
      </span>
    </div>
  );
}

export default ProgressRing;
