import { Sparkles } from "lucide-react";

export default function WelcomeModal({ onStart, onSkip }) {
  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="max-w-md w-full rounded-2xl bg-gray-900 border border-gray-800 p-8 text-center onboarding-fade-in">
        <div className="flex justify-center mb-5">
          <Sparkles className="w-10 h-10 text-violet-400 onboarding-pulse" />
        </div>
        <h2 className="text-xl font-bold text-white mb-3">
          Welcome to AI Social Manager
        </h2>
        <p className="text-sm text-gray-400 leading-relaxed mb-8">
          Let's get you set up in about 2 minutes. You'll create a brand
          profile, connect an AI provider, and generate your first post.
        </p>
        <button
          onClick={onStart}
          className="w-full py-2.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors"
        >
          Get Started
        </button>
        <button
          onClick={onSkip}
          className="mt-3 text-xs text-gray-600 hover:text-gray-400 transition-colors"
        >
          Skip Tutorial
        </button>
      </div>
    </div>
  );
}
