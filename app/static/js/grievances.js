/**
 * CivicAI - Grievance Redressal Controller (Vanilla JS)
 */

let allGrievances = [];
let allDepartments = [];

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  initGrievancesPage();
});

async function initGrievancesPage() {
  await Promise.all([loadDepartmentsForGrievance(), loadGrievances()]);

  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('new')) {
    openSubmitGrievanceModal();
  }

  const statusFilter = document.getElementById('grievanceStatusFilter');
  if (statusFilter) statusFilter.addEventListener('change', applyGrievanceFilters);
}

async function loadDepartmentsForGrievance() {
  try {
    allDepartments = await api.get('/departments/');
    const select = document.getElementById('grievanceDeptSelect');
    if (select) {
      select.innerHTML = '<option value="">Select Target Department...</option>' + 
        allDepartments.filter(d => d.is_active).map(d => `
          <option value="${d.id}">${escapeHtml(d.name)} (${d.code})</option>
        `).join('');
    }
  } catch (err) {
    console.error('Failed to load departments for grievance', err);
  }
}

async function loadGrievances() {
  const tbody = document.getElementById('grievancesTableBody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="6" style="text-align:center; padding: 32px;">
        <span class="loading-spinner"></span> Loading grievances...
      </td>
    </tr>
  `;

  try {
    allGrievances = await api.get('/grievances/');
    applyGrievanceFilters();
  } catch (err) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center; color: var(--danger); padding: 32px;">
          Failed to load grievances: ${escapeHtml(err.message)}
        </td>
      </tr>
    `;
  }
}

function applyGrievanceFilters() {
  const status = document.getElementById('grievanceStatusFilter')?.value || '';
  const filtered = allGrievances.filter(g => !status || g.status === status);
  renderGrievancesTable(filtered);
}

function renderGrievancesTable(grievances) {
  const tbody = document.getElementById('grievancesTableBody');
  const countEl = document.getElementById('grievanceCountDisplay');
  if (!tbody) return;

  if (countEl) countEl.innerText = `${grievances.length} grievances`;

  if (!grievances || grievances.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center; color: var(--text-muted); padding: 32px;">
          No grievances recorded.
        </td>
      </tr>
    `;
    return;
  }

  const user = api.getUser();
  const isOfficerOrAdmin = user && (user.role === 'admin' || user.role === 'department_officer');

  tbody.innerHTML = grievances.map(g => {
    const deptName = g.department ? g.department.name : `Dept #${g.department_id}`;
    return `
      <tr>
        <td><span class="ref-code">#GRV-${g.id}</span></td>
        <td><strong>${escapeHtml(g.subject)}</strong></td>
        <td>${escapeHtml(deptName)}</td>
        <td>${renderStatusBadge(g.status)}</td>
        <td>${formatDate(g.created_at)}</td>
        <td style="text-align: right; white-space: nowrap;">
          <button class="btn btn-outline btn-sm" onclick="viewGrievanceDetails(${g.id})">Details & Response</button>
          ${isOfficerOrAdmin ? `<button class="btn btn-primary btn-sm" onclick="openOfficerRespondModal(${g.id})">Officer Redressal</button>` : ''}
        </td>
      </tr>
    `;
  }).join('');
}

// Open Submit Grievance Modal
function openSubmitGrievanceModal() {
  document.getElementById('grievanceDeptSelect').value = '';
  document.getElementById('grievanceSubject').value = '';
  document.getElementById('grievanceDetails').value = '';
  document.getElementById('submitGrievanceModalBackdrop').classList.add('show');
}

function closeSubmitGrievanceModal() {
  const modal = document.getElementById('submitGrievanceModalBackdrop');
  if (modal) modal.classList.remove('show');
}

async function handleGrievanceSubmit(e) {
  e.preventDefault();
  const department_id = parseInt(document.getElementById('grievanceDeptSelect').value);
  const subject = document.getElementById('grievanceSubject').value.trim();
  const details = document.getElementById('grievanceDetails').value.trim();
  const submitBtn = document.getElementById('submitGrievanceBtn');

  if (!department_id || !subject || !details) {
    showToast('Please select a department and provide subject & grievance details.', 'warning');
    return;
  }

  try {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="loading-spinner"></span> Filing...';

    await api.post('/grievances/', {
      department_id,
      subject,
      details
    });

    showToast('Grievance registered successfully with municipal authorities.', 'success');
    closeSubmitGrievanceModal();
    await loadGrievances();
  } catch (err) {
    showToast(err.message || 'Failed to file grievance.', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = 'Submit Grievance';
  }
}

// View Grievance Details
function viewGrievanceDetails(id) {
  const g = allGrievances.find(item => String(item.id) === String(id));
  if (!g) {
    console.warn('Grievance not found for id:', id);
    return;
  }

  const dept = allDepartments.find(d => String(d.id) === String(g.department_id));
  const deptName = g.department ? g.department.name : (dept ? dept.name : `Dept #${g.department_id}`);
  
  const idEl = document.getElementById('detailGrievanceId');
  if (idEl) idEl.innerText = `#GRV-${g.id}`;

  const deptEl = document.getElementById('detailGrievanceDept');
  if (deptEl) deptEl.innerText = deptName;

  const subjEl = document.getElementById('detailGrievanceSubject');
  if (subjEl) subjEl.innerText = g.subject || 'No Subject';

  const statusEl = document.getElementById('detailGrievanceStatus');
  if (statusEl) statusEl.innerHTML = renderStatusBadge(g.status || 'submitted');

  const dateEl = document.getElementById('detailGrievanceDate');
  if (dateEl) dateEl.innerText = formatDate(g.created_at);

  const detailsEl = document.getElementById('detailGrievanceDetails');
  if (detailsEl) detailsEl.innerText = g.details || 'No additional details provided.';

  const respBox = document.getElementById('detailGrievanceResponse');
  if (respBox) {
    if (g.response && g.response.trim()) {
      respBox.innerHTML = `
        <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: var(--radius-sm); padding: 14px; color: #065f46;">
          <div style="font-weight: 700; font-size: 13px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
            <span>✅</span> Official Municipal Redressal / Action Taken:
          </div>
          <p style="margin-top: 6px; font-size: 14px; line-height: 1.5; color: #064e3b;">${escapeHtml(g.response)}</p>
        </div>
      `;
    } else {
      respBox.innerHTML = `
        <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: var(--radius-sm); padding: 14px; color: #92400e;">
          <div style="font-weight: 700; font-size: 13px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
            <span>⏳</span> Redressal Pending
          </div>
          <p style="margin-top: 4px; font-size: 13px; line-height: 1.4;">Grievance has been logged and assigned to the relevant department officer for inspection and corrective action.</p>
        </div>
      `;
    }
  }

  const modal = document.getElementById('grievanceDetailsModalBackdrop');
  if (modal) modal.classList.add('show');
}

function closeGrievanceDetailsModal() {
  const modal = document.getElementById('grievanceDetailsModalBackdrop');
  if (modal) modal.classList.remove('show');
}

// Officer Redressal Modal
function openOfficerRespondModal(id) {
  const g = allGrievances.find(item => String(item.id) === String(id));
  if (!g) return;

  const idEl = document.getElementById('respondGrievanceId');
  if (idEl) idEl.value = g.id;

  const subjEl = document.getElementById('respondGrievanceSubjectDisplay');
  if (subjEl) subjEl.innerText = g.subject || '';

  const statEl = document.getElementById('respondGrievanceStatusSelect');
  if (statEl) statEl.value = g.status === 'submitted' ? 'in_progress' : g.status;

  const textEl = document.getElementById('respondOfficerText');
  if (textEl) textEl.value = g.response || '';

  const modal = document.getElementById('officerRespondModalBackdrop');
  if (modal) modal.classList.add('show');
}

function closeOfficerRespondModal() {
  const modal = document.getElementById('officerRespondModalBackdrop');
  if (modal) modal.classList.remove('show');
}

async function handleOfficerRespondSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('respondGrievanceId').value;
  const status = document.getElementById('respondGrievanceStatusSelect').value;
  const responseText = document.getElementById('respondOfficerText').value.trim();
  const saveBtn = document.getElementById('saveRespondBtn');

  if (!responseText) {
    showToast('Please provide the official response details.', 'warning');
    return;
  }

  try {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="loading-spinner"></span> Saving...';

    await api.put(`/grievances/${id}/respond`, {
      status,
      response: responseText
    });

    showToast(`Grievance status updated to '${status}'.`, 'success');
    closeOfficerRespondModal();
    await loadGrievances();
  } catch (err) {
    showToast(err.message || 'Failed to submit grievance response.', 'error');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerText = 'Submit Resolution';
  }
}

// Close modals when clicking backdrop
document.addEventListener('click', (e) => {
  if (e.target.classList && e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('show');
  }
});

// Explicitly export to window scope
window.openSubmitGrievanceModal = openSubmitGrievanceModal;
window.closeSubmitGrievanceModal = closeSubmitGrievanceModal;
window.handleGrievanceSubmit = handleGrievanceSubmit;
window.viewGrievanceDetails = viewGrievanceDetails;
window.closeGrievanceDetailsModal = closeGrievanceDetailsModal;
window.openOfficerRespondModal = openOfficerRespondModal;
window.closeOfficerRespondModal = closeOfficerRespondModal;
window.handleOfficerRespondSubmit = handleOfficerRespondSubmit;
