/* app.js — Asosiy navigatsiya */
const pageRenderers = {
  dashboard: renderDashboard,
  menu: renderMenu,
  orders: renderOrders,
  payments: renderPayments,
};

const pageTitles = {
  dashboard: '📊 Dashboard',
  menu: '🍽️ Menyu',
  orders: '📋 Buyurtmalar',
  payments: '💳 To\'lovlar',
};

let currentPage = 'dashboard';

function navigateTo(page) {
  if (!pageRenderers[page]) return;

  // Nav items
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.page === page);
  });

  // Pages
  document.querySelectorAll('.page').forEach(el => el.classList.remove('active'));
  document.getElementById(`page-${page}`).classList.add('active');

  // Title
  document.getElementById('pageTitle').textContent = pageTitles[page] || page;

  currentPage = page;
  pageRenderers[page]();
}

// Sidebar toggle
document.getElementById('hamburger').addEventListener('click', () => {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('collapsed');
  sidebar.classList.toggle('open');
});

// Nav clicks
document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', e => {
    e.preventDefault();
    navigateTo(el.dataset.page);
  });
});

// Modal close
document.getElementById('modalClose').addEventListener('click', closeModal);
document.getElementById('modalOverlay').addEventListener('click', e => {
  if (e.target === e.currentTarget) closeModal();
});

// Start
startClock();
navigateTo('dashboard');
