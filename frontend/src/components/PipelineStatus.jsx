import { Search, Lightbulb, PenTool, ShieldCheck, Loader2 } from "lucide-react";

const stages = [
  { key: "research", icon: Search, label: "Trend Research" },
  { key: "strategy", icon: Lightbulb, label: "Strategy" },
  { key: "writing", icon: PenTool, label: "Writing" },
  { key: "review", icon: ShieldCheck, label: "Critic Review" },
];

export default function PipelineStatus({ activeStage, completed }) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {stages.map(({ key, icon: Icon, label }, i) => {
        const isActive = activeStage === key;
        const isDone = completed?.includes(key);

        return (
          <div key={key} className="flex items-center gap-2">
            <div
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? "bg-violet-500/20 text-violet-300 border border-violet-500/30"
                  : isDone
                    ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                    : "bg-gray-800/50 text-gray-500 border border-gray-800"
              }`}
            >
              {isActive ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Icon className="w-3.5 h-3.5" />
              )}
              {label}
            </div>
            {i < stages.length - 1 && (
              <div
                className={`w-6 h-px ${isDone ? "bg-emerald-500/50" : "bg-gray-800"}`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
