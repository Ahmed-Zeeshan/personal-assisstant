export class Header {
  private el: HTMLElement;

  constructor(parent: HTMLElement) {
    this.el = document.createElement('header');
    this.el.className = 'h-12 px-5 flex items-center justify-between border-b border-border bg-surface/40';
    this.el.innerHTML = `
      <div class="flex items-center gap-3">
        <span class="font-mono text-sm">voice-assistant</span>
        <span class="text-dim text-xs">·</span>
        <span data-status class="text-xs text-muted">idle</span>
      </div>
      <button data-settings aria-label="Settings"
        class="h-9 w-9 grid place-items-center rounded-md hover:bg-bg/40 transition-colors text-muted hover:text-fg">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
      </button>
    `;
    parent.appendChild(this.el);
  }

  setStatus(value: string): void {
    const node = this.el.querySelector<HTMLElement>('[data-status]');
    if (node) node.textContent = value;
  }

  onSettingsClick(handler: () => void): void {
    this.el.querySelector<HTMLButtonElement>('[data-settings]')!
      .addEventListener('click', handler);
  }
}
