// SPDX-License-Identifier: AGPL-3.0-only
import { icon, decorateIcons, actionIcon, actionLabel } from './icons.js';
import { installMotion, enter } from './motion.js';
installMotion();
decorateIcons();
const $ = (id) => { const el = document.getElementById(id); if (!el)
    throw new Error(`Missing element ${id}`); return el; };
const input = (id) => $(id);
const managed = document.documentElement.dataset.managed === 'true';
if (managed) {
    $('login-title').textContent = 'Sign in to Fetch';
    $('password').setAttribute('aria-label', 'Password');
    actionLabel($('login-submit'), 'Sign in', 'shield');
    actionLabel($('session-button'), 'Sign in', 'shield');
}
let token = '';
let jobs = [];
let inspected = null;
let requestKey = crypto.randomUUID();
let view = 'overview';
let developer = false;
let taps = 0;
let lastTap = 0;
let lastInteraction = Date.now();
let editing = null;
const titles = { overview: 'Overview', queue: 'Download queue', library: 'Media library', history: 'History', server: 'Server & security', about: 'About Fetch', ideas: 'Developer ideas' };
let toastTimer;
function toast(message) { $('toast').textContent = message; $('toast').hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { $('toast').hidden = true; }, 6500); }
function bytes(value) { if (value == null)
    return 'Unknown'; if (value < 1024)
    return `${value} B`; const i = Math.min(3, Math.floor(Math.log(value) / Math.log(1024))); return `${(value / 1024 ** i).toFixed(i === 3 ? 1 : 0)} ${['B', 'KB', 'MB', 'GB'][i]}`; }
function node(tag, text, cls) { const e = document.createElement(tag); if (text)
    e.textContent = text; if (cls)
    e.className = cls; return e; }
function button(label, run, cls = 'button') { const b = node('button', label, cls); b.type = 'button'; b.dataset.label = label; const meaning = actionIcon(label); if (meaning)
    b.prepend(icon(meaning)); b.onclick = () => { b.disabled = true; Promise.resolve().then(run).catch(e => toast(String(e.message ?? e))).finally(() => { b.disabled = false; }); }; return b; }
async function api(path, method = 'GET', body) {
    if (!token && path !== 'auth/login') {
        $('login-dialog').hidden = false;
        $('login-dialog').showModal();
        throw new Error('Connect to your server first.');
    }
    const response = await fetch(`/api/v1/${path}`, { method, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: body === undefined ? undefined : JSON.stringify(body), cache: 'no-store' });
    const result = response.status === 204 ? {} : await response.json();
    if (!response.ok) {
        if (response.status === 401 && path !== 'auth/login') {
            token = '';
            connected(false);
        }
        throw new Error(typeof result.detail === 'string' ? result.detail : `Request failed (${response.status})`);
    }
    return result;
}
function connected(online) { $('connection-dot').classList.toggle('online', online); $('connection-label').textContent = online ? 'Server connected' : 'Not connected'; actionLabel($('session-button'), token ? 'Sign out' : managed ? 'Sign in' : 'Connect server', token ? 'logout' : managed ? 'shield' : 'server'); }
function navigate(target) {
    if (target === 'ideas' && !developer)
        return;
    if (view !== target && target !== 'ideas') {
        developer = false;
        taps = 0;
        $('ideas-nav').hidden = true;
    }
    view = target;
    document.querySelectorAll('.view').forEach(e => { e.hidden = e.id !== `view-${target}`; });
    document.querySelectorAll('[data-view]').forEach(e => e.classList.toggle('active', e.dataset.view === target));
    $('breadcrumb').textContent = titles[target] ?? target;
    enter($('view-' + target));
    if (target === 'ideas')
        renderIdeas();
    if (target === 'server' && token && !managed)
        void diagnostics().catch(e => toast(e.message));
}
function renderJobs() {
    const active = jobs.filter(j => ['queued', 'downloading', 'postprocessing', 'pausing', 'paused'].includes(j.state));
    $('queue-count').textContent = String(active.length);
    $('stat-active').textContent = String(active.length);
    $('stat-ready').textContent = String(jobs.filter(j => j.state === 'ready').length);
    const search = input('library-search').value.toLowerCase();
    const sets = { 'recent-jobs': jobs.slice(0, 4), 'queue-jobs': active, 'library-jobs': jobs.filter(j => j.state === 'ready' && j.title.toLowerCase().includes(search)), 'history-jobs': jobs.filter(j => !active.includes(j)) };
    for (const [id, list] of Object.entries(sets)) {
        const container = $(id);
        const signature = JSON.stringify([list, Boolean(token)]);
        if (container.dataset.signature === signature)
            continue;
        container.dataset.signature = signature;
        const previous = new Set(Array.from(container.querySelectorAll('[data-job-id]')).map(el => el.dataset.jobId));
        const focused = document.activeElement instanceof HTMLButtonElement && container.contains(document.activeElement) ? { job: document.activeElement.closest('[data-job-id]')?.dataset.jobId, label: document.activeElement.dataset.label } : null;
        container.replaceChildren();
        if (!list.length) {
            const empty = node('div', undefined, 'empty');
            const emptyIcon = node('div', undefined, 'empty-symbol');
            emptyIcon.append(icon('download'));
            empty.append(emptyIcon, node('strong', token ? 'Nothing here yet' : 'Your next great find starts here'), node('p', token ? 'New downloads will appear here.' : 'Sign in, then paste your first link.'));
            container.append(empty);
        }
        for (const job of list) {
            const row = node('article', undefined, 'job');
            row.dataset.jobId = job.id;
            const symbol = node('div', undefined, 'job-icon');
            symbol.append(icon(job.state === 'ready' ? 'check' : job.state === 'failed' ? 'alert' : 'download'));
            row.append(symbol);
            const body = node('div', undefined, 'job-content');
            body.append(node('h3', job.title));
            const details = [job.progress.stage ?? job.state];
            if (job.progress.downloaded_bytes != null)
                details.push(`${bytes(job.progress.downloaded_bytes)}${job.progress.total_bytes ? ` / ${job.progress.total_estimated ? '≈ ' : ''}${bytes(job.progress.total_bytes)}` : ''}`);
            if (job.progress.speed)
                details.push(`${bytes(job.progress.speed)}/s`);
            if (job.size)
                details.push(bytes(job.size));
            body.append(node('p', details.join(' · ')));
            if (job.error)
                body.append(node('p', job.error));
            if (job.state === 'downloading' && job.progress.total_bytes) {
                const progress = node('progress');
                progress.max = job.progress.total_bytes;
                progress.value = job.progress.downloaded_bytes ?? 0;
                progress.setAttribute('aria-label', 'Server download progress');
                body.append(progress);
            }
            row.append(body, node('span', job.state.replaceAll('_', ' '), 'status'));
            const actions = node('div', undefined, 'job-actions');
            if (job.state === 'ready')
                actions.append(button('Save file ↓', () => saveFile(job), 'button primary'));
            for (const [label, action, states] of [['Pause', 'pause', ['queued', 'downloading']], ['Resume', 'resume', ['paused']], ['Retry', 'retry', ['failed', 'cancelled']], ['Cancel', 'cancel', ['queued', 'downloading', 'postprocessing', 'paused']]]) {
                if (states.includes(job.state))
                    actions.append(button(label, async () => { await api(`downloads/${job.id}/${action}`, 'POST'); await refresh(); }));
            }
            if (['ready', 'failed', 'cancelled', 'expired', 'paused'].includes(job.state))
                actions.append(button('Remove', async () => { if (confirm('Delete this server artifact and history entry? This cannot be undone.')) {
                    await api(`downloads/${job.id}`, 'DELETE');
                    await refresh();
                } }));
            if (job.state === 'queued')
                actions.append(button('Move first', async () => { await api(`downloads/${job.id}`, 'PATCH', { priority: 100 }); await refresh(); }));
            row.append(actions);
            container.append(row);
            if (!previous.has(job.id))
                enter(row, 'row');
        }
        if (focused?.job && focused.label)
            container.querySelector(`[data-job-id="${CSS.escape(focused.job)}"] button[data-label="${CSS.escape(focused.label)}"]`)?.focus({ preventScroll: true });
    }
}
async function refresh() { if (!token)
    return; try {
    jobs = await api('downloads');
    const status = await api('status');
    $('stat-storage').textContent = bytes(status.storage.free);
    connected(true);
    if (!status.worker_online)
        $('connection-label').textContent = 'Worker offline';
    renderJobs();
}
catch {
    connected(false);
} }
function downloadJSON(value, name) { const a = node('a'); const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' })); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 2000); }
async function saveFile(job) {
    const ticket = await api(`downloads/${job.id}/transfer`, 'POST');
    if (ticket.size > 128 * 1024 ** 2)
        throw new Error('For files over 128 MB, use the native Fetch client for streaming background transfers. Browser saving currently verifies the whole file in memory.');
    const response = await fetch(ticket.path, { headers: { Authorization: `Bearer ${ticket.token}` }, cache: 'no-store' });
    if (!response.ok)
        throw new Error('File transfer failed. Request a fresh transfer and retry.');
    const data = await response.arrayBuffer();
    const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', data))).map(x => x.toString(16).padStart(2, '0')).join('');
    if (data.byteLength !== ticket.size || hash !== ticket.sha256)
        throw new Error('File checksum mismatch. The file was not saved.');
    const url = URL.createObjectURL(new Blob([data], { type: response.headers.get('Content-Type') ?? 'application/octet-stream' }));
    const a = node('a');
    a.href = url;
    a.download = ticket.filename;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
    await api(`transfers/${ticket.id}/complete`, 'POST', { sha256: hash });
    toast('File verified. Your browser will handle saving it.');
}
const enteredKey = 'fetch.workspace-entered.v1';
let entered = false;
try {
    entered = localStorage.getItem(enteredKey) === 'yes';
}
catch { /* Storage may be unavailable. */ }
function routeWorkspace(target, record = true, focus = true) {
    if (!Object.hasOwn(titles, target) || (target === 'ideas' && !developer))
        target = 'overview';
    $('product').hidden = true;
    $('workspace').hidden = false;
    entered = true;
    try {
        localStorage.setItem(enteredKey, 'yes');
    }
    catch { /* The preference survives this document session. */ }
    if (record)
        history.pushState(null, '', target === 'overview' ? '/#app' : '/#' + target);
    navigate(target);
    if (focus) {
        const heading = $('view-' + target).querySelector('h1');
        if (heading) {
            heading.tabIndex = -1;
            heading.focus();
        }
    }
}
function routeProduct(record = true, focus = true) {
    document.querySelectorAll('dialog[open]').forEach(dialog => dialog.close());
    $('workspace').hidden = true;
    $('product').hidden = false;
    if (record)
        history.pushState({ fetchView: 'product' }, '', '/?welcome');
    enter($('product').querySelector('.hero-copy'));
    if (focus) {
        const heading = $('hero-title');
        heading.tabIndex = -1;
        heading.focus();
    }
}
function restoreRoute(fromHistory = false) {
    const route = location.hash.slice(1);
    if (route === 'app' || Object.hasOwn(titles, route))
        routeWorkspace(route === 'app' ? 'overview' : route, false, false);
    else if (new URLSearchParams(location.search).has('welcome') || (fromHistory && history.state?.fetchView === 'product') || !entered || route === 'how' || route === 'platforms')
        routeProduct(false, false);
    else
        routeWorkspace('overview', false, false);
}
window.addEventListener('popstate', () => restoreRoute(true));
window.addEventListener('hashchange', () => restoreRoute(true));
document.querySelectorAll('[data-open-app], [data-show-product], #product-link').forEach(link => {
    link.addEventListener('click', event => {
        if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)
            return;
        event.preventDefault();
        if (link.hasAttribute('data-open-app'))
            routeWorkspace(view);
        else
            routeProduct();
    });
});
document.querySelectorAll('[data-view]').forEach(el => el.onclick = () => routeWorkspace(el.dataset.view ?? 'overview'));
document.querySelectorAll('[data-go]').forEach(el => el.onclick = () => routeWorkspace(el.dataset.go ?? 'overview'));
restoreRoute();
if (!$("product").hidden)
    history.replaceState({ fetchView: "product" }, "", location.href);
document.querySelectorAll('[data-close]').forEach(e => e.onclick = () => $(e.dataset.close ?? '').close());
$('session-button').onclick = () => { if (token) {
    void api('auth/logout', 'POST').finally(() => { token = ''; jobs = []; connected(false); renderJobs(); });
}
else
    $('login-dialog').showModal(); };
$('login-form').onsubmit = async (e) => { e.preventDefault(); $('login-error').textContent = ''; try {
    const result = await api('auth/login', 'POST', { username: input('username').value, password: input('password').value, device_name: 'Fetch Web' });
    token = result.token;
    input('password').value = '';
    $('login-dialog').close();
    await refresh();
}
catch (error) {
    $('login-error').textContent = error.message;
} };
$('inspect-form').onsubmit = async (e) => {
    e.preventDefault();
    const b = $('inspect-button');
    b.disabled = true;
    b.textContent = 'Inspecting…';
    try {
        inspected = await api('media/inspect', 'POST', { url: input('source-url').value });
        requestKey = crypto.randomUUID();
        $('media-title').textContent = inspected.title;
        $('media-meta').textContent = [inspected.creator, inspected.source, inspected.duration ? `${Math.round(inspected.duration)} seconds` : null].filter(Boolean).join(' · ');
        $('format-id').replaceChildren();
        $('audio-id').replaceChildren(new Option('None', ''));
        $('format-details').replaceChildren();
        for (const f of inspected.formats) {
            const label = [f.format_id, f.ext, f.height ? `${f.height}p` : null, f.vcodec, f.acodec].filter(Boolean).join(' · ');
            $('format-id').add(new Option(label, f.format_id));
            if (f.vcodec === 'none')
                $('audio-id').add(new Option(label, f.format_id));
            $('format-details').append(node('p', label));
        }
        input('authorized').checked = false;
        $('media-dialog').showModal();
    }
    catch (error) {
        toast(error.message);
    }
    finally {
        b.disabled = false;
        actionLabel(b, 'Inspect link', 'search');
    }
};
$('preset').onchange = () => { $('custom-selectors').hidden = $('preset').value !== 'custom'; };
$('download-form').onsubmit = async (e) => {
    e.preventDefault();
    if (!inspected)
        return;
    const b = $('queue-button');
    b.disabled = true;
    try {
        const preset = $('preset').value;
        await api('downloads', 'POST', { inspection_id: inspected.id, request_key: requestKey, authorized: input('authorized').checked, selection: { preset, audio_format: $('audio-format').value, format_id: preset === 'custom' ? $('format-id').value : null, audio_id: preset === 'custom' ? ($('audio-id').value || null) : null, subtitles: input('subtitles').checked } });
        $('media-dialog').close();
        input('source-url').value = '';
        toast('Queued on your server.');
        await refresh();
    }
    catch (error) {
        toast(error.message);
    }
    finally {
        b.disabled = false;
    }
};
$('batch-toggle').onclick = () => { $('batch-form').hidden = !$('batch-form').hidden; };
$('batch-form').onsubmit = async (e) => { e.preventDefault(); const urls = [...new Set($('batch-urls').value.split('\n').map(x => x.trim()).filter(Boolean))]; if (urls.length > 50) {
    toast('Use at most 50 links per batch.');
    return;
} let count = 0; const b = $('batch-form').querySelector('button'); b.disabled = true; try {
    for (const url of urls) {
        const info = await api('media/inspect', 'POST', { url });
        await api('downloads', 'POST', { inspection_id: info.id, request_key: crypto.randomUUID(), authorized: input('batch-authorized').checked, selection: { preset: 'compatible' } });
        count++;
    }
    toast(`Queued ${count} items.`);
}
catch (error) {
    toast(`Queued ${count} items. ${error.message}`);
}
finally {
    b.disabled = false;
    await refresh();
} };
input('library-search').oninput = renderJobs;
$('export-history').onclick = () => downloadJSON({ exportedAt: new Date().toISOString(), jobs }, 'Fetch-history.json');
async function diagnostics() {
    const versions = await api('versions');
    $('diagnostics').textContent = Object.entries(versions).map(([k, v]) => `${k}: ${v}`).join('\n');
    try {
        const settings = await api('admin/settings');
        input('concurrency').value = String(settings.concurrency);
        input('retention').value = String(settings.retention_hours);
    }
    catch { /* Paired devices may inspect versions without administration. */ }
}
$('refresh-diagnostics').onclick = () => { void diagnostics().catch(e => toast(e.message)); };
$('settings-form').onsubmit = async (e) => { e.preventDefault(); try {
    await api('admin/settings', 'PATCH', { concurrency: Number(input('concurrency').value), retention_hours: Number(input('retention').value) });
    toast('Resource policies saved.');
}
catch (error) {
    toast(error.message);
} };
$('pair-button').onclick = async () => { try {
    const pair = await api('pairing/start', 'POST', { server_url: location.origin });
    $('pair-result').textContent = `${pair.challenge}\nExpires in 3 minutes. Enter in Fetch on your trusted device.`;
    if (pair.qr_data_uri) {
        const qr = node('img');
        qr.src = pair.qr_data_uri;
        qr.alt = 'One-use Fetch device pairing QR code';
        qr.width = 240;
        qr.height = 240;
        $('pair-result').append(qr);
    }
}
catch (error) {
    toast(error.message);
} };
$('refresh-devices').onclick = async () => { try {
    const devices = await api('devices');
    $('devices').replaceChildren();
    for (const d of devices) {
        const row = node('p', `${d.name}${d.admin ? ' · admin' : ''} `);
        row.append(button('Revoke', async () => { if (confirm(`Revoke ${d.name}?`)) {
            await api(`devices/${d.id}`, 'DELETE');
            row.remove();
        } }));
        $('devices').append(row);
    }
}
catch (error) {
    toast(error.message);
} };
let ideaStorageLocked = false;
function readIdeas() { try {
    const stored = localStorage.getItem('fetch.ideas.v1');
    return stored ? validateArchive(JSON.parse(stored)).ideas : [];
}
catch {
    ideaStorageLocked = true;
    toast('Ideas storage could not be read. Existing data was preserved.');
    return [];
} }
let ideas = managed ? [] : readIdeas();
function archive() { return { schemaVersion: 1, project: 'org.openrecode.fetch', exportedAt: Date.now() / 1000, ideas }; }
function persistIdeas(next) { if (ideaStorageLocked) {
    toast("Existing Ideas storage is unreadable and was preserved. Export the recovery file before repairing storage.");
    return;
} try {
    localStorage.setItem('fetch.ideas.v1', JSON.stringify({ ...archive(), ideas: next }));
    ideas = next;
    renderIdeas();
}
catch {
    toast('Could not save ideas. Export your collection before closing this browser.');
} }
function renderIdeas() {
    const list = $('ideas-list');
    list.replaceChildren();
    const query = input('idea-search').value.toLowerCase();
    for (const idea of [...ideas].sort((a, b) => b.modified - a.modified).filter(i => `${i.title} ${i.description}`.toLowerCase().includes(query))) {
        const row = node('article', undefined, 'panel');
        row.append(node('h2', idea.title), node('p', `${idea.category} · ${idea.priority} · ${idea.status}`));
        const details = node('details');
        details.append(node('summary', 'Description & history'), node('p', idea.description), node('p', idea.history.join('\n')));
        row.append(details);
        const actions = node('div', undefined, 'toolbar');
        actions.append(button('Edit', () => editIdea(idea)), button('Duplicate', () => { persistIdeas([...ideas, { ...structuredClone(idea), id: crypto.randomUUID(), title: idea.title + ' (copy)', created: Date.now() / 1000, modified: Date.now() / 1000 }]); }), button('Delete', () => { if (confirm('Delete this recorded idea?'))
            persistIdeas(ideas.filter(i => i.id !== idea.id)); }));
        row.append(actions);
        list.append(row);
    }
    if (!ideas.length)
        list.append(node('p', 'No ideas yet. Record your next improvement, even offline.'));
}
function editIdea(idea) { editing = idea?.id ?? null; input('idea-title').value = idea?.title ?? ''; $('idea-description').value = idea?.description ?? ''; $('idea-category').value = idea?.category ?? 'Feature'; $('idea-priority').value = idea?.priority ?? 'Normal'; $('idea-status').value = idea?.status ?? 'pending'; $('idea-dialog').showModal(); }
$('new-idea').onclick = () => editIdea();
$('idea-form').onsubmit = e => { e.preventDefault(); const previous = ideas.find(i => i.id === editing); const status = $('idea-status').value; const now = Date.now() / 1000; const idea = { id: editing ?? crypto.randomUUID(), title: input('idea-title').value.trim(), description: $('idea-description').value, category: $('idea-category').value, priority: $('idea-priority').value, status, created: previous?.created ?? now, modified: now, implementationReferences: previous?.implementationReferences ?? [], history: [...(previous?.history ?? []), `${new Date().toISOString()}: ${status}`] }; if (!idea.title)
    return; persistIdeas([...ideas.filter(i => i.id !== editing), idea]); $('idea-dialog').close(); };
$('export-ideas').onclick = () => { if (ideaStorageLocked) {
    const raw = localStorage.getItem('fetch.ideas.v1') ?? '';
    const url = URL.createObjectURL(new Blob([raw], { type: 'application/json' }));
    const link = node('a');
    link.href = url;
    link.download = 'Fetch-Ideas-recovery.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
}
else
    downloadJSON(archive(), 'Fetch-Ideas.json'); };
input('idea-search').oninput = renderIdeas;
function validateArchive(value) {
    if (!value || typeof value !== 'object')
        throw new Error('Invalid ideas file');
    const a = value;
    if (a.schemaVersion !== 1 || a.project !== 'org.openrecode.fetch' || !Array.isArray(a.ideas) || a.ideas.length > 10000)
        throw new Error('Unsupported ideas schema or project');
    const ids = new Set();
    for (const idea of a.ideas) {
        if (typeof idea.id !== 'string' || !idea.id || ids.has(idea.id) || typeof idea.title !== 'string' || !idea.title || idea.title.length > 500 || typeof idea.description !== 'string' || idea.description.length > 50000 || !['Feature', 'Improvement', 'Bug Fix', 'UI/UX', 'Performance', 'Other'].includes(idea.category) || !['Low', 'Normal', 'High', 'Critical'].includes(idea.priority) || !['pending', 'approved', 'deferred', 'inProgress', 'implemented', 'rejected'].includes(idea.status) || !Array.isArray(idea.history) || !idea.history.every(h => typeof h === 'string') || !Array.isArray(idea.implementationReferences) || !idea.implementationReferences.every(h => typeof h === 'string') || !Number.isFinite(idea.created) || !Number.isFinite(idea.modified))
            throw new Error('Invalid idea entry');
        ids.add(idea.id);
    }
    return a;
}
input('import-ideas').onchange = async () => { const file = input('import-ideas').files?.[0]; if (!file)
    return; try {
    if (file.size > 10_000_000)
        throw new Error('Ideas file too large');
    const incoming = validateArchive(JSON.parse(await file.text()));
    if (!confirm(`Import ${incoming.ideas.length} ideas? Existing ideas are preserved. Conflicts become separate copies.`))
        return;
    const merged = [...ideas];
    for (const idea of incoming.ideas) {
        const old = merged.find(i => i.id === idea.id);
        if (!old)
            merged.push(idea);
        else if (JSON.stringify(old, Object.keys(old).sort()) !== JSON.stringify(idea, Object.keys(idea).sort()))
            merged.push({ ...idea, id: crypto.randomUUID(), title: idea.title + ' (imported conflict)', history: [...idea.history, `Conflict preserved from ${idea.id}`] });
    }
    persistIdeas(merged);
}
catch (error) {
    toast(error.message);
}
finally {
    input('import-ideas').value = '';
} };
function unlockDeveloper() { if (managed)
    return; const now = Date.now(); taps = now - lastTap < 2000 ? taps + 1 : 1; lastTap = now; if (taps === 3) {
    developer = true;
    $('ideas-nav').hidden = false;
    toast('Developer options enabled.');
} }
$('version-button').onclick = unlockDeveloper;
$('version-button-about').onclick = unlockDeveloper;
for (const event of ['pointerdown', 'keydown', 'scroll'])
    document.addEventListener(event, () => { lastInteraction = Date.now(); }, { passive: true });
setInterval(() => { if (developer && Date.now() - lastInteraction > 30000) {
    developer = false;
    $('ideas-nav').hidden = true;
    if (view === 'ideas')
        navigate('about');
} }, 1000);
setInterval(() => { if (document.visibilityState === 'visible')
    void refresh(); }, 3000);
window.addEventListener('online', () => { $('offline').hidden = true; void refresh(); });
window.addEventListener('offline', () => { $('offline').hidden = false; connected(false); });
$('offline').hidden = navigator.onLine;
renderJobs();
let pendingWorker = null;
if ('serviceWorker' in navigator) {
    void navigator.serviceWorker.register('/sw.js').then(reg => {
        const offer = () => { pendingWorker = reg.waiting; if (pendingWorker) {
            $('update-banner').hidden = false;
            void workerRelease(pendingWorker).then(data => renderRelease($('update-notes'), data)).catch(() => { $('update-notes').textContent = 'Version details unavailable. Review About Fetch before reloading.'; });
        } };
        offer();
        reg.addEventListener('updatefound', () => { const worker = reg.installing; worker?.addEventListener('statechange', () => { if (worker.state === 'installed' && navigator.serviceWorker.controller)
            offer(); }); });
    }).catch(() => toast('Offline support could not be registered in this browser.'));
}
$('apply-update').onclick = () => { if (!confirm('Reload Fetch now? Finish or export unsaved form entries first.'))
    return; pendingWorker?.postMessage({ type: 'ACTIVATE' }); };
navigator.serviceWorker?.addEventListener('controllerchange', () => { if (pendingWorker)
    location.reload(); });
let install = null;
window.addEventListener('beforeinstallprompt', event => { event.preventDefault(); install = event; $('install-button').hidden = false; });
$('install-button').onclick = () => { void install?.prompt(); };
function workerRelease(worker) { return new Promise((resolve, reject) => { const channel = new MessageChannel(); const timer = setTimeout(() => reject(new Error('Release details unavailable')), 3000); channel.port1.onmessage = e => { clearTimeout(timer); resolve(e.data); }; worker.postMessage({ type: 'RELEASE_METADATA' }, [channel.port2]); }); }
function renderRelease(container, data) { container.replaceChildren(); container.append(node('h3', `Fetch ${data.version}`)); const icons = { 'server.rack': '▤', 'folder': '▣', 'arrow.down.circle': '↓' }; for (const item of data.highlights ?? [])
    container.append(node('p', `${icons[item.icon] ?? '✦'} ${item.text}`)); const details = node('details'); details.append(node('summary', 'Fixes & Improvements')); for (const text of data.fixes ?? [])
    details.append(node('p', text)); container.append(details); }
if ('serviceWorker' in navigator) {
    void navigator.serviceWorker.ready.then(reg => reg.active ? workerRelease(reg.active) : null).then(data => { if (!data)
        return; const previous = localStorage.getItem('fetch.lastWebBuild'); localStorage.setItem('fetch.lastWebBuild', data.webBuild); if (previous && previous !== data.webBuild) {
        renderRelease($('whatsnew-notes'), data);
        if (!$('workspace').hidden)
            $('whatsnew-dialog').showModal();
    } }).catch(() => { });
}
$('source-button').onclick = async () => { try {
    if (!token)
        throw new Error('Connect before downloading this server’s corresponding source.');
    const response = await fetch('/api/v1/source', { headers: { Authorization: `Bearer ${token}` }, cache: 'no-store' });
    if (!response.ok)
        throw new Error('The server administrator has not prepared a source archive for this revision.');
    const url = URL.createObjectURL(await response.blob());
    const link = node('a');
    link.href = url;
    link.download = 'Fetch-corresponding-source.tar.gz';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
}
catch (error) {
    toast(error.message);
} };
