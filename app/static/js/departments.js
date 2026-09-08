/**
 * CivicAI - Department Management Controller (Vanilla JS)
 */

let allDepartments = [];

document.addEventListener('DOMContentLoaded', () => {
  initDepartmentsPage();
});

async function initDepartmentsPage() {
  const user = api.getUser();
  const isAdmin = user && user.role === 'admin';

  // Toggle Admin specific buttons
  const addBtn = document.getElementById('addDeptBtn');
  if (addBtn) addBtn.style.display = isAdmin ? 'inline-flex' : 'none';

  await loadDepartments();

  // Search filter
  const searchInput = document.getElementById('deptSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      const filtered = allDepartments.filter(d => 
        d.name.toLowerCase().includes(q) || 
        d.code.toLowerCase().includes(q) || 
        (d.description && d.description.toLowerCase().includes(q))
      );
      renderDepartmentsTable(filtered);
    });
  }
}

async function loadDepartments() {
  const tbody = document.getElementById('departmentsTableBody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="6" style="text-align:center; padding: 32px;">
        <span class="loading-spinner"></span> Loading departments...
      </td>
    </tr>
  `;

  try {
    allDepartments = await api.get('/departments/');
    renderDepartmentsTable(allDepartments);
  } catch (err) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center; color: var(--danger); padding: 32px;">
          Failed to load departments: ${escapeHtml(err.message)}
        </td>
      </tr>
    `;
  }
}

function renderDepartmentsTable(depts) {
  const tbody = document.getElementById('departmentsTableBody');
  const countEl = document.getElementById('deptCountDisplay');
  if (!tbody) return;

  if (countEl) countEl.innerText = `${depts.length} departments`;

  if (!depts || depts.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center; color: var(--text-muted); padding: 32px;">
          No departments found.
        </td>
      </tr>
    `;
    return;
  }

  const user = api.getUser();
  const isAdmin = user && user.role === 'admin';

  tbody.innerHTML = depts.map(d => `
    <tr>
      <td><strong>${d.id}</strong></td>
      <td><span class="ref-code">${escapeHtml(d.code)}</span></td>
      <td><strong>${escapeHtml(d.name)}</strong></td>
      <td><span style="color: var(--text-muted); font-size: 13px;">${escapeHtml(d.description || 'No description provided.')}</span></td>
      <td>${d.is_active ? '<span class="badge badge-active">Active</span>' : '<span class="badge badge-inactive">Inactive</span>'}</td>
      <td style="text-align: right; white-space: nowrap;">
        ${isAdmin ? `
          <button class="btn btn-outline btn-sm" onclick="openEditDeptModal(${d.id})">Edit</button>
          <button class="btn btn-danger btn-sm" onclick="confirmDeleteDept(${d.id}, '${escapeHtml(d.name)}')">Delete</button>
        ` : `
          <a href="/static/services.html?dept=${d.id}" class="btn btn-outline btn-sm">View Services</a>
        `}
      </td>
    </tr>
  `).join('');
}

// Open Create Modal
function openCreateDeptModal() {
  document.getElementById('deptModalTitle').innerText = 'Register Civic Department';
  document.getElementById('deptId').value = '';
  document.getElementById('deptName').value = '';
  document.getElementById('deptCode').value = '';
  document.getElementById('deptDesc').value = '';
  document.getElementById('deptActive').checked = true;

  document.getElementById('deptModalBackdrop').classList.add('show');
}

// Open Edit Modal
function openEditDeptModal(id) {
  const dept = allDepartments.find(d => d.id === id);
  if (!dept) return;

  document.getElementById('deptModalTitle').innerText = 'Edit Civic Department';
  document.getElementById('deptId').value = dept.id;
  document.getElementById('deptName').value = dept.name;
  document.getElementById('deptCode').value = dept.code;
  document.getElementById('deptDesc').value = dept.description || '';
  document.getElementById('deptActive').checked = dept.is_active;

  document.getElementById('deptModalBackdrop').classList.add('show');
}

function closeDeptModal() {
  const modal = document.getElementById('deptModalBackdrop');
  if (modal) modal.classList.remove('show');
}

// Save Department Form Submission
async function handleDeptFormSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('deptId').value;
  const name = document.getElementById('deptName').value.trim();
  const code = document.getElementById('deptCode').value.trim().toUpperCase();
  const description = document.getElementById('deptDesc').value.trim();
  const is_active = document.getElementById('deptActive').checked;
  const saveBtn = document.getElementById('saveDeptBtn');

  if (!name || !code) {
    showToast('Name and department code are required.', 'warning');
    return;
  }

  try {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="loading-spinner"></span> Saving...';

    const payload = { name, code, description, is_active };

    if (id) {
      await api.put(`/departments/${id}`, payload);
      showToast(`Department '${name}' updated successfully.`, 'success');
    } else {
      await api.post('/departments/', payload);
      showToast(`Department '${name}' created successfully.`, 'success');
    }

    closeDeptModal();
    await loadDepartments();
  } catch (err) {
    showToast(err.message || 'Failed to save department.', 'error');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerText = 'Save Department';
  }
}

// Confirm Delete
function confirmDeleteDept(id, name) {
  confirmAction(
    'Delete Department',
    `Are you sure you want to delete '${name}'? This will cascade remove associated services and records.`,
    async () => {
      try {
        await api.delete(`/departments/${id}`);
        showToast(`Department '${name}' was deleted.`, 'success');
        await loadDepartments();
      } catch (err) {
        showToast(err.message || 'Could not delete department.', 'error');
      }
    }
  );
}
