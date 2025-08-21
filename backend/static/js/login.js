// static/js/login.js

const overlay = document.getElementById("bootOverlay");
const overlayText = document.getElementById("bootOverlayText");
const msg = document.getElementById("responseMessage");
const form = document.getElementById("loginForm");
const btn  = document.getElementById("loginButton");

function showOverlay(text = "Cargando…") {
  if (overlayText) overlayText.textContent = text;
  if (overlay) overlay.style.display = "flex";
}

function hideOverlay() {
  if (overlay) overlay.style.display = "none";
}

function unwrap(json) {
  // Soporta {ok:true,data:...} o respuesta directa
  if (json && typeof json === "object" && "ok" in json) {
    if (json.ok) return json.data ?? {};
    const e = new Error(json.error || "Error");
    e.code = json.code;
    throw e;
  }
  return json;
}

async function validateToken(token) {
  const r = await fetch("/auth/validate", { headers: { Authorization: `Bearer ${token}` } });
  if (!r.ok) throw new Error("Token inválido");
  const j = unwrap(await r.json());
  return j; // {id, role}
}

// Precarga datos del dashboard para que /dashboard abra “instantáneo”
async function preloadData(token) {
  const headers = { Authorization: `Bearer ${token}` };
  const tasks = [
    fetch("/dashboard/metrics", { headers }).then(r => r.ok ? r.json().then(unwrap) : {}),
    fetch("/reports/stock-by-category", { headers }).then(r => r.ok ? r.json().then(unwrap) : []),
    fetch("/reports/orders-history", { headers }).then(r => r.ok ? r.json().then(unwrap) : []),
  ];
  const [metrics, stockByCat, ordersHist] = await Promise.all(tasks);

  const stamp = Date.now();
  // Guardamos en sessionStorage para lectura rápida en dashboard.js (si lo querés usar)
  sessionStorage.setItem("preload:metrics", JSON.stringify({ t: stamp, v: metrics }));
  sessionStorage.setItem("preload:stockByCategory", JSON.stringify({ t: stamp, v: stockByCat }));
  sessionStorage.setItem("preload:ordersHistory", JSON.stringify({ t: stamp, v: ordersHist }));
}

async function tryAutoForward() {
  const token = localStorage.getItem("token");
  if (!token) return; // no hay sesión

  showOverlay("Verificando sesión…");
  try {
    await validateToken(token);

    // Opcional: precargar con timeout para no “quedarse pegado” si algo falla
    showOverlay("Preparando tu panel…");
    await Promise.race([
      preloadData(token),
      new Promise((resolve) => setTimeout(resolve, 2500)) // límite de 2.5s
    ]);

    window.location.href = "/dashboard";
  } catch {
    hideOverlay(); // token inválido -> mostramos el login
  }
}

document.addEventListener("DOMContentLoaded", tryAutoForward);

// Submit del login
form?.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  msg.style.display = "none";

  const username = (document.getElementById("username").value || "").trim();
  const password = (document.getElementById("password").value || "").trim();
  if (!username || !password) {
    msg.textContent = "Usuario y contraseña son obligatorios";
    msg.style.display = "block";
    return;
  }

  btn.disabled = true;
  showOverlay("Ingresando…");

  try {
    const res = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    const json = await res.json().catch(() => ({}));
    const data = unwrap(json); // {token, role, id}
    if (!data?.token) throw new Error("Respuesta de login inválida");

    localStorage.setItem("token", data.token);
    if (data.role) localStorage.setItem("role", data.role);
    if (data.id)   localStorage.setItem("user_id", data.id);

    // Precarga antes de ir al dashboard
    showOverlay("Preparando tu panel…");
    await Promise.race([
      preloadData(data.token),
      new Promise((resolve) => setTimeout(resolve, 2500))
    ]);

    window.location.href = "/dashboard";
  } catch (e) {
    hideOverlay();
    btn.disabled = false;
    msg.textContent = e.message || "No se pudo iniciar sesión";
    msg.style.display = "block";
  }
});
