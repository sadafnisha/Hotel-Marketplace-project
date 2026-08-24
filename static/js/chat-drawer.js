/**
 * Floating chat drawer. Talks to the existing DRF endpoints:
 *   GET  /api/conversations/            -> inbox list (+ unread_count, last_message)
 *   GET  /api/conversations/<id>/       -> thread detail (marks unread as read)
 *   POST /api/conversations/<id>/messages/  {body}
 *
 * No new backend code needed -- this is purely a nicer client for the
 * conversation/message schema that already exists.
 */
(function () {
    const fab = document.getElementById('chatDrawerToggle');
    const drawer = document.getElementById('chatDrawer');
    if (!fab || !drawer) return;

    const listPane = document.getElementById('chatDrawerList');
    const threadPane = document.getElementById('chatDrawerThread');
    const listBody = document.getElementById('chatDrawerConversations');
    const messagesBody = document.getElementById('chatDrawerMessages');
    const threadName = document.getElementById('chatDrawerThreadName');
    const threadListing = document.getElementById('chatDrawerThreadListing');
    const form = document.getElementById('chatDrawerForm');
    const input = document.getElementById('chatDrawerInput');
    const badge = document.getElementById('chatDrawerBadge');

    const currentUserId = window.CURRENT_USER_ID;
    let activeConversationId = null;
    let listPollTimer = null;
    let threadPollTimer = null;

    function open() {
        drawer.classList.add('open');
        drawer.setAttribute('aria-hidden', 'false');
        loadConversationList();
        listPollTimer = setInterval(loadConversationList, 15000);
    }

    function close() {
        drawer.classList.remove('open');
        drawer.setAttribute('aria-hidden', 'true');
        clearInterval(listPollTimer);
        clearInterval(threadPollTimer);
    }

    function showList() {
        activeConversationId = null;
        clearInterval(threadPollTimer);
        threadPane.classList.add('d-none');
        listPane.classList.remove('d-none');
        loadConversationList();
    }

    function showThread(id) {
        activeConversationId = id;
        listPane.classList.add('d-none');
        threadPane.classList.remove('d-none');
        loadThread(id);
        clearInterval(threadPollTimer);
        threadPollTimer = setInterval(() => loadThread(id, { silent: true }), 4000);
    }

    function otherPartyName(conv) {
        const other = conv.buyer.id === currentUserId ? conv.owner : conv.buyer;
        return other.username;
    }

    async function loadConversationList() {
        try {
            const data = await apiRequest('/api/conversations/');
            const conversations = data.results || data;
            renderList(conversations);
            const totalUnread = conversations.reduce((sum, c) => sum + (c.unread_count || 0), 0);
            updateBadge(totalUnread);
        } catch (err) {
            listBody.innerHTML = `<div class="chat-drawer-empty text-muted small">Couldn't load messages.</div>`;
        }
    }

    function renderList(conversations) {
        if (!conversations.length) {
            listBody.innerHTML = `<div class="chat-drawer-empty text-muted small">No conversations yet.</div>`;
            return;
        }
        listBody.innerHTML = conversations.map((c) => `
            <button type="button" class="chat-drawer-conv-item" data-conv-id="${c.id}">
                <div class="chat-drawer-conv-top">
                    <span class="fw-semibold">${escapeHtml(otherPartyName(c))}</span>
                    ${c.unread_count ? `<span class="chat-drawer-unread">${c.unread_count}</span>` : ''}
                </div>
                <div class="chat-drawer-conv-listing text-truncate">${escapeHtml(c.listing_detail ? c.listing_detail.title : '')}</div>
                <div class="chat-drawer-conv-last text-truncate text-muted">${c.last_message ? escapeHtml(c.last_message.body) : 'No messages yet'}</div>
            </button>
        `).join('');
        listBody.querySelectorAll('[data-conv-id]').forEach((btn) => {
            btn.addEventListener('click', () => showThread(btn.dataset.convId));
        });
    }

    async function loadThread(id, { silent = false } = {}) {
        try {
            const conv = await apiRequest(`/api/conversations/${id}/`);
            threadName.textContent = otherPartyName(conv);
            threadListing.textContent = conv.listing_detail ? conv.listing_detail.title : '';
            renderMessages(conv.messages);
            loadConversationList(); // keep the badge/list in sync as reads happen
        } catch (err) {
            if (!silent) messagesBody.innerHTML = `<div class="chat-drawer-empty text-muted small">Couldn't load this conversation.</div>`;
        }
    }

    function renderMessages(messages) {
        const wasAtBottom = messagesBody.scrollTop + messagesBody.clientHeight >= messagesBody.scrollHeight - 20;
        messagesBody.innerHTML = messages.map((m) => `
            <div class="chat-bubble-row ${m.sender.id === currentUserId ? 'is-self' : ''}">
                <div class="chat-bubble">
                    ${m.sender.id !== currentUserId ? `<div class="chat-bubble-sender">${escapeHtml(m.sender.username)}</div>` : ''}
                    <div>${escapeHtml(m.body)}</div>
                    <div class="chat-bubble-time">${formatTime(m.created_at)}</div>
                </div>
            </div>
        `).join('');
        if (wasAtBottom || messages.length <= 1) {
            messagesBody.scrollTop = messagesBody.scrollHeight;
        }
    }

    function updateBadge(count) {
        if (count > 0) {
            badge.textContent = count > 9 ? '9+' : count;
            badge.classList.remove('d-none');
        } else {
            badge.classList.add('d-none');
        }
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    }

    function formatTime(iso) {
        const d = new Date(iso);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const body = input.value.trim();
        if (!body || !activeConversationId) return;
        input.value = '';
        input.disabled = true;
        try {
            await apiRequest(`/api/conversations/${activeConversationId}/messages/`, {
                method: 'POST',
                body: { body },
            });
            await loadThread(activeConversationId, { silent: true });
        } catch (err) {
            showToast(err.message || 'Message failed to send.', 'error');
            input.value = body;
        } finally {
            input.disabled = false;
            input.focus();
        }
    });

    fab.addEventListener('click', () => (drawer.classList.contains('open') ? close() : open()));
    drawer.addEventListener('click', (e) => {
        if (e.target.closest('[data-close-drawer]')) close();
        if (e.target.closest('[data-back-to-list]')) showList();
    });

    // Poll for a badge count even while the drawer is closed.
    loadConversationList();
    setInterval(() => {
        if (!drawer.classList.contains('open')) loadConversationList();
    }, 30000);
})();
