// SPDX-License-Identifier: AGPL-3.0-only
import { decorateIcons } from './icons.js';
import { installMotion } from './motion.js';
decorateIcons();
installMotion();
if ('serviceWorker' in navigator)
    void navigator.serviceWorker.register('/sw.js').catch(() => { });
