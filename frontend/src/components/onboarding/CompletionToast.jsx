import { useEffect, useState, useRef } from "react";
import { PartyPopper } from "lucide-react";

function Confetti() {
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    const colors = [
      "#8b5cf6", "#a78bfa", "#c4b5fd", // violet
      "#10b981", "#34d399", "#6ee7b7", // emerald
      "#f59e0b", "#fbbf24", "#fcd34d", // amber
    ];
    const items = [];
    for (let i = 0; i < 50; i++) {
      items.push({
        id: i,
        color: colors[Math.floor(Math.random() * colors.length)],
        left: Math.random() * 100,
        delay: Math.random() * 400,
        size: Math.random() * 6 + 4,
        drift: (Math.random() - 0.5) * 200,
        rotation: Math.random() * 360,
      });
    }
    setParticles(items);
  }, []);

  return (
    <div className="fixed inset-0 z-[1100] pointer-events-none overflow-hidden">
      {particles.map((p) => (
        <div
          key={p.id}
          className="absolute onboarding-confetti"
          style={{
            left: `${p.left}%`,
            top: -20,
            width: p.size,
            height: p.size * 0.6,
            backgroundColor: p.color,
            borderRadius: 2,
            animationDelay: `${p.delay}ms`,
            "--drift": `${p.drift}px`,
            "--rotation": `${p.rotation}deg`,
          }}
        />
      ))}
    </div>
  );
}

export default function CompletionToast({ onDone }) {
  const [showToast, setShowToast] = useState(false);
  const timerRef = useRef();

  useEffect(() => {
    // Show toast 800ms after confetti starts
    const t1 = setTimeout(() => setShowToast(true), 800);
    // Auto-dismiss after 6 seconds
    timerRef.current = setTimeout(() => onDone(), 6000);
    return () => {
      clearTimeout(t1);
      clearTimeout(timerRef.current);
    };
  }, [onDone]);

  return (
    <>
      <Confetti />
      {showToast && (
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-[1101] onboarding-toast-enter">
          <div className="flex items-center gap-3 bg-gray-900 border border-violet-500/30 rounded-xl shadow-2xl shadow-violet-500/10 px-5 py-3.5">
            <PartyPopper className="w-5 h-5 text-violet-400 shrink-0" />
            <p className="text-sm text-gray-200">
              You just generated your first post! You're all set.
            </p>
            <button
              onClick={onDone}
              className="ml-2 px-3 py-1 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-xs font-medium transition-colors shrink-0"
            >
              Got it
            </button>
          </div>
        </div>
      )}
    </>
  );
}
