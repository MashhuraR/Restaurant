/* api.js — Backend bilan muloqot */
const API_BASE = 'https://restaurant-auym.onrender.com/api';

const API = {
  async _req(method, path, body = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store'
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(API_BASE + path, opts);
    const json = await res.json();
    if (!json.success) throw new Error(json.message || 'Xato');
    return json.data;
  },
  // Menu
  getMenu: (params = '') => API._req('GET', `/menu${params}`),
  getCategories: () => API._req('GET', '/menu/categories'),
  searchMenu: q => API._req('GET', `/menu/search?q=${encodeURIComponent(q)}`),
  createMenuItem: data => API._req('POST', '/menu', data),
  updateMenuItem: (id, data) => API._req('PUT', `/menu/${id}`, data),
  deleteMenuItem: id => API._req('DELETE', `/menu/${id}`),
  toggleMenuItem: id => API._req('PATCH', `/menu/${id}/toggle`),
  // Orders
  getOrders: (status = '') => API._req('GET', `/orders${status ? '?status=' + status : ''}`),
  getActiveOrders: () => API._req('GET', '/orders/active'),
  getOrder: id => API._req('GET', `/orders/${id}`),
  createOrder: data => API._req('POST', '/orders', data),
  updateOrderStatus: (id, status) => API._req('PATCH', `/orders/${id}/status`, { status }),
  cancelOrder: (id, reason = '') => API._req('PATCH', `/orders/${id}/cancel`, { reason }),
  addOrderItem: (id, item) => API._req('POST', `/orders/${id}/items`, item),
  removeOrderItem: (orderId, itemId) => API._req('DELETE', `/orders/${orderId}/items/${itemId}`),
  // Payments
  getPayments: (status = '') => API._req('GET', `/payments${status ? '?status=' + status : ''}`),
  getPayment: id => API._req('GET', `/payments/${id}`),
  getPaymentsByOrder: orderId => API._req('GET', `/payments/order/${orderId}`),
  createPayment: data => API._req('POST', '/payments', data),
  refundPayment: id => API._req('PATCH', `/payments/${id}/refund`),
  getPaymentMethods: () => API._req('GET', '/payments/methods'),
  getRevenue: () => API._req('GET', '/payments/revenue'),
  // Stats
  getStatistics: () => API._req('GET', '/statistics'),
};
