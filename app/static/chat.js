// ==============================================================================
// CivicAI Assistant - Interactive Web Application Logic
// ==============================================================================

// Global Application State
let ws = null;
let currentSessionId = localStorage.getItem("civic_chat_session_id") || null;
let authToken = null;
let currentRole = "citizen";
let activeLanguage = "en";
let cachedServices = [];
let cachedDepartments = [];

// User Presets for 1-Click Role Simulation
const USER_PRESETS = {
  citizen: { email: "citizen@civic.local", password: "CitizenPassword123!" },
  citizen2: { email: "test_citizen_two@civic.local", password: "CitizenTwoPass123!" },
  officer: { email: "officer@civic.local", password: "OfficerPassword123!" },
  admin: { email: "admin@civic.local", password: "AdminPassword123!" },
  anonymous: null
};

// DOM Elements
const navItems = document.querySelectorAll(".nav-item");
const tabContents = document.querySelectorAll(".tab-content");
const currentTabTitle = document.getElementById("currentTabTitle");
const currentTabDesc = document.getElementById("currentTabDesc");
const languageSelector = document.getElementById("languageSelector");

const chatMessages = document.getElementById("chatMessages");
const messageInput = document.getElementById("messageInput");
const chatForm = document.getElementById("chatForm");
const typingIndicator = document.getElementById("typingIndicator");
const wsStatusDot = document.getElementById("wsStatusDot");
const wsStatusText = document.getElementById("wsStatusText");
const roleSelector = document.getElementById("roleSelector");
const userInfoDisplay = document.getElementById("userInfoDisplay");
const quickPromptBtns = document.querySelectorAll(".quick-prompt-btn");

// Tab Title Mappings
const TAB_INFO = {
  chat: { title: "AI Civic Service Assistant", desc: "Grounded knowledge retrieval from approved public department guidelines" },
  applications: { title: "Service Applications & Status Pipeline", desc: "Track civic submissions with verifiable reference IDs" },
  grievances: { title: "Citizen Grievance Redressal Cell", desc: "Transparent complaint tracking and official department responses" },
  services: { title: "Public Service Catalogue", desc: "Browse procedures, mandatory documents, and statutory SLAs" },
  sla: { title: "Officer Operations & SLA Dashboard", desc: "Real-time compliance monitoring and workflow management" },
  notifications: { title: "Live Activity & Status Alerts", desc: "Real-time timeline alerts and status update logs" }
};

// ==============================================================================
// 1. Navigation & Tab Switching
// ==============================================================================
navItems.forEach(item => {
  item.addEventListener("click", () => {
    const tabId = item.getAttribute("data-tab");
    switchTab(tabId);
  });
});

function switchTab(tabId) {
  navItems.forEach(btn => {
    if (btn.getAttribute("data-tab") === tabId) btn.classList.add("active");
    else btn.classList.remove("active");
  });

  tabContents.forEach(content => {
    if (content.id === `tab-${tabId}`) content.classList.add("active");
    else content.classList.remove("active");
  });

  if (TAB_INFO[tabId]) {
    currentTabTitle.innerText = TAB_INFO[tabId].title;
    currentTabDesc.innerText = TAB_INFO[tabId].desc;
  }

  // Auto-refresh tab data
  if (tabId === "applications") loadApplications();
  else if (tabId === "grievances") loadGrievances();
  else if (tabId === "services") loadServices();
  else if (tabId === "sla") loadSlaMetrics();
  else if (tabId === "notifications") loadNotifications();
}

// ==============================================================================
// 2. Authentication & Identity Management
// ==============================================================================
async function switchRole(role) {
  currentRole = role;
  const preset = USER_PRESETS[role];

  if (!preset) {
    authToken = null;
    userInfoDisplay.innerText = "Mode: Public / Anonymous Citizen";
    return;
  }

  userInfoDisplay.innerText = `Authenticating as ${preset.email}...`;

  try {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(preset)
    });

    if (res.ok) {
      const data = await res.json();
      authToken = data.access_token;
      userInfoDisplay.innerText = `Logged in: ${data.name} (${data.role})`;
    } else {
      userInfoDisplay.innerText = `Login: Please run create_admin.py to seed (${res.status})`;
    }
  } catch (err) {
    console.error("Auth error:", err);
    userInfoDisplay.innerText = "Backend API server offline";
  }
}

roleSelector.addEventListener("change", (e) => switchRole(e.target.value));
languageSelector.addEventListener("change", (e) => { activeLanguage = e.target.value; });

// ==============================================================================
// 3. WebSocket Real-time Assistant
// ==============================================================================
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

  wsStatusDot.className = "dot dot-disconnected";
  wsStatusText.innerText = "Connecting...";

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    wsStatusDot.className = "dot dot-connected";
    wsStatusText.innerText = "WebSocket Live";
  };

  ws.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data);
      handleWebSocketMessage(payload);
    } catch (err) {
      console.error("WS Parse error:", err);
    }
  };

  ws.onclose = () => {
    wsStatusDot.className = "dot dot-disconnected";
    wsStatusText.innerText = "Reconnecting...";
    setTimeout(initWebSocket, 3000);
  };

  ws.onerror = (err) => {
    console.error("WebSocket error:", err);
    ws.close();
  };
}

function handleWebSocketMessage(payload) {
  if (payload.type === "typing") {
    typingIndicator.classList.remove("hidden");
    scrollToBottom();
    return;
  }

  typingIndicator.classList.add("hidden");

  if (payload.type === "answer") {
    currentSessionId = payload.session_id;
    localStorage.setItem("civic_chat_session_id", currentSessionId);
    appendAssistantMessage(payload);
  } else if (payload.type === "error") {
    appendSystemErrorMessage(payload.error || "An error occurred");
  }
}

function appendUserMessage(text) {
  const wrapper = document.createElement("div");
  wrapper.className = "message-wrapper user";
  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  wrapper.innerHTML = `
    <div class="message-avatar">👤</div>
    <div class="message-bubble">
      <div class="message-header">
        <span class="sender-name">You</span>
        <span class="timestamp">${time}</span>
      </div>
      <div class="message-body">${escapeHTML(text)}</div>
    </div>
  `;

  chatMessages.appendChild(wrapper);
  scrollToBottom();
}

function appendAssistantMessage(data) {
  const wrapper = document.createElement("div");
  wrapper.className = "message-wrapper assistant";
  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // Format verified sources
  let sourcesHTML = "";
  if (data.sources && data.sources.length > 0) {
    const sourceCards = data.sources.map(s => `
      <div class="source-card">
        <div class="source-title">
          <span>📄 ${escapeHTML(s.title)}</span>
          <span class="badge badge-gov">Page ${s.page_number || 1}</span>
        </div>
        ${s.snippet ? `<div class="source-snippet">"${escapeHTML(s.snippet)}"</div>` : ""}
      </div>
    `).join("");

    sourcesHTML = `
      <div class="sources-container">
        <button class="sources-toggle" onclick="toggleSources(this)">
          <span>📚 Verified Department Guidelines (${data.sources.length})</span>
          <span>▼</span>
        </button>
        <div class="sources-list hidden">${sourceCards}</div>
      </div>
    `;
  }

  const disclaimerHTML = data.disclaimer ? `
    <div class="disclaimer-banner">
      ⚖️ ${escapeHTML(data.disclaimer)}
    </div>
  ` : "";

  wrapper.innerHTML = `
    <div class="message-avatar">🏛️</div>
    <div class="message-bubble">
      <div class="message-header">
        <span class="sender-name">CivicAI Assistant</span>
        <span class="timestamp">${time}</span>
      </div>
      <div class="message-body">${formatMarkdown(data.answer)}</div>
      ${sourcesHTML}
      ${disclaimerHTML}
    </div>
  `;

  chatMessages.appendChild(wrapper);
  scrollToBottom();
}

function appendSystemErrorMessage(errorText) {
  const wrapper = document.createElement("div");
  wrapper.className = "message-wrapper assistant";
  wrapper.innerHTML = `
    <div class="message-avatar">⚠️</div>
    <div class="message-bubble" style="border-color: var(--error);">
      <div class="message-header">
        <span class="sender-name" style="color: var(--error);">System Error</span>
      </div>
      <div class="message-body" style="color: var(--error);">${escapeHTML(errorText)}</div>
    </div>
  `;
  chatMessages.appendChild(wrapper);
  scrollToBottom();
}

function toggleSources(btn) {
  const list = btn.nextElementSibling;
  const isHidden = list.classList.toggle("hidden");
  btn.querySelector("span:last-child").innerText = isHidden ? "▼" : "▲";
}

// Chat Form Submit
chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = messageInput.value.trim();
  if (!text) return;

  appendUserMessage(text);
  messageInput.value = "";
  messageInput.style.height = "auto";

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: "message",
      question: text,
      session_id: currentSessionId,
      token: authToken,
      language: activeLanguage
    }));
  } else {
    sendHTTPQuery(text);
  }
});

async function sendHTTPQuery(question) {
  typingIndicator.classList.remove("hidden");
  scrollToBottom();

  try {
    const headers = { "Content-Type": "application/json" };
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    const res = await fetch("/api/v1/chat/query", {
      method: "POST",
      headers,
      body: JSON.stringify({
        question,
        session_id: currentSessionId,
        language: activeLanguage
      })
    });

    const data = await res.json();
    typingIndicator.classList.add("hidden");

    if (res.ok) {
      currentSessionId = data.session_id;
      localStorage.setItem("civic_chat_session_id", currentSessionId);
      appendAssistantMessage(data);
    } else {
      appendSystemErrorMessage(data.detail || "Query failed");
    }
  } catch (err) {
    typingIndicator.classList.add("hidden");
    appendSystemErrorMessage("Failed to connect to civic backend service.");
  }
}

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event("submit"));
  }
});

quickPromptBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    switchTab("chat");
    messageInput.value = btn.getAttribute("data-query");
    chatForm.dispatchEvent(new Event("submit"));
  });
});

// ==============================================================================
// 4. Application Tracker & Timeline
// ==============================================================================
const trackRefMainInput = document.getElementById("trackRefMainInput");
const trackRefMainBtn = document.getElementById("trackRefMainBtn");
const applicationTimelineBox = document.getElementById("applicationTimelineBox");
const trackedAppDetails = document.getElementById("trackedAppDetails");
const applicationsTableBody = document.getElementById("applicationsTableBody");
const refreshAppsBtn = document.getElementById("refreshAppsBtn");

trackRefMainBtn.addEventListener("click", () => lookupApplication(trackRefMainInput.value.trim()));

async function lookupApplication(refNo) {
  if (!refNo) return;
  applicationTimelineBox.classList.remove("hidden");
  trackedAppDetails.innerHTML = `<em>Looking up reference '${escapeHTML(refNo)}'...</em>`;

  try {
    const headers = {};
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    const res = await fetch(`/api/v1/applications/ref/${encodeURIComponent(refNo)}`, { headers });
    const data = await res.json();

    if (res.ok) {
      renderApplicationTimeline(data);
    } else {
      trackedAppDetails.innerHTML = `<span style="color: var(--error);">${data.detail || "Application not found or unauthorized access."}</span>`;
      resetTimelineSteps();
    }
  } catch (err) {
    trackedAppDetails.innerHTML = `<span style="color: var(--error);">Lookup request failed.</span>`;
  }
}

function renderApplicationTimeline(app) {
  resetTimelineSteps();
  const s1 = document.getElementById("step-submitted");
  const s2 = document.getElementById("step-under_review");
  const s3 = document.getElementById("step-additional_info");
  const s4 = document.getElementById("step-decision");

  s1.querySelector(".step-node").className = "step-node completed";

  if (app.status === "under_review") {
    s2.querySelector(".step-node").className = "step-node active";
  } else if (app.status === "additional_info_required") {
    s2.querySelector(".step-node").className = "step-node completed";
    s3.querySelector(".step-node").className = "step-node active";
  } else if (app.status === "approved") {
    s2.querySelector(".step-node").className = "step-node completed";
    s4.querySelector(".step-node").className = "step-node completed";
    s4.querySelector(".step-label").innerText = "Approved ✅";
  } else if (app.status === "rejected") {
    s2.querySelector(".step-node").className = "step-node completed";
    s4.querySelector(".step-node").className = "step-node rejected";
    s4.querySelector(".step-label").innerText = "Rejected ❌";
  }

  trackedAppDetails.innerHTML = `
    <div style="font-weight: 700; font-size: 14px; color: var(--primary); margin-bottom: 4px;">
      Reference: ${app.reference_no}
    </div>
    <div>Status: <span class="badge-status status-${app.status}">${app.status}</span></div>
    <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Submitted: ${new Date(app.created_at).toLocaleString()}</div>
    ${app.officer_remarks ? `<div style="margin-top: 6px; padding: 6px 10px; background: rgba(255,255,255,0.04); border-radius: 4px; font-style: italic;">Officer Remarks: "${escapeHTML(app.officer_remarks)}"</div>` : ""}
    <div style="margin-top: 6px; font-size: 11px; font-family: var(--font-mono); color: var(--text-secondary);">Payload: ${JSON.stringify(app.payload)}</div>
  `;
}

function resetTimelineSteps() {
  ["step-submitted", "step-under_review", "step-additional_info", "step-decision"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.querySelector(".step-node").className = "step-node";
  });
}

async function loadApplications() {
  applicationsTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">Fetching applications...</td></tr>`;
  try {
    const headers = {};
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    const res = await fetch("/api/v1/applications/", { headers });
    const data = await res.json();

    if (res.ok && Array.isArray(data)) {
      if (data.length === 0) {
        applicationsTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No applications found for this account. Click "Apply Service" to submit one.</td></tr>`;
        return;
      }
      applicationsTableBody.innerHTML = data.map(app => `
        <tr>
          <td><strong style="color: var(--primary); cursor: pointer;" onclick="document.getElementById('trackRefMainInput').value='${app.reference_no}'; lookupApplication('${app.reference_no}');">${app.reference_no}</strong></td>
          <td>Service #${app.service_id}</td>
          <td><span class="badge-status status-${app.status}">${app.status}</span></td>
          <td>${new Date(app.created_at).toLocaleDateString()}</td>
          <td>${escapeHTML(app.officer_remarks || "—")}</td>
        </tr>
      `).join("");
    } else {
      applicationsTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--error);">Failed to load applications (${data.detail || res.status})</td></tr>`;
    }
  } catch (err) {
    applicationsTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--error);">Network error.</td></tr>`;
  }
}
refreshAppsBtn.addEventListener("click", loadApplications);

// ==============================================================================
// 5. Grievances Management
// ==============================================================================
const grievancesTableBody = document.getElementById("grievancesTableBody");
const refreshGrievancesBtn = document.getElementById("refreshGrievancesBtn");

async function loadGrievances() {
  grievancesTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Fetching grievances...</td></tr>`;
  try {
    const headers = {};
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    const res = await fetch("/api/v1/grievances/", { headers });
    const data = await res.json();

    if (res.ok && Array.isArray(data)) {
      if (data.length === 0) {
        grievancesTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No grievances registered. Click "File Grievance" to lodge one.</td></tr>`;
        return;
      }
      grievancesTableBody.innerHTML = data.map(g => `
        <tr>
          <td><strong>#${g.id}</strong></td>
          <td>Dept #${g.department_id}</td>
          <td><strong>${escapeHTML(g.subject)}</strong><br><small style="color: var(--text-muted);">${escapeHTML(g.details.slice(0, 60))}...</small></td>
          <td><span class="badge-status status-${g.status}">${g.status}</span></td>
          <td>${new Date(g.created_at).toLocaleDateString()}</td>
          <td>${escapeHTML(g.response || "Pending review")}</td>
        </tr>
      `).join("");
    } else {
      grievancesTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--error);">Failed to load grievances (${data.detail || res.status})</td></tr>`;
    }
  } catch (err) {
    grievancesTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--error);">Network error.</td></tr>`;
  }
}
refreshGrievancesBtn.addEventListener("click", loadGrievances);

// ==============================================================================
// 6. Service Catalogue Explorer
// ==============================================================================
const servicesContainer = document.getElementById("servicesContainer");
const serviceSearchInput = document.getElementById("serviceSearchInput");
const loadServicesBtn = document.getElementById("loadServicesBtn");

async function loadServices() {
  servicesContainer.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted);">Loading catalogue...</div>`;
  const query = serviceSearchInput.value.trim();
  const url = query ? `/api/v1/services/?search=${encodeURIComponent(query)}` : "/api/v1/services/";

  try {
    const res = await fetch(url);
    const data = await res.json();

    if (res.ok && Array.isArray(data)) {
      cachedServices = data;
      populateApplyServiceDropdown(data);

      if (data.length === 0) {
        servicesContainer.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted);">No services matched your search.</div>`;
        return;
      }

      servicesContainer.innerHTML = data.map(srv => {
        const reqDocs = srv.requirements?.required_documents || ["Standard Municipal Form"];
        return `
          <div class="service-card">
            <div class="service-header">
              <div>
                <div class="service-title">${escapeHTML(srv.name)}</div>
                <div style="font-size: 11px; color: var(--text-muted);">${srv.code}</div>
              </div>
              <span class="service-sla">SLA: ${srv.processing_time_days} Days</span>
            </div>
            <p class="service-desc">${escapeHTML(srv.description || "Public civic service.")}</p>
            <div class="service-reqs">
              <strong style="color: var(--primary); font-size: 11px;">Mandatory Documents:</strong>
              <ul>
                ${reqDocs.map(d => `<li>${escapeHTML(d)}</li>`).join("")}
              </ul>
            </div>
            <div style="display: flex; gap: 8px; margin-top: auto;">
              <button class="btn btn-primary btn-sm" onclick="openApplyForService(${srv.id})" style="flex: 1;">Apply Online</button>
              <button class="btn btn-ghost btn-sm" onclick="askAboutService('${escapeHTML(srv.name)}')">Ask AI</button>
            </div>
          </div>
        `;
      }).join("");
    }
  } catch (err) {
    servicesContainer.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--error);">Error loading service catalogue.</div>`;
  }
}
loadServicesBtn.addEventListener("click", loadServices);
serviceSearchInput.addEventListener("keydown", (e) => { if (e.key === "Enter") loadServices(); });

function askAboutService(serviceName) {
  switchTab("chat");
  messageInput.value = `What are the required documents and procedure for ${serviceName}?`;
  chatForm.dispatchEvent(new Event("submit"));
}

function openApplyForService(serviceId) {
  document.getElementById("applyServiceSelect").value = serviceId;
  openModal("applyModal");
}

// ==============================================================================
// 7. Officer SLA Dashboard & Status Update Tool
// ==============================================================================
const slaTotalServices = document.getElementById("slaTotalServices");
const slaTotalApps = document.getElementById("slaTotalApps");
const slaAppRate = document.getElementById("slaAppRate");
const slaTotalGrievances = document.getElementById("slaTotalGrievances");
const slaGrievanceRate = document.getElementById("slaGrievanceRate");
const officerAppIdInput = document.getElementById("officerAppIdInput");
const officerNewStatusSelect = document.getElementById("officerNewStatusSelect");
const officerRemarksInput = document.getElementById("officerRemarksInput");
const officerUpdateStatusBtn = document.getElementById("officerUpdateStatusBtn");
const officerActionStatusBox = document.getElementById("officerActionStatusBox");

async function loadSlaMetrics() {
  try {
    const headers = {};
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    const res = await fetch("/api/v1/services/stats/sla-dashboard", { headers });
    if (res.ok) {
      const data = await res.json();
      slaTotalServices.innerText = data.total_services;
      slaTotalApps.innerText = data.total_applications;
      slaAppRate.innerText = `${data.application_resolution_rate_pct}% Processed`;
      slaTotalGrievances.innerText = data.total_grievances;
      slaGrievanceRate.innerText = `${data.grievance_resolution_rate_pct}% Redressed`;
    }
  } catch (err) {
    console.error("SLA fetch error:", err);
  }
}

officerUpdateStatusBtn.addEventListener("click", async () => {
  const appId = officerAppIdInput.value.trim();
  const status = officerNewStatusSelect.value;
  const remarks = officerRemarksInput.value.trim();
  if (!appId) return;

  officerActionStatusBox.classList.remove("hidden");
  officerActionStatusBox.innerHTML = `<em>Updating application #${appId} to '${status}'...</em>`;

  try {
    const headers = { "Content-Type": "application/json" };
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    const res = await fetch(`/api/v1/applications/${appId}/status`, {
      method: "PUT",
      headers,
      body: JSON.stringify({ status, officer_remarks: remarks })
    });

    const data = await res.json();
    if (res.ok) {
      officerActionStatusBox.innerHTML = `
        <span style="color: var(--success); font-weight: 700;">✅ Success:</span> Application #${data.id} (${data.reference_no}) updated to <strong>${data.status}</strong>.
      `;
      loadSlaMetrics();
    } else {
      officerActionStatusBox.innerHTML = `
        <span style="color: var(--error); font-weight: 700;">❌ Error (${res.status}):</span> ${data.detail || "Permission denied"}
      `;
    }
  } catch (err) {
    officerActionStatusBox.innerHTML = `<span style="color: var(--error);">Update failed.</span>`;
  }
});

// ==============================================================================
// 8. Notifications / Activity Feed
// ==============================================================================
const notificationsList = document.getElementById("notificationsList");
const refreshNotifsBtn = document.getElementById("refreshNotifsBtn");

async function loadNotifications() {
  notificationsList.innerHTML = `<div style="color: var(--text-muted); font-size: 13px;">Loading notifications...</div>`;
  try {
    const headers = {};
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    const res = await fetch("/api/v1/notifications/me", { headers });
    const data = await res.json();

    if (res.ok && Array.isArray(data)) {
      if (data.length === 0) {
        notificationsList.innerHTML = `<div style="color: var(--text-muted); font-size: 13px;">No notifications yet. Perform submissions to generate timeline alerts.</div>`;
        return;
      }
      notificationsList.innerHTML = data.map(n => `
        <div class="track-result-box" style="display: flex; justify-content: space-between; align-items: flex-start;">
          <div>
            <strong style="color: var(--primary);">${escapeHTML(n.title)}</strong>
            <p style="margin-top: 2px;">${escapeHTML(n.message)}</p>
            <small style="color: var(--text-muted);">${new Date(n.created_at).toLocaleString()}</small>
          </div>
          <span class="badge ${n.is_read ? 'badge-ghost' : 'badge-gov'}">${n.is_read ? 'Read' : 'New'}</span>
        </div>
      `).join("");
    } else {
      notificationsList.innerHTML = `<div style="color: var(--text-muted); font-size: 13px;">Log in to view user notifications.</div>`;
    }
  } catch (err) {
    notificationsList.innerHTML = `<div style="color: var(--error); font-size: 13px;">Failed to fetch notifications.</div>`;
  }
}
refreshNotifsBtn.addEventListener("click", loadNotifications);

// ==============================================================================
// 9. Modals & Submission Forms
// ==============================================================================
const openApplyModalBtn = document.getElementById("openApplyModalBtn");
const openGrievanceModalBtn = document.getElementById("openGrievanceModalBtn");
const applyForm = document.getElementById("applyForm");
const grievanceForm = document.getElementById("grievanceForm");
const applyServiceSelect = document.getElementById("applyServiceSelect");
const grievanceDeptSelect = document.getElementById("grievanceDeptSelect");

openApplyModalBtn.addEventListener("click", () => openModal("applyModal"));
openGrievanceModalBtn.addEventListener("click", () => openModal("grievanceModal"));

function openModal(id) {
  document.getElementById(id).classList.remove("hidden");
  loadDropdownOptions();
}

function closeModal(id) {
  document.getElementById(id).classList.add("hidden");
}

async function loadDropdownOptions() {
  // Load departments
  if (cachedDepartments.length === 0) {
    try {
      const res = await fetch("/api/v1/departments/");
      if (res.ok) {
        cachedDepartments = await res.json();
        grievanceDeptSelect.innerHTML = cachedDepartments.map(d => `<option value="${d.id}">${escapeHTML(d.name)} (${d.code})</option>`).join("");
      }
    } catch (e) {}
  }
  // Load services
  if (cachedServices.length === 0) {
    try {
      const res = await fetch("/api/v1/services/");
      if (res.ok) {
        cachedServices = await res.json();
        populateApplyServiceDropdown(cachedServices);
      }
    } catch (e) {}
  }
}

function populateApplyServiceDropdown(services) {
  applyServiceSelect.innerHTML = services.map(s => `<option value="${s.id}">${escapeHTML(s.name)} (${s.code})</option>`).join("");
}

applyForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const serviceId = parseInt(applyServiceSelect.value);
  const applicantName = document.getElementById("applyApplicantName").value.trim();
  const propertyId = document.getElementById("applyPropertyId").value.trim();
  const docs = document.getElementById("applyDocsPayload").value.trim();

  try {
    const headers = { "Content-Type": "application/json" };
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    const res = await fetch("/api/v1/applications/", {
      method: "POST",
      headers,
      body: JSON.stringify({
        service_id: serviceId,
        payload: { applicant_name: applicantName, property_id: propertyId, attached_documents: docs }
      })
    });

    const data = await res.json();
    if (res.ok) {
      closeModal("applyModal");
      switchTab("applications");
      trackRefMainInput.value = data.reference_no;
      lookupApplication(data.reference_no);
      loadApplications();
    } else {
      alert(`Submission error: ${data.detail || "Failed"}`);
    }
  } catch (err) {
    alert("Application submission failed.");
  }
});

grievanceForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const deptId = parseInt(grievanceDeptSelect.value);
  const subject = document.getElementById("grievanceSubject").value.trim();
  const details = document.getElementById("grievanceDetails").value.trim();

  try {
    const headers = { "Content-Type": "application/json" };
    if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

    const res = await fetch("/api/v1/grievances/", {
      method: "POST",
      headers,
      body: JSON.stringify({ department_id: deptId, subject, details })
    });

    const data = await res.json();
    if (res.ok) {
      closeModal("grievanceModal");
      switchTab("grievances");
      loadGrievances();
    } else {
      alert(`Grievance error: ${data.detail || "Failed"}`);
    }
  } catch (err) {
    alert("Grievance submission failed.");
  }
});

// ==============================================================================
// Utilities
// ==============================================================================
function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHTML(str) {
  if (!str) return "";
  return str.replace(/[&<>'"]/g, tag => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  }[tag] || tag));
}

function formatMarkdown(text) {
  if (!text) return "";
  let formatted = escapeHTML(text);
  // Bold
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Lists
  formatted = formatted.replace(/^- (.*)$/gim, '<li>$1</li>');
  formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul style="padding-left: 18px; margin: 6px 0;">$1</ul>');
  return formatted;
}

// Initial Boot on Load
window.addEventListener("DOMContentLoaded", async () => {
  await switchRole("citizen");
  initWebSocket();
  loadServices();
  loadDropdownOptions();
});
