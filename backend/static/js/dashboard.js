// static/js/dashboard.js
import { apiGet } from "/static/js/common.js";

let stockChart, ordersChart;

const baseOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: "bottom" } },
  scales: { y: { beginAtZero: true } }
};

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

async function loadKpis() {
  try {
    const m = await apiGet("/dashboard/metrics");
    setText("kpi-products", m.products ?? 0);
    setText("kpi-categories", m.categories ?? 0);
    setText("kpi-suppliers", m.suppliers ?? 0);
    setText("kpi-orders-today", m.orders_today ?? 0);
    setText("kpi-low-stock", m.low_stock ?? 0);
  } catch (e) {
    console.error("KPIs error:", e);
  }
}

async function loadStockByCategory() {
  try {
    const data = await apiGet("/reports/stock-by-category");
    const labels = data.map(d => d.category);
    const values = data.map(d => Number(d.total_stock || 0));

    const ctx = document.getElementById("chart-stock-by-category").getContext("2d");
    if (stockChart) stockChart.destroy();
    stockChart = new Chart(ctx, {
      type: "bar",
      data: { labels, datasets: [{ label: "Stock", data: values }] },
      options: baseOptions
    });
  } catch (e) {
    console.error("Chart stock-by-category error:", e);
  }
}

async function loadOrdersHistory() {
  try {
    const data = await apiGet("/reports/orders-history");
    const labels = data.map(d => d.month); // ej: "2025-08"
    const values = data.map(d => Number(d.count || 0));

    const ctx = document.getElementById("chart-orders-history").getContext("2d");
    if (ordersChart) ordersChart.destroy();
    ordersChart = new Chart(ctx, {
      type: "line",
      data: { labels, datasets: [{ label: "Órdenes", data: values, tension: 0.3, fill: true }] },
      options: baseOptions
    });
  } catch (e) {
    console.error("Chart orders-history error:", e);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await loadKpis();
  await Promise.all([loadStockByCategory(), loadOrdersHistory()]);
});
