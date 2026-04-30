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
    this.refreshModelOptions();
    this.refreshSecretFields();
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
    const provider = (this.el.querySelector('[data-field="provider"]') as HTMLSelectElement).value as Provider;
    const model    = (this.el.querySelector('[data-field="model"]') as HTMLSelectElement).value.trim();
    const hotkey   = (this.el.querySelector('[data-field="hotkey"]') as HTMLInputElement).value.trim();
    const roots    = (this.el.querySelector('[data-field="roots"]') as HTMLInputElement).value
      .split(',').map(s => s.trim()).filter(Boolean);
    const secret   = (this.el.querySelector('[data-field="secret"]') as HTMLInputElement).value.trim();
    const cfg: AppConfig & { _secret?: string } = {
      provider, model, hotkey,
      allowed_roots: roots,
      ollama_base_url: provider === 'ollama' ? (secret || this.currentCfg?.ollama_base_url || 'http://localhost:11434') : null,
    };
    if (provider !== 'ollama' && secret) cfg._secret = secret;
    return cfg;
  }
}
