// SPDX-License-Identifier: AGPL-3.0-only
/** Original, shared 24px line icons. Text labels carry meaning; SVGs are decorative. */
const shapes = {
    grid: ['M3 3h7v7H3z', 'M14 3h7v7h-7z', 'M3 14h7v7H3z', 'M14 14h7v7h-7z'],
    download: ['M12 3v12', 'm7 10 5 5 5-5', 'M4 16v4h16v-4'],
    folder: ['M3 6h7l2 3h9v11H3z', 'M3 9V4h7l2 2'],
    history: ['M3 11a9 9 0 1 1 2 7', 'M3 4v7h7', 'M12 7v5l3 2'],
    server: ['M4 3h16v7H4z', 'M4 14h16v7H4z', 'M7 6h.01M7 17h.01', 'M11 6h6M11 17h6'],
    shield: ['M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6z', 'm8 12 3 3 5-6'],
    info: ['M12 11v6', 'M12 7h.01', 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0'],
    idea: ['M9 18h6M10 21h4', 'M8 15a6 6 0 1 1 8 0l-1 3H9z'],
    link: ['m10 13 4-4', 'M8 15 6 17a4 4 0 0 1-5-5l5-5a4 4 0 0 1 6 0', 'm16 9 2-2a4 4 0 0 1 5 5l-5 5a4 4 0 0 1-6 0'],
    arrow: ['M4 12h16', 'm14 6 6 6-6 6'],
    check: ['m5 12 4 4L19 6'],
    storage: ['M4 4h16v16H4z', 'M7 8h10M7 12h10M7 16h4'],
    globe: ['M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0', 'M3 12h18', 'M12 3c5 5 5 13 0 18-5-5-5-13 0-18'],
    pause: ['M8 5v14M16 5v14'], play: ['m8 4 12 8-12 8z'],
    close: ['m6 6 12 12M18 6 6 18'], trash: ['M3 6h18M9 6V3h6v3', 'm5 6 1 15h12l1-15', 'M10 10v7M14 10v7'],
    retry: ['M3 10a9 9 0 1 1 2 8', 'M3 4v6h6'], up: ['M12 20V4', 'm6 10 6-6 6 6'],
    edit: ['m15 4 5 5L8 21H3v-5z', 'm13 6 5 5'], copy: ['M8 8h13v13H8z', 'M4 16H3V3h13v1'],
    search: ['M18 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0', 'm15 15 6 6'],
    logout: ['M9 4H3v16h6', 'M8 12h13', 'm16 7 5 5-5 5'],
    alert: ['m12 3 10 18H2z', 'M12 9v5M12 17h.01'],
    sparkle: ['m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3z'],
    code: ['m8 6-6 6 6 6M16 6l6 6-6 6', 'm14 3-4 18'],
    phone: ['M7 2h10v20H7z', 'M10 5h4M12 19h.01'],
    list: ['M9 6h12M9 12h12M9 18h12', 'M3 6h.01M3 12h.01M3 18h.01'],
};
export function icon(name) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    for (const [key, value] of Object.entries({ viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.8', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true', focusable: 'false', class: 'icon' }))
        svg.setAttribute(key, value);
    for (const d of shapes[name]) {
        const path = document.createElementNS(svg.namespaceURI, 'path');
        path.setAttribute('d', d);
        svg.append(path);
    }
    return svg;
}
export function decorateIcons(root = document) {
    root.querySelectorAll('[data-icon]').forEach(el => { const name = el.dataset.icon; if (name in shapes)
        el.replaceChildren(icon(name)); });
}
export function actionLabel(el, label, name) { el.replaceChildren(icon(name), document.createTextNode(label)); }
export function actionIcon(label) {
    return label.startsWith('Save file') ? 'download' : { 'Pause': 'pause', 'Resume': 'play', 'Retry': 'retry', 'Cancel': 'close', 'Remove': 'trash', 'Move first': 'up', 'Edit': 'edit', 'Duplicate': 'copy', 'Delete': 'trash', 'Revoke': 'close' }[label];
}
