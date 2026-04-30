type Level = 'info'|'warn'|'error';

export class Toast {
  private el: HTMLElement;
  private timer: number | null = null;

  constructor(parent: HTMLElement) {
    this.el = document.createElement('div');
    this.el.className = 'fixed top-16 left-1/2 -translate-x-1/2 px-4 py-2 rounded-md text-sm font-medium opacity-0 pointer-events-none transition-opacity duration-200 z-40';
    parent.appendChild(this.el);
  }

  show(level: Level, message: string): void {
    if (this.timer !== null) clearTimeout(this.timer);
    const colors: Record<Level, string> = {
      info:  'bg-surface border border-border text-fg',
      warn:  'bg-warn/10 border border-warn/40 text-warn',
      error: 'bg-warn/10 border border-warn/40 text-warn',
    };
    this.el.className = `fixed top-16 left-1/2 -translate-x-1/2 px-4 py-2 rounded-md text-sm font-medium opacity-100 transition-opacity duration-200 z-40 ${colors[level]}`;
    this.el.textContent = message;
    this.timer = window.setTimeout(() => {
      this.el.classList.replace('opacity-100', 'opacity-0');
    }, 4000);
  }
}
