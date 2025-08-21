// static/js/categories.js
const API_CATEGORIES = "/categories";

const $tbody   = document.getElementById("categories-tbody");
const $btnNew  = document.getElementById("btnNewCategory");
const $form    = document.getElementById("categoryForm");
const $title   = document.getElementById("categoryModalTitle");
const $alert   = document.getElementById("alertBox");

const $id   = document.getElementById("categoryId");
const $name = document.getElementById("categoryName");

let IS_ADMIN = false;

// ----------------- helpers -----------------
function token(){ return localStorage.getItem("token"); }

function showAlert(msg, type="info", ms=2500){
  if(!$alert) return;
  $alert.className = `alert alert-${type}`;
  $alert.textContent = msg;
  $alert.style.display = "block";
  if(ms) setTimeout(()=> ($alert.style.display="none"), ms);
}

async function whoAmI(){
  try{
    const r = await fetch("/auth/validate", { headers:{ Authorization:`Bearer ${token()}` }});
    const j = await r.json();
    IS_ADMIN = j?.data?.role === "admin";
  }catch{
    IS_ADMIN = false;
  }
}

async function unwrap(res){
  let j = null;
  try { j = await res.json(); } catch {}
  if(!res.ok){
    const e = new Error(j?.error || `HTTP ${res.status}`);
    e.status = res.status;
    e.code   = j?.code;
    throw e;
  }
  if(Array.isArray(j)) return j;
  if(j && j.ok && "data" in j) return j.data;
  return j;
}

function actionsHTML(id){
  if(!IS_ADMIN) return `<span class="text-muted">—</span>`;
  return `
    <button class="btn btn-sm btn-outline-primary mr-1" data-edit="${id}">Editar</button>
    <button class="btn btn-sm btn-outline-danger"  data-del="${id}">Eliminar</button>
  `;
}

function rowHTML(c){
  return `
    <tr data-id="${c.id}">
      <td>${c.id}</td>
      <td>${c.name}</td>
      <td class="text-right" style="width:160px">${actionsHTML(c.id)}</td>
    </tr>
  `;
}

async function loadCategories(){
  const r = await fetch(API_CATEGORIES, { headers:{ Authorization:`Bearer ${token()}` }});
  const items = await unwrap(r);
  $tbody.innerHTML = items.map(rowHTML).join("");
  // si tenés un empty state opcional:
  document.getElementById("emptyState")?.style.setProperty("display", items.length ? "none" : "block");
}

function resetForm(){
  $id.value = "";
  $name.value = "";
}

function openModal(edit=false){
  $title.textContent = edit ? "Editar Categoría" : "Nueva Categoría";
  window.jQuery && jQuery("#categoryModal").modal("show");
}

// ----------------- eventos -----------------
$btnNew?.addEventListener("click", () => {
  if(!IS_ADMIN){ showAlert("Solo un administrador puede crear categorías","danger",3000); return; }
  resetForm(); openModal(false);
});

$tbody?.addEventListener("click", async (ev) => {
  const btn = ev.target.closest("button");
  if(!btn) return;

  const tr = ev.target.closest("tr");
  const id = tr?.dataset.id;
  if(!id) return;

  // EDITAR
  if(btn.dataset.edit){
    if(!IS_ADMIN){ showAlert("No tenés permisos para editar categorías","danger",3000); return; }
    try{
      // No hay GET /categories/<id> en el backend; usamos la lista y buscamos
      const r = await fetch(API_CATEGORIES, { headers:{ Authorization:`Bearer ${token()}` }});
      const list = await unwrap(r);
      const c = list.find(x => String(x.id) === String(id));
      if(!c){ showAlert("Categoría no encontrada","warning",2500); return; }

      $id.value = c.id;
      $name.value = c.name || "";
      openModal(true);
    }catch(e){
      showAlert(e.message || "No se pudo cargar la categoría","danger",3000);
    }
  }

  // ELIMINAR
  if(btn.dataset.del){
    if(!IS_ADMIN){ showAlert("No tenés permisos para eliminar categorías","danger",3000); return; }
    if(!confirm(`¿Eliminar categoría #${id}?`)) return;

    btn.disabled = true;
    try{
      const r = await fetch(`${API_CATEGORIES}/${id}`, {
        method: "DELETE",
        headers: { Authorization:`Bearer ${token()}` }
      });
      await unwrap(r);
      showAlert("Categoría eliminada","success");
      await loadCategories();
    }catch(e){
      if(e.status === 403) showAlert("No autorizado: se requiere rol administrador","danger",3500);
      else if(e.status === 404){ showAlert("La categoría no existe","warning",3000); await loadCategories(); }
      else showAlert(e.message || "No se pudo eliminar","danger",3500);
    }finally{
      btn.disabled = false;
    }
  }
});

$form?.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const id = $id.value;
  const payload = { name: ($name.value || "").trim() };

  if(!payload.name){ showAlert("El nombre es obligatorio","danger",2500); return; }

  try{
    const r = await fetch(id ? `${API_CATEGORIES}/${id}` : API_CATEGORIES, {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type":"application/json", Authorization:`Bearer ${token()}` },
      body: JSON.stringify(payload)
    });
    await unwrap(r);
    window.jQuery && jQuery("#categoryModal").modal("hide");
    showAlert(id ? "Categoría actualizada" : "Categoría creada","success");
    await loadCategories();
  }catch(e){
    if(e.status === 403) showAlert("No autorizado: se requiere rol administrador","danger",3500);
    else if(e.status === 401){ showAlert("Sesión expirada. Volvé a iniciar sesión","warning",3500); setTimeout(()=> (window.location.href="/login"),1200); }
    else showAlert(e.message || "Error al guardar","danger",3500);
  }
});

// ----------------- init -----------------
(async function init(){
  await whoAmI();
  if(!IS_ADMIN) $btnNew?.classList.add("d-none");
  await loadCategories();
})();
