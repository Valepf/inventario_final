// static/js/reports.js
// Export solo desde Reportes. Si no sos admin, escondemos botones de export.

let IS_ADMIN = false;
function token(){ return localStorage.getItem("token"); }
async function me(){
  try{
    const r=await fetch("/auth/validate",{headers:{Authorization:`Bearer ${token()}`}});
    const j=await r.json(); IS_ADMIN = j?.data?.role==="admin";
  }catch{ IS_ADMIN=false; }
}

const sbcCSV = document.getElementById("exp-sbc-csv");
const sbcPDF = document.getElementById("exp-sbc-pdf");
const ohCSV  = document.getElementById("exp-oh-csv");
const ohPDF  = document.getElementById("exp-oh-pdf");
const lowCSV = document.getElementById("exp-low-csv");
const lowPDF = document.getElementById("exp-low-pdf");

function hideExportsIfNotAdmin(){
  if(!IS_ADMIN){
    [sbcCSV,sbcPDF,ohCSV,ohPDF,lowCSV,lowPDF].forEach(b=> b?.classList.add("d-none"));
  }
}

function download(name, data, type="text/csv"){
  const blob = new Blob([data], { type });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = name; a.click();
  setTimeout(()=> URL.revokeObjectURL(a.href), 1000);
}

async function unwrap(res){ let j=null; try{ j=await res.json(); }catch{} if(!res.ok){ throw new Error(j?.error||`HTTP ${res.status}`); } if(Array.isArray(j)) return j; if(j?.ok&&"data"in j) return j.data; return j; }

let chartSBC, chartOH;

async function loadStockByCategory(){
  const r = await fetch("/reports/stock-by-category",{headers:{Authorization:`Bearer ${token()}`}});
  const data = await unwrap(r);
  const labels = data.map(d=>d.category);
  const values = data.map(d=>Number(d.total_stock||0));
  const ctx = document.getElementById("chart-stock-by-category").getContext("2d");
  if(chartSBC) chartSBC.destroy();
  chartSBC = new Chart(ctx,{ type:"bar", data:{ labels, datasets:[{label:"Stock", data:values}] }, options:{ responsive:true, maintainAspectRatio:false, plugins:{legend:{position:"bottom"}}, scales:{y:{beginAtZero:true}} } });
  return { labels, values };
}

async function loadOrdersHistory(){
  const r = await fetch("/reports/orders-history",{headers:{Authorization:`Bearer ${token()}`}});
  const data = await unwrap(r);
  const labels = data.map(d=>d.month);
  const values = data.map(d=>Number(d.count||0));
  const ctx = document.getElementById("chart-orders-history").getContext("2d");
  if(chartOH) chartOH.destroy();
  chartOH = new Chart(ctx,{ type:"line", data:{ labels, datasets:[{label:"Órdenes", data:values, tension:0.3, fill:true}] }, options:{ responsive:true, maintainAspectRatio:false, plugins:{legend:{position:"bottom"}}, scales:{y:{beginAtZero:true}} } });
  return { labels, values };
}

// Low stock: si /reports/low-stock no existe, calculamos desde /products
async function loadLowStock(th=5){
  try{
    const r = await fetch(`/reports/low-stock?threshold=${th}`,{headers:{Authorization:`Bearer ${token()}`}});
    if(r.status===404) throw new Error("fallback");
    const data = await unwrap(r);
    paintLowStock(data);
    return data;
  }catch{
    const rp = await fetch("/products",{headers:{Authorization:`Bearer ${token()}`}});
    const items = await unwrap(rp);
    const data = items.filter(p => Number(p.stock||0) <= th).map(p => ({
      id:p.id, name:p.name, category:p.category_name||p.category_id, stock:p.stock
    }));
    paintLowStock(data);
    return data;
  }
}
function paintLowStock(rows){
  const tbody = document.querySelector("#low-stock-table tbody");
  tbody.innerHTML = rows.map(r=>`
    <tr><td>${r.id}</td><td>${r.name}</td><td>${r.category}</td><td>${r.stock}</td></tr>
  `).join("");
}

// --- Exports (CSV client-side) ---
function csvFromColumns(headers, rows){
  const head = headers.join(",");
  const body = rows.map(r => r.map(v => `"${String(v??"").replace(/"/g,'""')}"`).join(",")).join("\n");
  return head + "\n" + body;
}

sbcCSV?.addEventListener("click", async ()=>{
  if(!IS_ADMIN) return;
  const {labels, values} = await loadStockByCategory();
  const rows = labels.map((cat,i)=> [cat, values[i]]);
  download("stock_por_categoria.csv", csvFromColumns(["category","total_stock"], rows));
});
sbcPDF?.addEventListener("click", ()=> alert("Exportar a PDF desde Reportes no está habilitado en esta build. Usá imprimir a PDF."));

ohCSV?.addEventListener("click", async ()=>{
  if(!IS_ADMIN) return;
  const {labels, values} = await loadOrdersHistory();
  const rows = labels.map((m,i)=> [m, values[i]]);
  download("ordenes_por_mes.csv", csvFromColumns(["month","orders"], rows));
});
ohPDF?.addEventListener("click", ()=> alert("Exportar a PDF desde Reportes no está habilitado en esta build. Usá imprimir a PDF."));

lowCSV?.addEventListener("click", async ()=>{
  if(!IS_ADMIN) return;
  const rows = await loadLowStock(5);
  const data = rows.map(r => [r.id, r.name, r.category, r.stock]);
  download("bajo_stock.csv", csvFromColumns(["id","name","category","stock"], data));
});
lowPDF?.addEventListener("click", ()=> alert("Exportar a PDF desde Reportes no está habilitado en esta build. Usá imprimir a PDF."));

document.addEventListener("DOMContentLoaded", async ()=>{
  await me(); hideExportsIfNotAdmin();
  await loadStockByCategory();
  await loadOrdersHistory();
  await loadLowStock(5);
});
