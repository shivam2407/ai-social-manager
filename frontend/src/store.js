// Simple localStorage-backed state management

const BRAND_KEY = "aisocial_brands";
const HISTORY_KEY = "aisocial_history";

// --- Brand Profiles ---

export function getBrandProfiles() {
  try {
    return JSON.parse(localStorage.getItem(BRAND_KEY)) || [];
  } catch {
    return [];
  }
}

export function saveBrandProfile(profile) {
  const profiles = getBrandProfiles();
  const idx = profiles.findIndex((p) => p.id === profile.id);
  if (idx >= 0) {
    profiles[idx] = profile;
  } else {
    profile.id = crypto.randomUUID();
    profiles.push(profile);
  }
  localStorage.setItem(BRAND_KEY, JSON.stringify(profiles));
  return profile;
}

export function deleteBrandProfile(id) {
  const profiles = getBrandProfiles().filter((p) => p.id !== id);
  localStorage.setItem(BRAND_KEY, JSON.stringify(profiles));
}

// --- Generation History ---

export function getHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
  } catch {
    return [];
  }
}

export function addToHistory(entry) {
  const history = getHistory();
  history.unshift({
    ...entry,
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
  });
  // Keep last 50
  if (history.length > 50) history.length = 50;
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  return history;
}

export function clearHistory() {
  localStorage.removeItem(HISTORY_KEY);
}
