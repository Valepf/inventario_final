// static/js/suppliers.js
const API_SUP = "/suppliers";
const $tbody = document.getElementById("suppliers-tbody");
const $alert = document.getElementById("alertBox");
const $btnNew = document.getElementById("btnNewSupplier");

const $form = document.getElementById("supplierForm");
const $title = document.getElementById("supplierModalTitle");
const $id = document.getElementById("supplierId");
const $name = document.getElementById("supplierName");
const $email = document.getElementById("supplierEmail");
const $phone = document.getElementById("supplierPhone");

let IS_ADMIN = false;
function token(){ return localStorage.getItem("token"); }
function showAlert(m,t="info",ms=2500){ if(!$alert) return; $alert.className=`alert alert-${t}`; $alert.textContent=m; $alert.style.display="block"; if(ms) setTimeout(()=>($alert.style.display="none"),ms); }
async function me(){ try{ const r=await fetch("/auth/validate",{headers:{Authorization:`Bearer ${token()}`}}); const j=await r.json(); IS_ADMIN=j?.data?.role==="admin"; }catch{ IS_ADMIN=false; } }
async function unwrap(res){ let j=null; try{ j=await res.json(); }catch{} if(!res.ok){ const e=new Error(j?.error||`HTTP ${res.status}`); e.status=res.status; throw e; } if(Array.isArray(j)) return j; if(j?.ok&&"data"in j) return j.data; return j; }

function actionsHTML(id){ return IS_ADMIN ? `
  <button class="btn btn-sm btn-outline-primary mr-1" data-edit="${id}">Editar</button>
  <button class="btn btn-sm btn-outline-danger" data-del="${id}">Borrar</button>` : `<span class="text-muted">—</span>`; }

function rowHTML(s){ return `
  <tr data-id="${s.id}">
    <td>${s.id}</td>
    <td>${s.name}</td>
    <td>${s.contact ?? [s.email,s.phone].filter(Boolean).join(" | ")}</td>
    <td class="text-right" style="width:180px">${actionsHTML(s.id)}</td>
  </tr>`; }

async function loadList(){
  const r = await fetch(API_SUP,{headers:{Authorization:`Bearer ${token()}`}});
  const items = await unwrap(r);
  $tbody.innerHTML = items.map(rowHTML).join("");
  document.getElementById("emptyState")?.style.setProperty("display", items.length?"none":"block");
}

function resetForm(){ $id.value=""; $name.value=""; $email.value=""; $phone.value=""; }
function openModal(edit=false){ $title.textContent = edit? "Editar Proveedor":"Nuevo Proveedor"; window.jQuery && jQuery("#supplierModal").modal("show"); }

$btnNew?.addEventListener("click", ()=>{
  if(!IS_ADMIN){ showAlert("Solo un administrador puede crear proveedores","danger",3000); return; }
  resetForm(); openModal(false);
});

$tbody?.addEventListener("click", async (ev)=>{
  const btn=ev.target.closest("button"); if(!btn) return;
  const id = btn.dataset.edit || btn.dataset.del || ev.target.closest("tr")?.dataset.id;

  if(btn.dataset.edit){
    if(!IS_ADMIN){ showAlert("No autorizado para editar","danger",3000); return; }
    const r = await fetch(API_SUP,{headers:{Authorization:`Bearer ${token()}`}});
    const list = await unwrap(r);
    const s = list.find(x=>String(x.id)===String(id)); if(!s) return;
    $id.value=s.id; $name.value=s.name; $email.value=s.email||""; $phone.value=s.phone||"";
    openModal(true);
  }

  if(btn.dataset.del){
    if(!IS_ADMIN){ showAlert("No autorizado para borrar","danger",3000); return; }
    if(!confirm(`¿Eliminar proveedor #${id}?`)) return;
    try{
      const r=await fetch(`${API_SUP}/${id}`,{method:"DELETE",headers:{Authorization:`Bearer ${token()}`}});
      await unwrap(r); showAlert("Proveedor eliminado","success"); await loadList();
    }catch(e){ showAlert(e.status===403?"No autorizado":(e.message||"Error al eliminar"),"danger",3000); }
  }
});

$form?.addEventListener("submit", async (ev)=>{
  ev.preventDefault();
  if(!IS_ADMIN){ showAlert("No autorizado","danger",3000); return; }
  const contact = [($email.value||"").trim(), ($phone.value||"").trim()].filter(Boolean).join(" | ");
  const payload = { name:($name.value||"").trim(), email:($email.value||"").trim(), phone:($phone.value||"").trim(), contact };
  const id = $id.value;
  try{
    const r = await fetch(id?`${API_SUP}/${id}`:API_SUP,{
      method: id?"PUT":"POST",
      headers:{ "Content-Type":"application/json", Authorization:`Bearer ${token()}` },
      body: JSON.stringify(payload)
    });
    await unwrap(r);
    window.jQuery && jQuery("#supplierModal").modal("hide");
    showAlert(id?"Proveedor actualizado":"Proveedor creado","success");
    await loadList();
  }catch(e){ showAlert(e.status===403?"No autorizado":(e.message||"Error al guardar"),"danger",3500); }
});

(async function init(){ await me(); if(!IS_ADMIN) $btnNew?.classList.add("d-none"); await loadList(); })();
