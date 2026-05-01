/**
 * ListeningWave — 20 animated vertical bars that pulse during recording.
 *
 * Visible only when the listening state is active.  Uses CSS animations with
 * random per-bar animation offsets so the wave looks organic.  Respects
 * `prefers-reduced-motion`.
 */
export class ListeningWave {
  private el: HTMLElement;
  private BAR_COUNT = 20;

  constructor(parent: HTMLElement) {
    this.el = document.createElement('div');
    this.el.className = 'va-wave hidden';
    this.el.setAttribute('aria-hidden', 'true');

    for (let i = 0; i < this.BAR_COUNT; i++) {
      const bar = document.createElement('span');
      bar.className = 'va-wave__bar';
      // Random delay so bars don't all move in sync.
      const delay = (Math.random() * 0.6).toFixed(2);
      const dur   = (0.5 + Math.random() * 0.5).toFixed(2);
      bar.style.cssText = `animation-delay: ${delay}s; animation-duration: ${dur}s;`;
      this.el.appendChild(bar);
    }
    parent.appendChild(this.el);
    this._injectStyles();
  }

  show(): void  { this.el.classList.remove('hidden'); }
  hide(): void  { this.el.classList.add('hidden'); }

  destroy(): void { this.el.remove(); }

  private _injectStyles(): void {
    if (document.querySelector('#va-wave-style')) return;
    const style = document.createElement('style');
    style.id = 'va-wave-style';
    style.textContent = `
      .va-wave {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 3px;
        height: 40px;
        padding: 0 12px;
      }
      .va-wave.hidden { display: none; }

      .va-wave__bar {
        display: inline-block;
        width: 3px;
        min-height: 4px;
        border-radius: 2px;
        background: var(--color-accent, #9580ff);
        animation: va-wave-bar 0.5s ease-in-out infinite alternate;
        transform-origin: bottom;
      }
      @keyframes va-wave-bar {
        0%   { transform: scaleY(0.2); opacity: 0.5; }
        100% { transform: scaleY(1.0); opacity: 1.0; }
      }
      @media (prefers-reduced-motion: reduce) {
        .va-wave__bar { animation: none; transform: scaleY(0.5); }
      }
    `;
    document.head.appendChild(style);
  }
}
