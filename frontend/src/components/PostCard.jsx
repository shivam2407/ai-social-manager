import PlatformBadge from "./PlatformBadge";
import ScoreRing from "./ScoreRing";
import { Copy, Check } from "lucide-react";
import { useState } from "react";

export default function PostCard({ post }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(post.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <PlatformBadge platform={post.platform} />
        <ScoreRing score={post.critic_score || 0} />
      </div>

      {/* Content */}
      <div className="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">
        {post.content}
      </div>

      {/* Hashtags */}
      {post.hashtags?.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {post.hashtags.map((tag) => (
            <span
              key={tag}
              className="text-xs px-2 py-0.5 rounded-full bg-gray-800 text-violet-400"
            >
              #{tag.replace(/^#/, "")}
            </span>
          ))}
        </div>
      )}

      {/* CTA */}
      {post.call_to_action && (
        <p className="text-xs text-gray-500">
          <span className="text-gray-400 font-medium">CTA:</span>{" "}
          {post.call_to_action}
        </p>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-2 border-t border-gray-800">
        <span className="text-xs text-gray-600 capitalize">
          {post.content_type?.replace("_", " ")}
        </span>
        <button
          onClick={handleCopy}
          className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" /> Copied
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" /> Copy
            </>
          )}
        </button>
      </div>
    </div>
  );
}
