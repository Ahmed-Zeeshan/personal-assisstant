export class Composer {
  private el: HTMLElement;
  private input: HTMLInputElement;
  private submitHandler: (text: string) => void = () => {};
  private recordHandler: () => void = () => {};

  constructor(parent: HTMLElement) {
    this.el = document.createElement('footer');
    this.el.className = 'p-4 border-t border-border bg-surface/40 flex gap-2';
    this.el.innerHTML = `
      <button data-record aria-label="Hold to record"
        class="h-11 w-11 shrink-0 grid place-items-center rounded-md border border-border bg-surface hover:border-accent/40 transition-colors">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <rect x="9" y="2" width="6" height="12" rx="3"/>
          <path d="M5 10v2a7 7 0 0 0 14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="22"/>
        </svg>
      </button>
      <input data-input type="text" placeholder="Type a command..."
        class="flex-1 h-11 px-4 rounded-md border border-border bg-bg text-fg placeholder:text-dim focus:outline-none focus:border-accent" />
    `;
    parent.appendChild(this.el);
    this.input = this.el.querySelector<HTMLInputElement>('[data-input]')!;
    this.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && this.input.value.trim()) {
        this.submitHandler(this.input.value.trim());
        this.input.value = '';
      }
    });
    this.el.querySelector<HTMLButtonElement>('[data-record]')!
      .addEventListener('click', () => this.recordHandler());
  }

  onSubmit(handler: (text: string) => void): void { this.submitHandler = handler; }
  onRecord(handler: () => void): void { this.recordHandler = handler; }
}
