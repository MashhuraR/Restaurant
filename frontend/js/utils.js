/* utils.js — Yordamchi funksiyalar */

function formatMoney(n) {
  return Number(n).toLocaleString('uz-UZ') + ' so\'m';
}

function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('uz-UZ', { day:'2-digit', month:'2-digit', year:'numeric' })
    + ' ' + d.toLocaleTimeString('uz-UZ', { hour:'2-digit', minute:'2-digit' });
}

function statusLabel(status) {
  const map = {
    pending: 'Kutilmoqda', confirmed: 'Tasdiqlangan',
    preparing: 'Tayyorlanmoqda', ready: 'Tayyor',
    delivered: 'Yetkazildi', cancelled: 'Bekor',
    completed: 'Amalga oshirildi', failed: 'Muvaffaqiyatsiz', refunded: 'Qaytarildi'
  };
  return map[status] || status;
}

function statusBadge(status) {
  return `<span class="badge badge-${status}">${statusLabel(status)}</span>`;
}

function categoryIcon(cat) {
  const icons = {
    'Salatlar': '🥗', 'Asosiy taomlar': '🍽️',
    'Sho\'rvalar': '🍲', 'Shirinliklar': '🍰',
    'Ichimliklar': '🥤', 'Tez taomlar': '🍔'
  };
  return icons[cat] || '🍴';
}

function toast(msg, type = 'success') {
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type]||''}</span> ${msg}`;
  document.getElementById('toastContainer').appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function openModal(title, bodyHTML, size = '') {
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalBody').innerHTML = bodyHTML;
  document.getElementById('modal').className = `modal ${size}`;
  document.getElementById('modalOverlay').classList.add('open');
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
}

function confirm(msg) {
  return window.confirm(msg);
}

function emptyState(icon, text) {
  return `<div class="empty-state"><i class="${icon}"></i><p>${text}</p></div>`;
}

function escapeJS(str) {
  if (!str) return '';
  return str.replace(/'/g, "\\'");
}

// Clock
function startClock() {
  const el = document.getElementById('clock');
  if (!el) return;
  const tick = () => {
    const now = new Date();
    el.textContent = now.toLocaleTimeString('uz-UZ', { hour:'2-digit', minute:'2-digit', second:'2-digit' });
  };
  tick();
  setInterval(tick, 1000);
}
