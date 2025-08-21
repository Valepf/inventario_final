// static/js/layout.js
document.addEventListener("DOMContentLoaded", async () => {
  // Logout
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", (ev) => {
      ev.preventDefault();
      localStorage.clear();
      window.location.href = "/login";
    });
  }

  // Toggle sidebar
  const sidebarToggle = document.getElementById("sidebarToggle");
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      document.body.classList.toggle("sidebar-toggled");
      const sidebar = document.querySelector(".sidebar");
      if (sidebar) sidebar.classList.toggle("toggled");
    });
  }

  // Mostrar "Usuarios" solo si el rol es admin
  const token = localStorage.getItem("token");
  if (!token) return;

  try {
    const resp = await fetch("/auth/validate", {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!resp.ok) throw new Error("Token inválido");

    const data = await resp.json();
    // Soporta {ok:true,data:{role}} o {role:"admin"}
    const role = data?.data?.role ?? data?.role ?? null;

    if (role === "admin") {
      const userLink = document.getElementById("usuariosLink");
      if (userLink) userLink.classList.remove("d-none");
    }
  } catch (err) {
    console.warn("No se pudo validar el rol:", err.message);
  }
});
