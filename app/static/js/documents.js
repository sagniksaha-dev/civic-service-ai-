/**
 * CivicAI - Approved Knowledge Documents & Vector RAG Controller (Vanilla JS)
 */

let allDocuments = [];
let allDepartments = [];

document.addEventListener('DOMContentLoaded', () => {
  if (!requireAuth()) return;
  initDocumentsPage();
});

async function initDocumentsPage() {
  const user = api.getUser();
  const isAdmin = user && user.role === 'admin';
  const isOfficerOrAdmin = user && (user.role === 'admin' || user.role === 'department_officer');

  // Toggle Admin / Officer action buttons
  const uploadCard = document.getElementById('uploadDocumentCard');
  if (uploadCard) uploadCard.style.display = isOfficerOrAdmin ? 'block' : 'none';

  const reindexAllBtn = document.getElementById('reindexAllBtn');
  if (reindexAllBtn) reindexAllBtn.style.display = isAdmin ? 'inline-flex' : 'none';

  await Promise.all([loadDepartmentsForDocs(), loadDocuments()]);
}

async function loadDepartmentsForDocs() {
  try {
    allDepartments = await api.get('/departments/');
    const select = document.getElementById('docDepartmentId');
    if (select) {
      select.innerHTML = '<option value="">Optional: Associate with Department...</option>' + 
        allDepartments.map(d => `<option value="${d.id}">${escapeHtml(d.name)} (${d.code})</option>`).join('');
    }
  } catch (err) {
    console.error('Failed to load departments for documents', err);
  }
}

async function loadDocuments() {
  const tbody = document.getElementById('documentsTableBody');
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="7" style="text-align:center; padding: 32px;">
        <span class="loading-spinner"></span> Loading approved guideline documents...
      </td>
    </tr>
  `;

  try {
    allDocuments = await api.get('/documents/');
    renderDocumentsTable(allDocuments);
  } catch (err) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center; color: var(--danger); padding: 32px;">
          Failed to load documents: ${escapeHtml(err.message)}
        </td>
      </tr>
    `;
  }
}

function renderDocumentsTable(docs) {
  const tbody = document.getElementById('documentsTableBody');
  const countEl = document.getElementById('docCountDisplay');
  if (!tbody) return;

  if (countEl) countEl.innerText = `${docs.length} documents indexed`;

  if (!docs || docs.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center; color: var(--text-muted); padding: 32px;">
          No knowledge documents uploaded yet.
        </td>
      </tr>
    `;
    return;
  }

  const user = api.getUser();
  const isOfficerOrAdmin = user && (user.role === 'admin' || user.role === 'department_officer');

  tbody.innerHTML = docs.map(doc => {
    const dept = allDepartments.find(d => d.id === doc.department_id);
    const deptName = dept ? dept.name : (doc.department_id ? `Dept #${doc.department_id}` : 'General Civic');

    return `
      <tr>
        <td><strong>#${doc.id}</strong></td>
        <td>
          <div style="font-weight: 700; color: var(--text-main);">${escapeHtml(doc.title)}</div>
          <div style="font-size: 12px; color: var(--text-muted); font-family: var(--font-mono);">${escapeHtml(doc.file_name)}</div>
        </td>
        <td>${escapeHtml(deptName)}</td>
        <td><span class="ref-code">${escapeHtml(doc.file_type.toUpperCase())}</span></td>
        <td><strong>${doc.total_chunks || (doc.chunks ? doc.chunks.length : 0)} chunks</strong></td>
        <td>${renderStatusBadge(doc.status)}</td>
        <td style="text-align: right; white-space: nowrap;">
          ${isOfficerOrAdmin ? `
            <button class="btn btn-outline btn-sm" onclick="reindexSingleDoc(${doc.id})">Re-index</button>
            <button class="btn btn-danger btn-sm" onclick="confirmDeleteDoc(${doc.id}, '${escapeHtml(doc.title)}')">Delete</button>
          ` : `
            <span style="color: var(--text-muted); font-size: 12px;">Active Guideline</span>
          `}
        </td>
      </tr>
    `;
  }).join('');
}

// Upload Document Form Submission
async function handleDocumentUpload(e) {
  e.preventDefault();
  const fileInput = document.getElementById('docFileInput');
  const title = document.getElementById('docTitle').value.trim();
  const department_id = document.getElementById('docDepartmentId').value;
  const category = document.getElementById('docCategory').value;
  const uploadBtn = document.getElementById('uploadDocBtn');

  if (!fileInput.files || fileInput.files.length === 0) {
    showToast('Please select a file to upload.', 'warning');
    return;
  }

  if (!title) {
    showToast('Document title is required.', 'warning');
    return;
  }

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('title', title);
  if (department_id) formData.append('department_id', department_id);
  formData.append('category', category);

  try {
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<span class="loading-spinner"></span> Extracting & Indexing...';

    const result = await api.uploadFile('/documents/upload', formData);
    showToast(`Successfully indexed '${result.title}' with ${result.total_chunks || 0} chunks.`, 'success');

    // Reset Form
    document.getElementById('docUploadForm').reset();
    await loadDocuments();
  } catch (err) {
    showToast(err.message || 'Failed to upload and index document.', 'error');
  } finally {
    uploadBtn.disabled = false;
    uploadBtn.innerText = 'Upload & Index into Vector Store';
  }
}

// Re-index Single Document
async function reindexSingleDoc(id) {
  try {
    showToast(`Re-indexing document #${id}...`, 'info');
    await api.post(`/documents/${id}/reindex`, {});
    showToast(`Document #${id} re-indexed successfully.`, 'success');
    await loadDocuments();
  } catch (err) {
    showToast(err.message || 'Re-indexing failed.', 'error');
  }
}

// Re-index All Documents (Admin)
async function reindexAllDocuments() {
  confirmAction(
    'Re-index Complete Knowledge Base',
    'This will re-embed and vectorize all approved guidelines across all departments. Proceed?',
    async () => {
      try {
        showToast('Vector store re-indexing in progress...', 'info');
        const res = await api.post('/documents/reindex-all', {});
        showToast(`Successfully re-indexed ${res.reindexed_count} documents into ChromaDB!`, 'success');
        await loadDocuments();
      } catch (err) {
        showToast(err.message || 'Bulk re-indexing failed.', 'error');
      }
    }
  );
}

// Confirm Delete Document
function confirmDeleteDoc(id, title) {
  confirmAction(
    'Delete Knowledge Document',
    `Are you sure you want to delete '${title}'? This will purge its embedding chunks from the vector database.`,
    async () => {
      try {
        await api.delete(`/documents/${id}`);
        showToast(`Document '${title}' deleted and vectors purged.`, 'success');
        await loadDocuments();
      } catch (err) {
        showToast(err.message || 'Could not delete document.', 'error');
      }
    }
  );
}
