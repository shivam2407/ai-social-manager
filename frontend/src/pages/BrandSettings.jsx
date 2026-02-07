import { useState, useEffect } from "react";
import { Trash2, Edit2, Plus } from "lucide-react";
import {
  getBrandProfiles,
  saveBrandProfile,
  deleteBrandProfile,
} from "../store";
import BrandForm from "../components/BrandForm";

export default function BrandSettings() {
  const [profiles, setProfiles] = useState([]);
  const [editing, setEditing] = useState(null); // null = list, "new" | profile.id
  const [editData, setEditData] = useState(null);

  useEffect(() => {
    setProfiles(getBrandProfiles());
  }, []);

  const refresh = () => setProfiles(getBrandProfiles());

  const handleSave = (form) => {
    const profile = {
      ...form,
      id: editing === "new" ? undefined : editing,
    };
    saveBrandProfile(profile);
    refresh();
    setEditing(null);
    setEditData(null);
  };

  const handleDelete = (id) => {
    if (window.confirm("Delete this brand profile?")) {
      deleteBrandProfile(id);
      refresh();
    }
  };

  const handleEdit = (profile) => {
    setEditing(profile.id);
    setEditData(profile);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Brand Settings</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage saved brand profiles (stored in your browser)
          </p>
        </div>
        {!editing && (
          <button
            onClick={() => {
              setEditing("new");
              setEditData(null);
            }}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Profile
          </button>
        )}
      </div>

      {editing ? (
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
              {editing === "new" ? "New Brand Profile" : "Edit Profile"}
            </h2>
            <button
              onClick={() => {
                setEditing(null);
                setEditData(null);
              }}
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              Cancel
            </button>
          </div>
          <BrandForm
            initial={editData || undefined}
            onSubmit={handleSave}
            submitLabel={editing === "new" ? "Create Profile" : "Save Changes"}
          />
        </div>
      ) : profiles.length === 0 ? (
        <div className="rounded-xl border border-gray-800 border-dashed bg-gray-900/30 p-10 text-center">
          <p className="text-sm text-gray-500 mb-3">No brand profiles saved</p>
          <button
            onClick={() => setEditing("new")}
            className="text-sm text-violet-400 hover:text-violet-300"
          >
            Create your first profile
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {profiles.map((profile) => (
            <div
              key={profile.id}
              className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 flex items-start justify-between"
            >
              <div className="space-y-2 min-w-0 flex-1">
                <h3 className="text-base font-semibold text-white">
                  {profile.brand_name}
                </h3>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span>{profile.niche}</span>
                  <span>&middot;</span>
                  <span>{profile.target_audience}</span>
                </div>
                {profile.tone_keywords?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {profile.tone_keywords.map((kw, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded-full bg-violet-500/15 text-violet-400 text-xs"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                )}
                <p className="text-xs text-gray-600 line-clamp-2">
                  {profile.voice_description}
                </p>
              </div>
              <div className="flex items-center gap-2 ml-4 shrink-0">
                <button
                  onClick={() => handleEdit(profile)}
                  className="p-2 rounded-lg text-gray-500 hover:text-white hover:bg-gray-800 transition-colors"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(profile.id)}
                  className="p-2 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
