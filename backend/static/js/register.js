// static/js/register.js
const form = document.getElementById("registerForm");
const msg = document.getElementById("responseMessage");

function token(){ return localStorage.getItem("token"); }
function alertMsg(t){ msg.textContent=t; msg.style.display="block"; }

async function ensureAdmin(){
  try{
    const r = await fetch("/auth/validate",{headers:{Authorization:`Bearer ${token()}`}});
    const j = await r.json();
    if(j?.data?.role !== "admin"){
      alertMsg("Solo un administrador puede registrar usuarios.");
      setTimeout(()=> (window.location.href="/dashboard"), 1200);
      return false;
    }
    return true;
  }catch{ window.location.href="/login"; return false; }
}

form?.addEventListener("submit", async (ev)=>{
  ev.preventDefault(); msg.style.display="none";
  const username = (document.getElementById("username").value||"").trim();
  const password = (document.getElementById("password").value||"").trim();
  let   role     = (document.getElementById("role").value||"user").trim();
  if(role==="general") role="user"; // tu UI ofrece "general", el backend usa "user"

  if(!username || !password){ alertMsg("Usuario y contraseña son obligatorios"); return; }

  try{
    const r = await fetch("/auth/register",{
      method:"POST",
      headers:{ "Content-Type":"application/json", Authorization:`Bearer ${token()}` },
      body: JSON.stringify({ username, password, role })
    });
    const j = await r.json();
    if(!r.ok || !j?.ok){ throw new Error(j?.error || `HTTP ${r.status}`); }
    alertMsg("Usuario registrado ✔"); setTimeout(()=> (window.location.href="/usuarios"), 800);
  }catch(e){ alertMsg(e.message || "No se pudo registrar"); }
});

document.addEventListener("DOMContentLoaded", ensureAdmin);
