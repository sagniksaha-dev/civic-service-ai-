/**
 * CivicAI - Multi-Role Profile Controller (Vanilla JS)
 * Supports Administrator, Department Officer, and Citizen Profile Management
 */

let initialCitizenProfileData = {};

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  initProfilePage();
});

async function initProfilePage() {
  const user = api.getUser();
  if (!user) return;

  const role = user.role || 'citizen';
  const name = user.name || 'User';
  const email = user.email || 'Email';

  // Common identity header
  document.getElementById('profileUserName').innerText = name;
  document.getElementById('profileUserEmail').innerText = email;

  const avatarBadge = document.getElementById('profileAvatarBadge');
  if (avatarBadge) {
    avatarBadge.innerText = name.charAt(0).toUpperCase();
  }

  // Role-specific routing
  if (role === 'admin') {
    renderAdminProfileView(user);
  } else if (role === 'department_officer') {
    renderOfficerProfileView(user);
  } else {
    renderCitizenProfileView(user);
  }
}

// --------------------------------------------------------------------------
// 1. Administrator Profile View
// --------------------------------------------------------------------------
function renderAdminProfileView(user) {
  document.getElementById('profilePageHeaderTitle').innerText = 'System Administrator Profile & Account';
  document.title = 'CivicAI - Administrator Profile';

  document.getElementById('profileUserRoleBadge').innerHTML = `
    <span class="badge-admin-tag">👑 System Administrator</span>
  `;
  document.getElementById('profileUserIdDisplay').innerText = `#ADMIN-USER-${user.id}`;

  // Show Admin section, hide others
  document.getElementById('adminProfileSection').style.display = 'block';
  document.getElementById('officerProfileSection').style.display = 'none';
  document.getElementById('citizenProfileSection').style.display = 'none';

  // Pre-fill form
  document.getElementById('adminName').value = user.name || '';
  document.getElementById('adminEmail').value = user.email || '';
}

async function handleAdminCredentialsSubmit(e) {
  e.preventDefault();
  const user = api.getUser();
  if (!user) return;

  const name = document.getElementById('adminName').value.trim();
  const email = document.getElementById('adminEmail').value.trim();
  const password = document.getElementById('adminPassword').value;
  const confirmPassword = document.getElementById('adminConfirmPassword').value;
  const saveBtn = document.getElementById('saveAdminBtn');

  if (password && password.length < 6) {
    showToast('Password must be at least 6 characters long.', 'warning');
    return;
  }
  if (password && password !== confirmPassword) {
    showToast('Passwords do not match. Please re-check.', 'error');
    return;
  }

  const payload = {
    name,
    email
  };
  if (password) {
    payload.password = password;
  }

  try {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="loading-spinner"></span> Saving...';

    const updated = await api.put(`/users/${user.id}`, payload);
    showToast('Administrator profile updated successfully!', 'success');

    // Update session user
    user.name = updated.name;
    user.email = updated.email;
    api.setUser(user);

    document.getElementById('profileUserName').innerText = user.name;
    document.getElementById('profileUserEmail').innerText = user.email;
    const sidebarName = document.getElementById('sidebarUserName');
    if (sidebarName) sidebarName.innerText = user.name;

    document.getElementById('adminPassword').value = '';
    document.getElementById('adminConfirmPassword').value = '';
  } catch (err) {
    showToast('Failed to update administrator profile: ' + err.message, 'error');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerText = 'Save Administrator Profile';
  }
}

// --------------------------------------------------------------------------
// 2. Department Officer Profile View
// --------------------------------------------------------------------------
function renderOfficerProfileView(user) {
  document.getElementById('profilePageHeaderTitle').innerText = 'Department Officer Profile & Account';
  document.title = 'CivicAI - Officer Profile';

  document.getElementById('profileUserRoleBadge').innerHTML = `
    <span class="badge-officer-tag">👮‍♂️ Review Officer</span>
  `;
  document.getElementById('profileUserIdDisplay').innerText = `#OFFICER-USER-${user.id}`;

  document.getElementById('adminProfileSection').style.display = 'none';
  document.getElementById('officerProfileSection').style.display = 'block';
  document.getElementById('citizenProfileSection').style.display = 'none';

  document.getElementById('officerName').value = user.name || '';
  document.getElementById('officerEmail').value = user.email || '';
}

async function handleOfficerCredentialsSubmit(e) {
  e.preventDefault();
  const user = api.getUser();
  if (!user) return;

  const name = document.getElementById('officerName').value.trim();
  const email = document.getElementById('officerEmail').value.trim();
  const password = document.getElementById('officerPassword').value;
  const confirmPassword = document.getElementById('officerConfirmPassword').value;
  const saveBtn = document.getElementById('saveOfficerBtn');

  if (password && password.length < 6) {
    showToast('Password must be at least 6 characters long.', 'warning');
    return;
  }
  if (password && password !== confirmPassword) {
    showToast('Passwords do not match. Please re-check.', 'error');
    return;
  }

  const payload = { name, email };
  if (password) payload.password = password;

  try {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="loading-spinner"></span> Saving...';

    const updated = await api.put(`/users/${user.id}`, payload);
    showToast('Officer profile updated successfully!', 'success');

    user.name = updated.name;
    user.email = updated.email;
    api.setUser(user);

    document.getElementById('profileUserName').innerText = user.name;
    document.getElementById('profileUserEmail').innerText = user.email;
    const sidebarName = document.getElementById('sidebarUserName');
    if (sidebarName) sidebarName.innerText = user.name;

    document.getElementById('officerPassword').value = '';
    document.getElementById('officerConfirmPassword').value = '';
  } catch (err) {
    showToast('Failed to update officer profile: ' + err.message, 'error');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerText = 'Save Officer Profile';
  }
}

// --------------------------------------------------------------------------
// 3. Citizen Profile View (JSONB Address & Smart Partial Update)
// --------------------------------------------------------------------------
async function renderCitizenProfileView(user) {
  document.getElementById('profilePageHeaderTitle').innerText = 'Citizen Profile & Address Details';
  document.title = 'CivicAI - Citizen Profile';

  document.getElementById('profileUserRoleBadge').innerHTML = `
    <span class="badge-citizen-tag">👨‍💼 Citizen</span>
  `;

  document.getElementById('adminProfileSection').style.display = 'none';
  document.getElementById('officerProfileSection').style.display = 'none';
  document.getElementById('citizenProfileSection').style.display = 'block';

  await loadCitizenProfile();
}

async function loadCitizenProfile() {
  try {
    const profile = await api.get('/citizens/me');
    initialCitizenProfileData = profile || {};

    const addr = profile.address || {};
    document.getElementById('profilePhone').value = profile.phone || '';
    document.getElementById('profileDOB').value = profile.date_of_birth || '';

    document.getElementById('addrStreet').value = addr.street || '';
    document.getElementById('addrCity').value = addr.city || '';
    document.getElementById('addrDistrict').value = addr.district || '';
    document.getElementById('addrState').value = addr.state || '';
    document.getElementById('addrPostalCode').value = addr.postal_code || '';

    document.getElementById('profileUserIdDisplay').innerText = `#CIT-${profile.id || 'NEW'}`;
    document.getElementById('profileUpdatedDisplay').innerText = formatDate(profile.updated_at);
  } catch (err) {
    showToast('Failed to load citizen profile details: ' + err.message, 'error');
  }
}

// Smart Partial Update for Citizen
async function handleCitizenProfileSubmit(e) {
  e.preventDefault();
  const phone = document.getElementById('profilePhone').value.trim();
  const date_of_birth = document.getElementById('profileDOB').value.trim();

  const street = document.getElementById('addrStreet').value.trim();
  const city = document.getElementById('addrCity').value.trim();
  const district = document.getElementById('addrDistrict').value.trim();
  const state = document.getElementById('addrState').value.trim();
  const postal_code = document.getElementById('addrPostalCode').value.trim();

  const saveBtn = document.getElementById('saveCitizenProfileBtn');

  // Smart Partial Payload Builder
  const payload = {};

  if (phone !== (initialCitizenProfileData.phone || '')) {
    payload.phone = phone;
  }
  if (date_of_birth !== (initialCitizenProfileData.date_of_birth || '')) {
    payload.date_of_birth = date_of_birth;
  }

  const initialAddr = initialCitizenProfileData.address || {};
  const newAddr = {};
  if (street !== (initialAddr.street || '')) newAddr.street = street;
  if (city !== (initialAddr.city || '')) newAddr.city = city;
  if (district !== (initialAddr.district || '')) newAddr.district = district;
  if (state !== (initialAddr.state || '')) newAddr.state = state;
  if (postal_code !== (initialAddr.postal_code || '')) newAddr.postal_code = postal_code;

  if (Object.keys(newAddr).length > 0) {
    payload.address = newAddr;
  }

  if (Object.keys(payload).length === 0) {
    showToast('No changes detected in your citizen profile.', 'info');
    return;
  }

  try {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="loading-spinner"></span> Updating Profile...';

    const updated = await api.put('/citizens/me', payload);
    showToast('Citizen profile updated successfully (smart partial update applied)!', 'success');
    initialCitizenProfileData = updated;
    await loadCitizenProfile();
  } catch (err) {
    showToast(err.message || 'Failed to update citizen profile.', 'error');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerText = 'Save Profile Changes (Partial Update)';
  }
}
