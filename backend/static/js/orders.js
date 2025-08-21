// static/js/orders.js

const API_ORDERS   = "/orders";
const API_PRODUCTS = "/products";

// ---------- refs ----------
const $tbody   = document.getElementById("orders-tbody");
const $btnNew  = document.getElementById("btnNewOrder");
const $form    = document.getElementById("orderForm");
const $title   = document.getElementById("orderModalTitle");
const $alert   = document.getElementById("alertBox");

const $orderId   = document.getElementById("orderId");
const $productId = document.getElementById("productId");
const $quantity  = document.getElementById("quantity");
const $status    = document.getElementById("status");

let IS_ADMIN = false;

// ---------- helpers ----------
function getToken(){ return localStorage.getItem("token"); }

function showAlert(msg, type="info", ms=2500) {
  if (!$alert) return;
  $alert.className = `alert alert-${type}`;
  $alert.textContent = msg;
  $alert.style.display = "block";
  if (ms) setTimeout(() => ($alert.style.display = "none"), ms);
}

async function whoAmI(){
  try {
    const r = await fetch("/auth/validate", { headers: { Authorization: `Bearer ${getToken()}` }});
    if (!r.ok) throw new Error("401");
    const j = await r.json();
    IS_ADMIN = (j?.data?.role === "admin");
  } catch {
    IS_ADMIN = false;
  }
}

async function unwrapResponse(res){
  let payload = null;
  try { payload = await res.json(); } catch { /* ignore parse */ }

  if (!res.ok) {
    const apiMsg = payload?.error || payload?.message;
    const e = new Error(apiMsg || `HTTP ${res.status}`);
    e.status = res.status;
    e.code   = payload?.code;
    throw e;
  }

  // soporta {ok:true,data:...} o array directo
  if (Array.isArray(payload)) return payload;
  if (payload && payload.ok && "data" in payload) return payload.data;
  return payload;
}

function fmtDate(dt) {
  if (!dt) return "-";
  const s = String(dt).replace("T", " ");
  return s.slice(0, 16);
}

function badgeStatus(s) {
  const v = (s || "").toLowerCase();
  const map = { pending: "secondary", received: "info", completed: "success", cancelled: "danger", canceled: "danger" };
  const cls = map[v] || "light";
  return `<span class="badge badge-${cls}">${s}</span>`;
}

async function loadProducts() {
  const res = await fetch(API_PRODUCTS, { headers: { Authorization: `Bearer ${getToken()}` } });
  const items = await unwrapResponse(res);
  $productId.innerHTML = items.map(p => `<option value="${p.id}">${p.name}</option>`).join("");
}

function actionsHTML(oId){
  if (!IS_ADMIN) return `<span class="text-muted">—</span>`;
  return `
    <button class="btn btn-sm btn-outline-primary mr-1" data-action="edit" data-id="${oId}">Editar</button>
    <button class="btn btn-sm btn-outline-danger" data-action="del" data-id="${oId}">Borrar</button>
  `;
}

function rowHTML(o) {
  return `
    <tr data-id="${o.id}">
      <td>${o.id}</td>
      <td>${o.product_name || o.productId || o.product_id}</td>
      <td>${o.quantity}</td>
      <td>${badgeStatus(o.status)}</td>
      <td>${fmtDate(o.order_date)}</td>
      <td>${fmtDate(o.receipt_date)}</td>
      <td class="text-right">${actionsHTML(o.id)}</td>
    </tr>
  `;
}

async function loadOrders() {
  const res = await fetch(API_ORDERS, { headers: { Authorization: `Bearer ${getToken()}` } });
  const items = await unwrapResponse(res);
  $tbody.innerHTML = items.map(rowHTML).join("");
}

function resetForm() {
  $orderId.value = "";
  $quantity.value = 1;
  $status.value = "pending";
  if ($productId.options.length) $productId.selectedIndex = 0;
}

function openModal(editing=false) {
  $title.textContent = editing ? "Editar Orden" : "Nueva Orden";
  window.jQuery && jQuery('#orderModal').modal('show');
}

// ---------- eventos ----------
$btnNew?.addEventListener("click", async () => {
  resetForm();
  await loadProducts();
  openModal(false);
});

$tbody?.addEventListener("click", async (ev) => {
  const btn = ev.target.closest("button");
  if (!btn) return;

  const action = btn.dataset.action;
  const id = btn.dataset.id || ev.target.closest("tr")?.dataset.id;

  if (action === "edit") {
    if (!IS_ADMIN) { showAlert("No tenés permisos para editar órdenes", "danger", 3000); return; }
    try {
      const res = await fetch(`${API_ORDERS}/${id}`, { headers: { Authorization: `Bearer ${getToken()}` } });
      const o = await unwrapResponse(res);
      await loadProducts();
      $orderId.value = o.id;
      $quantity.value = o.quantity;
      $status.value   = (o.status || "pending").toLowerCase();
      $productId.value = o.product_id || o.productId || "";
      openModal(true);
    } catch (e) {
      showAlert(e.message || "No se pudo cargar la orden", "danger", 3000);
    }
  }

  if (action === "del") {
    if (!IS_ADMIN) { showAlert("No tenés permisos para borrar órdenes", "danger", 3000); return; }
    if (!confirm(`¿Eliminar orden #${id}?`)) return;

    btn.disabled = true;
    try {
      const res = await fetch(`${API_ORDERS}/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      await unwrapResponse(res);
      showAlert("Orden eliminada", "success");
      await loadOrders();
    } catch (e) {
      if (e.status === 403) {
        showAlert("No autorizado: se requiere rol administrador", "danger", 3500);
      } else if (e.status === 404) {
        showAlert("La orden no existe", "warning", 3000);
        await loadOrders(); // refrescar para alinear UI
      } else {
        showAlert(e.message || "No se pudo eliminar la orden", "danger", 3500);
      }
    } finally {
      btn.disabled = false;
    }
  }
});

$form?.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const payload = {
    product_id: Number($productId.value),
    quantity:   Number($quantity.value),
    status:     ($status.value || "pending").toLowerCase(),
  };
  const id = $orderId.value;

  try {
    const res = await fetch(id ? `${API_ORDERS}/${id}` : API_ORDERS, {
      method: id ? "PUT" : "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getToken()}`,
      },
      body: JSON.stringify(payload),
    });
    const data = await unwrapResponse(res);
    window.jQuery && jQuery('#orderModal').modal('hide');

    showAlert(id ? "Orden actualizada" : "Orden creada", "success");
    await loadOrders();
  } catch (e) {
    if (e.status === 403) {
      showAlert("No autorizado: se requiere rol administrador", "danger", 3500);
    } else if (e.status === 401) {
      showAlert("Sesión expirada. Volvé a iniciar sesión.", "warning", 3500);
      setTimeout(() => (window.location.href = "/login"), 1200);
    } else {
      showAlert(e.message || "Error al guardar la orden", "danger", 3500);
    }
  }
});

// ---------- init ----------
(async function init(){
  await whoAmI();     // define IS_ADMIN
  await loadOrders(); // render con/ sin acciones según rol
})();
