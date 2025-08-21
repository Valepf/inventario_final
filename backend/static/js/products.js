// static/js/products.js
const API_PRODUCTS   = "/products";
const API_CATEGORIES = "/categories";
const API_SUPPLIERS  = "/suppliers";

const $tbody      = document.getElementById("products-tbody");
const $alert      = document.getElementById("alertBox");
const $btnNew     = document.getElementById("btnNewProduct");
const $emptyState = document.getElementById("emptyState");

// Modal / Form
const $form        = document.getElementById("productForm");
const $modalTitle  = document.getElementById("productModalTitle");
const $id          = document.getElementById("productId");
const $name        = document.getElementById("name");
const $description = document.getElementById("description"); // opcional
const $categoryId  = document.getElementById("categoryId");
const $supplierId  = document.getElementById("supplier_id"); // ✅ nuevo
const $price       = document.getElementById("price");
const $stock       = document.getElementById("stock");

let IS_ADMIN = false;

// -------- Helpers base --------
function token(){ return localStorage.getItem("token"); }

function showAlert(msg, type="info", ms=2500){
  if(!$alert) return;
  $alert.className = `alert alert-${type}`;
  $alert.textContent = msg;
  $alert.style.display = "block";
  if(ms) setTimeout(()=>($alert.style.display="none"), ms);
}

async function me(){
  try{
    const r = await fetch("/auth/validate",{ headers:{ Authorization:`Bearer ${token()}` }});
    const j = await r.json();
    IS_ADMIN = j?.data?.role === "admin";
  }catch{
    IS_ADMIN = false;
  }
}

async function unwrap(res){
  let j=null; try{ j=await res.json(); }catch{}
  if(!res.ok){
    const e = new Error(j?.error || j?.message || `HTTP ${res.status}`);
    e.status = res.status;
    throw e;
  }
  if(Array.isArray(j)) return j;
  if(j?.ok && "data" in j) return j.data;
  return j;
}

function actionsHTML(id){
  if(!IS_ADMIN) return `<span class="text-muted">—</span>`;
  return `
    <button class="btn btn-sm btn-outline-primary mr-1" data-edit="${id}">Editar</button>
    <button class="btn btn-sm btn-outline-danger" data-del="${id}">Borrar</button>
  `;
}

// ✅ Ahora la fila refleja las columnas: ID, Nombre, Categoría, Proveedor, Precio, Stock, Acciones
function rowHTML(p){
  return `
    <tr data-id="${p.id}">
      <td>${p.id}</td>
      <td>${p.name}</td>
      <td>${p.category_name ?? p.category_id ?? "-"}</td>
      <td>${p.supplier_name ?? (p.supplier_id ?? "-")}</td>
      <td class="text-right">${Number(p.price).toFixed(2)}</td>
      <td class="text-right">${p.stock}</td>
      <td style="width:180px" class="text-right">${actionsHTML(p.id)}</td>
    </tr>
  `;
}

// -------- Cargas iniciales --------
async function loadCategories(){
  const r = await fetch(API_CATEGORIES, { headers:{ Authorization:`Bearer ${token()}` }});
  const items = await unwrap(r);
  if($categoryId){
    $categoryId.innerHTML = items.map(c=>`<option value="${c.id}">${c.name}</option>`).join("");
  }
}

// ✅ Cargar proveedores para el select del formulario
async function loadSuppliersForSelect(selectedId=null){
  try{
    const resp = await fetch(API_SUPPLIERS, { headers:{ Authorization:`Bearer ${token()}` }});
    const list = await unwrap(resp);
    if($supplierId){
      const opts = ['<option value="">— Sin proveedor —</option>']
        .concat(list.map(s => `<option value="${s.id}">${s.name}</option>`));
      $supplierId.innerHTML = opts.join("");
      if(selectedId !== null && selectedId !== undefined){
        $supplierId.value = String(selectedId);
      }
    }
  }catch(e){
    showAlert(`No se pudieron cargar proveedores: ${e.message}`, "danger");
  }
}

async function loadProducts(){
  const r = await fetch(API_PRODUCTS, { headers:{ Authorization:`Bearer ${token()}` }});
  const items = await unwrap(r);
  if($tbody) $tbody.innerHTML = items.map(rowHTML).join("");
  if($emptyState) $emptyState.style.display = items.length ? "none" : "block";
}

// -------- Modal / Form --------
function resetForm(){
  $id.value="";
  $name.value="";
  if($description) $description.value="";
  $price.value="0";
  $stock.value="0";
  if($categoryId?.options.length) $categoryId.selectedIndex = 0;
  if($supplierId?.options.length) $supplierId.value = "";
}

function openModal(edit=false){
  $modalTitle.textContent = edit? "Editar Producto" : "Nuevo Producto";
  if(window.jQuery) jQuery("#productModal").modal("show");
}

// -------- Eventos --------
$btnNew?.addEventListener("click", async ()=>{
  if(!IS_ADMIN){ showAlert("Solo un administrador puede crear productos","danger",3000); return; }
  resetForm();
  await Promise.all([loadCategories(), loadSuppliersForSelect()]);
  openModal(false);
});

// editar / borrar
$tbody?.addEventListener("click", async (ev)=>{
  const btn = ev.target.closest("button");
  if(!btn) return;
  const tr = ev.target.closest("tr");
  const id = tr?.dataset.id;

  if(btn.dataset.edit){
    if(!IS_ADMIN){ showAlert("No tenés permisos para editar","danger",3000); return; }
    try{
      // Podrías optimizar trayendo sólo el producto por id si tenés endpoint específico
      const r = await fetch(API_PRODUCTS, { headers:{ Authorization:`Bearer ${token()}` }});
      const list = await unwrap(r);
      const p = list.find(x=>String(x.id)===String(id));
      if(!p) return;

      await Promise.all([
        loadCategories(),
        loadSuppliersForSelect(p.supplier_id ?? null)
      ]);

      $id.value = p.id;
      $name.value = p.name;
      if($description) $description.value = p.description || "";
      $price.value = p.price;
      $stock.value = p.stock;
      $categoryId.value = p.category_id;

      openModal(true);
    }catch(e){
      showAlert(e.message || "No se pudo cargar el producto", "danger", 3000);
    }
  }

  if(btn.dataset.del){
    if(!IS_ADMIN){ showAlert("No tenés permisos para borrar","danger",3000); return; }
    if(!confirm(`¿Eliminar producto #${id}?`)) return;
    try{
      const r = await fetch(`${API_PRODUCTS}/${id}`, {
        method:"DELETE",
        headers:{ Authorization:`Bearer ${token()}` }
      });
      await unwrap(r);
      showAlert("Producto eliminado", "success");
      await loadProducts();
    }catch(e){
      showAlert(e.status===403?"No autorizado":"No se pudo eliminar","danger",3000);
    }
  }
});

// crear / actualizar
$form?.addEventListener("submit", async (ev)=>{
  ev.preventDefault();
  if(!IS_ADMIN){ showAlert("No autorizado","danger",3000); return; }

  const payload = {
    name: ($name.value||"").trim(),
    description: ($description?.value||"").trim(), // si tu backend lo acepta
    price: Number($price.value||0),
    stock: Number($stock.value||0),
    category_id: Number($categoryId.value),
    supplier_id: $supplierId?.value ? Number($supplierId.value) : null // ✅ enviar proveedor
  };

  const id = $id.value;
  try{
    const r = await fetch(id ? `${API_PRODUCTS}/${id}` : API_PRODUCTS, {
      method: id ? "PUT" : "POST",
      headers:{ "Content-Type":"application/json", Authorization:`Bearer ${token()}` },
      body: JSON.stringify(payload)
    });
    await unwrap(r);
    if(window.jQuery) jQuery("#productModal").modal("hide");
    showAlert(id ? "Producto actualizado" : "Producto creado", "success");
    await loadProducts();
  }catch(e){
    showAlert(e.status===403 ? "No autorizado" : (e.message||"Error al guardar"), "danger", 3500);
  }
});

// -------- Init --------
(async function init(){
  await me();
  if(!IS_ADMIN) $btnNew?.classList.add("d-none");
  await loadProducts();
})();
