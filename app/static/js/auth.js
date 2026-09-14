/**
 * CivicAI - Authentication & Role State Manager (Vanilla JS)
 */

document.addEventListener('DOMContentLoaded', () => {
  initAuthUI();
});

// Also run immediately if DOM is already ready
if (document.readyState === 'interactive' || document.readyState === 'complete') {
  initAuthUI();
}

function initAuthUI() {
  const user = api.getUser();
  const token = api.getToken();

  // If on public landing, login or register page
  const path = window.location.pathname;
  if (path.includes('login.html') || path.includes('register.html')) {
    initAuthForms();
    return;
  }

  const role = user ? (user.role || 'citizen') : 'citizen';

  // Populate sidebar/header user chips if present
  const nameEl = document.getElementById('sidebarUserName');
  if (nameEl) nameEl.innerText = user ? (user.name || 'Civic User') : 'Guest Citizen';

  const roleEl = document.getElementById('sidebarUserRole');
  if (roleEl) roleEl.innerText = user && user.role ? user.role.replace(/_/g, ' ') : 'Citizen';

  const avatarEl = document.getElementById('sidebarUserAvatar');
  if (avatarEl) {
    avatarEl.innerText = (user && user.name ? user.name : 'U').charAt(0).toUpperCase();
  }

  // Update My Account sidebar label based on role
  const profileLink = document.querySelector('a[href*="profile.html"]');
  if (profileLink) {
    if (role === 'admin') {
      profileLink.innerHTML = '<span class="icon">👑</span> Administrator Profile';
    } else if (role === 'department_officer') {
      profileLink.innerHTML = '<span class="icon">👮‍♂️</span> Officer Profile';
    } else {
      profileLink.innerHTML = '<span class="icon">👤</span> Citizen Profile';
    }
  }

  // Role-based navigation visibility
  applyRoleNavigation(role);
}

// Guard Route by Role
function requireAuth(allowedRoles = []) {
  const token = api.getToken();
  const user = api.getUser();

  if (!token || !user) {
    api.clearAuth();
    window.location.href = '/static/login.html';
    return false;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    showToast(`Access restricted. Required roles: ${allowedRoles.join(', ')}`, 'error');
    setTimeout(() => {
      window.location.href = '/static/dashboard.html';
    }, 1500);
    return false;
  }

  return true;
}

// Dynamically display sidebar links based on role
function applyRoleNavigation(role) {
  const currentRole = String(role || 'citizen').toLowerCase().trim();
  document.querySelectorAll('[data-allowed-roles]').forEach(el => {
    const raw = el.getAttribute('data-allowed-roles') || '';
    const roles = raw.split(',').map(r => r.trim().toLowerCase());
    if (roles.includes(currentRole) || roles.includes('*')) {
      el.style.display = '';
    } else {
      el.style.display = 'none';
    }
  });
}

// Logout
function handleLogout() {
  api.clearAuth();
  showToast('Logged out successfully.', 'info');
  setTimeout(() => {
    window.location.href = '/static/login.html';
  }, 400);
}

// Initialize Login & Register Pages
function initAuthForms() {
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    // Check if redirected because of expired session
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('expired')) {
      showToast('Your session has expired. Please log in again.', 'warning');
    }

    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;
      const submitBtn = loginForm.querySelector('button[type="submit"]');

      if (!email || !password) {
        showToast('Please enter both email and password.', 'warning');
        return;
      }

      try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner"></span> Authenticating...';

        const data = await api.post('/auth/login', { email, password });
        
        // Store Token & Profile
        api.setToken(data.access_token);
        api.setUser({
          id: data.user_id,
          name: data.name,
          email: data.email,
          role: data.role
        });

        showToast(`Welcome back, ${data.name}!`, 'success');
        setTimeout(() => {
          window.location.href = '/static/dashboard.html';
        }, 800);
      } catch (err) {
        showToast(err.message || 'Authentication failed. Please check credentials.', 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Sign In to Portal';
      }
    });
  }

  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('name').value.trim();
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;
      const confirmPassword = document.getElementById('confirmPassword').value;
      const submitBtn = registerForm.querySelector('button[type="submit"]');

      if (!name || !email || !password) {
        showToast('Please fill in all required fields.', 'warning');
        return;
      }

      if (password !== confirmPassword) {
        showToast('Passwords do not match.', 'error');
        return;
      }

      try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner"></span> Creating Account...';

        await api.post('/auth/register', {
          name,
          email,
          password,
          role: 'citizen'
        });

        showToast('Account created successfully! Logging you in...', 'success');
        
        // Auto-login
        const loginData = await api.post('/auth/login', { email, password });
        api.setToken(loginData.access_token);
        api.setUser({
          id: loginData.user_id,
          name: loginData.name,
          email: loginData.email,
          role: loginData.role
        });

        setTimeout(() => {
          window.location.href = '/static/dashboard.html';
        }, 1000);
      } catch (err) {
        showToast(err.message || 'Registration failed.', 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Create Citizen Account';
      }
    });
  }
}

// 1-Click Demo Account Quick Filler
function fillDemoAccount(role) {
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  if (!emailInput || !passwordInput) return;

  const demoCredentials = {
    citizen: { email: 'citizen@civic.local', pass: 'CitizenPassword123!' },
    officer: { email: 'officer@civic.local', pass: 'OfficerPassword123!' },
    admin: { email: 'admin@civic.local', pass: 'AdminPassword123!' }
  };

  const creds = demoCredentials[role];
  if (creds) {
    emailInput.value = creds.email;
    passwordInput.value = creds.pass;
    showToast(`Filled ${role.toUpperCase()} test credentials`, 'info');
  }
}
