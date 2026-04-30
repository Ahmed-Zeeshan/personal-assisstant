import type { AppConfig, Provider } from '../types';

export class Settings {
  private el: HTMLElement;
  private saveHandler: (cfg: AppConfig) => Promise<{ok: boolean; errors?: string[]}> = async () => ({ok: true});

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
          <input data-field="model" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg" />
        </div>
        <div data-secret-row>
          <label class="block text-muted mb-1" data-secret-label>API key</label>
          <input data-field="secret" type="password" class="w-full h-10 px-3 rounded-md border border-border bg-bg text-fg" placeholder="sk-…" />
          <p class="text-xs text-dim mt-1">Stored in ~/.voice-assistant/.env, mode 0600.</p>
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
    this.el.querySelector<HTMLSelectElement>('[data-field="provider"]')!.addEventListener('change', (e) => {
      const v = (e.target as HTMLSelectElement).value as Provider;
      const label = this.el.querySelector<HTMLElement>('[data-secret-label]')!;
      label.textContent = v === 'ollama' ? 'Ollama base URL' : 'API key';
      const input = this.el.querySelector<HTMLInputElement>('[data-field="secret"]')!;
      input.type = v === 'ollama' ? 'text' : 'password';
      input.placeholder = v === 'ollama' ? 'http://localhost:11434' : 'sk-…';
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
    (this.el.querySelector('[data-field="provider"]') as HTMLSelectElement).value = cfg.provider;
    (this.el.querySelector('[data-field="model"]') as HTMLInputElement).value = cfg.model;
    (this.el.querySelector('[data-field="hotkey"]') as HTMLInputElement).value = cfg.hotkey;
    (this.el.querySelector('[data-field="roots"]') as HTMLInputElement).value = cfg.allowed_roots.join(', ');
    const secret = this.el.querySelector<HTMLInputElement>('[data-field="secret"]')!;
    secret.value = '';
    secret.placeholder = cfg.provider === 'ollama' ? (cfg.ollama_base_url || 'http://localhost:11434') : 'sk-…';
    secret.type = cfg.provider === 'ollama' ? 'text' : 'password';
    const label = this.el.querySelector<HTMLElement>('[data-secret-label]')!;
    label.textContent = cfg.provider === 'ollama' ? 'Ollama base URL' : 'API key';
  }

  private read(): AppConfig {
    const provider = (this.el.querySelector('[data-field="provider"]') as HTMLSelectElement).value as Provider;
    const model    = (this.el.querySelector('[data-field="model"]') as HTMLInputElement).value.trim();
    const hotkey   = (this.el.querySelector('[data-field="hotkey"]') as HTMLInputElement).value.trim();
    const roots    = (this.el.querySelector('[data-field="roots"]') as HTMLInputElement).value
      .split(',').map(s => s.trim()).filter(Boolean);
    const secret   = (this.el.querySelector('[data-field="secret"]') as HTMLInputElement).value.trim();
    return {
      provider, model, hotkey,
      allowed_roots: roots,
      ollama_base_url: provider === 'ollama' ? (secret || 'http://localhost:11434') : null,
      ...(provider !== 'ollama' && secret ? { _secret: secret } as object : {}) as object,
    } as AppConfig & { _secret?: string };
  }
}
