/**
 * CivicAI - Application Workflow & Tracking Controller (Vanilla JS)
 */

let allApplications = [];
let availableServices = [];

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  initApplicationsPage();
});

async function initApplicationsPage() {
  await Promise.all([loadServicesForApp(), loadApplications()]);

  // Handle URL query params
  const urlParams = new URLSearchParams(window.location.search);
  const newParam = urlParams.get('new');
  const serviceIdParam = urlParams.get('service_id');
  const refParam = urlParams.get('ref');

  if (serviceIdParam || newParam) {
    openSubmitAppModal(serviceIdParam);
  }

  if (refParam) {
    document.getElementById('refSearchInput').value = refParam;
    lookupApplicationByRef(refParam);
  }

  // Filter listeners
  const statusFilter = document.getElementById('appStatusFilter');
  if (statusFilter) statusFilter.addEventListener('change', applyAppFilters);

  const refInput = document.getElementById('refSearchInput');
  if (refInput) {
    refInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const val = refInput.value.trim();
        if (val) lookupApplicationByRef(val);
        else loadApplications();
      }
    });
  }
}

async function loadServicesForApp() {
  try {
    availableServices = await api.get('/services/');
    const select = document.getElementById('appServiceSelect');
    if (select) {
      select.innerHTML = '<option value="">Choose a Civic Service...</option>' + 
        availableServices.filter(s => s.status === 'active').map(s => `
          <option value="${s.id}">${escapeHtml(s.name)} (${s.code}) - ${s.processing_time_days} days SLA</option>
        `).join('');
    }
  } catch (err) {
    console.error('Failed to load services for application', err);
  }
}

async function loadApplications() {
  const tbody = document.getElementById('applicationsTableBody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="6" style="text-align:center; padding: 32px;">
        <span class="loading-spinner"></span> Loading applications...
      </td>
    </tr>
  `;

  try {
    allApplications = await api.get('/applications/');
    applyAppFilters();
  } catch (err) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center; color: var(--danger); padding: 32px;">
          Failed to load applications: ${escapeHtml(err.message)}
        </td>
      </tr>
    `;
  }
}

function applyAppFilters() {
  const status = document.getElementById('appStatusFilter')?.value || '';
  const filtered = allApplications.filter(a => !status || a.status === status);
  renderApplicationsTable(filtered);
}

function renderApplicationsTable(apps) {
  const tbody = document.getElementById('applicationsTableBody');
  const countEl = document.getElementById('appCountDisplay');
  if (!tbody) return;

  if (countEl) countEl.innerText = `${apps.length} records`;

  if (!apps || apps.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center; color: var(--text-muted); padding: 32px;">
          No service applications found.
        </td>
      </tr>
    `;
    return;
  }

  const user = api.getUser();
  const isOfficerOrAdmin = user && (user.role === 'admin' || user.role === 'department_officer');

  tbody.innerHTML = apps.map(app => {
    const serviceName = app.service ? app.service.name : `Service #${app.service_id}`;
    return `
      <tr>
        <td><span class="ref-code">${escapeHtml(app.reference_no)}</span></td>
        <td><strong>${escapeHtml(serviceName)}</strong></td>
        <td>${renderStatusBadge(app.status)}</td>
        <td>${formatDate(app.created_at)}</td>
        <td>${escapeHtml(app.officer_remarks || 'Pending Review')}</td>
        <td style="text-align: right; white-space: nowrap;">
          <button class="btn btn-outline btn-sm" onclick="viewAppDetails(${app.id})">Details & Timeline</button>
          ${isOfficerOrAdmin ? `<button class="btn btn-primary btn-sm" onclick="openOfficerReviewModal(${app.id})">Review / Update</button>` : ''}
        </td>
      </tr>
    `;
  }).join('');
}

// Open Submit Application Modal
function openSubmitAppModal(preSelectedServiceId = null) {
  const select = document.getElementById('appServiceSelect');
  if (select && preSelectedServiceId) {
    select.value = preSelectedServiceId;
    onAppServiceSelected();
  }
  document.getElementById('submitAppModalBackdrop').classList.add('show');
}

function closeSubmitAppModal() {
  const modal = document.getElementById('submitAppModalBackdrop');
  if (modal) modal.classList.remove('show');
}

function onAppServiceSelected() {
  const select = document.getElementById('appServiceSelect');
  const serviceId = parseInt(select.value);
  const guideBox = document.getElementById('appServiceGuideBox');
  
  if (!serviceId) {
    guideBox.style.display = 'none';
    return;
  }

  const service = availableServices.find(s => s.id === serviceId);
  if (service) {
    guideBox.style.display = 'block';
    const docs = service.requirements?.required_documents || [];
    document.getElementById('guideReqDocs').innerHTML = docs.length > 0 
      ? docs.map(d => `<li>📄 ${escapeHtml(d)}</li>`).join('')
      : '<li>Standard verification</li>';
    document.getElementById('guideSLA').innerText = `${service.processing_time_days} days`;
  }
}

// Submit Application
async function handleAppSubmit(e) {
  e.preventDefault();
  const serviceId = parseInt(document.getElementById('appServiceSelect').value);
  const applicantName = document.getElementById('appApplicantName').value.trim();
  const premiseDetails = document.getElementById('appPremiseDetails').value.trim();
  const holdingNumber = document.getElementById('appHoldingNo').value.trim();
  const declarationChecked = document.getElementById('appDeclaration').checked;
  const submitBtn = document.getElementById('submitAppBtn');

  if (!serviceId || !applicantName) {
    showToast('Please select a service and provide applicant name.', 'warning');
    return;
  }

  if (!declarationChecked) {
    showToast('Please accept the accuracy declaration.', 'warning');
    return;
  }

  const payload = {
    applicant_name: applicantName,
    premise_details: premiseDetails,
    holding_number: holdingNumber,
    submission_timestamp: new Date().toISOString()
  };

  try {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="loading-spinner"></span> Submitting...';

    const result = await api.post('/applications/', {
      service_id: serviceId,
      payload: payload
    });

    closeSubmitAppModal();
    showSubmissionSuccessModal(result.reference_no);
    await loadApplications();
  } catch (err) {
    showToast(err.message || 'Failed to submit application.', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = 'Submit Application';
  }
}

// Reference Confirmation Dialog
function showSubmissionSuccessModal(refNo) {
  document.getElementById('createdRefNoDisplay').innerText = refNo;
  document.getElementById('refSuccessModalBackdrop').classList.add('show');
}

function closeRefSuccessModal() {
  const modal = document.getElementById('refSuccessModalBackdrop');
  if (modal) modal.classList.remove('show');
}

// View Application Details & Timeline
function viewAppDetails(id) {
  const app = allApplications.find(a => String(a.id) === String(id));
  if (!app) return;

  const refEl = document.getElementById('detailAppRef');
  if (refEl) refEl.innerText = app.reference_no;

  const svcEl = document.getElementById('detailAppService');
  if (svcEl) svcEl.innerText = app.service ? app.service.name : `Service #${app.service_id}`;

  const statEl = document.getElementById('detailAppStatus');
  if (statEl) statEl.innerHTML = renderStatusBadge(app.status);

  const dateEl = document.getElementById('detailAppDate');
  if (dateEl) dateEl.innerText = formatDate(app.created_at);

  const remEl = document.getElementById('detailAppRemarks');
  if (remEl) remEl.innerText = app.officer_remarks || 'None provided yet.';
  
  // Render Payload JSON nicely
  const payloadBox = document.getElementById('detailAppPayload');
  if (payloadBox) payloadBox.innerText = JSON.stringify(app.payload, null, 2);

  // Render Status Timeline
  renderAppTimeline(app.status, app.created_at, app.updated_at, app.officer_remarks);

  const modal = document.getElementById('appDetailsModalBackdrop');
  if (modal) modal.classList.add('show');
}

function closeAppDetailsModal() {
  const modal = document.getElementById('appDetailsModalBackdrop');
  if (modal) modal.classList.remove('show');
}

function renderAppTimeline(status, created_at, updated_at, remarks) {
  const container = document.getElementById('appTimelineContainer');
  if (!container) return;

  const stages = [
    { key: 'submitted', title: 'Application Submitted', desc: 'Received in municipal database' },
    { key: 'under_review', title: 'Officer Scrutiny & Field Inspection', desc: 'Documents and premises under review' },
    { key: 'approved', title: 'Final Determination', desc: status === 'rejected' ? 'Application Rejected' : 'Application Approved' }
  ];

  let currentIdx = 0;
  if (status === 'under_review' || status === 'additional_info_required') currentIdx = 1;
  if (status === 'approved' || status === 'rejected') currentIdx = 2;

  container.innerHTML = `
    <div class="timeline">
      ${stages.map((stage, idx) => {
        const isCompleted = idx < currentIdx || (idx === 2 && (status === 'approved' || status === 'rejected'));
        const isActive = idx === currentIdx;
        const markerClass = isCompleted ? 'completed' : (isActive ? 'active' : '');
        const timeDisplay = idx === 0 ? formatDate(created_at) : (isCompleted ? formatDate(updated_at) : '');

        return `
          <div class="timeline-item ${markerClass}">
            <div class="timeline-marker">${isCompleted ? '✓' : (idx + 1)}</div>
            <div class="timeline-content">
              <div class="timeline-title">
                <span>${stage.title}</span>
                <span class="timeline-time">${timeDisplay}</span>
              </div>
              <div class="timeline-desc">
                ${stage.desc}
                ${idx === 2 && remarks ? `<div style="margin-top: 6px; color: var(--primary); font-weight: 500;">Officer Remarks: "${escapeHtml(remarks)}"</div>` : ''}
              </div>
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

// Officer Review Modal
function openOfficerReviewModal(id) {
  const app = allApplications.find(a => String(a.id) === String(id));
  if (!app) return;

  const idEl = document.getElementById('reviewAppId');
  if (idEl) idEl.value = app.id;

  const refEl = document.getElementById('reviewAppRefDisplay');
  if (refEl) refEl.innerText = app.reference_no;

  const svcEl = document.getElementById('reviewAppServiceName');
  if (svcEl) svcEl.innerText = app.service ? app.service.name : `Service #${app.service_id}`;

  const statEl = document.getElementById('reviewAppStatusSelect');
  if (statEl) statEl.value = app.status;

  const remEl = document.getElementById('reviewOfficerRemarks');
  if (remEl) remEl.value = app.officer_remarks || '';

  const modal = document.getElementById('officerReviewModalBackdrop');
  if (modal) modal.classList.add('show');
}

function closeOfficerReviewModal() {
  const modal = document.getElementById('officerReviewModalBackdrop');
  if (modal) modal.classList.remove('show');
}

async function handleOfficerReviewSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('reviewAppId').value;
  const status = document.getElementById('reviewAppStatusSelect').value;
  const officer_remarks = document.getElementById('reviewOfficerRemarks').value.trim();
  const saveBtn = document.getElementById('saveReviewBtn');

  try {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="loading-spinner"></span> Updating...';

    await api.put(`/applications/${id}/status`, {
      status,
      officer_remarks
    });

    showToast(`Application status successfully updated to '${status}'.`, 'success');
    closeOfficerReviewModal();
    await loadApplications();
  } catch (err) {
    showToast(err.message || 'Failed to update application status.', 'error');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerText = 'Update Status';
  }
}

// Search by Reference
async function lookupApplicationByRef(refNo) {
  try {
    const app = await api.get(`/applications/ref/${encodeURIComponent(refNo)}`);
    renderApplicationsTable([app]);
    showToast(`Found record for reference ${refNo}`, 'success');
  } catch (err) {
    showToast(`No application found for reference '${refNo}' (or unauthorized).`, 'error');
    loadApplications();
  }
}
