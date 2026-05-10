/* pages/payments.js */
async function renderPayments() {
  const el = document.getElementById('page-payments');
  el.innerHTML = `<div class="loading-overlay"><div class="spinner"></div></div>`;
  try {
    const [payments, revenue] = await Promise.all([API.getPayments(), API.getRevenue()]);
    const methodLabels = {
      cash: '💵 Naqd', card: '💳 Karta', online: '🌐 Online', payme: '📱 Payme', click: '📱 Click'
    };

    const rows = payments.length
      ? payments.map(p => `
          <tr>
            <td><strong>${p.id}</strong></td>
            <td>${p.order_id}</td>
            <td><strong style="color:var(--primary)">${formatMoney(p.amount)}</strong></td>
            <td>${methodLabels[p.method] || p.method}</td>
            <td>${statusBadge(p.status)}</td>
            <td>${p.cashier_name || '—'}</td>
            <td>${p.transaction_id || '—'}</td>
            <td>${formatDate(p.created_at)}</td>
            <td>
              ${p.status === 'completed' ? `<button class="btn-icon" title="Qaytarish" onclick="doRefund('${p.id}')"><i class="fas fa-undo" style="color:var(--warning)"></i></button>` : '—'}
            </td>
          </tr>`).join('')
      : `<tr><td colspan="9" style="text-align:center;padding:40px;color:var(--text-muted)">To'lovlar yo'q</td></tr>`;

    const byMethodHTML = Object.entries(revenue.by_method || {}).map(([method, amount]) =>
      `<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:14px">
        <span>${methodLabels[method] || method}</span>
        <strong>${formatMoney(amount)}</strong>
      </div>`).join('') || '<div style="color:var(--text-muted);font-size:13px">Ma\'lumot yo\'q</div>';

    el.innerHTML = `
      <div class="stats-grid" style="grid-template-columns:repeat(3,1fr);margin-bottom:20px">
        <div class="stat-card green">
          <div class="stat-icon"><i class="fas fa-money-bill-wave"></i></div>
          <div class="stat-info">
            <div class="stat-value">${formatMoney(revenue.total_revenue || 0)}</div>
            <div class="stat-label">Jami daromad</div>
          </div>
        </div>
        <div class="stat-card blue">
          <div class="stat-icon"><i class="fas fa-receipt"></i></div>
          <div class="stat-info">
            <div class="stat-value">${revenue.total_transactions || 0}</div>
            <div class="stat-label">To'lovlar soni</div>
          </div>
        </div>
        <div class="stat-card red">
          <div class="stat-icon"><i class="fas fa-undo"></i></div>
          <div class="stat-info">
            <div class="stat-value">${formatMoney(revenue.total_refunded || 0)}</div>
            <div class="stat-label">Qaytarilgan</div>
          </div>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 300px;gap:20px">
        <div class="card" style="padding:0">
          <div class="card-header" style="padding:16px 20px">
            <span class="card-title"><i class="fas fa-history" style="color:var(--primary)"></i> To'lovlar tarixi</span>
          </div>
          <div class="table-wrap">
            <table>
              <thead><tr>
                <th>ID</th><th>Buyurtma</th><th>Summa</th><th>Usul</th>
                <th>Status</th><th>Kassir</th><th>Tranzaksiya</th><th>Vaqt</th><th></th>
              </tr></thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <span class="card-title"><i class="fas fa-chart-pie" style="color:var(--accent)"></i> Usul bo'yicha</span>
          </div>
          ${byMethodHTML}
        </div>
      </div>`;
  } catch(e) {
    el.innerHTML = `<div class="card" style="color:var(--danger);text-align:center">Backend ulanmagan!</div>`;
  }
}

async function doRefund(paymentId) {
  if (!confirm('Bu to\'lovni qaytarishni tasdiqlaysizmi?')) return;
  try {
    await API.refundPayment(paymentId);
    toast('To\'lov qaytarildi!', 'warning');
    await renderPayments();
  } catch(e) { toast(e.message, 'error'); }
}

window.renderPayments = renderPayments;
window.doRefund = doRefund;
