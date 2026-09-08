/**
 * CivicAI - Service Catalogue Controller (Vanilla JS)
 */

let allServices = [];
let allDepartments = [];

document.addEventListener('DOMContentLoaded', () => {
  initServicesPage();
});

async function initServicesPage() {
  const user = api.getUser();
  const isOfficerOrAdmin = user && (user.role === 'admin' || user.role === 'department_officer');

  const addBtn = document.getElementById('addServiceBtn');
  if (addBtn) addBtn.style.display = isOfficerOrAdmin ? 'inline-flex' : 'none';

  await Promise.all([loadDepartments(), loadServices()]);

  // URL query filter support
  const urlParams = new URLSearchParams(window.location.search);
  const deptParam = urlParams.get('dept');
  if (deptParam) {
    const deptSelect = document.getElementById('deptFilterSelect');
    if (deptSelect) deptSelect.value = deptParam;
    applyServiceFilters();
  }

  // Attach search & filter listeners
  const searchInput = document.getElementById('serviceSearchInput');
  if (searchInput) searchInput.addEventListener('input', applyServiceFilters);

  const deptSelect = document.getElementById('deptFilterSelect');
  if (deptSelect) deptSelect.addEventListener('change', applyServiceFilters);

  const statusSelect = document.getElementById('statusFilterSelect');
  if (statusSelect) statusSelect.addEventListener('change', applyServiceFilters);
}

async function loadDepartments() {
  try {
    allDepartments = await api.get('/departments/');
    const filterSelect = document.getElementById('deptFilterSelect');
    const formSelect = document.getElementById('serviceDeptId');

    if (filterSelect) {
      filterSelect.innerHTML = '<option value="">All Departments</option>' + 
        allDepartments.map(d => `<option value="${d.id}">${escapeHtml(d.name)} (${d.code})</option>`).join('');
    }
    if (formSelect) {
      formSelect.innerHTML = '<option value="">Select Department...</option>' + 
        allDepartments.map(d => `<option value="${d.id}">${escapeHtml(d.name)} (${d.code})</option>`).join('');
    }
  } catch (err) {
    console.error('Failed to load departments for services', err);
  }
}

async function loadServices() {
  const container = document.getElementById('servicesGridContainer');
  if (!container) return;

  container.innerHTML = `
    <div style="grid-column: 1/-1; text-align: center; padding: 48px;">
      <span class="loading-spinner"></span> Loading civic service catalogue...
    </div>
  `;

  try {
    allServices = await api.get('/services/');
    applyServiceFilters();
  } catch (err) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; color: var(--danger); padding: 48px;">
        Failed to load services: ${escapeHtml(err.message)}
      </div>
    `;
  }
}

function applyServiceFilters() {
  const search = (document.getElementById('serviceSearchInput')?.value || '').toLowerCase().trim();
  const deptId = document.getElementById('deptFilterSelect')?.value || '';
  const status = document.getElementById('statusFilterSelect')?.value || '';

  const filtered = allServices.filter(s => {
    const matchesSearch = !search || 
      s.name.toLowerCase().includes(search) || 
      s.code.toLowerCase().includes(search) || 
      (s.description && s.description.toLowerCase().includes(search));
    const matchesDept = !deptId || String(s.department_id) === String(deptId);
    const matchesStatus = !status || s.status === status;
    return matchesSearch && matchesDept && matchesStatus;
  });

  renderServicesGrid(filtered);
}

function renderServicesGrid(services) {
  const container = document.getElementById('servicesGridContainer');
  const countEl = document.getElementById('servicesCountDisplay');
  if (!container) return;

  if (countEl) countEl.innerText = `${services.length} services`;

  if (!services || services.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1;" class="empty-state">
        <div class="empty-icon">📚</div>
        <h3 class="empty-title">No services found</h3>
        <p class="empty-text">Try adjusting your filters or search keywords.</p>
      </div>
    `;
    return;
  }

  const user = api.getUser();
  const isOfficerOrAdmin = user && (user.role === 'admin' || user.role === 'department_officer');
  const isAdmin = user && user.role === 'admin';

  container.innerHTML = services.map(s => {
    const dept = allDepartments.find(d => d.id === s.department_id);
    const deptName = dept ? dept.name : `Department #${s.department_id}`;
    
    // Extract document requirements list
    let docList = [];
    if (s.requirements && s.requirements.required_documents) {
      docList = Array.isArray(s.requirements.required_documents) ? s.requirements.required_documents : [];
    }

    return `
      <div class="card" style="display: flex; flex-direction: column; height: 100%; margin-bottom: 0;">
        <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px;">
          <span class="ref-code">${escapeHtml(s.code)}</span>
          ${s.status === 'active' ? '<span class="badge badge-active">Active</span>' : '<span class="badge badge-inactive">Inactive</span>'}
        </div>
        <h3 style="font-size: 16px; font-weight: 700; color: var(--text-main); margin-bottom: 6px;">
          ${escapeHtml(s.name)}
        </h3>
        <p style="font-size: 12px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; margin-bottom: 10px;">
          🏛️ ${escapeHtml(deptName)}
        </p>
        <p style="font-size: 13px; color: var(--text-muted); flex: 1; margin-bottom: 14px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
          ${escapeHtml(s.description || 'Public civic service application.')}
        </p>

        <div style="background: #f8fafc; border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 10px 12px; margin-bottom: 16px; font-size: 12px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: var(--text-muted);">SLA Processing Time:</span>
            <strong>⏱️ ${s.processing_time_days} days</strong>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: var(--text-muted);">Required Documents:</span>
            <strong>📁 ${docList.length} items</strong>
          </div>
        </div>

        <div style="display: flex; gap: 8px; align-items: center; justify-content: flex-end; padding-top: 10px; border-top: 1px solid var(--border-color);">
          <button class="btn btn-outline btn-sm" onclick="viewServiceDetails(${s.id})">Details & Checklist</button>
          <a href="/static/applications.html?service_id=${s.id}" class="btn btn-primary btn-sm">Apply Now</a>
          ${isOfficerOrAdmin ? `<button class="btn btn-outline btn-sm" onclick="openEditServiceModal(${s.id})">Edit</button>` : ''}
          ${isAdmin ? `<button class="btn btn-danger btn-sm" onclick="confirmDeleteService(${s.id}, '${escapeHtml(s.name)}')">Delete</button>` : ''}
        </div>
      </div>
    `;
  }).join('');
}

// View Detailed Service Modal
function viewServiceDetails(id) {
  const service = allServices.find(s => s.id === id);
  if (!service) return;

  const dept = allDepartments.find(d => d.id === service.department_id);
  document.getElementById('detailServiceName').innerText = service.name;
  document.getElementById('detailServiceCode').innerText = service.code;
  document.getElementById('detailServiceDept').innerText = dept ? dept.name : `Dept #${service.department_id}`;
  document.getElementById('detailServiceDesc').innerText = service.description || 'No detailed scope provided.';
  document.getElementById('detailServiceSLA').innerText = `${service.processing_time_days} Working Days`;
  document.getElementById('detailServiceStatus').innerHTML = service.status === 'active' ? '<span class="badge badge-active">Active</span>' : '<span class="badge badge-inactive">Inactive</span>';

  // Requirements checklist
  const reqContainer = document.getElementById('detailReqDocuments');
  let docs = service.requirements?.required_documents || [];
  if (typeof docs === 'string') docs = [docs];
  reqContainer.innerHTML = docs.length > 0 
    ? docs.map(doc => `<li style="margin-bottom: 6px;">📄 ${escapeHtml(doc)}</li>`).join('')
    : '<li style="color: var(--text-muted);">No mandatory physical documents specified.</li>';

  // Fee Structure
  const feeEl = document.getElementById('detailFeeStructure');
  feeEl.innerText = service.requirements?.fee_structure || service.requirements?.fee_amount || 'Free / Standard Municipal Schedule';

  // Eligibility
  const eligContainer = document.getElementById('detailEligibility');
  const elig = service.eligibility_criteria || {};
  let eligItems = [];
  if (elig.min_age) eligItems.push(`Minimum Age: ${elig.min_age} years`);
  if (elig.residency_required) eligItems.push('Must be a legal resident within municipal jurisdiction');
  if (elig.details && Array.isArray(elig.details)) eligItems.push(...elig.details);

  eligContainer.innerHTML = eligItems.length > 0
    ? eligItems.map(item => `<li style="margin-bottom: 6px;">✔️ ${escapeHtml(item)}</li>`).join('')
    : '<li style="color: var(--text-muted);">Standard citizen eligibility criteria applies.</li>';

  document.getElementById('applyFromDetailsBtn').href = `/static/applications.html?service_id=${service.id}`;
  document.getElementById('serviceDetailsModalBackdrop').classList.add('show');
}

function closeServiceDetailsModal() {
  const modal = document.getElementById('serviceDetailsModalBackdrop');
  if (modal) modal.classList.remove('show');
}

// Create Service Modal
function openCreateServiceModal() {
  document.getElementById('serviceModalTitle').innerText = 'Add New Civic Service';
  document.getElementById('serviceId').value = '';
  document.getElementById('serviceName').value = '';
  document.getElementById('serviceCode').value = '';
  document.getElementById('serviceDeptId').value = '';
  document.getElementById('serviceDesc').value = '';
  document.getElementById('serviceSLA').value = '15';
  document.getElementById('serviceStatus').value = 'active';
  document.getElementById('serviceDocs').value = 'Proof of Identity\nProof of Address\nApplication Fee Challan';
  document.getElementById('serviceFee').value = 'Rs. 500 Processing Fee';
  document.getElementById('serviceMinAge').value = '18';

  document.getElementById('serviceFormModalBackdrop').classList.add('show');
}

// Edit Service Modal
function openEditServiceModal(id) {
  const service = allServices.find(s => s.id === id);
  if (!service) return;

  document.getElementById('serviceModalTitle').innerText = 'Edit Civic Service';
  document.getElementById('serviceId').value = service.id;
  document.getElementById('serviceName').value = service.name;
  document.getElementById('serviceCode').value = service.code;
  document.getElementById('serviceDeptId').value = service.department_id;
  document.getElementById('serviceDesc').value = service.description || '';
  document.getElementById('serviceSLA').value = service.processing_time_days || 15;
  document.getElementById('serviceStatus').value = service.status || 'active';
  
  const docs = service.requirements?.required_documents || [];
  document.getElementById('serviceDocs').value = Array.isArray(docs) ? docs.join('\n') : '';
  document.getElementById('serviceFee').value = service.requirements?.fee_structure || service.requirements?.fee_amount || '';
  document.getElementById('serviceMinAge').value = service.eligibility_criteria?.min_age || 18;

  document.getElementById('serviceFormModalBackdrop').classList.add('show');
}

function closeServiceFormModal() {
  const modal = document.getElementById('serviceFormModalBackdrop');
  if (modal) modal.classList.remove('show');
}

// Form Submission
async function handleServiceFormSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('serviceId').value;
  const name = document.getElementById('serviceName').value.trim();
  const code = document.getElementById('serviceCode').value.trim().toUpperCase();
  const department_id = parseInt(document.getElementById('serviceDeptId').value);
  const description = document.getElementById('serviceDesc').value.trim();
  const processing_time_days = parseInt(document.getElementById('serviceSLA').value) || 15;
  const status = document.getElementById('serviceStatus').value;
  
  const docsRaw = document.getElementById('serviceDocs').value.trim();
  const required_documents = docsRaw.split('\n').map(d => d.trim()).filter(d => d.length > 0);
  const fee_structure = document.getElementById('serviceFee').value.trim();
  const min_age = parseInt(document.getElementById('serviceMinAge').value) || 18;

  const saveBtn = document.getElementById('saveServiceBtn');

  if (!name || !code || !department_id) {
    showToast('Name, Service Code, and Department are required.', 'warning');
    return;
  }

  const payload = {
    name,
    code,
    department_id,
    description,
    processing_time_days,
    status,
    requirements: {
      required_documents,
      fee_structure
    },
    eligibility_criteria: {
      min_age,
      residency_required: true
    }
  };

  try {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="loading-spinner"></span> Saving...';

    if (id) {
      await api.put(`/services/${id}`, payload);
      showToast(`Service '${name}' updated successfully.`, 'success');
    } else {
      await api.post('/services/', payload);
      showToast(`Service '${name}' created successfully.`, 'success');
    }

    closeServiceFormModal();
    await loadServices();
  } catch (err) {
    showToast(err.message || 'Failed to save service.', 'error');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerText = 'Save Service';
  }
}

// Confirm Delete
function confirmDeleteService(id, name) {
  confirmAction(
    'Delete Service',
    `Are you sure you want to delete '${name}'? This will remove all associated service submissions.`,
    async () => {
      try {
        await api.delete(`/services/${id}`);
        showToast(`Service '${name}' was deleted.`, 'success');
        await loadServices();
      } catch (err) {
        showToast(err.message || 'Could not delete service.', 'error');
      }
    }
  );
}
