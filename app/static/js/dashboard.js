/**
 * CivicAI - Dashboard Controller (Vanilla JS)
 */

document.addEventListener('DOMContentLoaded', async () => {
  if (!requireAuth()) return;
  loadDashboardData();
});

async function loadDashboardData() {
  const user = api.getUser();
  const dashboardContainer = document.getElementById('dashboardContent');
  if (!dashboardContainer) return;

  const role = user.role || 'citizen';
  document.getElementById('userRoleHeaderBadge').innerHTML = renderRoleBadge(role);
  document.getElementById('welcomeUserName').innerText = user.name || 'User';

  try {
    if (role === 'citizen') {
      await renderCitizenDashboard();
    } else if (role === 'department_officer') {
      await renderOfficerDashboard();
    } else if (role === 'admin') {
      await renderAdminDashboard();
    }
  } catch (err) {
    dashboardContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <h3 class="empty-title">Failed to load dashboard metrics</h3>
        <p class="empty-text">${escapeHtml(err.message)}</p>
        <button class="btn btn-primary" onclick="loadDashboardData()">Retry</button>
      </div>
    `;
  }
}

// 1. Citizen Dashboard
// 1. Citizen Dashboard
async function renderCitizenDashboard() {
  const [apps, grievances, profile, notifs] = await Promise.all([
    api.get('/applications/'),
    api.get('/grievances/'),
    api.get('/citizens/me').catch(() => null),
    api.get('/notifications/me?unread_only=true').catch(() => [])
  ]);

  const activeApps = apps.filter(a => a.status !== 'approved' && a.status !== 'rejected').length;
  const activeGrievances = grievances.filter(g => g.status !== 'resolved' && g.status !== 'closed').length;

  document.getElementById('statsGrid').innerHTML = `
    <a href="/static/applications.html" class="stat-card" title="View all applications">
      <div class="stat-icon-wrapper stat-icon-blue">📋</div>
      <div class="stat-details">
        <div class="stat-label">Total Applications</div>
        <div class="stat-value">${apps.length}</div>
        <div class="stat-meta">${activeApps} active in progress ➔</div>
      </div>
    </a>
    <a href="/static/grievances.html" class="stat-card" title="View all grievances">
      <div class="stat-icon-wrapper stat-icon-amber">⚠️</div>
      <div class="stat-details">
        <div class="stat-label">Filed Grievances</div>
        <div class="stat-value">${grievances.length}</div>
        <div class="stat-meta">${activeGrievances} pending resolution ➔</div>
      </div>
    </a>
    <div class="stat-card" onclick="openNotificationsModal()" title="View unread alerts and notifications">
      <div class="stat-icon-wrapper stat-icon-green">🔔</div>
      <div class="stat-details">
        <div class="stat-label">Unread Alerts</div>
        <div class="stat-value">${(notifs || []).length}</div>
        <div class="stat-meta">Status & timeline updates ➔</div>
      </div>
    </div>
    <a href="/static/chat.html" class="stat-card" title="Ask AI Civic Assistant">
      <div class="stat-icon-wrapper stat-icon-purple">🤖</div>
      <div class="stat-details">
        <div class="stat-label">AI Civic Help</div>
        <div class="stat-value">24/7</div>
        <div class="stat-meta">Grounded guideline assistant ➔</div>
      </div>
    </a>
  `;

  // Quick Actions
  document.getElementById('quickActionsContainer').innerHTML = `
    <div class="quick-actions-grid">
      <a href="/static/services.html" class="quick-action-card">
        <span class="quick-action-icon">🏛️</span>
        <span class="quick-action-title">Browse Services</span>
      </a>
      <a href="/static/applications.html?new=true" class="quick-action-card">
        <span class="quick-action-icon">📝</span>
        <span class="quick-action-title">Submit Application</span>
      </a>
      <a href="/static/grievances.html?new=true" class="quick-action-card">
        <span class="quick-action-icon">📢</span>
        <span class="quick-action-title">File Grievance</span>
      </a>
      <a href="/static/chat.html" class="quick-action-card">
        <span class="quick-action-icon">💬</span>
        <span class="quick-action-title">Ask Civic AI</span>
      </a>
    </div>
  `;

  // Recent Submissions
  renderRecentApplicationsTable(apps.slice(0, 5));
  renderRecentGrievancesTable(grievances.slice(0, 5));
}

// 2. Officer Dashboard
async function renderOfficerDashboard() {
  const [slaData, apps, grievances] = await Promise.all([
    api.get('/services/stats/sla-dashboard'),
    api.get('/applications/'),
    api.get('/grievances/')
  ]);

  const pendingApps = apps.filter(a => a.status === 'submitted' || a.status === 'under_review').length;
  const pendingGrievances = grievances.filter(g => g.status === 'submitted' || g.status === 'in_progress').length;

  document.getElementById('statsGrid').innerHTML = `
    <a href="/static/applications.html" class="stat-card" title="Review incoming applications">
      <div class="stat-icon-wrapper stat-icon-blue">📋</div>
      <div class="stat-details">
        <div class="stat-label">Applications Queue</div>
        <div class="stat-value">${apps.length}</div>
        <div class="stat-meta">${pendingApps} pending officer review ➔</div>
      </div>
    </a>
    <a href="/static/grievances.html" class="stat-card" title="Respond to filed grievances">
      <div class="stat-icon-wrapper stat-icon-amber">⚠️</div>
      <div class="stat-details">
        <div class="stat-label">Grievances Redressal</div>
        <div class="stat-value">${grievances.length}</div>
        <div class="stat-meta">${pendingGrievances} requiring response ➔</div>
      </div>
    </a>
    <a href="/static/applications.html" class="stat-card" title="View application SLAs">
      <div class="stat-icon-wrapper stat-icon-green">⚡</div>
      <div class="stat-details">
        <div class="stat-label">App Resolution Rate</div>
        <div class="stat-value">${slaData.application_resolution_rate_pct || 100}%</div>
        <div class="stat-meta">Avg SLA: ${slaData.sla_target_days_avg || 15} days ➔</div>
      </div>
    </a>
    <a href="/static/grievances.html" class="stat-card" title="View grievance resolution metrics">
      <div class="stat-icon-wrapper stat-icon-purple">🎯</div>
      <div class="stat-details">
        <div class="stat-label">Grievance Redressal Rate</div>
        <div class="stat-value">${slaData.grievance_resolution_rate_pct || 100}%</div>
        <div class="stat-meta">Department standard ➔</div>
      </div>
    </a>
  `;

  // Quick Actions for Officer
  document.getElementById('quickActionsContainer').innerHTML = `
    <div class="quick-actions-grid">
      <a href="/static/applications.html" class="quick-action-card">
        <span class="quick-action-icon">🔍</span>
        <span class="quick-action-title">Review Applications</span>
      </a>
      <a href="/static/grievances.html" class="quick-action-card">
        <span class="quick-action-icon">📝</span>
        <span class="quick-action-title">Respond to Grievances</span>
      </a>
      <a href="/static/documents.html" class="quick-action-card">
        <span class="quick-action-icon">📄</span>
        <span class="quick-action-title">Upload Guidelines</span>
      </a>
      <a href="/static/services.html" class="quick-action-card">
        <span class="quick-action-icon">📚</span>
        <span class="quick-action-title">Manage Catalogue</span>
      </a>
    </div>
  `;

  renderRecentApplicationsTable(apps.slice(0, 5));
  renderRecentGrievancesTable(grievances.slice(0, 5));
}

// 3. Admin Dashboard
async function renderAdminDashboard() {
  const [slaData, depts, services, docs, users] = await Promise.all([
    api.get('/services/stats/sla-dashboard'),
    api.get('/departments/'),
    api.get('/services/'),
    api.get('/documents/'),
    api.get('/users/').catch(() => [])
  ]);

  document.getElementById('statsGrid').innerHTML = `
    <a href="/static/departments.html" class="stat-card" title="Manage Departments">
      <div class="stat-icon-wrapper stat-icon-blue">🏛️</div>
      <div class="stat-details">
        <div class="stat-label">Civic Departments</div>
        <div class="stat-value">${depts.length}</div>
        <div class="stat-meta">Public active divisions ➔</div>
      </div>
    </a>
    <a href="/static/services.html" class="stat-card" title="Manage Service Catalogue">
      <div class="stat-icon-wrapper stat-icon-green">📚</div>
      <div class="stat-details">
        <div class="stat-label">Service Catalogue</div>
        <div class="stat-value">${services.length}</div>
        <div class="stat-meta">Configured with JSONB ➔</div>
      </div>
    </a>
    <a href="/static/documents.html" class="stat-card" title="Knowledge Base & Vector Index">
      <div class="stat-icon-wrapper stat-icon-purple">📑</div>
      <div class="stat-details">
        <div class="stat-label">Knowledge Documents</div>
        <div class="stat-value">${docs.length}</div>
        <div class="stat-meta">Indexed in Vector Store ➔</div>
      </div>
    </a>
    <a href="/static/users.html" class="stat-card" title="Registered Users & Citizen Management">
      <div class="stat-icon-wrapper stat-icon-amber">👥</div>
      <div class="stat-details">
        <div class="stat-label">Registered Users</div>
        <div class="stat-value">${users.length}</div>
        <div class="stat-meta">Admins, Officers, Citizens ➔</div>
      </div>
    </a>
  `;

  // Quick Actions for Admin
  document.getElementById('quickActionsContainer').innerHTML = `
    <div class="quick-actions-grid">
      <a href="/static/users.html" class="quick-action-card">
        <span class="quick-action-icon">👥</span>
        <span class="quick-action-title">Manage Users</span>
      </a>
      <a href="/static/departments.html" class="quick-action-card">
        <span class="quick-action-icon">🏛️</span>
        <span class="quick-action-title">Manage Departments</span>
      </a>
      <a href="/static/services.html" class="quick-action-card">
        <span class="quick-action-icon">📚</span>
        <span class="quick-action-title">Service Catalogue</span>
      </a>
      <a href="/static/documents.html" class="quick-action-card">
        <span class="quick-action-icon">📄</span>
        <span class="quick-action-title">Vector Knowledge Base</span>
      </a>
      <a href="/static/applications.html" class="quick-action-card">
        <span class="quick-action-icon">📋</span>
        <span class="quick-action-title">All Applications</span>
      </a>
    </div>
  `;

  const apps = await api.get('/applications/');
  const grievances = await api.get('/grievances/');
  renderRecentApplicationsTable(apps.slice(0, 5));
  renderRecentGrievancesTable(grievances.slice(0, 5));
}

// Table Renderers
function renderRecentApplicationsTable(apps) {
  const container = document.getElementById('recentAppsTableBody');
  if (!container) return;

  if (!apps || apps.length === 0) {
    container.innerHTML = `
      <tr>
        <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 24px;">
          No applications recorded yet.
        </td>
      </tr>
    `;
    return;
  }

  container.innerHTML = apps.map(app => `
    <tr>
      <td><span class="ref-code">${escapeHtml(app.reference_no)}</span></td>
      <td><strong>${escapeHtml(app.service ? app.service.name : `Service #${app.service_id}`)}</strong></td>
      <td>${renderStatusBadge(app.status)}</td>
      <td>${formatDate(app.created_at)}</td>
      <td>
        <a href="/static/applications.html?ref=${encodeURIComponent(app.reference_no)}" class="btn btn-outline btn-sm">
          Details
        </a>
      </td>
    </tr>
  `).join('');
}

function renderRecentGrievancesTable(grievances) {
  const container = document.getElementById('recentGrievancesTableBody');
  if (!container) return;

  if (!grievances || grievances.length === 0) {
    container.innerHTML = `
      <tr>
        <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 24px;">
          No grievances recorded yet.
        </td>
      </tr>
    `;
    return;
  }

  container.innerHTML = grievances.map(g => `
    <tr>
      <td><span class="ref-code">#${g.id}</span></td>
      <td><strong>${escapeHtml(g.subject)}</strong></td>
      <td>${escapeHtml(g.department ? g.department.name : `Dept #${g.department_id}`)}</td>
      <td>${renderStatusBadge(g.status)}</td>
      <td>${formatDate(g.created_at)}</td>
    </tr>
  `).join('');
}

// Notifications Modal Handler
async function openNotificationsModal() {
  const modal = document.getElementById('notificationsModalBackdrop');
  const body = document.getElementById('notificationsModalBody');
  if (modal) modal.classList.add('show');
  if (body) body.innerHTML = '<div style="text-align: center; padding: 24px;"><span class="loading-spinner"></span> Loading alerts...</div>';

  try {
    const notifs = await api.get('/notifications/me');
    if (!notifs || notifs.length === 0) {
      body.innerHTML = `
        <div style="text-align: center; padding: 32px 16px; color: var(--text-muted);">
          <div style="font-size: 32px; margin-bottom: 8px;">🔕</div>
          <p style="font-weight: 600;">No notifications found.</p>
          <p style="font-size: 13px;">You are completely up to date!</p>
        </div>
      `;
      return;
    }

    body.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 10px;">
        ${notifs.map(n => `
          <div style="padding: 12px 16px; border-radius: var(--radius-sm); border: 1px solid ${n.is_read ? 'var(--border-color)' : '#93c5fd'}; background: ${n.is_read ? '#f8fafc' : '#eff6ff'}; display: flex; justify-content: space-between; align-items: flex-start; gap: 12px;">
            <div>
              <div style="font-size: 13px; font-weight: 700; color: var(--text-main); margin-bottom: 2px;">
                ${n.is_read ? '' : '<span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #2563eb; margin-right: 6px;"></span>'}
                ${escapeHtml(n.title)}
              </div>
              <p style="font-size: 13px; color: var(--text-muted); margin: 0; line-height: 1.4;">${escapeHtml(n.message)}</p>
              <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">${formatDate(n.created_at)}</div>
            </div>
            ${!n.is_read ? `
              <button class="btn btn-outline btn-sm" onclick="markReadAndRefresh(${n.id})" style="padding: 3px 8px; font-size: 11px; white-space: nowrap;">
                Mark Read
              </button>
            ` : ''}
          </div>
        `).join('')}
      </div>
    `;
  } catch (err) {
    if (body) body.innerHTML = `<div style="color: var(--danger); text-align: center; padding: 20px;">Failed to load alerts: ${escapeHtml(err.message)}</div>`;
  }
}

function closeNotificationsModal() {
  const modal = document.getElementById('notificationsModalBackdrop');
  if (modal) modal.classList.remove('show');
}

async function markReadAndRefresh(id) {
  try {
    await api.put(`/notifications/${id}/read`);
    openNotificationsModal();
    loadDashboardData();
  } catch (err) {
    showToast(err.message || 'Failed to mark as read', 'error');
  }
}

// Close modals when clicking backdrop
document.addEventListener('click', (e) => {
  if (e.target.classList && e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('show');
  }
});

// Explicitly export functions to window scope
window.loadDashboardData = loadDashboardData;
window.openNotificationsModal = openNotificationsModal;
window.closeNotificationsModal = closeNotificationsModal;
window.markReadAndRefresh = markReadAndRefresh;
