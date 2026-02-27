import { useState, useEffect } from "react";
import {
  Key,
  Check,
  X,
  Loader2,
  Trash2,
  FlaskConical,
  AlertTriangle,
  Star,
} from "lucide-react";
import {
  getProviders,
  getApiKeys,
  upsertApiKey,
  deleteApiKey,
  testApiKey,
} from "../api";
import useOnboarding from "../components/onboarding/useOnboarding";

const PROVIDER_COLORS = {
  claude: { bg: "bg-orange-500/10", border: "border-orange-500/30", text: "text-orange-400" },
  gemini: { bg: "bg-blue-500/10", border: "border-blue-500/30", text: "text-blue-400" },
  grok: { bg: "bg-red-500/10", border: "border-red-500/30", text: "text-red-400" },
  chatgpt: { bg: "bg-green-500/10", border: "border-green-500/30", text: "text-green-400" },
  mock: { bg: "bg-gray-500/10", border: "border-gray-500/30", text: "text-gray-400" },
};

const PROVIDER_LABELS = {
  claude: "Claude",
  gemini: "Gemini",
  grok: "Grok",
  chatgpt: "ChatGPT",
  mock: "Mock (Testing)",
};

export default function Settings() {
  const [providers, setProviders] = useState([]);
  const [savedKeys, setSavedKeys] = useState([]);
  const [drafts, setDrafts] = useState({});
  const [testing, setTesting] = useState({});
  const [testResults, setTestResults] = useState({});
  const [saving, setSaving] = useState({});
  const [deleting, setDeleting] = useState({});
  const [loading, setLoading] = useState(true);
  const [defaultPrompt, setDefaultPrompt] = useState(null); // provider name to prompt for
  const onboarding = useOnboarding();

  useEffect(() => {
    Promise.all([getProviders(), getApiKeys()])
      .then(([provs, keys]) => {
        setProviders(provs);
        setSavedKeys(keys);
        const initial = {};
        for (const p of provs) {
          const existing = keys.find((k) => k.provider === p.provider);
          initial[p.provider] = {
            api_key: "",
            model: existing?.model || p.default_model,
            is_default: existing?.is_default || false,
          };
        }
        setDrafts(initial);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const hasDefault = savedKeys.some((k) => k.is_default);

  const updateDraft = (provider, field, value) => {
    setDrafts((prev) => ({
      ...prev,
      [provider]: { ...prev[provider], [field]: value },
    }));
  };

  const handleTest = async (provider) => {
    const draft = drafts[provider];
    if (!draft.api_key) return;

    setTesting((p) => ({ ...p, [provider]: true }));
    setTestResults((p) => ({ ...p, [provider]: null }));
    try {
      const result = await testApiKey({
        provider,
        api_key: draft.api_key,
        model: draft.model,
      });
      setTestResults((p) => ({ ...p, [provider]: result }));
    } catch {
      setTestResults((p) => ({
        ...p,
        [provider]: { success: false, message: "Request failed" },
      }));
    } finally {
      setTesting((p) => ({ ...p, [provider]: false }));
    }
  };

  const handleSave = async (provider) => {
    const draft = drafts[provider];
    if (!draft.api_key) return;

    setSaving((p) => ({ ...p, [provider]: true }));
    try {
      await upsertApiKey({
        provider,
        api_key: draft.api_key,
        model: draft.model,
        is_default: draft.is_default,
      });
      // Reload keys
      const keys = await getApiKeys();
      setSavedKeys(keys);
      // Clear the api_key field after save
      setDrafts((prev) => ({
        ...prev,
        [provider]: { ...prev[provider], api_key: "" },
      }));
      if (keys.some((k) => k.is_default)) {
        onboarding.signal("default-key-set");
      } else if (onboarding.isActive) {
        // Key saved but no default yet — prompt user during onboarding
        setDefaultPrompt(provider);
      }
    } catch {
      // error handled by api.js
    } finally {
      setSaving((p) => ({ ...p, [provider]: false }));
    }
  };

  const handleDelete = async (provider) => {
    setDeleting((p) => ({ ...p, [provider]: true }));
    try {
      await deleteApiKey(provider);
      const keys = await getApiKeys();
      setSavedKeys(keys);
      setTestResults((p) => ({ ...p, [provider]: null }));
    } catch {
      // error handled by api.js
    } finally {
      setDeleting((p) => ({ ...p, [provider]: false }));
    }
  };

  const handleConfirmDefault = async () => {
    if (!defaultPrompt) return;
    await handleSetDefault(defaultPrompt);
    setDefaultPrompt(null);
  };

  const handleSetDefault = async (provider) => {
    const saved = savedKeys.find((k) => k.provider === provider);
    if (!saved) return;
    setSaving((p) => ({ ...p, [provider]: true }));
    try {
      await upsertApiKey({
        provider,
        model: saved.model,
        is_default: true,
      });
      const keys = await getApiKeys();
      setSavedKeys(keys);
      if (keys.some((k) => k.is_default)) onboarding.signal("default-key-set");
    } catch {
      // error handled by api.js
    } finally {
      setSaving((p) => ({ ...p, [provider]: false }));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 animate-spin text-gray-500" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">API Keys</h1>
        <p className="text-sm text-gray-500 mt-1">
          Configure your LLM provider API keys. One key per provider, one
          default for generation.
        </p>
      </div>

      {!hasDefault && savedKeys.length > 0 && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-sm">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          No default provider selected. Set one as default to enable content
          generation.
        </div>
      )}

      {savedKeys.length === 0 && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-sm">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          No API keys configured yet. Add at least one key and set it as
          default to start generating content.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {providers.map((prov, provIndex) => {
          const p = prov.provider;
          const colors = PROVIDER_COLORS[p] || PROVIDER_COLORS.claude;
          const saved = savedKeys.find((k) => k.provider === p);
          const draft = drafts[p] || {};
          const result = testResults[p];

          return (
            <div
              key={p}
              data-onboarding={provIndex === 0 ? "provider-card-first" : undefined}
              className={`rounded-xl border ${colors.border} ${colors.bg} p-5 space-y-4`}
            >
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Key className={`w-4 h-4 ${colors.text}`} />
                  <h3 className={`font-semibold ${colors.text}`}>
                    {PROVIDER_LABELS[p] || p}
                  </h3>
                </div>
                {saved && (
                  <div className="flex items-center gap-2">
                    {saved.is_default && (
                      <span className="flex items-center gap-1 text-xs bg-violet-500/20 text-violet-400 px-2 py-0.5 rounded-full">
                        <Star className="w-3 h-3" /> Default
                      </span>
                    )}
                    <span className="text-xs text-gray-500">
                      {saved.key_hint}
                    </span>
                  </div>
                )}
              </div>

              {/* API Key input */}
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">
                  API Key
                </label>
                <input
                  type="password"
                  className="w-full bg-gray-800/50 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30"
                  placeholder={saved ? "Enter new key to update" : "Enter API key"}
                  value={draft.api_key || ""}
                  onChange={(e) => updateDraft(p, "api_key", e.target.value)}
                />
              </div>

              {/* Model select */}
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">
                  Model
                </label>
                <select
                  className="w-full bg-gray-800/50 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-violet-500"
                  value={draft.model || prov.default_model}
                  onChange={(e) => updateDraft(p, "model", e.target.value)}
                >
                  {prov.models.map((m) => (
                    <option key={m} value={m}>
                      {m}
                      {m === prov.default_model ? " (default)" : ""}
                    </option>
                  ))}
                </select>
              </div>

              {/* Test result */}
              {result && (
                <div
                  className={`flex items-center gap-2 text-xs px-3 py-2 rounded-lg ${
                    result.success
                      ? "bg-green-500/10 text-green-400 border border-green-500/20"
                      : "bg-red-500/10 text-red-400 border border-red-500/20"
                  }`}
                >
                  {result.success ? (
                    <Check className="w-3 h-3" />
                  ) : (
                    <X className="w-3 h-3" />
                  )}
                  {result.message}
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center gap-2 pt-1">
                <button
                  onClick={() => handleTest(p)}
                  disabled={testing[p] || !draft.api_key}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-gray-700 text-gray-300 hover:bg-gray-800/50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  {testing[p] ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <FlaskConical className="w-3 h-3" />
                  )}
                  Test
                </button>

                <button
                  onClick={() => handleSave(p)}
                  disabled={saving[p] || !draft.api_key}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-violet-600 hover:bg-violet-500 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  {saving[p] ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <Check className="w-3 h-3" />
                  )}
                  Save
                </button>

                {saved && !saved.is_default && (
                  <button
                    onClick={() => handleSetDefault(p)}
                    disabled={saving[p]}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-violet-500/30 text-violet-400 hover:bg-violet-500/10 disabled:opacity-40 transition-colors"
                  >
                    <Star className="w-3 h-3" />
                    Set Default
                  </button>
                )}

                {saved && (
                  <button
                    onClick={() => handleDelete(p)}
                    disabled={deleting[p]}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-red-500/20 text-red-400 hover:bg-red-500/10 disabled:opacity-40 transition-colors ml-auto"
                  >
                    {deleting[p] ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <Trash2 className="w-3 h-3" />
                    )}
                    Delete
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* "Set as default?" prompt during onboarding */}
      {defaultPrompt && (
        <div className="fixed inset-0 z-[1010] flex items-center justify-center bg-black/60">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 max-w-sm w-full mx-4 space-y-4">
            <h3 className="text-sm font-semibold text-white">Set as default provider?</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Your <span className="text-white font-medium">{PROVIDER_LABELS[defaultPrompt] || defaultPrompt}</span> key
              was saved. Set it as the default provider for content generation?
            </p>
            <div className="flex items-center gap-3 pt-1">
              <button
                onClick={handleConfirmDefault}
                className="flex-1 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-xs font-medium transition-colors"
              >
                Yes, set as default
              </button>
              <button
                onClick={() => setDefaultPrompt(null)}
                className="flex-1 py-2 rounded-lg border border-gray-700 text-gray-400 hover:text-gray-200 text-xs font-medium transition-colors"
              >
                Not now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
