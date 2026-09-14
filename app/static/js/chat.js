/**
 * CivicAI - Grounded AI Civic Chatbot Controller (Vanilla JS + WebSocket)
 */

let ws = null;
let currentSessionId = 'session_' + Math.random().toString(36).substring(2, 9);
let isConnected = false;
let isTyping = false;

document.addEventListener('DOMContentLoaded', () => {
  initChatBot();
});

function initChatBot() {
  connectWebSocket();

  // Send message on form submit
  const form = document.getElementById('chatInputForm');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      sendUserMessage();
    });
  }

  // Quick Prompt buttons
  document.querySelectorAll('.quick-prompt-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const query = btn.getAttribute('data-query');
      if (query) {
        document.getElementById('chatInputField').value = query;
        sendUserMessage();
      }
    });
  });

  // Enter to send
  const input = document.getElementById('chatInputField');
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendUserMessage();
      }
    });
  }
}

// Connect WebSocket with Automatic Fallback & Reconnect
function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/chat`;
  const statusDot = document.getElementById('wsStatusDot');
  const statusText = document.getElementById('wsStatusText');

  if (statusText) statusText.innerText = 'Connecting...';
  if (statusDot) statusDot.className = 'dot dot-connecting';

  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      isConnected = true;
      if (statusText) statusText.innerText = 'WebSocket Live';
      if (statusDot) statusDot.className = 'dot dot-connected';
      console.log('WebSocket connected to Civic Assistant');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleIncomingMessage(data);
      } catch (err) {
        console.error('Error parsing WebSocket message', err);
      }
    };

    ws.onclose = () => {
      isConnected = false;
      if (statusText) statusText.innerText = 'HTTP Fallback Mode';
      if (statusDot) statusDot.className = 'dot dot-disconnected';
      console.warn('WebSocket disconnected. Fallback to HTTP RAG endpoint.');
    };

    ws.onerror = (err) => {
      console.warn('WebSocket encountered error, falling back to HTTP', err);
    };

  } catch (err) {
    isConnected = false;
    if (statusText) statusText.innerText = 'HTTP Mode';
  }
}

// Send Message
async function sendUserMessage() {
  const input = document.getElementById('chatInputField');
  const question = input.value.trim();
  if (!question || isTyping) return;

  // Clear input
  input.value = '';
  
  // Render user message bubble
  appendMessageBubble('user', question);
  showTypingIndicator();

  const token = api.getToken();

  // Try WebSocket First
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'message',
      question: question,
      session_id: currentSessionId,
      token: token || null
    }));
  } else {
    // Fallback to HTTP RAG Endpoint
    try {
      const res = await api.post('/chat/query', {
        question: question,
        session_id: currentSessionId
      });

      hideTypingIndicator();
      renderAssistantResponse(res);
    } catch (err) {
      hideTypingIndicator();
      appendMessageBubble('error', 'Unable to process inquiry: ' + err.message);
    }
  }
}

// Handle Incoming WS Message
function handleIncomingMessage(data) {
  if (data.type === 'connected') {
    return;
  }

  if (data.type === 'typing') {
    showTypingIndicator();
    return;
  }

  if (data.type === 'answer') {
    hideTypingIndicator();
    renderAssistantResponse(data);
    return;
  }

  if (data.type === 'error') {
    hideTypingIndicator();
    appendMessageBubble('error', data.error || 'Failed to generate answer.');
    return;
  }
}

// Render Structured Assistant Response with Sources & Disclaimer
function renderAssistantResponse(data) {
  const chatArea = document.getElementById('chatMessagesArea');
  if (!chatArea) return;

  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-message-row assistant-row';

  let sourcesHtml = '';
  if (data.sources && Array.isArray(data.sources) && data.sources.length > 0) {
    sourcesHtml = `
      <div class="chat-sources-box">
        <div class="chat-sources-header">📚 Grounded Document Sources:</div>
        <div class="chat-sources-list">
          ${data.sources.map(s => `
            <div class="chat-source-item">
              <span class="source-icon">📄</span>
              <div style="flex: 1;">
                <strong>${escapeHtml(s.document_title || s.title || 'Civic Document')}</strong>
                <span style="font-size: 11px; color: #64748b; margin-left: 6px;">(Page ${s.page_number || 1}, Chunk #${s.chunk_index !== undefined ? s.chunk_index + 1 : (s.chunk_id || '1')})</span>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  const disclaimerText = data.disclaimer || 
    'This information is based on approved indexed sample documents and does not guarantee eligibility, approval, legal outcome or statutory processing time.';

  msgDiv.innerHTML = `
    <div class="chat-bubble assistant-bubble">
      <div class="bubble-header">
        <span class="assistant-avatar">🏛️</span>
        <strong>Civic AI Assistant</strong>
      </div>
      <div class="bubble-content">
        ${formatMarkdownText(data.answer)}
      </div>
      ${sourcesHtml}
      <div class="chat-disclaimer-box">
        <span class="disclaimer-icon">🛡️</span>
        <div class="disclaimer-text">
          <strong>Compliance Disclaimer:</strong> ${escapeHtml(disclaimerText)}
        </div>
      </div>
    </div>
  `;

  chatArea.appendChild(msgDiv);
  scrollChatToBottom();
}

// Append Simple User or Error Bubble
function appendMessageBubble(type, text) {
  const chatArea = document.getElementById('chatMessagesArea');
  if (!chatArea) return;

  const row = document.createElement('div');
  row.className = `chat-message-row ${type}-row`;

  if (type === 'user') {
    row.innerHTML = `
      <div class="chat-bubble user-bubble">
        <div class="bubble-content">${escapeHtml(text)}</div>
      </div>
    `;
  } else if (type === 'error') {
    row.innerHTML = `
      <div class="chat-bubble error-bubble">
        <div class="bubble-content">⚠️ ${escapeHtml(text)}</div>
      </div>
    `;
  }

  chatArea.appendChild(row);
  scrollChatToBottom();
}

// Typing Indicator
function showTypingIndicator() {
  if (isTyping) return;
  isTyping = true;

  const chatArea = document.getElementById('chatMessagesArea');
  if (!chatArea) return;

  let indicator = document.getElementById('typingIndicator');
  if (!indicator) {
    indicator = document.createElement('div');
    indicator.id = 'typingIndicator';
    indicator.className = 'chat-message-row assistant-row typing-row';
    indicator.innerHTML = `
      <div class="chat-bubble assistant-bubble typing-bubble">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    `;
    chatArea.appendChild(indicator);
  }
  indicator.style.display = 'flex';
  scrollChatToBottom();
}

function hideTypingIndicator() {
  isTyping = false;
  const indicator = document.getElementById('typingIndicator');
  if (indicator) {
    indicator.remove();
  }
}

function scrollChatToBottom() {
  const chatArea = document.getElementById('chatMessagesArea');
  if (chatArea) {
    chatArea.scrollTop = chatArea.scrollHeight;
  }
}

function clearChatHistory() {
  const chatArea = document.getElementById('chatMessagesArea');
  if (chatArea) {
    chatArea.innerHTML = `
      <div class="chat-welcome-card">
        <div class="welcome-icon">🏛️</div>
        <h2>Grounded Civic Assistant</h2>
        <p>Ask questions regarding sample civic procedures, mandatory document requirements, and department guidelines. All responses are strictly grounded in approved municipal documents.</p>
      </div>
    `;
    currentSessionId = 'session_' + Math.random().toString(36).substring(2, 9);
    showToast('Conversation cleared.', 'info');
  }
}

// Enhanced markdown format helper (bold, italic, headers, tables, code blocks, lists)
function formatMarkdownText(text) {
  if (!text) return '';
  let formatted = escapeHtml(text);

  // Inline Code `code`
  formatted = formatted.replace(/`([^`]+)`/g, '<code class="chat-code">$1</code>');

  // Bold **text**
  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Italic *text*
  formatted = formatted.replace(/(^|[^\*])\*([^\*]+)\*([^\*]|$)/g, '$1<em>$2</em>$3');

  // Headers ###, ##, #
  formatted = formatted.replace(/^###\s*(.*)$/gm, '<h4 class="chat-h4">$1</h4>');
  formatted = formatted.replace(/^##\s*(.*)$/gm, '<h3 class="chat-h3">$1</h3>');
  formatted = formatted.replace(/^#\s*(.*)$/gm, '<h2 class="chat-h2">$1</h2>');

  // Handle tables and list structures
  const lines = formatted.split('\n');
  let inList = false;
  let inTable = false;
  let tableRows = [];
  let result = [];

  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();

    // Table line: | ... |
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      if (inList) { result.push('</ul>'); inList = false; }
      // Skip separator row: |---|---|
      if (/^\|(\s*[-:]+\s*\|)+$/.test(trimmed)) {
        continue;
      }
      if (!inTable) {
        inTable = true;
        tableRows = [];
      }
      const cells = trimmed.split('|').slice(1, -1).map(c => c.trim());
      tableRows.push(cells);
      continue;
    } else if (inTable) {
      result.push('<table class="chat-table">');
      if (tableRows.length > 0) {
        result.push('<thead><tr>' + tableRows[0].map(c => `<th>${c}</th>`).join('') + '</tr></thead>');
        result.push('<tbody>');
        for (let r = 1; r < tableRows.length; r++) {
          result.push('<tr>' + tableRows[r].map(c => `<td>${c}</td>`).join('') + '</tr>');
        }
        result.push('</tbody>');
      }
      result.push('</table>');
      inTable = false;
      tableRows = [];
    }

    if (trimmed.startsWith('* ') || trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
      if (!inList) {
        result.push('<ul class="chat-ul">');
        inList = true;
      }
      result.push(`<li>${trimmed.substring(2)}</li>`);
    } else if (/^\d+\.\s+/.test(trimmed)) {
      if (!inList) {
        result.push('<ol class="chat-ol">');
        inList = true;
      }
      result.push(`<li>${trimmed.replace(/^\d+\.\s+/, '')}</li>`);
    } else {
      if (inList) {
        result.push('</ul>');
        inList = false;
      }
      if (trimmed.startsWith('<h2') || trimmed.startsWith('<h3') || trimmed.startsWith('<h4')) {
        result.push(trimmed);
      } else if (trimmed.length > 0) {
        result.push(`<p class="chat-p">${trimmed}</p>`);
      }
    }
  }

  if (inList) result.push('</ul>');
  if (inTable && tableRows.length > 0) {
    result.push('<table class="chat-table">');
    result.push('<thead><tr>' + tableRows[0].map(c => `<th>${c}</th>`).join('') + '</tr></thead>');
    result.push('<tbody>');
    for (let r = 1; r < tableRows.length; r++) {
      result.push('<tr>' + tableRows[r].map(c => `<td>${c}</td>`).join('') + '</tr>');
    }
    result.push('</tbody></table>');
  }

  return result.join('');
}
