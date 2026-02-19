import { Check } from "lucide-react";

const STEPS = [
  { number: 1, label: "Select Brand" },
  { number: 2, label: "Compose" },
  { number: 3, label: "Results" },
];

export default function StepIndicator({ currentStep, onStepClick }) {
  return (
    <div className="flex items-center justify-center gap-0">
      {STEPS.map((s, i) => {
        const isCompleted = currentStep > s.number;
        const isActive = currentStep === s.number;
        const isClickable = isCompleted;

        return (
          <div key={s.number} className="flex items-center">
            {/* Step circle + label */}
            <button
              onClick={() => isClickable && onStepClick(s.number)}
              disabled={!isClickable}
              className={`flex items-center gap-2 ${
                isClickable ? "cursor-pointer" : "cursor-default"
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                  isCompleted
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                    : isActive
                      ? "bg-violet-500/20 text-violet-400 border border-violet-500/30"
                      : "bg-gray-800/50 text-gray-500 border border-gray-800"
                }`}
              >
                {isCompleted ? <Check className="w-4 h-4" /> : s.number}
              </div>
              <span
                className={`text-sm font-medium hidden sm:inline transition-colors ${
                  isCompleted
                    ? "text-emerald-400"
                    : isActive
                      ? "text-violet-400"
                      : "text-gray-500"
                }`}
              >
                {s.label}
              </span>
            </button>

            {/* Connector line */}
            {i < STEPS.length - 1 && (
              <div
                className={`w-12 h-px mx-3 ${
                  isCompleted ? "bg-emerald-500/50" : "bg-gray-800"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
