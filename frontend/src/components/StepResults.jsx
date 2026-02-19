import { RotateCcw, ArrowLeft } from "lucide-react";
import PipelineStatus from "./PipelineStatus";
import PostCard from "./PostCard";
import MarkdownText from "./MarkdownText";

export default function StepResults({
  result,
  loading,
  activeStage,
  completedStages,
  onGenerateAgain,
  onDifferentBrand,
}) {
  return (
    <div className="space-y-6">
      {/* Pipeline Progress */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Pipeline Progress
        </h3>
        <PipelineStatus
          activeStage={activeStage}
          completed={completedStages}
        />
      </div>

      {/* Critic Summary */}
      {result?.critic_summary && (
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Critic Summary
          </h3>
          <div className="text-sm text-gray-300 leading-relaxed">
            <MarkdownText text={result.critic_summary} />
          </div>
        </div>
      )}

      {/* Generated Posts */}
      {result?.posts?.length > 0 && (
        <>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">
              Generated Posts
            </h2>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span>Revisions: {result.revision_count}</span>
              <span>Thread: {result.thread_id?.slice(0, 8)}...</span>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {result.posts.map((post, i) => (
              <PostCard key={i} post={post} />
            ))}
          </div>
        </>
      )}

      {/* Action buttons */}
      {!loading && result && (
        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={onGenerateAgain}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Generate Again
          </button>
          <button
            onClick={onDifferentBrand}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm font-medium transition-colors border border-gray-700"
          >
            <ArrowLeft className="w-4 h-4" />
            Different Brand
          </button>
        </div>
      )}
    </div>
  );
}
