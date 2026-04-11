import PlatformBadge from "./PlatformBadge";
import ScoreRing from "./ScoreRing";
import { Copy, Check, Image, ChevronLeft, ChevronRight, Film, Clock, Clapperboard } from "lucide-react";
import { useState } from "react";

function CarouselSlides({ slides, imagePrompt, labelPrefix = "Slide" }) {
  const [active, setActive] = useState(0);

  const prev = () => setActive((i) => Math.max(0, i - 1));
  const next = () => setActive((i) => Math.min(slides.length - 1, i + 1));

  return (
    <div className="space-y-3">
      {/* Slide viewport */}
      <div className="relative rounded-lg border border-gray-800 bg-gray-950/60 overflow-hidden">
        {/* Image prompt placeholder */}
        {imagePrompt && (
          <div className="flex items-center gap-2 px-3 py-2 bg-gray-800/40 border-b border-gray-800 text-[11px] text-gray-500">
            <Image className="w-3.5 h-3.5 shrink-0 text-gray-600" />
            <span className="truncate">{imagePrompt}</span>
          </div>
        )}

        {/* Slide content */}
        <div className="px-4 py-3 min-h-[80px]">
          <div className="text-xs text-violet-400/70 font-medium mb-1.5">
            {labelPrefix} {active + 1} of {slides.length}
          </div>
          <div className="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">
            {slides[active]}
          </div>
        </div>

        {/* Nav arrows */}
        {slides.length > 1 && (
          <>
            <button
              onClick={prev}
              disabled={active === 0}
              className="absolute left-1.5 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-gray-800/80 border border-gray-700 flex items-center justify-center text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-default transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={next}
              disabled={active === slides.length - 1}
              className="absolute right-1.5 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-gray-800/80 border border-gray-700 flex items-center justify-center text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-default transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </>
        )}
      </div>

      {/* Dot indicators */}
      {slides.length > 1 && (
        <div className="flex items-center justify-center gap-1.5">
          {slides.map((_, i) => (
            <button
              key={i}
              onClick={() => setActive(i)}
              className={`w-1.5 h-1.5 rounded-full transition-colors ${
                i === active ? "bg-violet-400" : "bg-gray-700 hover:bg-gray-600"
              }`}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ReelBreakdown({ breakdown, duration }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-950/60 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 bg-gray-800/40 text-xs text-gray-400 hover:text-gray-200 transition-colors"
      >
        <Clapperboard className="w-3.5 h-3.5 shrink-0 text-violet-400" />
        <span className="font-medium">Reel Script</span>
        {duration && (
          <span className="flex items-center gap-1 text-gray-500">
            <Clock className="w-3 h-3" />
            {duration}
          </span>
        )}
        <span className="ml-auto text-gray-600">{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div className="px-3 py-2 space-y-2">
          {breakdown.map((shot, i) => (
            <div key={i} className="flex gap-2 text-xs">
              {shot.timestamp && (
                <span className="shrink-0 px-1.5 py-0.5 rounded bg-violet-500/10 text-violet-400 font-mono">
                  {shot.timestamp}
                </span>
              )}
              <div className="space-y-0.5">
                {shot.visual && (
                  <p className="text-gray-300">{shot.visual || shot.description}</p>
                )}
                {shot.audio && (
                  <p className="text-gray-500 italic">{shot.audio}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function RawDataSection({ raw }) {
  const [expanded, setExpanded] = useState(false);

  // Collect extra fields not already shown by the card
  const skip = new Set([
    "platform", "content", "content_type", "hashtags",
    "call_to_action", "image_prompt", "character_count",
    "critic_score", "status", "scheduled_at",
    "breakdown", "scenes", "shots", "duration",
    "reel_caption", "reel_script", "reel_description",
  ]);

  const extras = Object.entries(raw).filter(
    ([k, v]) => !skip.has(k) && v != null && v !== "" && !(Array.isArray(v) && v.length === 0)
  );

  if (extras.length === 0) return null;

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-950/60 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 bg-gray-800/40 text-xs text-gray-400 hover:text-gray-200 transition-colors"
      >
        <Film className="w-3.5 h-3.5 shrink-0 text-cyan-400" />
        <span className="font-medium">Full LLM Output</span>
        <span className="text-gray-600">({extras.length} fields)</span>
        <span className="ml-auto text-gray-600">{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div className="px-3 py-2 space-y-1.5">
          {extras.map(([key, val]) => (
            <div key={key} className="text-xs">
              <span className="text-cyan-400/70 font-medium">{key}: </span>
              <span className="text-gray-300 whitespace-pre-wrap">
                {typeof val === "string" ? val : JSON.stringify(val, null, 2)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function PostCard({ post }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(post.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const raw = post.raw_data || {};
  const isCarousel = post.content_type === "carousel";
  const isThread = post.content_type === "thread";

  // Detect reel breakdown from raw LLM data
  const breakdown = raw.breakdown || raw.scenes || raw.shots || [];
  const duration = raw.duration || "";
  const reelCaption = raw.reel_caption || "";
  const reelDescription = raw.reel_description || raw.reel_script || "";

  let slides = [];
  if (isCarousel) {
    slides = post.content.split(/\n{0,2}---\n{0,2}/).map((s) => s.trim()).filter(Boolean);
  } else if (isThread) {
    const markerParts = post.content.split(/(?:^|\n{1,2})(?=\d+\/\d+\b|\(\d+\)|\btweet\s*\d+)/im);
    const cleaned = markerParts.map((s) => s.trim()).filter(Boolean);

    if (cleaned.length > 2) {
      slides = cleaned;
    } else {
      const nlParts = post.content.split(/\n{2,}/).map((s) => s.trim()).filter(Boolean);
      slides = nlParts.filter((s) => !/^\d+\/\d+$/.test(s));
    }
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <PlatformBadge platform={post.platform} />
        <ScoreRing score={post.critic_score || 0} />
      </div>

      {/* Content */}
      {(isCarousel || isThread) && slides.length > 1 ? (
        <CarouselSlides
          slides={slides}
          imagePrompt={post.image_prompt}
          labelPrefix={isThread ? "Tweet" : "Slide"}
        />
      ) : (
        <div className="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">
          {post.content}
        </div>
      )}

      {/* Reel caption (if different from content) */}
      {reelCaption && reelCaption !== post.content && (
        <div className="rounded-lg border border-gray-800 bg-gray-950/60 px-3 py-2">
          <div className="text-[10px] text-violet-400/70 font-medium mb-1">Reel Caption</div>
          <div className="text-sm text-gray-200 whitespace-pre-wrap">{reelCaption}</div>
        </div>
      )}

      {/* Reel description / script */}
      {reelDescription && (
        <div className="rounded-lg border border-gray-800 bg-gray-950/60 px-3 py-2">
          <div className="text-[10px] text-violet-400/70 font-medium mb-1">Reel Script</div>
          <div className="text-xs text-gray-400 whitespace-pre-wrap">{reelDescription}</div>
        </div>
      )}

      {/* Reel shot-by-shot breakdown */}
      {breakdown.length > 0 && (
        <ReelBreakdown breakdown={breakdown} duration={duration} />
      )}

      {/* Duration badge */}
      {duration && breakdown.length === 0 && (
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <Clock className="w-3 h-3" />
          <span>{duration}</span>
        </div>
      )}

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

      {/* Extra raw LLM data */}
      {Object.keys(raw).length > 0 && <RawDataSection raw={raw} />}

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
