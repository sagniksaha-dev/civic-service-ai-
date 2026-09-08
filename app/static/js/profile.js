/**
 * CivicAI - Citizen Profile & Smart Partial Update Controller (Vanilla JS)
 */

let initialProfileData = {};

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  initProfilePage();
});

async function initProfilePage() {
  const user = api.getUser();
  if (!user) return;

  document.getElementById('profileUserName').innerText = user.name || 'User';
  document.getElementById('profileUserEmail').innerText = user.email || 'Email';
  document.getElementById('profileUserRoleBadge').innerHTML = renderRoleBadge(user.role);

  await loadProfile();
}

async function loadProfile() {
  try {
    const profile = await api.get('/citizens/me');
    initialProfileData = profile || {};

    const addr = profile.address || {};
    document.getElementById('profilePhone').value = profile.phone || '';
    document.getElementById('profileDOB').value = profile.date_of_birth || '';
    
    document.getElementById('addrStreet').value = addr.street || '';
    document.getElementById('addrCity').value = addr.city || '';
    document.getElementById('addrDistrict').value = addr.district || '';
    document.getElementById('addrState').value = addr.state || '';
    document.getElementById('addrPostalCode').value = addr.postal_code || '';

    document.getElementById('profileCitizenIdDisplay').innerText = `#CIT-${profile.id || 'NEW'}`;
    document.getElementById('profileUpdatedDisplay').innerText = formatDate(profile.updated_at);
  } catch (err) {
    showToast('Failed to load profile details: ' + err.message, 'error');
  }
}

// Smart Partial Update Form Submission
async function handleProfileSubmit(e) {
  e.preventDefault();
  const phone = document.getElementById('profilePhone').value.trim();
  const date_of_birth = document.getElementById('profileDOB').value.trim();
  
  const street = document.getElementById('addrStreet').value.trim();
  const city = document.getElementById('addrCity').value.trim();
  const district = document.getElementById('addrDistrict').value.trim();
  const state = document.getElementById('addrState').value.trim();
  const postal_code = document.getElementById('addrPostalCode').value.trim();

  const saveBtn = document.getElementById('saveProfileBtn');

  // Smart Partial Payload Builder
  const payload = {};

  if (phone !== (initialProfileData.phone || '')) {
    payload.phone = phone;
  }
  if (date_of_birth !== (initialProfileData.date_of_birth || '')) {
    payload.date_of_birth = date_of_birth;
  }

  const initialAddr = initialProfileData.address || {};
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
    showToast('No changes detected in your profile.', 'info');
    return;
  }

  try {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="loading-spinner"></span> Updating Profile...';

    const updated = await api.put('/citizens/me', payload);
    showToast('Citizen profile updated successfully (smart partial update applied)!', 'success');
    initialProfileData = updated;
    await loadProfile();
  } catch (err) {
    showToast(err.message || 'Failed to update profile.', 'error');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerText = 'Save Profile Changes';
  }
}
