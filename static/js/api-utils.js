/**
 * Small shared helper around fetch() for talking to the DRF API
 * (session-authenticated, so we just need to attach the CSRF cookie).
 */
function getCookie(name) {
    const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? decodeURIComponent(match.pop()) : '';
}

async function apiRequest(url, { method = 'GET', body = null } = {}) {
    const headers = { 'Accept': 'application/json' };
    const options = { method, headers, credentials: 'same-origin' };

    if (body !== null) {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
    }
    if (method !== 'GET' && method !== 'HEAD') {
        headers['X-CSRFToken'] = getCookie('csrftoken');
    }

    const response = await fetch(url, options);
    let data = null;
    try { data = await response.json(); } catch (e) { /* empty body */ }

    if (!response.ok) {
        const detail = (data && (data.detail || JSON.stringify(data))) || response.statusText;
        throw new Error(detail);
    }
    return data;
}

/** Minimal bootstrap-styled toast, no extra markup required in templates. */
function showToast(message, variant = 'success') {
    let host = document.getElementById('toastHost');
    if (!host) {
        host = document.createElement('div');
        host.id = 'toastHost';
        host.className = 'toast-host';
        document.body.appendChild(host);
    }
    const toast = document.createElement('div');
    toast.className = `app-toast app-toast-${variant}`;
    toast.innerHTML = `<i class="bi ${variant === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-circle-fill'}"></i><span>${message}</span>`;
    host.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 250);
    }, 3200);
}
