/**
 * Wires up every `.js-moderate-btn` button (Admin Dashboard "Pending
 * Approvals" widget + the full Admin > Listings table) to
 * POST /api/admin/listings/<id>/moderate/ instead of submitting a form,
 * so the status change happens instantly with no page reload.
 */
(function () {
    const STATUS_LABEL = {
        draft: 'Draft', pending: 'Pending Approval', published: 'Published',
        rejected: 'Rejected', closed: 'Closed',
    };
    const STATUS_BADGE = {
        draft: 'badge-draft', pending: 'badge-pending', published: 'badge-published',
        rejected: 'badge-rejected', closed: 'badge-closed',
    };
    const CONFIRM_MESSAGE = {
        reject: 'Reject this listing? The owner will see it as rejected.',
        suspend: 'Suspend this listing? It will be removed from the marketplace.',
    };

    function updatePendingCounters(delta) {
        document.querySelectorAll('[data-pending-count]').forEach((el) => {
            const next = Math.max(0, parseInt(el.textContent, 10) + delta);
            el.textContent = next;
        });
    }

    async function moderate(btn) {
        const listingId = btn.dataset.listingId;
        const action = btn.dataset.action;
        const row = btn.closest('[data-listing-row]');
        const scope = btn.dataset.scope; // "pending-widget" (dashboard) or "table" (full list)
        const filterStatus = btn.dataset.filterStatus; // current ?status= filter, if any

        if (CONFIRM_MESSAGE[action] && !window.confirm(CONFIRM_MESSAGE[action])) return;

        const groupButtons = row.querySelectorAll('.js-moderate-btn');
        groupButtons.forEach((b) => (b.disabled = true));
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

        try {
            const updated = await apiRequest(`/api/admin/listings/${listingId}/moderate/`, {
                method: 'POST',
                body: { action },
            });

            if (scope === 'pending-widget') {
                // This widget only ever shows pending listings, so any action removes the row.
                fadeOutRow(row, () => checkEmptyState(row.closest('tbody')));
                updatePendingCounters(-1);
            } else {
                // Full table: remove the row if it no longer matches the active filter,
                // otherwise update its badge + action buttons in place.
                if (filterStatus && filterStatus !== updated.status) {
                    fadeOutRow(row, () => checkEmptyState(row.closest('tbody')));
                } else {
                    updateRowInPlace(row, updated.status);
                }
            }

            showToast(`Listing "${updated.title}" is now ${STATUS_LABEL[updated.status] || updated.status}.`);
        } catch (err) {
            showToast(err.message || 'Could not update this listing.', 'error');
            groupButtons.forEach((b) => (b.disabled = false));
            btn.innerHTML = btn.dataset.originalLabel;
        }
    }

    function fadeOutRow(row, done) {
        row.style.transition = 'opacity .25s ease, transform .25s ease';
        row.style.opacity = '0';
        row.style.transform = 'translateX(8px)';
        setTimeout(() => {
            row.remove();
            if (done) done();
        }, 250);
    }

    function checkEmptyState(tbody) {
        if (tbody && !tbody.querySelector('[data-listing-row]')) {
            const cols = tbody.closest('table').querySelectorAll('thead th').length;
            tbody.innerHTML = `<tr><td colspan="${cols}" class="text-center text-muted py-4">Nothing here right now.</td></tr>`;
        }
    }

    function updateRowInPlace(row, status) {
        const badge = row.querySelector('[data-status-badge]');
        if (badge) {
            badge.textContent = STATUS_LABEL[status] || status;
            badge.className = `badge ${STATUS_BADGE[status] || 'badge-secondary'}`;
        }
        row.dataset.status = status;
        row.querySelectorAll('.js-moderate-btn').forEach((b) => {
            b.disabled = b.dataset.action === status || (status === 'published' && b.dataset.action === 'approve');
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.js-moderate-btn').forEach((btn) => {
            btn.dataset.originalLabel = btn.innerHTML;
        });
        document.body.addEventListener('click', (e) => {
            const btn = e.target.closest('.js-moderate-btn');
            if (btn) {
                e.preventDefault();
                moderate(btn);
            }
        });
    });
})();
