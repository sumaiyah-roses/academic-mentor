// Set VITE_API_URL at build time for deployment (e.g. https://my-api.onrender.com).
// Falls back to localhost so local development needs no configuration.
const BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/+$/, "");

async function get(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

async function post(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export function createSession() {
  return post("/api/session", {});
}

export function sendChat(sessionId, message) {
  return post("/api/chat", { session_id: sessionId, message });
}

export function finalizeIdea(sessionId) {
  return post("/api/finalize-idea", { session_id: sessionId, message: "" });
}

export function finalizeFeasibility(sessionId) {
  return post("/api/finalize-feasibility", { session_id: sessionId, message: "" });
}

export function finalizePlan(sessionId) {
  return post("/api/finalize-plan", { session_id: sessionId, message: "" });
}

export function getDocument(sessionId) {
  return get(`/api/document/${sessionId}`);
}

export function exportDocx(sessionId) {
  window.open(`${BASE_URL}/api/export/${sessionId}`, "_blank");
}
