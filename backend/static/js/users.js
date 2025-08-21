// static/js/users.js
const API_USERS = "/users";

const $tbody = document.querySelector("#users-table tbody");
const $alert = document.getElementById("alertBox");
const $btnNew = document.getElementById("btnNewUser");

const $form = document.getElementById("userForm");
const $title = document.getElementById("userModalTitle");
const $id = document.getElementById("userId");
const $username = document.getElementById("username");
const $password = document.getElementById("password");
const $role = document.getElementById("role");
const $saveBtn = document.getElementById("userSaveBtn");

function token(){ return localStorage.getItem("token"); }
function showAlert(m,t="info",ms=2500){ if(!$alert) return; $alert.className=`alert alert-${t}`; $alert.textContent=m; $alert.style.display="block"; if(ms) setTimeout(()=>($alert.style.display="none"),ms); }

async function ensureAdmin(){
  try{
    const r = await fetch("/auth/validate",{headers:{Authorization:`Bearer ${token()}`}});
    const j = await r.json();
    if(j?.data?.role !== "admin"){
      showAlert("Debes ser administrador para acceder a Usuarios", "danger", 4000);
      setTimeout(()=> (window.location.href="/dashboard"), 800);
      return false;
    }
    return true;
  }catch{ window.location.href="/login"; return false; }
}

async function unwrap(res){ let j=null; try{ j=await res.json(); }catch{} if(!res.ok){ const e=new Error(j?.error||`HTTP ${res.status}`); e.status=res.status; throw e; } if(Array.isArray(j)) return j; if(j?.ok&&"data"in j) return j.data; return j; }

function rowHTML(u){
  return `
    <tr data-id="${u.id}">
      <td>${u.id}</td>
      <td>${u.username}</td>
      <td>${u.role}</td>
      <td>${u.created_at ?? ""}</td>
      <td class="text-right" style="width:180px">
        <button class="btn btn-sm btn-outline-primary mr-1" data-edit="${u.id}">Editar</button>
        <button class="btn btn-sm btn-outline-danger" data-del="${u.id}">Borrar</button>
      </td>
    </tr>
  `;
}

async function loadUsers(){
  const r = await fetch(API_USERS,{headers:{Authorization:`Bearer ${token()}`}});
  const items = await unwrap(r);
  $tbody.innerHTML = items.map(rowHTML).join("");
  document.getElementById("emptyState")?.style.setProperty("display", items.length?"none":"block");
}

function resetForm(){ $id.value=""; $username.value=""; $password.value=""; $role.value="user"; }
function openModal(edit=false){ $title.textContent=edit?"Editar Usuario":"Nuevo Usuario"; window.jQuery && jQuery("#userModal").modal("show"); }

$btnNew?.addEventListener("click", ()=>{ resetForm(); openModal(false); });

$tbody?.addEventListener("click", async (ev)=>{
  const btn = ev.target.closest("button"); if(!btn) return;
  const rowId = btn.dataset.edit || btn.dataset.del || ev.target.closest("tr")?.dataset.id;

  if(btn.dataset.edit){
    const r = await fetch(API_USERS,{headers:{Authorization:`Bearer ${token()}`}});
    const list = await unwrap(r);
    const u = list.find(x=>String(x.id)===String(rowId)); if(!u) return;
    $id.value=u.id; $username.value=u.username; $role.value=u.role; $password.value="";
    openModal(true);
  }

  if(btn.dataset.del){
    if(!confirm(`¿Eliminar usuario #${rowId}?`)) return;
    try{
      const r = await fetch(`${API_USERS}/${rowId}`,{method:"DELETE",headers:{Authorization:`Bearer ${token()}`}});
      await unwrap(r); showAlert("Usuario eliminado","success"); await loadUsers();
    }catch(e){ showAlert(e.message||"No se pudo eliminar","danger",3000); }
  }
});

$form?.addEventListener("submit", async (ev)=>{
  ev.preventDefault();
  const id = $id.value;
  const payload = { username: ($username.value||"").trim(), role: ($role.value||"user").trim() };
  const pwd = ($password.value||"").trim(); if(!id && !pwd){ showAlert("Contraseña obligatoria para crear","danger"); return; }
  if(pwd) payload.password = pwd;

  try{
    const r = await fetch(id?`${API_USERS}/${id}`:API_USERS,{
      method: id?"PUT":"POST",
      headers:{ "Content-Type":"application/json", Authorization:`Bearer ${token()}` },
      body: JSON.stringify(payload)
    });
    await unwrap(r);
    window.jQuery && jQuery("#userModal").modal("hide");
    showAlert(id?"Usuario actualizado":"Usuario creado","success");
    await loadUsers();
  }catch(e){ showAlert(e.message||"Error al guardar","danger",3500); }
});

document.addEventListener("DOMContentLoaded", async ()=>{
  if(!(await ensureAdmin())) return;
  await loadUsers();
});
