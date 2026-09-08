/**
 * CivicAI - Centralized API Client & Frontend Utilities (Vanilla JS)
 */

const API_BASE = '/api/v1';

class ApiClient {
  constructor() {
    this.tokenKey = 'civic_access_token';
    this.userKey = 'civic_user_profile';
  }

  // Token Management
  getToken() {
    return localStorage.getItem(this.tokenKey);
  }

  setToken(token) {
    if (token) {
      localStorage.setItem(this.tokenKey, token);
    } else {
      localStorage.removeItem(this.tokenKey);
    }
  }

  getUser() {
    try {
      const userStr = localStorage.getItem(this.userKey);
      return userStr ? JSON.parse(userStr) : null;
    } catch (e) {
      return null;
    }
  }

  setUser(user) {
    if (user) {
      localStorage.setItem(this.userKey, JSON.stringify(user));
    } else {
      localStorage.removeItem(this.userKey);
    }
  }

  clearAuth() {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
  }

  isAuthenticated() {
    return !!this.getToken();
  }

  // Standard JSON API Request
  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    
    const headers = {
      'Accept': 'application/json',
      ...options.headers
    };

    // Attach Bearer token if present
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Set JSON content-type if body is provided and not FormData
    if (options.body && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
      if (typeof options.body === 'object') {
        options.body = JSON.stringify(options.body);
      }
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      // Handle 401 Unauthorized
      if (response.status === 401) {
        // If not already on login/register page, notify and redirect
        const currentPath = window.location.pathname;
        if (!currentPath.includes('login.html') && !currentPath.includes('register.html') && !currentPath.endsWith('index.html') && currentPath !== '/') {
          this.clearAuth();
          window.location.href = '/static/login.html?expired=true';
        }
        throw new Error('Authentication required or session expired.');
      }

      // Handle empty content or 204
      if (response.status === 204) {
        return null;
      }

      const contentType = response.headers.get('content-type');
      let data = null;
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        let errorMsg = 'An error occurred while processing your request.';
        if (data && data.detail) {
          if (Array.isArray(data.detail)) {
            // Pydantic validation error array
            errorMsg = data.detail.map(e => `${e.loc ? e.loc.join('.') : 'Field'}: ${e.msg}`).join(', ');
          } else {
            errorMsg = data.detail;
          }
        }
        const error = new Error(errorMsg);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      console.error(`API Error [${options.method || 'GET'} ${endpoint}]:`, err);
      throw err;
    }
  }

  // File Upload (FormData)
  async uploadFile(endpoint, formData) {
    const url = `${API_BASE}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    const headers = {
      'Accept': 'application/json'
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'File upload failed');
      }
      return data;
    } catch (err) {
      console.error(`Upload Error [POST ${endpoint}]:`, err);
      throw err;
    }
  }

  // Shorthand methods
  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  post(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: 'POST', body });
  }

  put(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: 'PUT', body });
  }

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }
}

// Global API Instance
const api = new ApiClient();

// Toast Notification Manager
function showToast(message, type = 'info', duration = 4500) {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  };

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span style="font-size: 18px;">${icons[type] || icons.info}</span>
    <div style="flex: 1;">
      <p style="margin: 0; font-weight: 500; color: #0f172a;">${escapeHtml(message)}</p>
    </div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Utility Helpers
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatDate(isoString) {
  if (!isoString) return 'N/A';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return isoString;
  }
}

function renderStatusBadge(status) {
  if (!status) return '<span class="badge">N/A</span>';
  const cleanStatus = String(status).toLowerCase();
  const label = cleanStatus.replace(/_/g, ' ');
  return `<span class="badge badge-${cleanStatus}">${label}</span>`;
}

function renderRoleBadge(role) {
  if (!role) return '<span class="badge">Citizen</span>';
  const cleanRole = String(role).toLowerCase();
  const label = cleanRole.replace(/_/g, ' ');
  return `<span class="badge badge-${cleanRole}">${label}</span>`;
}

// Confirmation Dialog Helper
function confirmAction(title, message, onConfirm) {
  let backdrop = document.getElementById('confirmModalBackdrop');
  if (!backdrop) {
    backdrop = document.createElement('div');
    backdrop.id = 'confirmModalBackdrop';
    backdrop.className = 'modal-backdrop';
    backdrop.innerHTML = `
      <div class="modal-dialog">
        <div class="modal-header">
          <h3 class="modal-title" id="confirmModalTitle">Confirm Action</h3>
          <button class="modal-close" onclick="closeConfirmModal()">✕</button>
        </div>
        <div class="modal-body" id="confirmModalBody">
          Are you sure you want to proceed?
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" onclick="closeConfirmModal()">Cancel</button>
          <button class="btn btn-danger" id="confirmModalBtn">Confirm</button>
        </div>
      </div>
    `;
    document.body.appendChild(backdrop);
  }

  document.getElementById('confirmModalTitle').innerText = title;
  document.getElementById('confirmModalBody').innerText = message;
  
  const confirmBtn = document.getElementById('confirmModalBtn');
  confirmBtn.onclick = () => {
    closeConfirmModal();
    if (typeof onConfirm === 'function') onConfirm();
  };

  backdrop.classList.add('show');
}

function closeConfirmModal() {
  const backdrop = document.getElementById('confirmModalBackdrop');
  if (backdrop) backdrop.classList.remove('show');
}
