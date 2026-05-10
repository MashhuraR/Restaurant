/* pages/orders.js */
let orderFilterStatus = '';
let cart = [];
let allMenuForOrder = [];

async function renderOrders() {
  const el = document.getElementById('page-orders');
  el.innerHTML = `<div class="loading-overlay"><div class="spinner"></div></div>`;
  try {
    await refreshOrdersList();
  } catch(e) {
    el.innerHTML = `<div class="card" style="color:var(--danger);text-align:center">Backend ulanmagan!</div>`;
  }
}

async function refreshOrdersList() {
  const el = document.getElementById('page-orders');
  const orders = await API.getOrders(orderFilterStatus);
  const statuses = ['', 'pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled'];
  const filterBtns = statuses.map(s => `
    <button class="filter-btn ${orderFilterStatus === s ? 'active' : ''}" onclick="orderFilter('${s}')">
      ${s ? statusLabel(s) : 'Barchasi'}
    </button>`).join('');

  const rows = orders.length
    ? orders.map(o => `
        <tr>
          <td><strong>${o.id}</strong></td>
          <td>${o.customer_name}</td>
          <td>${o.order_type === 'dine_in' ? '🪑 Zalda' : o.order_type === 'takeaway' ? '🥡 Olib ketish' : '🛵 Yetkazish'}</td>
          <td>${o.table_number ? `#${o.table_number}` : '—'}</td>
          <td>${o.item_count} ta</td>
          <td><strong>${formatMoney(o.total)}</strong></td>
          <td>${statusBadge(o.status)}</td>
          <td>${formatDate(o.created_at)}</td>
          <td>
            <div style="display:flex;gap:4px">
              <button class="btn-icon" title="Ko'rish" onclick="viewOrder('${o.id}')"><i class="fas fa-eye"></i></button>
              ${o.status === 'pending' ? `<button class="btn-icon" title="Tasdiqlash" onclick="changeStatus('${o.id}','confirmed')"><i class="fas fa-check" style="color:var(--success)"></i></button>` : ''}
              ${o.status === 'confirmed' ? `<button class="btn-icon" title="Tayyorlanmoqda" onclick="changeStatus('${o.id}','preparing')"><i class="fas fa-fire" style="color:var(--accent)"></i></button>` : ''}
              ${o.status === 'preparing' ? `<button class="btn-icon" title="Tayyor" onclick="changeStatus('${o.id}','ready')"><i class="fas fa-bell" style="color:var(--info)"></i></button>` : ''}
              ${o.status === 'ready' ? `<button class="btn-icon" title="Yetkazish va To'lov" onclick="openPaymentModal('${o.id}',${o.total})"><i class="fas fa-check-double" style="color:var(--success)"></i></button>` : ''}
              ${!['delivered','cancelled'].includes(o.status) ? `<button class="btn-icon" title="To'lov" onclick="openPaymentModal('${o.id}',${o.total})"><i class="fas fa-credit-card" style="color:var(--primary)"></i></button>` : ''}
              ${!['delivered','cancelled'].includes(o.status) ? `<button class="btn-icon" title="Bekor qilish" onclick="doCancelOrder('${o.id}')"><i class="fas fa-times" style="color:var(--danger)"></i></button>` : ''}
            </div>
          </td>
        </tr>`).join('')
    : `<tr><td colspan="9" style="text-align:center;padding:40px;color:var(--text-muted)">Buyurtmalar yo'q</td></tr>`;

  el.innerHTML = `
    <div class="card" style="padding:16px;margin-bottom:16px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
        <h2 style="font-size:18px;font-weight:700">📋 Buyurtmalar</h2>
        <button class="btn btn-primary" onclick="openNewOrderModal()"><i class="fas fa-plus"></i> Yangi buyurtma</button>
      </div>
      <div class="filter-bar">${filterBtns}</div>
    </div>
    <div class="card" style="padding:0">
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th>ID</th><th>Mijoz</th><th>Tur</th><th>Stol</th>
            <th>Soni</th><th>Summa</th><th>Status</th><th>Vaqt</th><th>Amallar</th>
          </tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>`;
}

function orderFilter(s) { orderFilterStatus = s; refreshOrdersList(); }

async function changeStatus(id, status) {
  try {
    await API.updateOrderStatus(id, status);
    toast('Status yangilandi!', 'success');
    await refreshOrdersList();
  } catch(e) { toast(e.message, 'error'); }
}

async function doCancelOrder(id) {
  const reason = prompt('Bekor qilish sababi (ixtiyoriy):') || '';
  try {
    await API.cancelOrder(id, reason);
    toast('Buyurtma bekor qilindi!', 'warning');
    await refreshOrdersList();
  } catch(e) { toast(e.message, 'error'); }
}

async function viewOrder(id) {
  try {
    const o = await API.getOrder(id);
    const itemsHTML = o.items.map(i => `
      <tr>
        <td>${i.menu_item_name}</td>
        <td>${i.quantity}</td>
        <td>${formatMoney(i.unit_price)}</td>
        <td><strong>${formatMoney(i.subtotal)}</strong></td>
      </tr>`).join('');
    openModal(`📋 Buyurtma: ${o.id}`, `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px">
        <div><b>Mijoz:</b> ${o.customer_name}</div>
        <div><b>Status:</b> ${statusBadge(o.status)}</div>
        <div><b>Tur:</b> ${o.order_type}</div>
        <div><b>Stol:</b> ${o.table_number || '—'}</div>
        <div><b>Yaratildi:</b> ${formatDate(o.created_at)}</div>
        <div><b>Chegirma:</b> ${o.discount_percent}%</div>
      </div>
      <div class="table-wrap" style="margin-bottom:14px">
        <table>
          <thead><tr><th>Taom</th><th>Soni</th><th>Narxi</th><th>Jami</th></tr></thead>
          <tbody>${itemsHTML}</tbody>
        </table>
      </div>
      <div style="text-align:right;padding:8px 0;border-top:2px solid var(--border)">
        <div style="color:var(--text-muted);font-size:13px">Chegirma: -${formatMoney(o.discount_amount)}</div>
        <div style="font-size:20px;font-weight:800;color:var(--primary)">Jami: ${formatMoney(o.total)}</div>
      </div>
      ${o.special_instructions ? `<div style="margin-top:10px;padding:10px;background:var(--bg);border-radius:8px;font-size:13px"><b>Izoh:</b> ${o.special_instructions}</div>` : ''}`,
      'modal-lg');
  } catch(e) { toast(e.message, 'error'); }
}

// ─── Yangi buyurtma ─────────────────────────────────────────
async function openNewOrderModal() {
  cart = [];
  allMenuForOrder = await API.getMenu('?available_only=true');
  renderOrderModal();
}

function renderOrderModal() {
  const cartHTML = cart.length
    ? cart.map(ci => `
        <div class="cart-item">
          <div class="cart-item-info">
            <div class="cart-item-name">${ci.name}</div>
            <div class="cart-item-price">${formatMoney(ci.price)}</div>
          </div>
          <div class="qty-ctrl">
            <button class="qty-btn" onclick="cartQty('${ci.id}',-1)">−</button>
            <span class="qty-val">${ci.qty}</span>
            <button class="qty-btn" onclick="cartQty('${ci.id}',1)">+</button>
          </div>
          <div class="cart-item-total">${formatMoney(ci.price * ci.qty)}</div>
        </div>`).join('')
    : `<div class="empty-cart-msg"><i class="fas fa-shopping-basket"></i><br>Savatchada taomlar yo'q</div>`;

  const subtotal = cart.reduce((s, i) => s + i.price * i.qty, 0);
  const discountInput = document.getElementById('ocDiscount');
  const discountPercent = discountInput ? parseInt(discountInput.value) || 0 : 0;
  const discountAmount = subtotal * (discountPercent / 100);
  const total = subtotal - discountAmount;

  const menuHTML = allMenuForOrder.map(item => `
    <div class="order-menu-item" onclick="addToCartById('${item.id}')">
      <div class="item-info">
        <div class="item-name">${categoryIcon(item.category)} ${item.name}</div>
        <div class="item-price">${formatMoney(item.price)}</div>
      </div>
      <button class="btn-add-item"><i class="fas fa-plus"></i></button>
    </div>`).join('');

  const modalHtml = `
    <div class="order-modal-content">
      <div class="order-client-info glass-panel">
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Mijoz ismi *</label>
            <input class="form-control" id="ocName" value="${escapeJS(document.getElementById('ocName')?.value || '')}" placeholder="Mijoz ismi...">
          </div>
          <div class="form-group">
            <label class="form-label">Buyurtma turi</label>
            <select class="form-control" id="ocType">
              <option value="dine_in" ${document.getElementById('ocType')?.value === 'dine_in' ? 'selected' : ''}>🪑 Zalda</option>
              <option value="takeaway" ${document.getElementById('ocType')?.value === 'takeaway' ? 'selected' : ''}>🥡 Olib ketish</option>
              <option value="delivery" ${document.getElementById('ocType')?.value === 'delivery' ? 'selected' : ''}>🛵 Yetkazish</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Stol / Manzil</label>
            <input class="form-control" id="ocTable" value="${escapeJS(document.getElementById('ocTable')?.value || '')}" placeholder="Masalan: 5-stol">
          </div>
          <div class="form-group">
            <label class="form-label">Chegirma (%)</label>
            <input class="form-control" id="ocDiscount" type="number" value="${discountPercent}" min="0" max="100" oninput="renderOrderModal()">
          </div>
        </div>
      </div>

      <div class="order-builder-modern">
        <div class="menu-selection-side">
          <div class="side-header"><i class="fas fa-list-ul"></i> Menyu</div>
          <div class="order-menu-list">${menuHTML}</div>
        </div>
        <div class="cart-side">
          <div class="side-header"><i class="fas fa-shopping-cart"></i> Savatcha (${cart.length})</div>
          <div class="cart-list">${cartHTML}</div>
          <div class="cart-footer">
            <div class="summary-row"><span>Oraliq jami:</span><span>${formatMoney(subtotal)}</span></div>
            <div class="summary-row"><span>Chegirma:</span><span>-${formatMoney(discountAmount)}</span></div>
            <div class="summary-total"><span>JAMI:</span><span>${formatMoney(total)}</span></div>
            <button class="btn btn-primary btn-lg submit-order-btn" style="width:100%" onclick="submitNewOrder()">
              <i class="fas fa-check-circle"></i> BUYURTMA BERISH
            </button>
          </div>
        </div>
      </div>
      
      <div class="form-group" style="margin-top:20px">
        <label class="form-label">Maxsus eslatma (izoh)</label>
        <textarea class="form-control" id="ocNote" rows="1" placeholder="Masalan: Achchiq bo'lmasin...">${escapeJS(document.getElementById('ocNote')?.value || '')}</textarea>
      </div>
    </div>`;

  openModal('✨ Yangi buyurtma yaratish', modalHtml, 'modal-lg');
}

// Global scope'ga chiqarish
window.addToCartById = (id) => {
  const item = allMenuForOrder.find(m => m.id == id);
  if (item) addToCart(item);
};
window.addToCart = addToCart;
window.cartQty = cartQty;
window.submitNewOrder = submitNewOrder;
window.renderOrderModal = renderOrderModal;

function addToCart(item) {
  const existing = cart.find(c => c.id === item.id);
  if (existing) existing.qty++;
  else cart.push({ id: item.id, name: item.name, price: item.price, qty: 1 });
  // Foydalanuvchi ism va boshqa ma'lumotlarni yo'qotmasligi uchun renderOrderModal ni chaqiramiz
  renderOrderModal();
}

function cartQty(id, delta) {
  const item = cart.find(c => c.id === id);
  if (!item) return;
  item.qty += delta;
  if (item.qty <= 0) cart = cart.filter(c => c.id !== id);
  renderOrderModal();
}

async function submitNewOrder() {
  const name = document.getElementById('ocName').value.trim();
  if (!name) return toast('Mijoz ismini kiriting!', 'warning');
  if (!cart.length) return toast('Savatga kamida bitta taom qo\'shing!', 'warning');
  
  const data = {
    customer_name: name,
    order_type: document.getElementById('ocType').value,
    table_number: document.getElementById('ocTable').value || null,
    discount_percent: parseFloat(document.getElementById('ocDiscount').value) || 0,
    special_instructions: document.getElementById('ocNote').value.trim(),
    items: cart.map(c => ({ menu_item_id: c.id, quantity: c.qty }))
  };

  try {
    const order = await API.createOrder(data);
    closeModal();
    toast(`Buyurtma #${order.id} muvaffaqiyatli yaratildi!`, 'success');
    cart = [];
    
    // Malumotlarni yangilash
    await refreshOrdersList();
    
    // Dashboardni ham yangilash (ko'rsatkichlar uchun)
    if (typeof renderDashboard === 'function') {
      renderDashboard(); 
    }
  } catch(e) { toast(e.message, 'error'); }
}

// ─── To'lov modali ──────────────────────────────────────────
async function openPaymentModal(orderId, total) {
  const methods = await API.getPaymentMethods();
  const methodOptions = methods.map(m => `<option value="${m.value}">${m.label}</option>`).join('');
  openModal('💳 To\'lov qilish', `
    <div style="text-align:center;margin-bottom:16px">
      <div style="font-size:13px;color:var(--text-muted)">Buyurtma</div>
      <div style="font-size:26px;font-weight:800;color:var(--primary)">${formatMoney(total)}</div>
    </div>
    <div class="form-group">
      <label class="form-label">To'lov usuli</label>
      <select class="form-control" id="pmMethod">${methodOptions}</select>
    </div>
    <div class="form-group">
      <label class="form-label">Kassir</label>
      <input class="form-control" id="pmCashier" value="Kassir" placeholder="Kassir ismi">
    </div>
    <div class="modal-footer" style="margin:-24px -24px 0;padding:16px 24px;border-top:1px solid var(--border)">
      <button class="btn btn-ghost" onclick="closeModal()">Bekor</button>
      <button class="btn btn-success" onclick="submitPayment('${orderId}',${total})">
        <i class="fas fa-check"></i> To'lovni tasdiqlash
      </button>
    </div>`);
}

async function submitPayment(orderId, amount) {
  try {
    const data = {
      order_id: orderId, amount,
      method: document.getElementById('pmMethod').value,
      cashier_name: document.getElementById('pmCashier').value || 'Kassir'
    };
    await API.createPayment(data);
    closeModal();
    toast('To\'lov muvaffaqiyatli amalga oshirildi!', 'success');
    await refreshOrdersList();
  } catch(e) { toast(e.message, 'error'); }
}

window.renderOrders = renderOrders;
window.orderFilter = orderFilter;
window.changeStatus = changeStatus;
window.doCancelOrder = doCancelOrder;
window.viewOrder = viewOrder;
window.openNewOrderModal = openNewOrderModal;
window.openPaymentModal = openPaymentModal;
window.submitPayment = submitPayment;
window.submitNewOrder = submitNewOrder;
window.updateCart = updateCart;
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
