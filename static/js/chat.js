let currentConversationId = null;
let currentSelectedDocId = null;

function initChat(initialConvId) {
    loadConversations(initialConvId);
    loadDocumentFilterOptions();
}

// 1. Load Conversations List
function loadConversations(selectConvId) {
    fetch('/api/conversations')
        .then(res => res.json())
        .then(conversations => {
            const listEl = document.getElementById('conversationsList');
            listEl.innerHTML = '';

            if (conversations.length === 0) {
                listEl.innerHTML = '<div class="p-3 text-muted small text-center">No conversation history.</div>';
                startNewConversation();
                return;
            }

            conversations.forEach(c => {
                const item = document.createElement('div');
                item.className = `chat-history-item ${c.id === selectConvId ? 'active' : ''}`;
                item.id = `conv-item-${c.id}`;
                item.onclick = (e) => {
                    if (e.target.closest('.delete-conv-btn')) return;
                    selectConversation(c.id);
                };

                item.innerHTML = `
                    <div class="d-flex align-items-center text-truncate" style="max-width: 200px;">
                        <i class="bi bi-chat-text me-2"></i>
                        <span class="text-truncate">${c.title}</span>
                    </div>
                    <button class="btn btn-sm text-danger p-0 delete-conv-btn opacity-50 hover-opacity-100" onclick="deleteConversation(${c.id}, event)" title="Delete Chat">
                        <i class="bi bi-trash3"></i>
                    </button>
                `;
                listEl.appendChild(item);
            });

            const targetId = selectConvId || (conversations.length > 0 ? conversations[0].id : null);
            if (targetId) {
                selectConversation(targetId);
            }
        });
}

// 2. Select a Conversation
function selectConversation(convId) {
    currentConversationId = convId;
    document.querySelectorAll('.chat-history-item').forEach(el => el.classList.remove('active'));
    const activeItem = document.getElementById(`conv-item-${convId}`);
    if (activeItem) activeItem.classList.add('active');

    fetch(`/api/conversations/${convId}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('currentChatTitle').textContent = data.conversation.title || 'Document Q&A';
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.innerHTML = '';

            if (!data.messages || data.messages.length === 0) {
                renderWelcomeMessage();
                return;
            }

            data.messages.forEach(m => {
                appendMessageToUI(m.role, m.content, m.sources, false);
            });
            scrollToBottom();
        });
}

// 3. Start New Conversation
function startNewConversation() {
    currentConversationId = null;
    document.querySelectorAll('.chat-history-item').forEach(el => el.classList.remove('active'));
    document.getElementById('currentChatTitle').textContent = 'New Document Q&A';
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = '';
    renderWelcomeMessage();
    document.getElementById('chatInput').focus();
}

function renderWelcomeMessage() {
    const messagesContainer = document.getElementById('chatMessages');
    const welcomeHtml = `
        <div class="message-row assistant">
            <div class="message-avatar"><i class="bi bi-robot"></i></div>
            <div class="message-bubble shadow-sm">
                <h5 class="fw-bold mb-2">Hello! How can I assist you with your documents?</h5>
                <p class="text-muted mb-0">I am your Academic RAG Assistant. Ask me anything about the uploaded PDF files and I will retrieve accurate answers with verified page references.</p>
            </div>
        </div>
    `;
    messagesContainer.innerHTML = welcomeHtml;
}

// 4. Handle Chat Submission
function handleChatSubmit(e) {
    e.preventDefault();
    const inputEl = document.getElementById('chatInput');
    const message = inputEl.value.trim();
    if (!message) return;

    inputEl.value = '';
    sendChatMessage(message);
}

function sendQuickPrompt(promptText) {
    sendChatMessage(promptText);
}

function sendChatMessage(message) {
    // Render user message immediately
    appendMessageToUI('user', message, [], true);
    scrollToBottom();

    // Render loading indicator
    const loadingId = 'loading-' + Date.now();
    const messagesContainer = document.getElementById('chatMessages');
    const loadingRow = document.createElement('div');
    loadingRow.className = 'message-row assistant';
    loadingRow.id = loadingId;
    loadingRow.innerHTML = `
        <div class="message-avatar"><i class="bi bi-robot"></i></div>
        <div class="message-bubble bg-light border d-flex align-items-center gap-2">
            <div class="spinner-grow spinner-grow-sm text-primary" role="status"></div>
            <span class="text-muted small fw-semibold">Searching FAISS index & generating grounded answer...</span>
        </div>
    `;
    messagesContainer.appendChild(loadingRow);
    scrollToBottom();

    // API Call
    const payload = {
        message: message,
        conversation_id: currentConversationId,
        document_ids: currentSelectedDocId ? [currentSelectedDocId] : null
    };

    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();

        if (data.error) {
            appendMessageToUI('assistant', `⚠️ **Error:** ${data.error}`, [], true);
            return;
        }

        // If conversation was new, reload sidebar
        if (!currentConversationId || currentConversationId !== data.conversation_id) {
            currentConversationId = data.conversation_id;
            loadConversations(currentConversationId);
        }

        appendMessageToUI('assistant', data.answer, data.sources, true);
        scrollToBottom();
    })
    .catch(err => {
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();
        appendMessageToUI('assistant', `⚠️ **Network Error:** Could not connect to RAG server. (${err})`, [], true);
    });
}

// 5. Append Message to UI
function appendMessageToUI(role, content, sources, animate) {
    const messagesContainer = document.getElementById('chatMessages');
    const row = document.createElement('div');
    row.className = `message-row ${role}`;

    const avatarHtml = role === 'user'
        ? '<div class="message-avatar"><i class="bi bi-person-fill"></i></div>'
        : '<div class="message-avatar"><i class="bi bi-robot"></i></div>';

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        const sourceItems = sources.map((s, idx) => `
            <div class="source-card">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="source-badge"><i class="bi bi-file-pdf me-1"></i>${s.filename} &bull; Page ${s.page}</span>
                    ${s.score ? `<small class="text-muted">Relevance Dist: ${s.score}</small>` : ''}
                </div>
                <div class="text-muted small">${s.snippet || ''}</div>
            </div>
        `).join('');

        sourcesHtml = `
            <div class="mt-3 pt-2 border-top">
                <div class="fw-bold small text-muted text-uppercase mb-2" style="font-size: 0.72rem; letter-spacing: 0.05em;">
                    <i class="bi bi-bookmark-check-fill text-primary me-1"></i> Verified Citations & Sources (${sources.length})
                </div>
                ${sourceItems}
            </div>
        `;
    }

    const copyBtnHtml = role === 'assistant'
        ? `<button class="btn btn-sm btn-link text-muted p-0 ms-auto text-decoration-none" onclick="copyToClipboard(this, \`${content.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`)" title="Copy Answer">
                <i class="bi bi-clipboard me-1"></i> Copy
           </button>`
        : '';

    row.innerHTML = `
        ${avatarHtml}
        <div class="message-bubble shadow-sm" style="max-width: 100%;">
            <div class="d-flex align-items-center justify-content-between mb-1">
                <small class="fw-bold text-uppercase" style="font-size: 0.72rem; letter-spacing: 0.05em; opacity: 0.8;">
                    ${role === 'user' ? 'You' : 'Academic RAG Assistant'}
                </small>
                ${copyBtnHtml}
            </div>
            <div class="message-text">${formatMarkdown(content)}</div>
            ${sourcesHtml}
        </div>
    `;

    messagesContainer.appendChild(row);
}

// 6. Delete Conversation
function deleteConversation(convId, e) {
    if (e) e.stopPropagation();
    if (!confirm('Are you sure you want to delete this conversation?')) return;

    fetch(`/api/conversations/${convId}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(() => {
            loadConversations(null);
        });
}

function clearCurrentChat() {
    if (currentConversationId) {
        deleteConversation(currentConversationId);
    } else {
        startNewConversation();
    }
}

// 7. Document Filter Options
function loadDocumentFilterOptions() {
    fetch('/api/documents')
        .then(res => res.json())
        .then(docs => {
            const menu = document.getElementById('docFilterMenu');
            menu.innerHTML = `
                <li><a class="dropdown-item active" href="javascript:void(0)" onclick="selectDocFilter(null, 'All Documents')">All Uploaded Documents</a></li>
                <li><hr class="dropdown-divider"></li>
            `;
            docs.forEach(d => {
                const li = document.createElement('li');
                li.innerHTML = `<a class="dropdown-item text-truncate" href="javascript:void(0)" onclick="selectDocFilter(${d.id}, '${d.filename}')"><i class="bi bi-file-pdf text-danger me-2"></i>${d.filename}</a>`;
                menu.appendChild(li);
            });
        });
}

function selectDocFilter(docId, label) {
    currentSelectedDocId = docId;
    document.getElementById('selectedDocLabel').textContent = label;
}

function scrollToBottom() {
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
