let currentMenuItems = [];
let menuCategories = [];
let menuActiveCategory = '';
let menuSearchQ = '';

async function renderMenu() {
  const el = document.getElementById('page-menu');
  el.innerHTML = `<div class="loading-overlay"><div class="spinner"></div></div>`;
  try {
    menuCategories = await API.getCategories();
    await refreshMenuGrid();
  } catch(e) {
    el.innerHTML = `<div class="card" style="color:var(--danger);text-align:center">Backend ulanmagan!</div>`;
  }
}

async function refreshMenuGrid() {
  const el = document.getElementById('page-menu');
  let params = '';
  if (menuActiveCategory) params += `?category=${encodeURIComponent(menuActiveCategory)}`;

  let items;
  if (menuSearchQ) {
    items = await API.searchMenu(menuSearchQ);
  } else {
    items = await API.getMenu(params);
  }
  currentMenuItems = items;

  const filterBtns = ['', ...menuCategories].map(cat => `
    <button class="filter-btn ${menuActiveCategory === cat ? 'active' : ''}"
      onclick="menuFilterBy('${cat.replace(/'/g, "\\'")}')">
      ${cat ? categoryIcon(cat) + ' ' + cat : '🍴 Barchasi'}
    </button>`).join('');

  const cards = items.length
    ? items.map(item => `
        <div class="menu-card ${item.is_available ? '' : 'unavailable'}">
          <div class="menu-card-img">${categoryIcon(item.category)}</div>
          <div class="menu-card-body">
            <div class="menu-card-category">${item.category}</div>
            <div class="menu-card-name">${item.name}</div>
            <div class="menu-card-desc">${item.description || '—'}</div>
            <div class="menu-card-footer">
              <div class="menu-price">${formatMoney(item.price)}</div>
              <div class="menu-actions">
                <button class="btn-icon" title="Tahrirlash" onclick="openEditMenu('${item.id}')"><i class="fas fa-pen"></i></button>
                <button class="btn-icon" title="${item.is_available ? 'Yopish' : 'Ochish'}"
                  onclick="menuToggle('${item.id}')">
                  <i class="fas ${item.is_available ? 'fa-eye' : 'fa-eye-slash'}"></i>
                </button>
                <button class="btn-icon" style="color:var(--danger)" title="O'chirish" onclick="menuDelete('${item.id}')"><i class="fas fa-trash"></i></button>
              </div>
            </div>
            <div style="margin-top:8px;font-size:11px;color:var(--text-muted)">
              ⏱ ${item.preparation_time} daqiqa &nbsp;|&nbsp;
              <span style="color:${item.is_available ? 'var(--success)' : 'var(--danger)'}">
                ${item.is_available ? '✅ Mavjud' : '❌ Mavjud emas'}
              </span>
            </div>
          </div>
        </div>`).join('')
    : `<div class="card" style="grid-column:1/-1">${emptyState('fas fa-utensils', 'Menyu elementlari topilmadi')}</div>`;

  el.innerHTML = `
    <div class="card" style="margin-bottom:0;padding:16px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
        <h2 style="font-size:18px;font-weight:700">🍽️ Menyu boshqaruvi</h2>
        <button class="btn btn-primary" onclick="openAddMenuModal()">
          <i class="fas fa-plus"></i> Yangi taom
        </button>
      </div>
      <div class="filter-bar">
        <div class="search-box">
          <i class="fas fa-search"></i>
          <input class="form-control" id="menuSearch" placeholder="Taom qidirish..." value="${menuSearchQ}"
            oninput="menuSearch(this.value)">
        </div>
        ${filterBtns}
      </div>
    </div>
    <div style="margin-top:20px" class="menu-grid">${cards}</div>`;
}

function menuFilterBy(cat) {
  menuActiveCategory = cat;
  menuSearchQ = '';
  document.getElementById('menuSearch') && (document.getElementById('menuSearch').value = '');
  refreshMenuGrid();
}

let searchTimer;
function menuSearch(q) {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => { menuSearchQ = q; refreshMenuGrid(); }, 350);
}

async function menuToggle(id) {
  try {
    await API.toggleMenuItem(id);
    await refreshMenuGrid();
    toast('Holat o\'zgartirildi', 'success');
  } catch(e) { toast(e.message, 'error'); }
}

async function menuDelete(id) {
  const item = currentMenuItems.find(i => i.id === id);
  const name = item ? item.name : 'bu taom';
  // if (!confirm(`"${name}" ni o'chirishni tasdiqlaysizmi?`)) return;
  try {
    await API.deleteMenuItem(id);
    toast(`"${name}" o'chirildi`, 'success');
    await refreshMenuGrid();
  } catch(e) { toast(e.message, 'error'); }
}

function openAddMenuModal() {
  const catOptions = menuCategories.map(c => `<option value="${c}">${c}</option>`).join('');
  openModal('➕ Yangi taom qo\'shish', `
    <form id="menuForm">
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Taom nomi *</label>
          <input class="form-control" id="mName" required placeholder="Masalan: Osh">
        </div>
        <div class="form-group">
          <label class="form-label">Narxi (so'm) *</label>
          <input class="form-control" id="mPrice" type="number" required min="0" placeholder="45000">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Kategoriya *</label>
          <select class="form-control" id="mCategory"><option value="">Tanlang...</option>${catOptions}</select>
        </div>
        <div class="form-group">
          <label class="form-label">Tayyorlanish vaqti (daqiqa)</label>
          <input class="form-control" id="mPrepTime" type="number" value="15" min="1">
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Tavsif</label>
        <textarea class="form-control" id="mDesc" rows="2" placeholder="Qisqacha tavsif..."></textarea>
      </div>
    </form>
    <div class="modal-footer" style="margin:-24px -24px 0;padding:16px 24px;border-top:1px solid var(--border)">
      <button class="btn btn-ghost" onclick="closeModal()">Bekor</button>
      <button class="btn btn-primary" onclick="submitAddMenu()"><i class="fas fa-save"></i> Saqlash</button>
    </div>`);
}

async function submitAddMenu() {
  const name = document.getElementById('mName').value.trim();
  const price = parseFloat(document.getElementById('mPrice').value);
  const category = document.getElementById('mCategory').value;
  const description = document.getElementById('mDesc').value.trim();
  const preparation_time = parseInt(document.getElementById('mPrepTime').value) || 15;
  if (!name || !price || !category) return toast('Barcha majburiy maydonlarni to\'ldiring!', 'warning');
  try {
    await API.createMenuItem({ name, price, category, description, preparation_time });
    closeModal(); toast(`"${name}" menyuga qo'shildi!`, 'success');
    await refreshMenuGrid();
  } catch(e) { toast(e.message, 'error'); }
}

function openEditMenu(id) {
  const item = currentMenuItems.find(i => i.id === id);
  if (!item) return toast('Taom topilmadi!', 'error');
  const catOptions = menuCategories.map(c =>
    `<option value="${c}" ${c === item.category ? 'selected' : ''}>${c}</option>`).join('');
  openModal('✏️ Taomni tahrirlash', `
    <form id="editMenuForm">
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Taom nomi *</label>
          <input class="form-control" id="eName" value="${item.name}" required>
        </div>
        <div class="form-group">
          <label class="form-label">Narxi (so'm) *</label>
          <input class="form-control" id="ePrice" type="number" value="${item.price}" required>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Kategoriya *</label>
          <select class="form-control" id="eCategory">${catOptions}</select>
        </div>
        <div class="form-group">
          <label class="form-label">Tayyorlanish vaqti</label>
          <input class="form-control" id="ePrepTime" type="number" value="${item.preparation_time}">
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Tavsif</label>
        <textarea class="form-control" id="eDesc" rows="2">${item.description || ''}</textarea>
      </div>
    </form>
    <div class="modal-footer" style="margin:-24px -24px 0;padding:16px 24px;border-top:1px solid var(--border)">
      <button class="btn btn-ghost" onclick="closeModal()">Bekor</button>
      <button class="btn btn-primary" onclick="submitEditMenu('${item.id}')"><i class="fas fa-save"></i> Saqlash</button>
    </div>`);
}

async function submitEditMenu(id) {
  const data = {
    name: document.getElementById('eName').value.trim(),
    price: parseFloat(document.getElementById('ePrice').value),
    category: document.getElementById('eCategory').value,
    description: document.getElementById('eDesc').value.trim(),
    preparation_time: parseInt(document.getElementById('ePrepTime').value) || 15,
  };
  if (!data.name || !data.price || !data.category) return toast('Barcha majburiy maydonlarni to\'ldiring!', 'warning');
  try {
    await API.updateMenuItem(id, data);
    closeModal(); toast('Taom yangilandi!', 'success');
    await refreshMenuGrid();
  } catch(e) { toast(e.message, 'error'); }
}

window.renderMenu = renderMenu;
window.menuFilterBy = menuFilterBy;
window.menuToggle = menuToggle;
window.menuDelete = menuDelete;
window.openAddMenuModal = openAddMenuModal;
window.openEditMenu = openEditMenu;
window.submitAddMenu = submitAddMenu;
window.submitEditMenu = submitEditMenu;
window.menuSearch = menuSearch;
// console.log("Menu functions bound to window");
