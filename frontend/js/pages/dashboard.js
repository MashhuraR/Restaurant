/* pages/dashboard.js */
async function renderDashboard() {
  const el = document.getElementById('page-dashboard');
  el.innerHTML = `<div class="loading-overlay"><div class="spinner"></div></div>`;
  try {
    const stats = await API.getStatistics();
    const orders = await API.getActiveOrders();

    const topItemsHTML = stats.top_items && stats.top_items.length
      ? stats.top_items.map((item, i) => {
          const max = stats.top_items[0].count || 1;
          const pct = Math.round(item.count / max * 100);
          return `
            <div class="top-item">
              <div class="top-item-rank">${i + 1}</div>
              <div style="flex:1">
                <div style="display:flex;justify-content:space-between">
                  <span class="top-item-name">${item.name}</span>
                  <span class="top-item-count">${item.count} ta</span>
                </div>
                <div class="top-item-bar"><div class="top-item-bar-fill" style="width:${pct}%"></div></div>
              </div>
            </div>`;
        }).join('')
      : emptyState('fas fa-chart-bar', 'Ma\'lumot yo\'q');

    const activeOrdersHTML = orders.length
      ? orders.map(o => `
          <tr>
            <td><strong>${o.id}</strong></td>
            <td>${o.customer_name}</td>
            <td>${statusBadge(o.status)}</td>
            <td>${o.item_count} ta</td>
            <td><strong>${formatMoney(o.total)}</strong></td>
            <td>${formatDate(o.created_at)}</td>
          </tr>`).join('')
      : `<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:30px">Faol buyurtmalar yo'q</td></tr>`;

    el.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon"><i class="fas fa-receipt"></i></div>
          <div class="stat-info">
            <div class="stat-value">${stats.total_orders || 0}</div>
            <div class="stat-label">Jami buyurtmalar</div>
          </div>
        </div>
        <div class="stat-card green">
          <div class="stat-icon"><i class="fas fa-check-circle"></i></div>
          <div class="stat-info">
            <div class="stat-value">${stats.completed_orders || 0}</div>
            <div class="stat-label">Bajarilgan</div>
          </div>
        </div>
        <div class="stat-card orange">
          <div class="stat-icon"><i class="fas fa-hourglass-half"></i></div>
          <div class="stat-info">
            <div class="stat-value">${stats.active_orders || 0}</div>
            <div class="stat-label">Kutilmoqda</div>
          </div>
        </div>
        <div class="stat-card blue">
          <div class="stat-icon"><i class="fas fa-coins"></i></div>
          <div class="stat-info">
            <div class="stat-value" style="font-size:18px">${formatMoney(stats.active_revenue || 0)}</div>
            <div class="stat-label">Kutilayotgan tushum</div>
          </div>
        </div>
        <div class="stat-card purple">
          <div class="stat-icon"><i class="fas fa-money-bill-wave"></i></div>
          <div class="stat-info">
            <div class="stat-value" style="font-size:18px">${formatMoney(stats.total_revenue || 0)}</div>
            <div class="stat-label">Jami daromad (To'langan)</div>
          </div>
        </div>
        <div class="stat-card red">
          <div class="stat-icon"><i class="fas fa-times-circle"></i></div>
          <div class="stat-info">
            <div class="stat-value">${stats.cancelled_orders || 0}</div>
            <div class="stat-label">Bekor qilingan</div>
          </div>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
        <div class="card">
          <div class="card-header">
            <span class="card-title"><i class="fas fa-fire" style="color:var(--primary)"></i> Faol buyurtmalar</span>
            <button class="btn btn-ghost btn-sm" onclick="navigateTo('orders')">
              <i class="fas fa-arrow-right"></i> Barchasi
            </button>
          </div>
          <div class="table-wrap">
            <table>
              <thead><tr>
                <th>ID</th><th>Mijoz</th><th>Status</th><th>Soni</th><th>Summa</th><th>Vaqt</th>
              </tr></thead>
              <tbody>${activeOrdersHTML}</tbody>
            </table>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <span class="card-title"><i class="fas fa-trophy" style="color:var(--accent)"></i> Top taomlar</span>
          </div>
          ${topItemsHTML}
        </div>
      </div>`;
  } catch (e) {
    el.innerHTML = `<div class="card" style="color:var(--danger);text-align:center;padding:40px">
      <i class="fas fa-exclamation-circle" style="font-size:32px;margin-bottom:10px;display:block"></i>
      Backend ulanmagan! <br><small>python app.py buyrug'ini ishga tushiring</small>
    </div>`;
  }
}
window.renderDashboard = renderDashboard;
