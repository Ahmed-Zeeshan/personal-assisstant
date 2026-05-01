/**
 * Settings drawer — tabbed (Brain / Voice / Audio / Identity / Privacy & Display).
 *
 * Public API (unchanged):
 *   open(cfg)        – open the drawer populated with cfg
 *   close()          – close the drawer
 *   onSave(handler)  – register async save callback
 *
 * Tabs:
 *   Brain            – provider, model, API key, reply-language
 *   Voice            – avatar, voice, STT language
 *   Audio            – trigger (hotkey/wake-word), hotkey or wake-word sub-form
 *   Identity         – name, address-as, title
 *   Privacy & Display – allowed folders + high-contrast + font-size
 */
import type { AppConfig, Provider } from '../types';
import { T } from '../i18n';

// 24 reply-language options + auto
const REPLY_LANGUAGES: { code: string; label: string }[] = [
  { code: 'auto',  label: 'Auto-detect (follow user)' },
  { code: 'en',    label: 'English' },
  { code: 'ar',    label: 'Arabic' },
  { code: 'bn',    label: 'Bengali' },
  { code: 'cs',    label: 'Czech' },
  { code: 'de',    label: 'German' },
  { code: 'es',    label: 'Spanish' },
  { code: 'fa',    label: 'Persian / Farsi' },
  { code: 'fr',    label: 'French' },
  { code: 'gu',    label: 'Gujarati' },
  { code: 'hi',    label: 'Hindi' },
  { code: 'id',    label: 'Indonesian' },
  { code: 'it',    label: 'Italian' },
  { code: 'ja',    label: 'Japanese' },
  { code: 'ko',    label: 'Korean' },
  { code: 'mr',    label: 'Marathi' },
  { code: 'nl',    label: 'Dutch' },
  { code: 'pa',    label: 'Punjabi' },
  { code: 'pl',    label: 'Polish' },
  { code: 'pt',    label: 'Portuguese' },
  { code: 'ru',    label: 'Russian' },
  { code: 'ta',    label: 'Tamil' },
  { code: 'te',    label: 'Telugu' },
  { code: 'tr',    label: 'Turkish' },
  { code: 'ur',    label: 'Urdu' },
  { code: 'zh',    label: 'Chinese (Mandarin)' },
];

const WAKE_WORDS = ['hey_jarvis', 'alexa', 'hey_mycroft', 'hey_rhasspy'];

type TabId = 'brain' | 'voice' | 'audio' | 'identity' | 'privacy';

const TABS: { id: TabId; labelKey: string }[] = [
  { id: 'brain',    labelKey: 'tab.brain' },
  { id: 'voice',    labelKey: 'tab.voice' },
  { id: 'audio',    labelKey: 'tab.audio' },
  { id: 'identity', labelKey: 'tab.identity' },
  { id: 'privacy',  labelKey: 'tab.privacy' },
];

/** Known LLM provider privacy policy URLs. */
const PROVIDER_PRIVACY_URLS: Record<string, string> = {
  anthropic: 'https://www.anthropic.com/legal/privacy',
  openai:    'https://openai.com/policies/privacy-policy',
  gemini:    'https://policies.google.com/privacy',
  ollama:    'https://ollama.com/privacy',
};

export class Settings {
  private el: HTMLElement;
  private saveHandler: (cfg: AppConfig) => Promise<{ok: boolean; errors?: string[]}> = async () => ({ok: true});
  private currentCfg: AppConfig | null = null;
  private activeTab: TabId = 'brain';

  constructor(parent: HTMLElement) {
    this.el = document.createElement('aside');
    this.el.className = 'va-settings';
    this.el.setAttribute('aria-modal', 'true');
    this.el.setAttribute('role', 'dialog');
    this.el.setAttribute('aria-label', 'Settings');

    this.el.innerHTML = `
      <div class="va-settings-backdrop"></div>
      <div class="va-settings-panel">
        <header class="va-settings-header">
          <h2 class="va-settings-title">${T('settings.title')}</h2>
          <button data-close type="button" aria-label="${T('settings.close')}" class="va-settings-close">×</button>
        </header>
        <div class="va-settings-body">
          <!-- Vertical tab bar -->
          <nav class="va-tab-nav" role="tablist" aria-label="Settings sections">
            ${TABS.map(t => `
              <button role="tab" id="va-tab-btn-${t.id}" data-tab="${t.id}" type="button"
                class="va-tab-btn${t.id === this.activeTab ? ' is-active' : ''}"
                aria-selected="${t.id === this.activeTab}"
                aria-controls="va-tab-${t.id}">
                ${T(t.labelKey)}
              </button>
            `).join('')}
          </nav>
          <!-- Tab panels -->
          <div class="va-tab-panels">
            ${TABS.map(t => `<div role="tabpanel" id="va-tab-${t.id}" data-panel="${t.id}" class="va-tab-panel${t.id === this.activeTab ? ' is-active' : ''}" aria-labelledby="va-tab-btn-${t.id}"></div>`).join('')}
          </div>
        </div>
        <div data-error class="hidden va-settings-error"></div>
        <!-- AI Act footer disclosure -->
        <p data-ai-footer class="va-settings-ai-footer"></p>
        <footer class="va-settings-footer">
          <button data-cancel type="button" class="va-btn va-btn--ghost">${T('settings.cancel')}</button>
          <button data-save   type="button" class="va-btn va-btn--primary">${T('settings.save')}</button>
        </footer>
      </div>
    `;
    parent.appendChild(this.el);

    this._wireEvents();
    this._injectStyles();
    this._buildPanels();
  }

  // ── Public API ────────────────────────────────────────────────────────────
  open(cfg: AppConfig): void {
    this.currentCfg = cfg;
    this._populate(cfg);
    this.el.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }

  close(): void {
    this.el.classList.remove('is-open');
    document.body.style.overflow = '';
  }

  onSave(handler: (cfg: AppConfig) => Promise<{ok: boolean; errors?: string[]}>): void {
    this.saveHandler = handler;
  }

  // ── Internal ──────────────────────────────────────────────────────────────
  private _wireEvents(): void {
    this.el.querySelector('[data-close]')!.addEventListener('click', () => this.close());
    this.el.querySelector('[data-cancel]')!.addEventListener('click', () => this.close());
    this.el.querySelector('.va-settings-backdrop')!.addEventListener('click', () => this.close());

    this.el.querySelectorAll<HTMLButtonElement>('[data-tab]').forEach(btn => {
      btn.addEventListener('click', () => this._switchTab(btn.dataset.tab as TabId));
    });

    this.el.querySelector('[data-save]')!.addEventListener('click', async () => {
      const cfg = this._read();
      const errEl = this.el.querySelector<HTMLElement>('[data-error]')!;
      const result = await this.saveHandler(cfg);
      if (result.ok) {
        errEl.classList.add('hidden');
        this.close();
      } else {
        errEl.textContent = (result.errors || ['Save failed']).join(' · ');
        errEl.classList.remove('hidden');
      }
    });
  }

  private _switchTab(id: TabId): void {
    this.activeTab = id;
    this.el.querySelectorAll<HTMLButtonElement>('[data-tab]').forEach(btn => {
      const active = btn.dataset.tab === id;
      btn.classList.toggle('is-active', active);
      btn.setAttribute('aria-selected', String(active));
    });
    this.el.querySelectorAll<HTMLElement>('[data-panel]').forEach(panel => {
      panel.classList.toggle('is-active', panel.dataset.panel === id);
    });
  }

  private _buildPanels(): void {
    this._buildBrainPanel();
    this._buildVoicePanel();
    this._buildAudioPanel();
    this._buildIdentityPanel();
    this._buildPrivacyPanel();
  }

  // ── Brain tab ─────────────────────────────────────────────────────────────
  private _buildBrainPanel(): void {
    const p = this._panel('brain');
    p.innerHTML = `
      <div class="va-field">
        <label class="va-label">Provider</label>
        <select data-field="provider" class="va-select">
          <option value="anthropic">Anthropic Claude</option>
          <option value="openai">OpenAI GPT</option>
          <option value="gemini">Google Gemini</option>
          <option value="ollama">Ollama (local)</option>
        </select>
      </div>
      <div class="va-field">
        <label class="va-label">Model</label>
        <select data-field="model" class="va-select"></select>
      </div>
      <div data-secret-row class="va-field">
        <label class="va-label flex-row">
          <span data-secret-label>API key</span>
          <span data-saved-badge class="hidden va-badge-saved">✓ saved</span>
        </label>
        <div class="va-input-wrap">
          <input data-field="secret" type="password" class="va-input" placeholder="sk-…" />
          <button type="button" data-toggle-secret aria-label="Show or hide key" class="va-eye-btn">
            <svg data-eye-show width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            <svg data-eye-hide class="hidden" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
          </button>
        </div>
        <p class="va-hint" data-secret-hint>Stored in ~/.voice-assistant/.env, mode 0600.</p>
      </div>
      <div class="va-field">
        <label class="va-label">Reply language</label>
        <select data-field="respond_in" class="va-select">
          ${REPLY_LANGUAGES.map(l => `<option value="${l.code}">${l.label}</option>`).join('')}
        </select>
        <p class="va-hint">Override auto-detection and always reply in this language.</p>
      </div>
    `;

    p.querySelector('[data-field="provider"]')!.addEventListener('change', () => {
      this._refreshSecretFields();
      this._refreshModelOptions();
    });
    p.querySelector('[data-toggle-secret]')!.addEventListener('click', () => {
      const input = p.querySelector<HTMLInputElement>('[data-field="secret"]')!;
      const show  = p.querySelector<HTMLElement>('[data-eye-show]')!;
      const hide  = p.querySelector<HTMLElement>('[data-eye-hide]')!;
      const showing = input.type === 'text';
      input.type = showing ? 'password' : 'text';
      show.classList.toggle('hidden', !showing);
      hide.classList.toggle('hidden', showing);
    });
  }

  // ── Voice tab ─────────────────────────────────────────────────────────────
  private _buildVoicePanel(): void {
    const p = this._panel('voice');
    p.innerHTML = `
      <div class="va-field">
        <label class="va-label">Avatar</label>
        <div data-field="avatar" class="va-avatar-grid"></div>
      </div>
      <div class="va-field">
        <label class="va-label">Voice</label>
        <select data-field="voice" class="va-select"></select>
        <button type="button" data-test-voice class="va-link-btn mt-2">&#9654; Test this voice</button>
      </div>
      <div class="va-field">
        <label class="va-label">Speech recognition language</label>
        <select data-field="stt_language" class="va-select"></select>
      </div>
    `;
  }

  // ── Audio tab ─────────────────────────────────────────────────────────────
  private _buildAudioPanel(): void {
    const p = this._panel('audio');
    p.innerHTML = `
      <div class="va-field">
        <label class="va-label">Trigger</label>
        <div class="va-radio-group">
          <label class="va-radio-label">
            <input type="radio" name="audio_trigger" value="hotkey" checked> Hotkey
          </label>
          <label class="va-radio-label">
            <input type="radio" name="audio_trigger" value="wake_word"> Wake word
          </label>
        </div>
      </div>
      <div data-hotkey-row class="va-field">
        <label class="va-label">Hotkey</label>
        <input data-field="hotkey" class="va-input" placeholder="ctrl+shift+space" />
      </div>
      <div data-wake-row class="va-field hidden">
        <label class="va-label">Wake word</label>
        <select data-field="wake_word" class="va-select">
          ${WAKE_WORDS.map(w => `<option value="${w}">${w.replace(/_/g, ' ')}</option>`).join('')}
        </select>
      </div>
      <div data-sensitivity-row class="va-field hidden">
        <label class="va-label">Sensitivity: <span data-sensitivity-val>0.5</span></label>
        <input data-field="wake_sensitivity" type="range" min="0" max="1" step="0.05" value="0.5" class="va-range" />
        <p class="va-hint">Higher = fewer false positives but easier to miss.</p>
      </div>
    `;
    // Wire trigger radio
    p.querySelectorAll<HTMLInputElement>('[name="audio_trigger"]').forEach(radio => {
      radio.addEventListener('change', () => this._refreshAudioTrigger(p));
    });
    // Sensitivity display
    const rangeEl = p.querySelector<HTMLInputElement>('[data-field="wake_sensitivity"]')!;
    const valEl   = p.querySelector<HTMLElement>('[data-sensitivity-val]')!;
    rangeEl.addEventListener('input', () => { valEl.textContent = rangeEl.value; });
  }

  // ── Identity tab ──────────────────────────────────────────────────────────
  private _buildIdentityPanel(): void {
    const p = this._panel('identity');
    p.innerHTML = `
      <div class="va-field">
        <label class="va-label">Your name</label>
        <input data-field="user_name" class="va-input" placeholder="(leave blank to skip)" />
      </div>
      <div class="va-field">
        <label class="va-label">How should the assistant address you?</label>
        <select data-field="user_address_as" class="va-select">
          <option value="none">Don't address me by name</option>
          <option value="first_name">By my first name</option>
          <option value="full_name">By my full name</option>
          <option value="title">By a title (Sir / Ma'am / etc)</option>
        </select>
      </div>
      <div data-title-row class="va-field hidden">
        <label class="va-label">Title</label>
        <input data-field="user_title" class="va-input" placeholder="Sir" />
      </div>
    `;
    p.querySelector('[data-field="user_address_as"]')!.addEventListener('change', () => {
      this._refreshTitleRow(p);
    });
  }

  // ── Privacy & Display tab ─────────────────────────────────────────────────
  private _buildPrivacyPanel(): void {
    const p = this._panel('privacy');
    p.innerHTML = `
      <div class="va-field">
        <label class="va-label">${T('allowed_folders.label')}</label>
        <input data-field="roots" class="va-input" placeholder="~" />
        <p class="va-hint">${T('allowed_folders.hint')}</p>
      </div>
      <!-- Display group -->
      <div class="va-section-divider"></div>
      <p class="va-section-heading">${T('display.group')}</p>
      <div class="va-field">
        <label class="va-label va-label--checkbox">
          <input data-field="display_hc" type="checkbox" />
          ${T('display.high_contrast')}
        </label>
      </div>
      <div class="va-field">
        <label class="va-label" for="display-font-size">${T('display.font_size')}</label>
        <select data-field="display_font_size" id="display-font-size" class="va-select">
          <option value="small">${T('display.font_small')}</option>
          <option value="medium" selected>${T('display.font_medium')}</option>
          <option value="large">${T('display.font_large')}</option>
          <option value="xl">${T('display.font_xl')}</option>
        </select>
      </div>
    `;
  }

  // ── Populate ──────────────────────────────────────────────────────────────
  private _populate(cfg: AppConfig): void {
    this.currentCfg = cfg;

    // Brain
    const brain = this._panel('brain');
    (brain.querySelector('[data-field="provider"]') as HTMLSelectElement).value = cfg.provider;
    (brain.querySelector('[data-field="respond_in"]') as HTMLSelectElement).value = cfg.respond_in || 'auto';
    this._refreshModelOptions();
    this._refreshSecretFields();

    // Voice
    this._refreshVoiceSection();

    // Audio
    const audio = this._panel('audio');
    const trigger = cfg.audio_trigger || 'hotkey';
    audio.querySelectorAll<HTMLInputElement>('[name="audio_trigger"]').forEach(r => {
      r.checked = r.value === trigger;
    });
    (audio.querySelector('[data-field="hotkey"]') as HTMLInputElement).value = cfg.hotkey;
    (audio.querySelector('[data-field="wake_word"]') as HTMLSelectElement).value = cfg.wake_word || 'hey_jarvis';
    const sens = cfg.wake_sensitivity ?? 0.5;
    const rangeEl = audio.querySelector<HTMLInputElement>('[data-field="wake_sensitivity"]')!;
    rangeEl.value = String(sens);
    audio.querySelector<HTMLElement>('[data-sensitivity-val]')!.textContent = String(sens);
    this._refreshAudioTrigger(audio);

    // Identity
    const identity = this._panel('identity');
    (identity.querySelector('[data-field="user_name"]') as HTMLInputElement).value = cfg.user_name || '';
    (identity.querySelector('[data-field="user_address_as"]') as HTMLSelectElement).value = cfg.user_address_as || 'none';
    (identity.querySelector('[data-field="user_title"]') as HTMLInputElement).value = cfg.user_title || '';
    this._refreshTitleRow(identity);

    // Privacy & Display
    const privacy = this._panel('privacy');
    (privacy.querySelector('[data-field="roots"]') as HTMLInputElement).value = cfg.allowed_roots.join(', ');
    (privacy.querySelector('[data-field="display_hc"]') as HTMLInputElement).checked = cfg.display_theme === 'hc';
    (privacy.querySelector('[data-field="display_font_size"]') as HTMLSelectElement).value = cfg.display_font_size ?? 'medium';

    // AI Act footer
    const footerEl = this.el.querySelector<HTMLElement>('[data-ai-footer]')!;
    const provider = cfg.provider;
    const privacyUrl = PROVIDER_PRIVACY_URLS[provider] ?? '#';
    footerEl.innerHTML = `AI assistant powered by <strong>${provider}</strong>. Inputs are sent to <a href="${privacyUrl}" target="_blank" rel="noopener noreferrer" class="va-ai-footer-link">${provider} privacy policy</a>.`;
  }

  private _refreshAudioTrigger(panel: HTMLElement): void {
    const val = (panel.querySelector<HTMLInputElement>('[name="audio_trigger"]:checked')?.value) || 'hotkey';
    panel.querySelector<HTMLElement>('[data-hotkey-row]')!.classList.toggle('hidden', val !== 'hotkey');
    panel.querySelector<HTMLElement>('[data-wake-row]')!.classList.toggle('hidden', val !== 'wake_word');
    panel.querySelector<HTMLElement>('[data-sensitivity-row]')!.classList.toggle('hidden', val !== 'wake_word');
  }

  private _refreshTitleRow(panel: HTMLElement): void {
    const val = (panel.querySelector('[data-field="user_address_as"]') as HTMLSelectElement).value;
    panel.querySelector<HTMLElement>('[data-title-row]')!.classList.toggle('hidden', val !== 'title');
  }

  private _refreshModelOptions(): void {
    const brain = this._panel('brain');
    const provider = (brain.querySelector('[data-field="provider"]') as HTMLSelectElement).value as Provider;
    const select = brain.querySelector('[data-field="model"]') as HTMLSelectElement;
    const models = this.currentCfg?.available_models?.[provider] ?? [];
    const current = this.currentCfg?.model;
    select.innerHTML = '';
    const seen = new Set<string>();
    for (const m of models) {
      seen.add(m);
      select.appendChild(this._opt(m));
    }
    if (current && !seen.has(current)) select.appendChild(this._opt(current + ' (custom)', current));
    if (current) select.value = current;
  }

  private _refreshSecretFields(): void {
    const brain = this._panel('brain');
    const provider = (brain.querySelector('[data-field="provider"]') as HTMLSelectElement).value as Provider;
    const label  = brain.querySelector<HTMLElement>('[data-secret-label]')!;
    const input  = brain.querySelector<HTMLInputElement>('[data-field="secret"]')!;
    const hint   = brain.querySelector<HTMLElement>('[data-secret-hint]')!;
    const badge  = brain.querySelector<HTMLElement>('[data-saved-badge]')!;
    const showSvg = brain.querySelector<HTMLElement>('[data-eye-show]')!;
    const hideSvg = brain.querySelector<HTMLElement>('[data-eye-hide]')!;

    label.textContent = provider === 'ollama' ? 'Ollama base URL' : 'API key';
    input.value = '';
    input.type = provider === 'ollama' ? 'text' : 'password';
    showSvg.classList.remove('hidden');
    hideSvg.classList.add('hidden');

    const hasSecret = provider === this.currentCfg?.provider && this.currentCfg?.has_secret === true;
    badge.classList.toggle('hidden', !hasSecret);

    if (provider === 'ollama') {
      input.placeholder = this.currentCfg?.ollama_base_url || 'http://localhost:11434';
      hint.textContent = 'URL of your local Ollama instance.';
    } else if (hasSecret) {
      input.placeholder = '✓ key on file — leave blank to keep current';
      hint.textContent = 'Stored in ~/.voice-assistant/.env, mode 0600. Type a new key only to replace it.';
    } else {
      input.placeholder = provider === 'anthropic' ? 'sk-ant-…' : provider === 'openai' ? 'sk-…' : 'AIza…';
      hint.textContent = 'Stored in ~/.voice-assistant/.env, mode 0600.';
    }
  }

  private _refreshVoiceSection(): void {
    const voice = this._panel('voice');

    // Avatars
    const avatars = this.currentCfg?.available_avatars ?? ['aria', 'liam', 'sage'];
    const grid = voice.querySelector<HTMLElement>('[data-field="avatar"]')!;
    grid.innerHTML = '';
    for (const name of avatars) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'va-avatar-btn';
      btn.dataset.avatar = name;
      const isSelected = name === (this.currentCfg?.avatar ?? 'aria');
      btn.setAttribute('aria-pressed', String(isSelected));
      if (isSelected) btn.classList.add('is-selected');
      btn.innerHTML = `<img src="avatars/${name}.svg" alt="${name}" class="va-avatar-img" /><p class="va-avatar-name">${name}</p>`;
      btn.addEventListener('click', () => {
        grid.querySelectorAll<HTMLButtonElement>('.va-avatar-btn').forEach(b => {
          b.setAttribute('aria-pressed', 'false');
          b.classList.remove('is-selected');
        });
        btn.setAttribute('aria-pressed', 'true');
        btn.classList.add('is-selected');
      });
      grid.appendChild(btn);
    }

    // Voices grouped by language
    const voices = this.currentCfg?.available_voices ?? [];
    const vSelect = voice.querySelector<HTMLSelectElement>('[data-field="voice"]')!;
    vSelect.innerHTML = '';
    const byLang: Record<string, typeof voices> = {};
    for (const v of voices) { (byLang[v.language] ??= []).push(v); }
    const langOrder = Object.keys(byLang).sort((a, b) => a === 'en' ? -1 : b === 'en' ? 1 : a.localeCompare(b));
    for (const lang of langOrder) {
      const og = document.createElement('optgroup');
      const firstLabel = byLang[lang][0].label;
      const match = firstLabel.match(/\(([^)]+)\)/);
      og.label = match ? match[1] : (lang === 'en' ? 'English' : lang);
      for (const v of byLang[lang]) {
        og.appendChild(this._opt(v.notes ? `${v.label} · ${v.notes}` : v.label, v.id));
      }
      vSelect.appendChild(og);
    }
    if (this.currentCfg?.voice) vSelect.value = this.currentCfg.voice;

    // STT languages
    const sttLangs = this.currentCfg?.available_stt_languages ?? [];
    const sttSelect = voice.querySelector<HTMLSelectElement>('[data-field="stt_language"]')!;
    sttSelect.innerHTML = '';
    for (const l of sttLangs) { sttSelect.appendChild(this._opt(l.label, l.code)); }
    if (this.currentCfg?.stt_language) sttSelect.value = this.currentCfg.stt_language;
  }

  // ── Read ──────────────────────────────────────────────────────────────────
  private _read(): AppConfig {
    const brain    = this._panel('brain');
    const voiceP   = this._panel('voice');
    const audio    = this._panel('audio');
    const identity = this._panel('identity');
    const privacy  = this._panel('privacy');

    const provider  = (brain.querySelector('[data-field="provider"]') as HTMLSelectElement).value as Provider;
    const model     = (brain.querySelector('[data-field="model"]') as HTMLSelectElement).value.trim();
    const secret    = (brain.querySelector('[data-field="secret"]') as HTMLInputElement).value.trim();
    const respond_in = (brain.querySelector('[data-field="respond_in"]') as HTMLSelectElement).value;

    const voice       = (voiceP.querySelector('[data-field="voice"]') as HTMLSelectElement)?.value || this.currentCfg?.voice || 'piper:en_US-amy-medium';
    const stt_language = (voiceP.querySelector('[data-field="stt_language"]') as HTMLSelectElement)?.value || this.currentCfg?.stt_language || 'auto';
    const avatarBtn   = voiceP.querySelector<HTMLElement>('[data-field="avatar"] [aria-pressed="true"]');
    const avatar      = (avatarBtn as HTMLElement & {dataset: DOMStringMap})?.dataset.avatar ?? this.currentCfg?.avatar ?? 'aria';

    const triggerRadio = audio.querySelector<HTMLInputElement>('[name="audio_trigger"]:checked');
    const audio_trigger = triggerRadio?.value || 'hotkey';
    const hotkey      = (audio.querySelector('[data-field="hotkey"]') as HTMLInputElement).value.trim() || 'ctrl+shift+space';
    const wake_word   = (audio.querySelector('[data-field="wake_word"]') as HTMLSelectElement).value || 'hey_jarvis';
    const wake_sensitivity = parseFloat((audio.querySelector('[data-field="wake_sensitivity"]') as HTMLInputElement).value || '0.5');

    const user_name     = (identity.querySelector('[data-field="user_name"]') as HTMLInputElement).value.trim() || null;
    const user_address_as = (identity.querySelector('[data-field="user_address_as"]') as HTMLSelectElement).value as AppConfig['user_address_as'];
    const user_title    = (identity.querySelector('[data-field="user_title"]') as HTMLInputElement).value.trim() || null;

    const roots = (privacy.querySelector('[data-field="roots"]') as HTMLInputElement).value
      .split(',').map(s => s.trim()).filter(Boolean);
    const display_hc = (privacy.querySelector('[data-field="display_hc"]') as HTMLInputElement).checked;
    const display_font_size = (privacy.querySelector('[data-field="display_font_size"]') as HTMLSelectElement).value as AppConfig['display_font_size'];

    const cfg: AppConfig & { _secret?: string } = {
      provider, model, hotkey,
      allowed_roots: roots,
      ollama_base_url: provider === 'ollama' ? (secret || this.currentCfg?.ollama_base_url || 'http://localhost:11434') : null,
      user_name, user_address_as, user_title,
      respond_in,
      voice, stt_language, avatar,
      audio_trigger, wake_word, wake_sensitivity,
      display_theme: display_hc ? 'hc' : 'default',
      display_font_size: display_font_size ?? 'medium',
      // preserve pass-through fields
      locale: this.currentCfg?.locale,
      transparency_acknowledged: this.currentCfg?.transparency_acknowledged,
    };
    if (provider !== 'ollama' && secret) cfg._secret = secret;
    return cfg;
  }

  // ── Helpers ───────────────────────────────────────────────────────────────
  private _panel(id: TabId): HTMLElement {
    return this.el.querySelector<HTMLElement>(`[data-panel="${id}"]`)!;
  }

  private _opt(label: string, value?: string): HTMLOptionElement {
    const opt = document.createElement('option');
    opt.textContent = label;
    opt.value = value ?? label;
    return opt;
  }

  private _injectStyles(): void {
    if (document.querySelector('#va-settings-style')) return;
    const s = document.createElement('style');
    s.id = 'va-settings-style';
    s.textContent = `
      .va-settings {
        position: fixed;
        inset: 0;
        z-index: 40;
        pointer-events: none;
        opacity: 0;
        transition: opacity 200ms ease;
      }
      .va-settings.is-open {
        pointer-events: auto;
        opacity: 1;
      }
      .va-settings-backdrop {
        position: absolute;
        inset: 0;
        background: rgba(0,0,0,0.45);
        backdrop-filter: blur(2px);
      }
      .va-settings-panel {
        position: absolute;
        top: 0; right: 0; bottom: 0;
        width: min(480px, 100vw);
        background: rgba(16, 18, 28, 0.96);
        backdrop-filter: blur(20px);
        border-left: 1px solid rgba(255,255,255,0.08);
        display: flex;
        flex-direction: column;
        transform: translateX(40px);
        transition: transform 200ms cubic-bezier(0.2, 0.8, 0.2, 1);
      }
      .va-settings.is-open .va-settings-panel { transform: translateX(0); }

      .va-settings-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 52px;
        padding: 0 18px;
        border-bottom: 1px solid rgba(255,255,255,0.07);
        flex-shrink: 0;
      }
      .va-settings-title { font-size: 0.875rem; font-weight: 600; color: #e8e8f0; }
      .va-settings-close {
        width: 32px; height: 32px;
        display: grid; place-items: center;
        border-radius: 8px; border: none;
        background: transparent; color: rgba(200,200,220,0.5);
        font-size: 1.2rem; cursor: pointer;
        transition: background 150ms ease, color 150ms ease;
      }
      .va-settings-close:hover { background: rgba(255,255,255,0.06); color: #e8e8f0; }

      .va-settings-body {
        display: flex;
        flex: 1;
        min-height: 0;
        overflow: hidden;
      }

      /* Vertical tab nav */
      .va-tab-nav {
        display: flex;
        flex-direction: column;
        width: 100px;
        border-right: 1px solid rgba(255,255,255,0.06);
        padding: 10px 0;
        flex-shrink: 0;
        gap: 2px;
      }
      .va-tab-btn {
        padding: 10px 14px;
        font-size: 0.78rem;
        font-weight: 500;
        text-align: start;
        background: transparent;
        border: none;
        color: rgba(180,185,210,0.6);
        cursor: pointer;
        border-radius: 0;
        transition: background 150ms ease, color 150ms ease;
      }
      .va-tab-btn:hover { background: rgba(255,255,255,0.04); color: rgba(200,205,230,0.9); }
      .va-tab-btn.is-active {
        color: #c5bfff;
        background: rgba(149,128,255,0.1);
      }

      /* Tab panels */
      .va-tab-panels { flex: 1; overflow-y: auto; padding: 18px 16px; }
      .va-tab-panel { display: none; flex-direction: column; gap: 16px; }
      .va-tab-panel.is-active { display: flex; }

      /* Form fields */
      .va-field { display: flex; flex-direction: column; gap: 5px; }
      .va-label { font-size: 0.75rem; font-weight: 500; color: rgba(180,185,210,0.7); }
      .va-label.flex-row { display: flex; align-items: center; justify-content: space-between; }
      .va-input, .va-select {
        height: 38px;
        padding: 0 10px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.1);
        background: rgba(20,24,36,0.8);
        color: #dde0f0;
        font: inherit;
        font-size: 0.83rem;
        outline: none;
        transition: border-color 150ms ease;
      }
      .va-input:focus, .va-select:focus { border-color: rgba(149,128,255,0.5); }
      .va-hint { font-size: 0.7rem; color: rgba(160,165,190,0.5); margin: 0; }
      .va-input-wrap { position: relative; }
      .va-input-wrap .va-input { width: 100%; padding-right: 42px; }
      .va-eye-btn {
        position: absolute; right: 2px; top: 2px;
        height: 34px; width: 38px;
        display: grid; place-items: center;
        border: none; background: transparent;
        color: rgba(160,165,190,0.5); cursor: pointer;
        border-radius: 6px;
        transition: color 150ms ease;
      }
      .va-eye-btn:hover { color: #dde0f0; }
      .va-badge-saved { font-size: 0.68rem; color: #5be080; font-weight: 600; }

      /* Avatar grid */
      .va-avatar-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
      .va-avatar-btn {
        border-radius: 10px; border: 2px solid rgba(255,255,255,0.08);
        padding: 8px; background: rgba(20,24,36,0.6);
        cursor: pointer; transition: border-color 150ms ease;
      }
      .va-avatar-btn:hover { border-color: rgba(149,128,255,0.3); }
      .va-avatar-btn.is-selected { border-color: #9580ff; }
      .va-avatar-img { width: 56px; height: 56px; border-radius: 50%; display: block; margin: 0 auto; }
      .va-avatar-name { font-size: 0.68rem; text-align: center; margin-top: 4px; text-transform: capitalize; color: rgba(180,185,210,0.7); }

      /* Radio group */
      .va-radio-group { display: flex; gap: 16px; }
      .va-radio-label { display: flex; align-items: center; gap: 6px; font-size: 0.83rem; color: rgba(180,185,210,0.8); cursor: pointer; }
      .va-radio-label input[type="radio"] { accent-color: #9580ff; }

      /* Range */
      .va-range { width: 100%; accent-color: #9580ff; }

      .va-link-btn { background: none; border: none; color: rgba(149,128,255,0.8); font-size: 0.75rem; cursor: pointer; padding: 0; }
      .va-link-btn:hover { color: #9580ff; text-decoration: underline; }
      .mt-2 { margin-top: 6px; }

      /* Footer */
      .va-settings-footer {
        display: flex; justify-content: flex-end; gap: 8px;
        padding: 14px 18px;
        border-top: 1px solid rgba(255,255,255,0.07);
        flex-shrink: 0;
      }
      .va-btn {
        height: 36px; padding: 0 16px;
        border-radius: 8px; font: inherit;
        font-size: 0.82rem; font-weight: 600;
        cursor: pointer; transition: opacity 150ms ease, background 150ms ease;
      }
      .va-btn--ghost {
        background: transparent;
        border: 1px solid rgba(255,255,255,0.1);
        color: rgba(180,185,210,0.8);
      }
      .va-btn--ghost:hover { background: rgba(255,255,255,0.05); }
      .va-btn--primary { background: #9580ff; border: none; color: #0b0d10; }
      .va-btn--primary:hover { opacity: 0.88; }

      .va-settings-error {
        padding: 8px 18px;
        font-size: 0.78rem;
        color: #ff8080;
        border-top: 1px solid rgba(255,255,255,0.05);
      }
      .va-settings-error.hidden { display: none; }

      /* AI Act footer */
      .va-settings-ai-footer {
        padding: 6px 18px;
        font-size: 0.68rem;
        color: rgba(160,165,190,0.45);
        border-top: 1px solid rgba(255,255,255,0.04);
        margin: 0;
      }
      .va-ai-footer-link {
        color: rgba(149,128,255,0.6);
        text-decoration: none;
      }
      .va-ai-footer-link:hover { text-decoration: underline; }

      /* Display section divider */
      .va-section-divider {
        height: 1px;
        background: rgba(255,255,255,0.07);
        margin: 4px 0;
      }
      .va-section-heading {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: rgba(180,185,210,0.4);
        margin: 0;
      }
      /* Checkbox label */
      .va-label--checkbox {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        font-size: 0.83rem;
        color: rgba(180,185,210,0.8);
      }
      .va-label--checkbox input[type="checkbox"] { accent-color: #9580ff; }

      /* RTL: flip the active-tab indicator from left to inline-start */
      .va-tab-btn {
        border-inline-start: 2px solid transparent;
        border-left: none;
      }
      .va-tab-btn.is-active { border-inline-start-color: #9580ff; }

      /* High-contrast overrides */
      [data-theme="hc"] {
        --color-bg: #000;
        --color-fg: #fff;
        --color-surface: #1a1a1a;
        --color-border: #fff;
        --color-accent: #ffd400;
      }
      [data-theme="hc"] .va-settings-panel,
      [data-theme="hc"] .va-transparency-panel {
        background: #1a1a1a;
        border-color: #fff;
        color: #fff;
      }
      [data-theme="hc"] .va-input,
      [data-theme="hc"] .va-select {
        background: #000;
        color: #fff;
        border-color: #fff;
      }
      [data-theme="hc"] .va-btn--primary {
        background: #ffd400;
        color: #000;
      }
    `;
    document.head.appendChild(s);
  }
}
