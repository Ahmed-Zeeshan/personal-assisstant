/**
 * TransparencyModal — EU AI Act first-run disclosure.
 *
 * Shows once on first launch (when config.transparency_acknowledged is false).
 * Persists acknowledgement via the onAck callback (which calls bridge.saveConfig).
 */
import { T } from '../i18n';

export class TransparencyModal {
  private el: HTMLElement;
  private _visible = false;

  constructor(parent: HTMLElement) {
    this.el = document.createElement('div');
    this.el.className = 'va-transparency-modal';
    this.el.setAttribute('role', 'dialog');
    this.el.setAttribute('aria-modal', 'true');
    this.el.setAttribute('aria-labelledby', 'va-transparency-title');
    this.el.setAttribute('aria-describedby', 'va-transparency-body');
    this.el.innerHTML = `
      <div class="va-transparency-backdrop"></div>
      <div class="va-transparency-panel" role="document">
        <h2 id="va-transparency-title" class="va-transparency-title"></h2>
        <p  id="va-transparency-body"  class="va-transparency-body"></p>
        <footer class="va-transparency-footer">
          <button data-ok type="button" class="va-btn va-btn--primary va-transparency-ok"></button>
        </footer>
      </div>
    `;
    parent.appendChild(this.el);
    this._injectStyles();
  }

  show(_provider: string, onAck: () => Promise<void>): void {
    if (this._visible) return;
    this._visible = true;

    const titleEl = this.el.querySelector<HTMLElement>('#va-transparency-title')!;
    const bodyEl  = this.el.querySelector<HTMLElement>('#va-transparency-body')!;
    const okBtn   = this.el.querySelector<HTMLButtonElement>('[data-ok]')!;

    titleEl.textContent = T('transparency.title');
    bodyEl.textContent  = T('transparency.body');
    okBtn.textContent   = T('transparency.ok');

    this.el.classList.add('is-open');
    document.body.style.overflow = 'hidden';
    okBtn.focus();

    const close = async () => {
      this.el.classList.remove('is-open');
      document.body.style.overflow = '';
      this._visible = false;
      await onAck();
    };

    okBtn.onclick = () => { void close(); };

    // Keyboard: Enter / Space on OK button handled natively; Escape is intentionally
    // disabled — the user must actively acknowledge.
  }

  private _injectStyles(): void {
    if (document.querySelector('#va-transparency-style')) return;
    const s = document.createElement('style');
    s.id = 'va-transparency-style';
    s.textContent = `
      .va-transparency-modal {
        position: fixed;
        inset: 0;
        z-index: 60;
        pointer-events: none;
        opacity: 0;
        transition: opacity 200ms ease;
      }
      .va-transparency-modal.is-open {
        pointer-events: auto;
        opacity: 1;
      }
      .va-transparency-backdrop {
        position: absolute;
        inset: 0;
        background: rgba(0,0,0,0.7);
        backdrop-filter: blur(4px);
      }
      .va-transparency-panel {
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        width: min(480px, 90vw);
        background: rgba(16, 18, 28, 0.98);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 28px 24px 20px;
        display: flex;
        flex-direction: column;
        gap: 16px;
      }
      .va-transparency-title {
        font-size: 1rem;
        font-weight: 700;
        color: #e8e8f0;
        margin: 0;
      }
      .va-transparency-body {
        font-size: 0.875rem;
        line-height: 1.6;
        color: rgba(200,205,220,0.85);
        margin: 0;
      }
      .va-transparency-footer {
        display: flex;
        justify-content: flex-end;
      }
      .va-transparency-ok {
        min-width: 120px;
      }
    `;
    document.head.appendChild(s);
  }
}
