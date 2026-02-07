import { useState, useRef, useEffect } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { generateContent } from "../api";
import { addToHistory, getBrandProfiles } from "../store";
import BrandForm from "../components/BrandForm";
import PostCard from "../components/PostCard";
import PipelineStatus from "../components/PipelineStatus";

const PLATFORMS = ["twitter", "linkedin", "instagram"];

const stageTimings = [
  { key: "research", delay: 0 },
  { key: "strategy", delay: 4000 },
  { key: "writing", delay: 8000 },
  { key: "review", delay: 12000 },
];

export default function Generate() {
  const [brand, setBrand] = useState({
    brand_name: "",
    niche: "",
    target_audience: "",
    voice_description:
      "Professional yet approachable. Clear, concise, and helpful.",
    tone_keywords: ["authentic", "knowledgeable"],
    example_posts: [],
  });
  const [contentRequest, setContentRequest] = useState("");
  const [platforms, setPlatforms] = useState(["twitter", "linkedin"]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [activeStage, setActiveStage] = useState(null);
  const [completedStages, setCompletedStages] = useState([]);
  const timersRef = useRef([]);
  const resultsRef = useRef(null);

  // Load saved brand if available
  useEffect(() => {
    const profiles = getBrandProfiles();
    if (profiles.length > 0) {
      const p = profiles[0];
      setBrand({
        brand_name: p.brand_name || "",
        niche: p.niche || "",
        target_audience: p.target_audience || "",
        voice_description: p.voice_description || "",
        tone_keywords: p.tone_keywords || [],
        example_posts: p.example_posts || [],
      });
    }
  }, []);

  const togglePlatform = (p) =>
    setPlatforms((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p],
    );

  const simulateStages = () => {
    setCompletedStages([]);
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];

    stageTimings.forEach(({ key, delay }, i) => {
      const t1 = setTimeout(() => setActiveStage(key), delay);
      timersRef.current.push(t1);
      if (i > 0) {
        const prevKey = stageTimings[i - 1].key;
        const t2 = setTimeout(
          () => setCompletedStages((prev) => [...prev, prevKey]),
          delay,
        );
        timersRef.current.push(t2);
      }
    });
  };

  const handleGenerate = async () => {
    if (!brand.brand_name || !brand.niche || !contentRequest || platforms.length === 0) {
      setError("Please fill in brand name, niche, content request, and select at least one platform.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    simulateStages();

    try {
      const data = await generateContent({
        brand_name: brand.brand_name,
        niche: brand.niche,
        target_audience: brand.target_audience || "general audience",
        voice_description: brand.voice_description,
        tone_keywords: brand.tone_keywords,
        example_posts: brand.example_posts,
        content_request: contentRequest,
        target_platforms: platforms,
      });

      setResult(data);
      setActiveStage(null);
      setCompletedStages(stageTimings.map((s) => s.key));

      addToHistory({
        thread_id: data.thread_id,
        content_request: contentRequest,
        brand_name: brand.brand_name,
        platforms,
        posts: data.posts,
        revision_count: data.revision_count,
        critic_summary: data.critic_summary,
      });

      // Scroll to results
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 200);
    } catch (err) {
      setError(err.message);
      setActiveStage(null);
      setCompletedStages([]);
    } finally {
      setLoading(false);
      timersRef.current.forEach(clearTimeout);
    }
  };

  const inputClass =
    "w-full bg-gray-800/50 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30";

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Generate Content</h1>
        <p className="text-sm text-gray-500 mt-1">
          Fill in your brand profile and content request to generate
          platform-specific posts.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-8">
        {/* Left: Brand Form */}
        <div className="space-y-6">
          <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
            <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
              Brand Profile
            </h2>
            <BrandForm
              initial={brand}
              onSubmit={setBrand}
              submitLabel="Apply Brand"
            />
          </div>
        </div>

        {/* Right: Content Request */}
        <div className="space-y-6">
          <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 space-y-4">
            <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
              Content Request
            </h2>

            <textarea
              className={`${inputClass} resize-none`}
              rows={5}
              placeholder="Write about our new feature launch — highlight ease of use and developer experience..."
              value={contentRequest}
              onChange={(e) => setContentRequest(e.target.value)}
            />

            {/* Platform selector */}
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-2">
                Target Platforms
              </label>
              <div className="flex gap-2">
                {PLATFORMS.map((p) => (
                  <button
                    key={p}
                    onClick={() => togglePlatform(p)}
                    className={`px-3.5 py-2 rounded-lg text-xs font-medium border transition-colors capitalize ${
                      platforms.includes(p)
                        ? "bg-violet-500/15 text-violet-400 border-violet-500/30"
                        : "bg-gray-800/50 text-gray-500 border-gray-800 hover:text-gray-300"
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>

            {/* Generate button */}
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="w-full py-3 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Generate Content
                </>
              )}
            </button>

            {error && (
              <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                {error}
              </p>
            )}
          </div>

          {/* Pipeline status */}
          {loading && (
            <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Pipeline Progress
              </h3>
              <PipelineStatus
                activeStage={activeStage}
                completed={completedStages}
              />
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      {result && (
        <div ref={resultsRef} className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">
              Generated Posts
            </h2>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span>
                Revisions: {result.revision_count}
              </span>
              <span>Thread: {result.thread_id?.slice(0, 8)}...</span>
            </div>
          </div>

          {result.critic_summary && (
            <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                Critic Summary
              </h3>
              <p className="text-sm text-gray-300">{result.critic_summary}</p>
            </div>
          )}

          <div className="grid grid-cols-1 gap-4">
            {result.posts?.map((post, i) => (
              <PostCard key={i} post={post} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
