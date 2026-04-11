import PlatformBadge from "./PlatformBadge";
import ScoreRing from "./ScoreRing";
import { Copy, Check, Image, ChevronLeft, ChevronRight } from "lucide-react";
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

export default function PostCard({ post }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(post.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isCarousel = post.content_type === "carousel";
  const isThread = post.content_type === "thread";

  let slides = [];
  if (isCarousel) {
    slides = post.content.split(/\n{0,2}---\n{0,2}/).map((s) => s.trim()).filter(Boolean);
  } else if (isThread) {
    // Try splitting on tweet number markers: "1/6", "2/6", "1.", "(1)", "Tweet 1:"
    const markerParts = post.content.split(/(?:^|\n{1,2})(?=\d+\/\d+\b|\(\d+\)|\btweet\s*\d+)/im);
    const cleaned = markerParts.map((s) => s.trim()).filter(Boolean);

    if (cleaned.length > 2) {
      // Markers worked — use them
      slides = cleaned;
    } else {
      // Fallback: split on double newlines
      const nlParts = post.content.split(/\n{2,}/).map((s) => s.trim()).filter(Boolean);
      // Filter out bare markers like "1/6" that are just numbering, not content
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
