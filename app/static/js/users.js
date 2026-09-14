/**
 * CivicAI - Users & Citizen Profiles Management Controller (Vanilla JS)
 */

let allUsers = [];
let allCitizensMap = {};

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;

  const user = api.getUser();
  if (user && user.role !== 'admin') {
    alert('Access restricted to System Administrators only.');
    window.location.href = '/static/dashboard.html';
    return;
  }

  initUsersPage();
});

async function initUsersPage() {
  await loadUsers();

  // Search input listener
  const searchInput = document.getElementById('userSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', applyFilters);
  }

  // Role filter listener
  const roleFilter = document.getElementById('userRoleFilter');
  if (roleFilter) {
    roleFilter.addEventListener('change', applyFilters);
  }

  // Status filter listener
  const statusFilter = document.getElementById('userStatusFilter');
  if (statusFilter) {
    statusFilter.addEventListener('change', applyFilters);
  }
}

async function loadUsers() {
  const tbody = document.getElementById('usersTableBody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="7" style="text-align:center; padding: 32px;">
        <span class="loading-spinner"></span> Loading registered users...
      </td>
    </tr>
  `;

  try {
    const [users, citizens] = await Promise.all([
      api.get('/users/'),
      api.get('/citizens/').catch(() => [])
    ]);

    allUsers = users || [];
    allCitizensMap = {};
    (citizens || []).forEach(c => {
      allCitizensMap[c.user_id] = c;
    });

    updateUserStats(allUsers);
    applyFilters();
  } catch (err) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center; color: var(--danger); padding: 32px;">
          Failed to load users: ${escapeHtml(err.message)}
        </td>
      </tr>
    `;
  }
}

function updateUserStats(users) {
  const total = users.length;
  const citizens = users.filter(u => u.role === 'citizen').length;
  const officers = users.filter(u => u.role === 'department_officer').length;
  const admins = users.filter(u => u.role === 'admin').length;

  document.getElementById('statTotalUsers').innerText = total;
  document.getElementById('statTotalCitizens').innerText = citizens;
  document.getElementById('statTotalOfficers').innerText = officers;
  document.getElementById('statTotalAdmins').innerText = admins;
}

function applyFilters() {
  const q = (document.getElementById('userSearchInput')?.value || '').toLowerCase().trim();
  const roleVal = document.getElementById('userRoleFilter')?.value || 'all';
  const statusVal = document.getElementById('userStatusFilter')?.value || 'all';

  const filtered = allUsers.filter(u => {
    // Role filter
    if (roleVal !== 'all' && u.role !== roleVal) return false;

    // Status filter
    if (statusVal === 'active' && !u.is_active) return false;
    if (statusVal === 'inactive' && u.is_active) return false;

    // Text search
    if (q) {
      const citizen = allCitizensMap[u.id] || u.citizen_profile || {};
      const phone = (citizen.phone || '').toLowerCase();
      const city = ((citizen.address && citizen.address.city) || '').toLowerCase();
      const name = (u.name || '').toLowerCase();
      const email = (u.email || '').toLowerCase();

      const matches = name.includes(q) || email.includes(q) || phone.includes(q) || city.includes(q);
      if (!matches) return false;
    }

    return true;
  });

  renderUsersTable(filtered);
}

function renderUsersTable(users) {
  const tbody = document.getElementById('usersTableBody');
  const countEl = document.getElementById('userCountDisplay');
  if (!tbody) return;

  if (countEl) countEl.innerText = `${users.length} of ${allUsers.length} registered accounts`;

  if (!users || users.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center; color: var(--text-muted); padding: 32px;">
          No matching registered users found.
        </td>
      </tr>
    `;
    return;
  }

  const currentUser = api.getUser();

  tbody.innerHTML = users.map(u => {
    const citizen = allCitizensMap[u.id] || u.citizen_profile;
    const phone = citizen && citizen.phone ? citizen.phone : '<span style="color: var(--text-muted);">Not provided</span>';
    const city = citizen && citizen.address && citizen.address.city ? citizen.address.city : '';
    const contactDisplay = citizen ? `${phone} ${city ? `(${escapeHtml(city)})` : ''}` : '<span style="color: var(--text-muted);">N/A (Staff)</span>';

    const initial = (u.name || 'U').charAt(0).toUpperCase();
    const joinedDate = u.created_at ? new Date(u.created_at).toLocaleDateString() : 'N/A';

    let roleBadge = '';
    if (u.role === 'admin') {
      roleBadge = '<span class="role-badge-admin">👑 Admin</span>';
    } else if (u.role === 'department_officer') {
      roleBadge = '<span class="role-badge-officer">👮‍♂️ Officer</span>';
    } else {
      roleBadge = '<span class="role-badge-citizen">👨‍💼 Citizen</span>';
    }

    const isSelf = currentUser && currentUser.id === u.id;

    return `
      <tr>
        <td><strong>#${u.id}</strong></td>
        <td>
          <div class="user-info-cell">
            <div class="user-table-avatar">${initial}</div>
            <div>
              <div class="user-name-text">${escapeHtml(u.name)} ${isSelf ? '<span style="font-size:10px; background:rgba(6,182,212,0.2); color:#06b6d4; padding:2px 5px; border-radius:4px; margin-left:4px;">You</span>' : ''}</div>
              <div class="user-email-text">${escapeHtml(u.email)}</div>
            </div>
          </div>
        </td>
        <td>${roleBadge}</td>
        <td><span style="font-size: 13px;">${contactDisplay}</span></td>
        <td>
          ${u.is_active 
            ? '<span class="badge badge-active">Active</span>' 
            : '<span class="badge badge-inactive">Inactive</span>'}
        </td>
        <td><span style="color: var(--text-muted); font-size: 12px;">${joinedDate}</span></td>
        <td style="text-align: right; white-space: nowrap;">
          <button class="btn btn-outline btn-sm" onclick="openViewProfileModal(${u.id})" title="View Full Details">Details</button>
          <button class="btn btn-outline btn-sm" onclick="openEditUserModal(${u.id})" title="Edit Role & Details">Edit</button>
          ${!isSelf ? `
            <button class="btn btn-danger btn-sm" onclick="confirmDeleteUser(${u.id}, '${escapeHtml(u.name)}')" title="Delete User">Delete</button>
          ` : ''}
        </td>
      </tr>
    `;
  }).join('');
}

// --------------------------------------------------------------------------
// Create / Register User Modal Logic
// --------------------------------------------------------------------------

function openCreateUserModal() {
  const form = document.getElementById('createUserForm');
  if (form) form.reset();
  document.getElementById('createUserActive').checked = true;
  document.getElementById('createUserRole').value = 'citizen';
  toggleCitizenFieldsOnCreate();

  const backdrop = document.getElementById('createUserModalBackdrop');
  if (backdrop) backdrop.classList.add('show');
}

function closeCreateUserModal() {
  const backdrop = document.getElementById('createUserModalBackdrop');
  if (backdrop) backdrop.classList.remove('show');
}

function toggleCitizenFieldsOnCreate() {
  const role = document.getElementById('createUserRole').value;
  const fields = document.getElementById('createCitizenFields');
  if (fields) {
    fields.style.display = (role === 'citizen') ? 'block' : 'none';
  }
}

async function handleCreateUserSubmit(event) {
  event.preventDefault();
  const btn = document.getElementById('createUserSubmitBtn');
  btn.disabled = true;
  btn.innerText = 'Creating...';

  const name = document.getElementById('createUserName').value.trim();
  const email = document.getElementById('createUserEmail').value.trim();
  const password = document.getElementById('createUserPassword').value;
  const role = document.getElementById('createUserRole').value;
  const isActive = document.getElementById('createUserActive').checked;
  const phone = document.getElementById('createUserPhone')?.value.trim() || '';
  const city = document.getElementById('createUserCity')?.value.trim() || '';

  try {
    const newUser = await api.post('/users/', {
      name,
      email,
      password,
      role,
      is_active: isActive
    });

    // If citizen and phone/city provided, update citizen record
    if (role === 'citizen' && (phone || city) && newUser.id) {
      const citizenRecord = allCitizensMap[newUser.id] || newUser.citizen_profile;
      if (citizenRecord && citizenRecord.id) {
        await api.put(`/citizens/${citizenRecord.id}`, {
          phone,
          address: {
            street: "",
            city: city,
            district: "",
            state: "",
            postal_code: ""
          }
        }).catch(err => console.warn('Could not auto-populate citizen details:', err));
      }
    }

    closeCreateUserModal();
    await loadUsers();
  } catch (err) {
    alert('Failed to create user: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerText = 'Create User';
  }
}

// --------------------------------------------------------------------------
// Edit User Modal Logic
// --------------------------------------------------------------------------

// --------------------------------------------------------------------------
// Edit User Modal Logic
// --------------------------------------------------------------------------

function openEditUserModal(userId) {
  const targetId = parseInt(userId, 10);
  const user = allUsers.find(u => u.id === targetId || u.id == userId);
  if (!user) return;

  document.getElementById('editUserId').value = user.id;
  document.getElementById('editUserName').value = user.name || '';
  document.getElementById('editUserEmail').value = user.email || '';
  document.getElementById('editUserRole').value = user.role || 'citizen';
  document.getElementById('editUserPassword').value = '';
  document.getElementById('editUserActive').checked = !!user.is_active;

  const backdrop = document.getElementById('editUserModalBackdrop');
  if (backdrop) backdrop.classList.add('show');
}

function closeEditUserModal() {
  const backdrop = document.getElementById('editUserModalBackdrop');
  if (backdrop) backdrop.classList.remove('show');
}

async function handleEditUserSubmit(event) {
  event.preventDefault();
  const btn = document.getElementById('editUserSubmitBtn');
  btn.disabled = true;
  btn.innerText = 'Saving...';

  const userId = parseInt(document.getElementById('editUserId').value, 10);
  const name = document.getElementById('editUserName').value.trim();
  const email = document.getElementById('editUserEmail').value.trim();
  const role = document.getElementById('editUserRole').value;
  const password = document.getElementById('editUserPassword').value;
  const isActive = document.getElementById('editUserActive').checked;

  const payload = {
    name,
    email,
    role,
    is_active: isActive
  };
  if (password && password.length >= 6) {
    payload.password = password;
  }

  try {
    await api.put(`/users/${userId}`, payload);
    closeEditUserModal();
    await loadUsers();
  } catch (err) {
    alert('Failed to update user: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerText = 'Save Changes';
  }
}

// --------------------------------------------------------------------------
// View Profile Details Modal Logic
// --------------------------------------------------------------------------

function openViewProfileModal(userId) {
  const targetId = parseInt(userId, 10);
  const user = allUsers.find(u => u.id === targetId || u.id == userId);
  if (!user) {
    console.error('User not found for ID:', userId);
    return;
  }

  const citizen = allCitizensMap[user.id] || user.citizen_profile || {};
  const addr = (citizen && typeof citizen.address === 'object' && citizen.address) ? citizen.address : {};

  const modalBody = document.getElementById('viewProfileModalBody');
  if (!modalBody) return;

  let roleLabel = 'Citizen (Public User)';
  if (user.role === 'admin') roleLabel = 'System Administrator 👑';
  else if (user.role === 'department_officer') roleLabel = 'Department Review Officer 👮‍♂️';

  const street = addr.street || '';
  const city = addr.city || '';
  const district = addr.district || '';
  const state = addr.state || '';
  const postal = addr.postal_code || '';

  const locationSummary = [city, district, state].filter(Boolean).join(', ') || 'Not provided';

  modalBody.innerHTML = `
    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid var(--border-color);">
      <div class="user-table-avatar" style="width: 50px; height: 50px; font-size: 20px;">
        ${(user.name || 'U').charAt(0).toUpperCase()}
      </div>
      <div>
        <h4 style="font-size: 18px; margin-bottom: 4px; color: var(--text-main); font-weight: 700;">${escapeHtml(user.name)}</h4>
        <div style="color: var(--text-muted); font-size: 13px;">${escapeHtml(user.email)}</div>
      </div>
    </div>

    <div class="profile-field-row">
      <span class="profile-field-label">User ID:</span>
      <span class="profile-field-val">#${user.id}</span>
    </div>
    <div class="profile-field-row">
      <span class="profile-field-label">Assigned Role:</span>
      <span class="profile-field-val">${roleLabel}</span>
    </div>
    <div class="profile-field-row">
      <span class="profile-field-label">Account Status:</span>
      <span class="profile-field-val">${user.is_active ? '✅ Active & Enabled' : '❌ Deactivated / Inactive'}</span>
    </div>
    <div class="profile-field-row">
      <span class="profile-field-label">Registered Phone:</span>
      <span class="profile-field-val">${escapeHtml(citizen.phone || 'Not provided')}</span>
    </div>
    <div class="profile-field-row">
      <span class="profile-field-label">Street / Locality:</span>
      <span class="profile-field-val">${escapeHtml(street || 'Not provided')}</span>
    </div>
    <div class="profile-field-row">
      <span class="profile-field-label">City / Municipality:</span>
      <span class="profile-field-val">${escapeHtml(city || 'Not provided')}</span>
    </div>
    <div class="profile-field-row">
      <span class="profile-field-label">District & State:</span>
      <span class="profile-field-val">${escapeHtml(locationSummary)}</span>
    </div>
    <div class="profile-field-row">
      <span class="profile-field-label">Postal PIN Code:</span>
      <span class="profile-field-val">${escapeHtml(postal || 'Not provided')}</span>
    </div>
    <div class="profile-field-row" style="border-bottom: none;">
      <span class="profile-field-label">Account Created:</span>
      <span class="profile-field-val">${user.created_at ? new Date(user.created_at).toLocaleString() : 'N/A'}</span>
    </div>
  `;

  const backdrop = document.getElementById('viewProfileModalBackdrop');
  if (backdrop) backdrop.classList.add('show');
}

function closeViewProfileModal() {
  const backdrop = document.getElementById('viewProfileModalBackdrop');
  if (backdrop) backdrop.classList.remove('show');
}

// --------------------------------------------------------------------------
// Delete User Logic
// --------------------------------------------------------------------------

async function confirmDeleteUser(userId, userName) {
  if (!confirm(`Are you sure you want to permanently delete user "${userName}" (ID #${userId})?\n\nThis will remove their account and citizen profile.`)) {
    return;
  }

  try {
    await api.delete(`/users/${userId}`);
    await loadUsers();
  } catch (err) {
    alert('Failed to delete user: ' + err.message);
  }
}
