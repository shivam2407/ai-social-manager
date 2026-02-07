export default function ScoreRing({ score, size = 56 }) {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const normalized = Math.max(0, Math.min(10, score)) / 10;
  const offset = circumference * (1 - normalized);

  const color =
    score >= 8
      ? "text-emerald-400"
      : score >= 6
        ? "text-amber-400"
        : "text-red-400";

  const strokeColor =
    score >= 8
      ? "stroke-emerald-400"
      : score >= 6
        ? "stroke-amber-400"
        : "stroke-red-400";

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={4}
          className="text-gray-800"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={4}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={`${strokeColor} score-ring-animated`}
        />
      </svg>
      <span className={`absolute text-sm font-bold ${color}`}>
        {score.toFixed(1)}
      </span>
    </div>
  );
}
