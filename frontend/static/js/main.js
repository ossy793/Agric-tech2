// Use relative URL so it works on any host (localhost, 127.0.0.1, etc.)
const API = '/api';

// ─── AUTH ──────────────────────────────────────────────────────────────────────
const Auth = {
  get: () => JSON.parse(localStorage.getItem('farmrent_user') || 'null'),
  set: (user) => localStorage.setItem('farmrent_user', JSON.stringify(user)),
  clear: () => localStorage.removeItem('farmrent_user'),
  isLoggedIn: () => !!Auth.get(),
  isFarmer: () => Auth.get()?.role === 'farmer',
  isCompany: () => Auth.get()?.role === 'company',
  require: (role) => {
    const user = Auth.get();
    if (!user) { window.location.href = '/auth'; return false; }
    if (role && user.role !== role) { window.location.href = '/'; return false; }
    return user;
  }
};

// ─── CART ──────────────────────────────────────────────────────────────────────
const Cart = {
  get: () => JSON.parse(localStorage.getItem('farmrent_cart') || '[]'),
  set: (items) => { localStorage.setItem('farmrent_cart', JSON.stringify(items)); Cart.updateBadge(); },
  add: (item) => {
    const cart = Cart.get();
    const existing = cart.find(c => c.equipment_id === item.equipment_id);
    if (existing) { existing.quantity += item.quantity; }
    else { cart.push(item); }
    Cart.set(cart);
    Toast.show('Added to cart! 🛒', 'success');
  },
  remove: (equipment_id) => { Cart.set(Cart.get().filter(c => c.equipment_id !== equipment_id)); },
  clear: () => { localStorage.removeItem('farmrent_cart'); Cart.updateBadge(); },
  total: () => Cart.get().reduce((sum, item) => sum + item.total_price, 0),
  count: () => Cart.get().length,
  updateBadge: () => {
    const count = Cart.count();
    document.querySelectorAll('.cart-count').forEach(el => { el.textContent = count; });
    document.querySelectorAll('.cart-total').forEach(el => { el.textContent = `₦${Cart.total().toLocaleString()}`; });
  }
};

// ─── API HELPERS ───────────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  try {
    const isFormData = options.body instanceof FormData;
    const headers = isFormData ? {} : { 'Content-Type': 'application/json' };
    const res = await fetch(`${API}${path}`, {
      headers: { ...headers, ...options.headers },
      ...options,
      body: options.body && !isFormData ? JSON.stringify(options.body) : options.body,
    });
    if (!res.ok) {
      let msg = `Server error (${res.status})`;
      try {
        const ct = res.headers.get('content-type') || '';
        if (ct.includes('application/json')) {
          const err = await res.json();
          msg = err.detail || msg;
        } else {
          msg = (await res.text()).slice(0, 120) || msg;
        }
      } catch (_) {}
      throw new Error(msg);
    }
    return res.json();
  } catch (e) {
    Toast.show(e.message, 'error');
    throw e;
  }
}

// ─── TOAST ─────────────────────────────────────────────────────────────────────
const Toast = {
  container: null,
  init: () => {
    Toast.container = document.querySelector('.toast-container');
    if (!Toast.container) {
      Toast.container = document.createElement('div');
      Toast.container.className = 'toast-container';
      document.body.appendChild(Toast.container);
    }
  },
  show: (msg, type = 'info') => {
    Toast.init();
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
    Toast.container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(20px)'; toast.style.transition = '0.3s'; setTimeout(() => toast.remove(), 300); }, 3000);
  }
};

// ─── MODAL ─────────────────────────────────────────────────────────────────────
const Modal = {
  open: (id) => { document.getElementById(id)?.classList.add('open'); },
  close: (id) => { document.getElementById(id)?.classList.remove('open'); },
  closeAll: () => { document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('open')); }
};

document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) Modal.closeAll();
  if (e.target.dataset.closeModal) Modal.close(e.target.dataset.closeModal);
});

// ─── NAV SETUP ─────────────────────────────────────────────────────────────────
function setupNav() {
  const user = Auth.get();
  const navUser = document.getElementById('nav-user');
  if (!navUser) return;

  if (user) {
    const roleLabel = user.role === 'farmer' ? '🌱 Farmer' : '🏢 Company';
    const roleStyle = user.role === 'farmer'
      ? 'background:rgba(34,197,94,0.2);color:#86efac;'
      : 'background:rgba(251,191,36,0.2);color:#fde68a;';
    const dashUrl = user.role === 'farmer' ? '/farmer-dashboard' : '/company-dashboard';
    navUser.innerHTML = `
      <div style="display:flex;align-items:center;gap:0.5rem">
        <span style="font-size:0.75rem;font-weight:700;padding:0.2rem 0.6rem;border-radius:100px;${roleStyle}">${roleLabel}</span>
        <span class="nav-user-name">${user.name.split(' ')[0]}</span>
      </div>
      <a href="${dashUrl}" class="btn btn-primary btn-sm">Dashboard</a>
      <button class="btn btn-outline btn-sm" onclick="logout()" style="color:rgba(255,255,255,0.7);border-color:rgba(255,255,255,0.3)">Logout</button>
    `;
  } else {
    navUser.innerHTML = `
      <a href="/auth" class="btn btn-outline btn-sm" style="color:rgba(255,255,255,0.7);border-color:rgba(255,255,255,0.3)">Login</a>
      <a href="/auth" class="btn btn-primary btn-sm">Sign Up</a>
    `;
  }
}

function logout() {
  Auth.clear();
  Cart.clear();
  window.location.href = '/';
}

// ─── UTILS ─────────────────────────────────────────────────────────────────────
function formatNaira(amount) { return `₦${Number(amount).toLocaleString()}`; }
function formatDate(dateStr) { return new Date(dateStr).toLocaleDateString('en-NG', { day: 'numeric', month: 'short', year: 'numeric' }); }
function categoryEmoji(cat) {
  const map = { tractors: '🚜', harvesters: '🌾', irrigation: '💧', planters: '🌱', processing: '⚙️', sprayers: '🔧', general: '🛠️' };
  return map[cat] || '🛠️';
}
function statusBadge(status) {
  const map = { pending: 'badge-gold', confirmed: 'badge-green', completed: 'badge-blue', cancelled: 'badge-red' };
  return `<span class="badge ${map[status] || 'badge-gray'}">${status}</span>`;
}

document.addEventListener('DOMContentLoaded', () => {
  setupNav();
  Cart.updateBadge();
});