import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, Sparkles, BarChart3, Clock, ArrowRight } from "lucide-react";
import { checkHealth, getStats, getHistoryApi } from "../api";
import PlatformBadge from "../components/PlatformBadge";
import ScoreRing from "../components/ScoreRing";

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [stats, setStats] = useState({ total_generations: 0, total_posts: 0, avg_critic_score: 0 });
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    checkHealth().then(setHealth).catch(() => setHealth({ status: "unreachable" }));
    getStats().then(setStats).catch(() => {});
    getHistoryApi(5).then(setRecent).catch(() => {});
  }, []);

  const isHealthy = health?.status === "healthy";

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            AI-powered social media content pipeline
          </p>
        </div>
        <Link
          to="/generate"
          data-onboarding="quick-generate-btn"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors"
        >
          <Sparkles className="w-4 h-4" />
          Quick Generate
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {/* API Status */}
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
          <div className="flex items-center gap-3 mb-3">
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                isHealthy ? "bg-emerald-500/15" : "bg-red-500/15"
              }`}
            >
              <Activity
                className={`w-4 h-4 ${isHealthy ? "text-emerald-400" : "text-red-400"}`}
              />
            </div>
            <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">
              API Status
            </span>
          </div>
          <p
            className={`text-lg font-semibold ${isHealthy ? "text-emerald-400" : "text-red-400"}`}
          >
            {health ? (isHealthy ? "Healthy" : "Unreachable") : "Checking..."}
          </p>
          {health?.graph_compiled !== undefined && (
            <p className="text-xs text-gray-600 mt-1">
              Graph: {health.graph_compiled ? "Compiled" : "Not ready"}
            </p>
          )}
        </div>

        {/* Total Posts */}
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-violet-500/15">
              <BarChart3 className="w-4 h-4 text-violet-400" />
            </div>
            <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">
              Posts Generated
            </span>
          </div>
          <p className="text-lg font-semibold text-white">{stats.total_posts}</p>
          <p className="text-xs text-gray-600 mt-1">
            {stats.total_generations} generation{stats.total_generations !== 1 ? "s" : ""}
          </p>
        </div>

        {/* Avg Score */}
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-amber-500/15">
              <BarChart3 className="w-4 h-4 text-amber-400" />
            </div>
            <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">
              Avg Critic Score
            </span>
          </div>
          <p className="text-lg font-semibold text-white">
            {stats.avg_critic_score > 0 ? stats.avg_critic_score.toFixed(1) : "--"}
          </p>
          <p className="text-xs text-gray-600 mt-1">out of 10</p>
        </div>
      </div>

      {/* Recent Generations */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
            Recent Generations
          </h2>
          {recent.length > 0 && (
            <Link
              to="/history"
              className="text-xs text-violet-400 hover:text-violet-300 inline-flex items-center gap-1"
            >
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          )}
        </div>

        {recent.length === 0 ? (
          <div className="rounded-xl border border-gray-800 border-dashed bg-gray-900/30 p-10 text-center">
            <Clock className="w-8 h-8 text-gray-700 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No generations yet</p>
            <Link
              to="/generate"
              className="text-sm text-violet-400 hover:text-violet-300 mt-2 inline-block"
            >
              Create your first post
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {recent.map((item) => (
              <div
                key={item.id}
                className="rounded-xl border border-gray-800 bg-gray-900/50 p-4 flex items-center justify-between"
              >
                <div className="space-y-1.5">
                  <p className="text-sm text-gray-200 line-clamp-1">
                    {item.content_request}
                  </p>
                  <div className="flex items-center gap-2">
                    {item.posts?.map((p) => (
                      <PlatformBadge key={p.platform} platform={p.platform} />
                    ))}
                    <span className="text-xs text-gray-600">
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {item.posts?.length > 0 && (
                    <ScoreRing
                      score={
                        item.posts.reduce(
                          (s, p) => s + (p.critic_score || 0),
                          0,
                        ) / item.posts.length
                      }
                      size={40}
                    />
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
