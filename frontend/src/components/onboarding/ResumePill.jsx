import { Sparkles } from "lucide-react";

export default function ResumePill({ onResume }) {
  return (
    <button
      onClick={onResume}
      className="fixed bottom-6 right-6 z-[999] flex items-center gap-2 bg-gray-800 border border-gray-700 rounded-full px-4 py-2 text-xs text-violet-400 hover:bg-gray-700 hover:border-gray-600 transition-colors shadow-lg onboarding-fade-in"
    >
      <Sparkles className="w-3.5 h-3.5" />
      Resume tutorial
    </button>
  );
}
