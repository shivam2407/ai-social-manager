import { useState, useEffect } from "react";
import { Trash2, ChevronDown, ChevronUp, Clock } from "lucide-react";
import { getHistoryApi, clearHistoryApi } from "../api";
import PostCard from "../components/PostCard";
import PlatformBadge from "../components/PlatformBadge";

const PLATFORMS_ALL = ["all", "twitter", "linkedin", "instagram"];

export default function History() {
  const [history, setHistory] = useState([]);
  const [filter, setFilter] = useState("all");
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    getHistoryApi().then(setHistory).catch(() => {});
  }, []);

  const filtered =
    filter === "all"
      ? history
      : history.filter((h) =>
          h.posts?.some((p) => p.platform === filter),
        );

  const handleClear = async () => {
    if (window.confirm("Clear all generation history?")) {
      try {
        await clearHistoryApi();
        setHistory([]);
      } catch {
        // ignore
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">History</h1>
          <p className="text-sm text-gray-500 mt-1">
            Past content generations
          </p>
        </div>
        {history.length > 0 && (
          <button
            onClick={handleClear}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-red-400 border border-red-500/20 hover:bg-red-500/10 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear History
          </button>
        )}
      </div>

      {/* Platform filter */}
      <div className="flex gap-2">
        {PLATFORMS_ALL.map((p) => (
          <button
            key={p}
            onClick={() => setFilter(p)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors capitalize ${
              filter === p
                ? "bg-violet-500/15 text-violet-400 border-violet-500/30"
                : "bg-gray-800/50 text-gray-500 border-gray-800 hover:text-gray-300"
            }`}
          >
            {p}
          </button>
        ))}
      </div>

      {/* List */}
      {filtered.length === 0 ? (
        <div className="rounded-xl border border-gray-800 border-dashed bg-gray-900/30 p-10 text-center">
          <Clock className="w-8 h-8 text-gray-700 mx-auto mb-3" />
          <p className="text-sm text-gray-500">
            {history.length === 0
              ? "No generations yet"
              : "No results match this filter"}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((item) => (
            <div
              key={item.id}
              className="rounded-xl border border-gray-800 bg-gray-900/50 overflow-hidden"
            >
              {/* Summary row */}
              <button
                onClick={() =>
                  setExpanded(expanded === item.id ? null : item.id)
                }
                className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-gray-800/30 transition-colors"
              >
                <div className="space-y-1.5 min-w-0 flex-1">
                  <p className="text-sm text-gray-200 truncate">
                    {item.content_request}
                  </p>
                  <div className="flex items-center gap-2">
                    {item.posts?.map((p) => (
                      <PlatformBadge
                        key={p.platform}
                        platform={p.platform}
                      />
                    ))}
                    <span className="text-xs text-gray-600">
                      {new Date(item.created_at).toLocaleString()}
                    </span>
                    {item.brand_name && (
                      <span className="text-xs text-gray-600">
                        &middot; {item.brand_name}
                      </span>
                    )}
                  </div>
                </div>
                {expanded === item.id ? (
                  <ChevronUp className="w-4 h-4 text-gray-500 shrink-0 ml-4" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-500 shrink-0 ml-4" />
                )}
              </button>

              {/* Expanded content */}
              {expanded === item.id && (
                <div className="px-5 pb-5 space-y-4 border-t border-gray-800">
                  {item.critic_summary && (
                    <div className="pt-4">
                      <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
                        Critic Summary
                      </h4>
                      <p className="text-sm text-gray-300">
                        {item.critic_summary}
                      </p>
                    </div>
                  )}
                  <div className="grid grid-cols-1 gap-3 pt-2">
                    {(filter === "all"
                      ? item.posts
                      : item.posts?.filter((p) => p.platform === filter)
                    )?.map((post, i) => (
                      <PostCard key={i} post={post} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
