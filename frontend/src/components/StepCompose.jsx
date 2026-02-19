import { useCallback } from "react";
import { Sparkles, Loader2, ImagePlus, X } from "lucide-react";

const PLATFORMS = ["twitter", "linkedin", "instagram"];
const MAX_IMAGES = 4;
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];

export default function StepCompose({
  brand,
  contentRequest,
  setContentRequest,
  images,
  setImages,
  platforms,
  togglePlatform,
  onGenerate,
  onChangeBrand,
  loading,
  error,
  hasDefaultKey,
}) {
  const handleFiles = useCallback(
    (fileList) => {
      const files = Array.from(fileList);
      const remaining = MAX_IMAGES - images.length;
      const valid = files
        .filter((f) => ACCEPTED_TYPES.includes(f.type) && f.size <= MAX_FILE_SIZE)
        .slice(0, remaining);

      valid.forEach((file) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          setImages((prev) =>
            prev.length < MAX_IMAGES ? [...prev, e.target.result] : prev,
          );
        };
        reader.readAsDataURL(file);
      });
    },
    [images.length, setImages],
  );

  const removeImage = (index) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles],
  );

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
  }, []);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Brand summary banner */}
      <div className="flex items-center gap-3 p-4 rounded-xl border border-gray-800 bg-gray-900/50">
        <div className="w-10 h-10 rounded-lg bg-violet-500/20 border border-violet-500/30 flex items-center justify-center text-violet-400 font-semibold text-sm shrink-0">
          {brand.brand_name?.charAt(0)?.toUpperCase() || "?"}
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-white font-medium text-sm truncate">
            {brand.brand_name}
          </h3>
          <p className="text-xs text-gray-500 truncate">
            {[brand.niche, brand.target_audience].filter(Boolean).join(" · ")}
          </p>
        </div>
        <button
          onClick={onChangeBrand}
          className="text-xs text-violet-400 hover:text-violet-300 font-medium shrink-0 transition-colors"
        >
          Change
        </button>
      </div>

      {/* Content request card */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 space-y-4">
        <label className="block text-sm font-medium text-gray-300">
          What do you want to post about?
        </label>

        <textarea
          className="w-full bg-gray-800/50 border border-gray-700 rounded-lg px-3 py-3 text-base text-gray-200 placeholder-gray-500 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30 resize-none"
          rows={6}
          autoFocus
          placeholder="e.g. Announce our summer sale, share a behind-the-scenes look, promote an upcoming event..."
          value={contentRequest}
          onChange={(e) => setContentRequest(e.target.value)}
        />

        {/* Reference photos */}
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-2">
            Reference Photos{" "}
            <span className="text-gray-600">(optional, up to {MAX_IMAGES})</span>
          </label>

          <div className="flex flex-wrap gap-2">
            {images.map((src, i) => (
              <div
                key={i}
                className="relative w-20 h-20 rounded-lg overflow-hidden border border-gray-700 group"
              >
                <img
                  src={src}
                  alt={`Reference ${i + 1}`}
                  className="w-full h-full object-cover"
                />
                <button
                  onClick={() => removeImage(i)}
                  className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                >
                  <X className="w-4 h-4 text-white" />
                </button>
              </div>
            ))}

            {images.length < MAX_IMAGES && (
              <label
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                className="w-20 h-20 rounded-lg border-2 border-dashed border-gray-700 hover:border-violet-500/50 flex flex-col items-center justify-center cursor-pointer transition-colors"
              >
                <ImagePlus className="w-5 h-5 text-gray-500" />
                <span className="text-[10px] text-gray-500 mt-1">
                  {images.length}/{MAX_IMAGES}
                </span>
                <input
                  type="file"
                  multiple
                  accept="image/jpeg,image/png,image/webp,image/gif"
                  className="hidden"
                  onChange={(e) => {
                    handleFiles(e.target.files);
                    e.target.value = "";
                  }}
                />
              </label>
            )}
          </div>
        </div>

        {/* Platform toggles */}
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
          onClick={onGenerate}
          disabled={loading || !hasDefaultKey}
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
    </div>
  );
}
