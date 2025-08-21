// static/js/common.js

export const API_URL = ""; // mismo origen; si tu API está aparte, ej: "http://127.0.0.1:5000"

// ========== TOKEN ==========
export const getToken   = () => localStorage.getItem("token") || "";
export const setToken   = (t) => localStorage.setItem("token", t || "");
export const clearToken = () => localStorage.removeItem("token");

// ========== FETCH UNIFICADO ==========
function buildHeaders(options) {
  const headers = { ...(options.headers || {}) };
  // Solo agregamos Content-Type si hay body JSON
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

function withTimeout(promise, ms = 20000) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("Timeout de red")), ms);
    promise.then(v => { clearTimeout(t); resolve(v); }, e => { clearTimeout(t); reject(e); });
  });
}

export async function apiFetch(path, options = {}) {
  const url = `${API_URL}${path}`;
  const headers = buildHeaders(options);

  let res;
  try {
    res = await withTimeout(fetch(url, { ...options, headers }));
  } catch (e) {
    // Error de red / timeout
    throw new Error(e?.message || "Fallo de red");
  }

  // 401: token caído → limpiar y redirigir al login (a menos que se pida lo contrario)
  if (res.status === 401) {
    clearToken();
    if (!options?.noAutoRedirect401) {
      window.location.href = "/security/login";
    }
  }

  if (res.status === 204) return null; // No Content

  let payload = null;
  try { payload = await res.json(); } catch { /* respuesta vacía o no JSON */ }

  if (!res.ok) {
    const msg = payload?.error || payload?.message || `${res.status} ${res.statusText}`;
    throw new Error(msg);
  }

  // Normalización
  if (payload && typeof payload === "object") {
    if (Array.isArray(payload)) return payload;                 // array directo
    if (payload.ok === true && "data" in payload) return payload.data; // {ok, data}
  }
  return payload;
}

// Atajos
export const apiGet    = (p, o)    => apiFetch(p, { method: "GET",    ...(o||{}) });
export const apiPost   = (p, b, o) => apiFetch(p, { method: "POST",   body: JSON.stringify(b || {}), ...(o||{}) });
export const apiPut    = (p, b, o) => apiFetch(p, { method: "PUT",    body: JSON.stringify(b || {}), ...(o||{}) });
export const apiDelete = (p, o)    => apiFetch(p, { method: "DELETE", ...(o||{}) });

// ========== DESCARGAS (CSV/PDF) ==========
export async function apiGetBlob(path) {
  const url = `${API_URL}${path}`;
  const headers = buildHeaders({});
  const res = await withTimeout(fetch(url, { headers }));
  if (res.status === 401) { clearToken(); window.location.href = "/security/login"; }
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return await res.blob();
}

export async function downloadFile(path, filename = "descarga") {
  const blob = await apiGetBlob(path);
  const u = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = u; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(u), 1000);
}

// ========== HELPERS DE UI ==========
export const $  = (sel, root=document) => root.querySelector(sel);
export const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));
export function showAlert(container, msg, type="success") {
  if (!container) return;
  container.innerHTML = `
    <div class="alert alert-${type} alert-dismissible fade show" role="alert">
      ${msg}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>`;
}

// ========== AUTH GUARD ==========
export function ensureAuthRedirect(loginPath = "/security/login") {
  const t = getToken();
  if (!t) { window.location.href = loginPath; return false; }
  return true;
}
