const BASE = "";

function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse(res, { redirectOn401 = true } = {}) {
  if (res.status === 401 && redirectOn401) {
    localStorage.removeItem("token");
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

// --- Health ---

export async function checkHealth() {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error("API unreachable");
  return res.json();
}

// --- Auth ---

export async function registerApi(email, password) {
  const res = await fetch(`${BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse(res, { redirectOn401: false });
}

export async function loginApi(email, password) {
  const res = await fetch(`${BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse(res, { redirectOn401: false });
}

export async function getMe(token) {
  const res = await fetch(`${BASE}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res, { redirectOn401: false });
}

// --- Brands ---

export async function getBrands() {
  const res = await fetch(`${BASE}/api/brands/`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}

export async function createBrand(data) {
  const res = await fetch(`${BASE}/api/brands/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

export async function updateBrand(id, data) {
  const res = await fetch(`${BASE}/api/brands/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

export async function deleteBrandApi(id) {
  const res = await fetch(`${BASE}/api/brands/${id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (res.status === 204) return;
  return handleResponse(res);
}

// --- Generate ---

export async function generateContent(request) {
  const res = await fetch(`${BASE}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(request),
  });
  return handleResponse(res);
}

export async function getStatus(threadId) {
  const res = await fetch(`${BASE}/api/status/${threadId}`);
  if (!res.ok) throw new Error("Status check failed");
  return res.json();
}

// --- History ---

export async function getHistoryApi(limit = 50) {
  const res = await fetch(`${BASE}/api/history/?limit=${limit}`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}

export async function getStats() {
  const res = await fetch(`${BASE}/api/history/stats`, {
    headers: authHeaders(),
  });
  return handleResponse(res);
}

export async function clearHistoryApi() {
  const res = await fetch(`${BASE}/api/history/`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (res.status === 204) return;
  return handleResponse(res);
}
