import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Plus, Building2, ChevronRight, Loader2 } from "lucide-react";

export default function StepSelectBrand({
  brands,
  loading,
  selectedBrandId,
  onSelect,
  onContinue,
}) {
  // Auto-select if only one brand
  useEffect(() => {
    if (!loading && brands.length === 1 && !selectedBrandId) {
      onSelect(brands[0].id);
    }
  }, [brands, loading, selectedBrandId, onSelect]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-gray-500">
        <Loader2 className="w-5 h-5 animate-spin mr-2" />
        Loading brands...
      </div>
    );
  }

  // Empty state
  if (brands.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-14 h-14 rounded-xl border-2 border-dashed border-gray-700 flex items-center justify-center mb-4">
          <Building2 className="w-7 h-7 text-gray-600" />
        </div>
        <h3 className="text-white font-medium mb-1">No brands yet</h3>
        <p className="text-sm text-gray-500 mb-4">
          Create a brand profile to start generating content.
        </p>
        <Link
          to="/brand"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Brand
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {brands.map((b) => {
          const isSelected = selectedBrandId === b.id;
          const toneKeywords = b.tone_keywords || [];
          const visibleTags = toneKeywords.slice(0, 4);
          const overflow = toneKeywords.length - 4;

          return (
            <button
              key={b.id}
              onClick={() => onSelect(b.id)}
              className={`text-left p-4 rounded-xl border transition-all ${
                isSelected
                  ? "border-violet-500/50 bg-violet-500/10 ring-1 ring-violet-500/20"
                  : "border-gray-800 bg-gray-900/50 hover:border-gray-700"
              }`}
            >
              <div className="flex items-start gap-3">
                {/* Radio dot */}
                <div
                  className={`mt-0.5 w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 ${
                    isSelected
                      ? "border-violet-500 bg-violet-500"
                      : "border-gray-600"
                  }`}
                >
                  {isSelected && (
                    <div className="w-1.5 h-1.5 rounded-full bg-white" />
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <h3 className="text-white font-medium text-sm truncate">
                    {b.brand_name}
                  </h3>
                  {b.niche && (
                    <p className="text-xs text-gray-500 mt-0.5 truncate">
                      {b.niche}
                    </p>
                  )}
                  {b.target_audience && (
                    <p className="text-xs text-gray-600 mt-0.5 truncate">
                      Audience: {b.target_audience}
                    </p>
                  )}
                  {visibleTags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {visibleTags.map((t) => (
                        <span
                          key={t}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-400"
                        >
                          {t}
                        </span>
                      ))}
                      {overflow > 0 && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-500">
                          +{overflow}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </button>
          );
        })}

        {/* Create New Brand card */}
        <Link
          to="/brand"
          className="flex items-center justify-center gap-2 p-4 rounded-xl border-2 border-dashed border-gray-800 hover:border-gray-700 text-gray-500 hover:text-gray-400 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span className="text-sm font-medium">Create New Brand</span>
        </Link>
      </div>

      {/* Continue button */}
      <div className="flex justify-end">
        <button
          onClick={onContinue}
          disabled={!selectedBrandId}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
        >
          Continue
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
