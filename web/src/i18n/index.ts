/**
 * Minimal i18n framework.
 *
 * Usage:
 *   import { T, setLocale } from './i18n';
 *   T('settings.save')            // → "Save" (or locale-specific value)
 *   setLocale('ur')               // switch locale, fires va:locale-change
 *
 * Bundles live next to this file as {code}.json.
 * Falls back to 'en' for any missing key.
 */

import enRaw from './en.json';
import urRaw from './ur.json';
import hiRaw from './hi.json';

type Bundle = Record<string, string>;

const en = enRaw as Bundle;
const ur = urRaw as Bundle;
const hi = hiRaw as Bundle;

const BUNDLES: Record<string, Bundle> = { en, ur, hi };

let _active: Bundle = en;
let _activeCode = 'en';

/** Look up *key* in the active locale, falling back to English. */
export function T(key: string): string {
  return _active[key] ?? en[key] ?? key;
}

/** Switch the active bundle and fire `va:locale-change` on document. */
export function setLocale(code: string): void {
  const base = code.split('-')[0]; // 'zh-TW' → 'zh'
  const bundle = BUNDLES[base] ?? BUNDLES[code] ?? en;
  _active = bundle;
  _activeCode = base;
  document.dispatchEvent(new CustomEvent('va:locale-change', { detail: { code: _activeCode } }));
}

/** Return the currently-active locale code. */
export function getLocale(): string {
  return _activeCode;
}
