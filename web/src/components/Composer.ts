/**
 * Composer — text input + mic button + send button.
 *
 * Public API (unchanged from original):
 *   onSubmit(handler)  – called with trimmed text when user submits
 *   onRecord(handler)  – called when mic button is clicked
 *
 * New behaviour:
 *   - Auto-grow textarea (1-4 lines)
 *   - Enter sends; Shift+Enter inserts newline
 *   - Mic button: idle (mic icon) | listening (pulsing red dot)
 *   - Send button (paper-airplane) visible when textarea has text
 */
import { T } from '../i18n';

export class Composer {
  private el: HTMLElement;
  private input: HTMLTextAreaElement;
  private micBtn: HTMLButtonElement;
  private sendBtn: HTMLButtonElement;
  private submitHandler: (text: string) => void = () => {};
  private recordHandler: () => void = () => {};

  constructor(parent: HTMLElement) {
    this.el = document.createElement('footer');
    this.el.className = 'va-composer';
    this.el.innerHTML = `
      <div class="va-composer-inner glass">
        <button data-record type="button" aria-label="${T('composer.start_listening')}" class="va-mic-btn" title="${T('composer.start_listening')}">
          <span data-mic-icon class="va-mic-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <rect x="9" y="2" width="6" height="12" rx="3"/>
              <path d="M5 10v2a7 7 0 0 0 14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="22"/>
            </svg>
          </span>
          <span data-listen-dot class="va-listen-dot hidden" aria-hidden="true"></span>
        </button>
        <textarea data-input rows="1" placeholder="${T('composer.placeholder')}"
          class="va-composer-input" aria-label="${T('composer.placeholder')}"></textarea>
        <button data-send type="button" aria-label="${T('composer.send')}" class="va-send-btn hidden" title="${T('composer.send')}">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
    `;
    parent.appendChild(this.el);

    this.input   = this.el.querySelector<HTMLTextAreaElement>('[data-input]')!;
    this.micBtn  = this.el.querySelector<HTMLButtonElement>('[data-record]')!;
    this.sendBtn = this.el.querySelector<HTMLButtonElement>('[data-send]')!;

    this._wireEvents();
    this._injectStyles();
  }

  onSubmit(handler: (text: string) => void): void { this.submitHandler = handler; }
  onRecord(handler: () => void): void { this.recordHandler = handler; }

  setListening(active: boolean): void {
    const micIcon = this.el.querySelector<HTMLElement>('[data-mic-icon]')!;
    const dot     = this.el.querySelector<HTMLElement>('[data-listen-dot]')!;
    micIcon.classList.toggle('hidden', active);
    dot.classList.toggle('hidden', !active);
    this.micBtn.setAttribute('aria-label', active ? T('composer.recording') : T('composer.start_listening'));
  }

  // ------------------------------------------------------------------
  private _wireEvents(): void {
    // Auto-grow
    this.input.addEventListener('input', () => {
      this._resize();
      this._toggleSend();
    });

    // Enter = submit; Shift+Enter = newline
    this.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this._submit();
      }
    });

    this.sendBtn.addEventListener('click', () => this._submit());
    this.micBtn.addEventListener('click', () => this.recordHandler());
  }

  private _submit(): void {
    const text = this.input.value.trim();
    if (!text) return;
    this.submitHandler(text);
    this.input.value = '';
    this._resize();
    this._toggleSend();
  }

  private _resize(): void {
    this.input.style.height = 'auto';
    const lineH = 24;   // approx 1 line in px
    const maxH  = lineH * 4 + 16;   // 4 lines + padding
    this.input.style.height = Math.min(this.input.scrollHeight, maxH) + 'px';
  }

  private _toggleSend(): void {
    const hasText = this.input.value.trim().length > 0;
    this.sendBtn.classList.toggle('hidden', !hasText);
  }

  private _injectStyles(): void {
    if (document.querySelector('#va-composer-style')) return;
    const s = document.createElement('style');
    s.id = 'va-composer-style';
    s.textContent = `
      .va-composer {
        padding: 10px 12px 12px;
        flex-shrink: 0;
      }
      .va-composer-inner {
        display: flex;
        align-items: flex-end;
        gap: 8px;
        border-radius: 16px;
        padding: 8px 10px;
      }
      .va-composer-input {
        flex: 1;
        background: transparent;
        border: none;
        outline: none;
        resize: none;
        font: inherit;
        font-size: 0.875rem;
        color: #e0e4f0;
        line-height: 1.5;
        min-height: 24px;
        max-height: 112px;
        overflow-y: auto;
        padding: 2px 0;
        scrollbar-width: thin;
        scrollbar-color: #2a2d38 transparent;
      }
      .va-composer-input::placeholder { color: rgba(160,165,190,0.5); }

      .va-mic-btn, .va-send-btn {
        flex-shrink: 0;
        width: 36px;
        height: 36px;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.1);
        background: rgba(30,34,46,0.5);
        color: rgba(180,185,210,0.8);
        display: grid;
        place-items: center;
        cursor: pointer;
        transition: background 150ms ease, color 150ms ease, border-color 150ms ease;
      }
      .va-mic-btn:hover, .va-send-btn:hover {
        background: rgba(149,128,255,0.18);
        border-color: rgba(149,128,255,0.4);
        color: #e8e6ff;
      }
      .va-send-btn { background: rgba(149,128,255,0.2); border-color: rgba(149,128,255,0.4); color: #c5bfff; }
      .va-send-btn:hover { background: rgba(149,128,255,0.35); }

      .va-mic-icon.hidden, .va-listen-dot.hidden, .va-send-btn.hidden { display: none; }
      .va-mic-icon { display: flex; }

      .va-listen-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #ff5050;
        animation: va-pulse 1s ease-in-out infinite;
      }
      @keyframes va-pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50%       { transform: scale(1.4); opacity: 0.7; }
      }
      @media (prefers-reduced-motion: reduce) {
        .va-listen-dot { animation: none; }
      }
    `;
    document.head.appendChild(s);
  }
}
