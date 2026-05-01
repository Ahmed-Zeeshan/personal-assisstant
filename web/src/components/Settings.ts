import type { AppConfig, Provider } from '../types';

export class Settings {
  private el: HTMLElement;
  private saveHandler: (cfg: AppConfig) => Promise<{ok: boolean; errors?: string[]}> = async () => ({ok: true});
  private currentCfg: AppConfig | null = null;

  constructor(parent: HTMLElement) {
    this.el = document.createElement('aside');
    this.el.className = 'fixed inset-y-0 right-0 w-full max-w-md bg-surface border-l border-border translate-x-full transition-transform duration-200 ease-out z-30 flex flex-col';
    this.el.innerHTML = `
      <header class="h-12 px-5 flex items-center justify-between border-b border-border">
        <h2 class="font-semibold">Settings</h2>
        <button data-close class="h-9 w-9 grid place-items-center rounded-md hover:bg-bg/40 text-muted hover:text-fg">×</button>
      </header>
      <form data-form class="flex-1 overflow-y-auto p-5 space-y-5 text-sm">
        <div>
          <label class="block text-muted mb-1">Provider</label>
          <select data-field="provider" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg">
            <option value="anthropic">Anthropic Claude</option>
            <option value="openai">OpenAI GPT</option>
            <option value="gemini">Google Gemini</option>
            <option value="ollama">Ollama (local)</option>
          </select>
        </div>
        <div>
          <label class="block text-muted mb-1">Model</label>
          <select data-field="model" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg"></select>
        </div>
        <div data-secret-row>
          <label class="flex items-center justify-between text-muted mb-1">
            <span data-secret-label>API key</span>
            <span data-saved-badge class="hidden text-success text-xs font-medium">✓ saved</span>
          </label>
          <div class="relative">
            <input data-field="secret" type="password" class="w-full h-10 px-3 pr-12 rounded-md border border-border bg-bg text-fg" placeholder="sk-…" />
            <button type="button" data-toggle-secret aria-label="Show or hide key"
              class="absolute right-1 top-1 h-8 w-10 grid place-items-center rounded text-dim hover:text-fg hover:bg-surface">
              <svg data-eye-show width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <svg data-eye-hide class="hidden" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
            </button>
          </div>
          <p class="text-xs text-dim mt-1" data-secret-hint>Stored in ~/.voice-assistant/.env, mode 0600.</p>
        </div>
        <div>
          <label class="block text-muted mb-1">Hotkey</label>
          <input data-field="hotkey" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg" placeholder="ctrl+shift+space" />
        </div>
        <div>
          <label class="block text-muted mb-1">Allowed folders (comma-separated)</label>
          <input data-field="roots" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg" placeholder="~" />
        </div>
        <div class="border-t border-border pt-5 space-y-3">
          <h3 class="font-medium text-fg">Voice &amp; Avatar</h3>
          <div>
            <label class="block text-muted mb-1">Avatar</label>
            <div data-field="avatar" class="grid grid-cols-3 gap-2"></div>
          </div>
          <div>
            <label class="block text-muted mb-1">Voice</label>
            <select data-field="voice" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg"></select>
            <button type="button" data-test-voice
              class="mt-2 text-xs text-accent hover:underline">&#9654; Test this voice</button>
          </div>
          <div>
            <label class="block text-muted mb-1">Speech recognition language</label>
            <select data-field="stt_language" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg"></select>
          </div>
        </div>
        <div class="border-t border-border pt-5 space-y-3">
          <h3 class="font-medium text-fg">Identity</h3>
          <div>
            <label class="block text-muted mb-1">Your name</label>
            <input data-field="user_name" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg" placeholder="(leave blank to skip)" />
          </div>
          <div>
            <label class="block text-muted mb-1">How should the assistant address you?</label>
            <select data-field="user_address_as" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg">
              <option value="none">Don't address me by name</option>
              <option value="first_name">By my first name</option>
              <option value="full_name">By my full name</option>
              <option value="title">By a title (Sir / Ma'am / etc)</option>
            </select>
          </div>
          <div data-title-row class="hidden">
            <label class="block text-muted mb-1">Title</label>
            <input data-field="user_title" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg" placeholder="Sir" />
          </div>
        </div>
        <div data-error class="hidden text-warn text-xs"></div>
      </form>
      <footer class="p-5 border-t border-border flex justify-end gap-2">
        <button data-cancel type="button" class="h-10 px-4 rounded-md border border-border text-fg hover:bg-bg/40">Cancel</button>
        <button data-save   type="button" class="h-10 px-4 rounded-md bg-accent text-bg font-semibold hover:opacity-90">Save</button>
      </footer>
    `;
    parent.appendChild(this.el);

    this.el.querySelector<HTMLButtonElement>('[data-close]')!.addEventListener('click', () => this.close());
    this.el.querySelector<HTMLButtonElement>('[data-cancel]')!.addEventListener('click', () => this.close());
    this.el.querySelector<HTMLSelectElement>('[data-field="provider"]')!.addEventListener('change', () => {
      this.refreshSecretFields();
      this.refreshModelOptions();
    });
    this.el.querySelector<HTMLSelectElement>('[data-field="user_address_as"]')!.addEventListener('change', () => {
      this.refreshTitleRow();
    });
    this.el.querySelector<HTMLButtonElement>('[data-toggle-secret]')!.addEventListener('click', () => {
      const input = this.el.querySelector<HTMLInputElement>('[data-field="secret"]')!;
      const show = this.el.querySelector<HTMLElement>('[data-eye-show]')!;
      const hide = this.el.querySelector<HTMLElement>('[data-eye-hide]')!;
      const showing = input.type === 'text';
      input.type = showing ? 'password' : 'text';
      show.classList.toggle('hidden', !showing);
      hide.classList.toggle('hidden', showing);
    });
    this.el.querySelector<HTMLButtonElement>('[data-save]')!.addEventListener('click', async () => {
      const cfg = this.read();
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

  open(cfg: AppConfig): void {
    this.populate(cfg);
    this.el.classList.remove('translate-x-full');
  }

  close(): void {
    this.el.classList.add('translate-x-full');
  }

  onSave(handler: (cfg: AppConfig) => Promise<{ok: boolean; errors?: string[]}>): void {
    this.saveHandler = handler;
  }

  private populate(cfg: AppConfig): void {
    this.currentCfg = cfg;
    (this.el.querySelector('[data-field="provider"]') as HTMLSelectElement).value = cfg.provider;
    (this.el.querySelector('[data-field="hotkey"]') as HTMLInputElement).value = cfg.hotkey;
    (this.el.querySelector('[data-field="roots"]') as HTMLInputElement).value = cfg.allowed_roots.join(', ');
    (this.el.querySelector('[data-field="user_name"]') as HTMLInputElement).value = cfg.user_name || '';
    (this.el.querySelector('[data-field="user_address_as"]') as HTMLSelectElement).value = cfg.user_address_as || 'none';
    (this.el.querySelector('[data-field="user_title"]') as HTMLInputElement).value = cfg.user_title || '';
    this.refreshModelOptions();
    this.refreshSecretFields();
    this.refreshTitleRow();
    this.refreshVoiceSection();
  }

  private refreshVoiceSection(): void {
    // Avatars
    const avatars = this.currentCfg?.available_avatars ?? ['aria', 'liam', 'sage'];
    const grid = this.el.querySelector<HTMLElement>('[data-field="avatar"]')!;
    grid.innerHTML = '';
    for (const name of avatars) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'rounded-md border-2 border-border p-2 hover:border-accent transition-colors';
      btn.dataset.avatar = name;
      btn.setAttribute('aria-pressed', String(name === (this.currentCfg?.avatar ?? 'aria')));
      if (name === (this.currentCfg?.avatar ?? 'aria')) btn.classList.add('border-accent');
      btn.innerHTML = `<img src="avatars/${name}.svg" alt="${name}" class="h-16 w-16 mx-auto rounded-full" />
        <p class="mt-1 text-xs capitalize text-center">${name}</p>`;
      btn.addEventListener('click', () => {
        grid.querySelectorAll('button').forEach(b => {
          b.setAttribute('aria-pressed', 'false');
          b.classList.remove('border-accent');
          b.classList.add('border-border');
        });
        btn.setAttribute('aria-pressed', 'true');
        btn.classList.remove('border-border');
        btn.classList.add('border-accent');
      });
      grid.appendChild(btn);
    }

    // Voices grouped by language (English first, then alphabetical)
    const voices = this.currentCfg?.available_voices ?? [];
    const select = this.el.querySelector<HTMLSelectElement>('[data-field="voice"]')!;
    select.innerHTML = '';
    const byLang: Record<string, typeof voices> = {};
    for (const v of voices) { (byLang[v.language] ??= []).push(v); }
    const langOrder = Object.keys(byLang).sort((a, b) =>
      a === 'en' ? -1 : b === 'en' ? 1 : a.localeCompare(b)
    );
    for (const lang of langOrder) {
      const og = document.createElement('optgroup');
      // Extract language label from first voice's parenthetical, or fallback to code
      const firstLabel = byLang[lang][0].label;
      const match = firstLabel.match(/\(([^)]+)\)/);
      og.label = match ? match[1] : (lang === 'en' ? 'English' : lang);
      for (const v of byLang[lang]) {
        const opt = document.createElement('option');
        opt.value = v.id;
        opt.textContent = v.notes ? `${v.label} · ${v.notes}` : v.label;
        og.appendChild(opt);
      }
      select.appendChild(og);
    }
    if (this.currentCfg?.voice) select.value = this.currentCfg.voice;

    // STT languages
    const sttLangs = this.currentCfg?.available_stt_languages ?? [];
    const sttSelect = this.el.querySelector<HTMLSelectElement>('[data-field="stt_language"]')!;
    sttSelect.innerHTML = '';
    for (const l of sttLangs) {
      const opt = document.createElement('option');
      opt.value = l.code;
      opt.textContent = l.label;
      sttSelect.appendChild(opt);
    }
    if (this.currentCfg?.stt_language) sttSelect.value = this.currentCfg.stt_language;
  }

  private refreshTitleRow(): void {
    const addressAs = (this.el.querySelector('[data-field="user_address_as"]') as HTMLSelectElement).value;
    const titleRow = this.el.querySelector<HTMLElement>('[data-title-row]')!;
    titleRow.classList.toggle('hidden', addressAs !== 'title');
  }

  private refreshModelOptions(): void {
    const provider = (this.el.querySelector('[data-field="provider"]') as HTMLSelectElement).value as Provider;
    const select = this.el.querySelector('[data-field="model"]') as HTMLSelectElement;
    const models = this.currentCfg?.available_models?.[provider] ?? [];
    const current = this.currentCfg?.model;

    select.innerHTML = '';
    const seen = new Set<string>();
    for (const m of models) {
      seen.add(m);
      select.appendChild(this.makeOption(m));
    }
    // If the saved config has a model not in the curated list (custom), keep it as an option.
    if (current && !seen.has(current)) {
      select.appendChild(this.makeOption(current + ' (custom)', current));
    }
    if (current && seen.has(current)) {
      select.value = current;
    }
  }

  private makeOption(label: string, value?: string): HTMLOptionElement {
    const opt = document.createElement('option');
    opt.textContent = label;
    opt.value = value ?? label;
    return opt;
  }

  private refreshSecretFields(): void {
    const provider = (this.el.querySelector('[data-field="provider"]') as HTMLSelectElement).value as Provider;
    const label = this.el.querySelector<HTMLElement>('[data-secret-label]')!;
    const input = this.el.querySelector<HTMLInputElement>('[data-field="secret"]')!;
    const hint  = this.el.querySelector<HTMLElement>('[data-secret-hint]')!;
    const badge = this.el.querySelector<HTMLElement>('[data-saved-badge]')!;
    const showSvg = this.el.querySelector<HTMLElement>('[data-eye-show]')!;
    const hideSvg = this.el.querySelector<HTMLElement>('[data-eye-hide]')!;

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
      input.placeholder = provider === 'anthropic' ? 'sk-ant-…'
        : provider === 'openai' ? 'sk-…'
        : 'AIza…';
      hint.textContent = 'Stored in ~/.voice-assistant/.env, mode 0600.';
    }
  }

  private read(): AppConfig {
    const provider      = (this.el.querySelector('[data-field="provider"]') as HTMLSelectElement).value as Provider;
    const model         = (this.el.querySelector('[data-field="model"]') as HTMLSelectElement).value.trim();
    const hotkey        = (this.el.querySelector('[data-field="hotkey"]') as HTMLInputElement).value.trim();
    const roots         = (this.el.querySelector('[data-field="roots"]') as HTMLInputElement).value
      .split(',').map(s => s.trim()).filter(Boolean);
    const secret        = (this.el.querySelector('[data-field="secret"]') as HTMLInputElement).value.trim();
    const user_name     = (this.el.querySelector('[data-field="user_name"]') as HTMLInputElement).value.trim() || null;
    const user_address_as = (this.el.querySelector('[data-field="user_address_as"]') as HTMLSelectElement).value as AppConfig['user_address_as'];
    const user_title    = (this.el.querySelector('[data-field="user_title"]') as HTMLInputElement).value.trim() || null;

    const voiceEl    = this.el.querySelector<HTMLSelectElement>('[data-field="voice"]');
    const sttLangEl  = this.el.querySelector<HTMLSelectElement>('[data-field="stt_language"]');
    const avatarBtn  = this.el.querySelector<HTMLElement>('[data-field="avatar"] [aria-pressed="true"]');
    const voice       = voiceEl?.value || this.currentCfg?.voice || 'piper:en_US-amy-medium';
    const stt_language = sttLangEl?.value || this.currentCfg?.stt_language || 'auto';
    const avatar      = (avatarBtn as HTMLElement & { dataset: DOMStringMap })?.dataset.avatar ?? this.currentCfg?.avatar ?? 'aria';

    const cfg: AppConfig & { _secret?: string } = {
      provider, model, hotkey,
      allowed_roots: roots,
      ollama_base_url: provider === 'ollama' ? (secret || this.currentCfg?.ollama_base_url || 'http://localhost:11434') : null,
      user_name, user_address_as, user_title,
      voice, stt_language, avatar,
    };
    if (provider !== 'ollama' && secret) cfg._secret = secret;
    return cfg;
  }
}
