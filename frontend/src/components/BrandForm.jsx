import { useState } from "react";
import { Plus, X } from "lucide-react";

const defaultBrand = {
  brand_name: "",
  niche: "",
  target_audience: "",
  voice_description: "Professional yet approachable. Clear, concise, and helpful.",
  tone_keywords: ["authentic", "knowledgeable"],
  example_posts: [],
};

export default function BrandForm({ initial, onSubmit, submitLabel = "Save" }) {
  const [form, setForm] = useState({ ...defaultBrand, ...initial });
  const [newKeyword, setNewKeyword] = useState("");
  const [newExample, setNewExample] = useState("");

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const addKeyword = () => {
    if (newKeyword.trim()) {
      set("tone_keywords", [...form.tone_keywords, newKeyword.trim()]);
      setNewKeyword("");
    }
  };

  const removeKeyword = (idx) =>
    set("tone_keywords", form.tone_keywords.filter((_, i) => i !== idx));

  const addExample = () => {
    if (newExample.trim()) {
      set("example_posts", [...form.example_posts, newExample.trim()]);
      setNewExample("");
    }
  };

  const removeExample = (idx) =>
    set("example_posts", form.example_posts.filter((_, i) => i !== idx));

  const inputClass =
    "w-full bg-gray-800/50 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30";

  return (
    <div className="space-y-4">
      {/* Brand Name */}
      <div>
        <label className="block text-xs font-medium text-gray-400 mb-1.5">
          Brand Name
        </label>
        <input
          className={inputClass}
          placeholder="e.g. Sunrise Bakery"
          value={form.brand_name}
          onChange={(e) => set("brand_name", e.target.value)}
        />
      </div>

      {/* Niche + Audience */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1.5">
            Niche
          </label>
          <input
            className={inputClass}
            placeholder="e.g. Fitness, Food, Fashion"
            value={form.niche}
            onChange={(e) => set("niche", e.target.value)}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1.5">
            Target Audience
          </label>
          <input
            className={inputClass}
            placeholder="e.g. Young professionals, parents"
            value={form.target_audience}
            onChange={(e) => set("target_audience", e.target.value)}
          />
        </div>
      </div>

      {/* Voice */}
      <div>
        <label className="block text-xs font-medium text-gray-400 mb-1.5">
          Voice Description
        </label>
        <textarea
          className={`${inputClass} resize-none`}
          rows={2}
          placeholder="Professional yet approachable..."
          value={form.voice_description}
          onChange={(e) => set("voice_description", e.target.value)}
        />
      </div>

      {/* Tone Keywords */}
      <div>
        <label className="block text-xs font-medium text-gray-400 mb-1.5">
          Tone Keywords
        </label>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {form.tone_keywords.map((kw, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-violet-500/15 text-violet-400 text-xs"
            >
              {kw}
              <button onClick={() => removeKeyword(i)}>
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            className={inputClass}
            placeholder="Add keyword..."
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addKeyword())}
          />
          <button
            type="button"
            onClick={addKeyword}
            className="px-3 rounded-lg bg-gray-800 text-gray-400 hover:text-white transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Example Posts */}
      <div>
        <label className="block text-xs font-medium text-gray-400 mb-1.5">
          Example Posts
        </label>
        {form.example_posts.map((post, i) => (
          <div
            key={i}
            className="flex items-start gap-2 mb-2 p-2 rounded-lg bg-gray-800/30 border border-gray-800"
          >
            <p className="flex-1 text-xs text-gray-300">{post}</p>
            <button onClick={() => removeExample(i)}>
              <X className="w-3.5 h-3.5 text-gray-500 hover:text-red-400" />
            </button>
          </div>
        ))}
        <div className="flex gap-2">
          <input
            className={inputClass}
            placeholder="Paste an example post..."
            value={newExample}
            onChange={(e) => setNewExample(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addExample())}
          />
          <button
            type="button"
            onClick={addExample}
            className="px-3 rounded-lg bg-gray-800 text-gray-400 hover:text-white transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Submit */}
      <button
        onClick={() => onSubmit(form)}
        className="w-full py-2.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors"
      >
        {submitLabel}
      </button>
    </div>
  );
}
