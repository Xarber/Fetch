// SPDX-License-Identifier: AGPL-3.0-only
/** Motion explains state changes; never delays input, moves live data or replays on polling. */
let keyboard = false;
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
const running = new WeakMap();
export function installMotion() {
    document.addEventListener('keydown', () => { keyboard = true; document.documentElement.dataset.input = 'keyboard'; }, true);
    document.addEventListener('pointerdown', () => { keyboard = false; document.documentElement.dataset.input = 'pointer'; }, true);
    document.addEventListener('toggle', event => {
        const details = event.target;
        if (details instanceof HTMLDetailsElement && details.open) {
            for (const child of details.children)
                if (child.tagName !== 'SUMMARY')
                    enter(child, 'detail');
        }
    }, true);
    reduce.addEventListener('change', () => { if (reduce.matches)
        document.getAnimations().forEach(a => a.cancel()); });
}
export function enter(el, kind = 'page') {
    if (keyboard || reduce.matches || typeof el.animate !== 'function')
        return;
    running.get(el)?.cancel();
    const animation = el.animate([{ opacity: 0, transform: `translateY(${kind === 'row' ? 4 : 6}px)` }, { opacity: 1, transform: 'translateY(0)' }], { duration: kind === 'row' ? 160 : 200, easing: 'cubic-bezier(0.23,1,0.32,1)' });
    running.set(el, animation);
}
