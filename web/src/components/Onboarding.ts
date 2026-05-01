/**
 * Onboarding — 4-slide overlay shown the first time the GUI launches
 * (or when onboarding_seen=false in config).
 *
 * Public API:
 *   show(onDone)  – show the overlay; calls onDone() when finished/skipped
 *   hide()        – hide without callback
 *
 * Re-runnable via Settings → Privacy → "Show onboarding tour again."
 * CSS-only transitions. Localised via T().
 */
import { T } from '../i18n';

interface Slide {
  titleKey: string;
  bodyKey: string;
  icon: string;
}

const SLIDES: Slide[] = [
  {
    titleKey: 'onboarding.slide1.title',
    bodyKey: 'onboarding.slide1.body',
    icon: `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
      <circle cx="12" cy="12" r="10"/>
      <path d="M12 8v4l3 3"/>
    </svg>`,
  },
  {
    titleKey: 'onboarding.slide2.title',
    bodyKey: 'onboarding.slide2.body',
    icon: `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
      <circle cx="12" cy="12" r="5"/>
      <circle cx="12" cy="12" r="9" stroke-dasharray="3 3"/>
      <circle cx="12" cy="12" r="1" fill="currentColor"/>
    </svg>`,
  },
  {
    titleKey: 'onboarding.slide3.title',
    bodyKey: 'onboarding.slide3.body',
    icon: `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
    </svg>`,
  },
  {
    titleKey: 'onboarding.slide4.title',
    bodyKey: 'onboarding.slide4.body',
    icon: `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
      <rect x="3" y="11" width="18" height="11" rx="2"/>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>`,
  },
];

export class Onboarding {
  private el: HTMLElement;
  private currentSlide = 0;
  private doneHandler: (() => void) | null = null;

  constructor(parent: HTMLElement) {
    this.el = document.createElement('div');
    this.el.className = 'va-onboarding';
    this.el.setAttribute('role', 'dialog');
    this.el.setAttribute('aria-modal', 'true');
    this.el.setAttribute('aria-label', T('onboarding.aria_label'));
    this.el.innerHTML = `
      <div class="va-onboarding-backdrop"></div>
      <div class="va-onboarding-panel">
        <button type="button" class="va-onboarding-skip" data-skip aria-label="${T('onboarding.skip')}">
          ${T('onboarding.skip')}
        </button>
        <div class="va-onboarding-slides" data-slides></div>
        <div class="va-onboarding-footer">
          <div class="va-onboarding-dots" data-dots></div>
          <div class="va-onboarding-btns">
            <button type="button" class="va-btn va-btn--ghost" data-prev>${T('onboarding.prev')}</button>
            <button type="button" class="va-btn va-btn--primary" data-next>${T('onboarding.next')}</button>
          </div>
        </div>
      </div>
    `;
    parent.appendChild(this.el);
    this._renderSlides();
    this._renderDots();
    this._wireEvents();
    this._injectStyles();
  }

  show(onDone: () => void): void {
    this.doneHandler = onDone;
    this.currentSlide = 0;
    this._update();
    this.el.classList.add('is-visible');
    document.body.style.overflow = 'hidden';
    this.el.querySelector<HTMLButtonElement>('[data-next]')?.focus();
  }

  hide(): void {
    this.el.classList.remove('is-visible');
    document.body.style.overflow = '';
  }

  // ── Private ──────────────────────────────────────────────────────────────
  private _renderSlides(): void {
    const container = this.el.querySelector('[data-slides]')!;
    container.innerHTML = SLIDES.map((slide, i) => `
      <div class="va-onboarding-slide${i === 0 ? ' is-active' : ''}" data-slide="${i}" aria-hidden="${i !== 0}">
        <div class="va-onboarding-icon">${slide.icon}</div>
        <h2 class="va-onboarding-title">${T(slide.titleKey)}</h2>
        <p class="va-onboarding-body">${T(slide.bodyKey)}</p>
      </div>
    `).join('');
  }

  private _renderDots(): void {
    const dots = this.el.querySelector('[data-dots]')!;
    dots.innerHTML = SLIDES.map((_, i) => `
      <button type="button" class="va-onboarding-dot${i === 0 ? ' is-active' : ''}"
        data-dot="${i}" aria-label="${T('onboarding.go_to_slide')} ${i + 1}">
      </button>
    `).join('');
    dots.querySelectorAll<HTMLButtonElement>('[data-dot]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.currentSlide = parseInt(btn.dataset.dot ?? '0', 10);
        this._update();
      });
    });
  }

  private _wireEvents(): void {
    this.el.querySelector('[data-skip]')!.addEventListener('click', () => this._finish());
    this.el.querySelector('[data-prev]')!.addEventListener('click', () => {
      if (this.currentSlide > 0) {
        this.currentSlide--;
        this._update();
      }
    });
    this.el.querySelector('[data-next]')!.addEventListener('click', () => {
      if (this.currentSlide < SLIDES.length - 1) {
        this.currentSlide++;
        this._update();
      } else {
        this._finish();
      }
    });
    this.el.querySelector('.va-onboarding-backdrop')!.addEventListener('click', () => this._finish());

    // Keyboard navigation
    this.el.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { this._finish(); return; }
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        if (this.currentSlide < SLIDES.length - 1) { this.currentSlide++; this._update(); }
      }
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        if (this.currentSlide > 0) { this.currentSlide--; this._update(); }
      }
    });
  }

  private _update(): void {
    const total = SLIDES.length;
    const cur = this.currentSlide;

    // Slides
    this.el.querySelectorAll<HTMLElement>('[data-slide]').forEach(s => {
      const idx = parseInt(s.dataset.slide ?? '0', 10);
      const active = idx === cur;
      s.classList.toggle('is-active', active);
      s.setAttribute('aria-hidden', String(!active));
    });

    // Dots
    this.el.querySelectorAll<HTMLElement>('[data-dot]').forEach(d => {
      d.classList.toggle('is-active', parseInt(d.dataset.dot ?? '0', 10) === cur);
    });

    // Buttons
    const prevBtn = this.el.querySelector<HTMLButtonElement>('[data-prev]')!;
    const nextBtn = this.el.querySelector<HTMLButtonElement>('[data-next]')!;
    prevBtn.disabled = cur === 0;
    nextBtn.textContent = cur === total - 1 ? T('onboarding.get_started') : T('onboarding.next');
  }

  private _finish(): void {
    this.hide();
    if (this.doneHandler) {
      this.doneHandler();
      this.doneHandler = null;
    }
  }

  private _injectStyles(): void {
    if (document.querySelector('#va-onboarding-style')) return;
    const s = document.createElement('style');
    s.id = 'va-onboarding-style';
    s.textContent = `
      .va-onboarding {
        position: fixed;
        inset: 0;
        z-index: 900;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        pointer-events: none;
        transition: opacity 250ms ease;
      }
      .va-onboarding.is-visible {
        opacity: 1;
        pointer-events: auto;
      }
      .va-onboarding-backdrop {
        position: absolute;
        inset: 0;
        background: rgba(0,0,0,0.65);
        backdrop-filter: blur(4px);
      }
      .va-onboarding-panel {
        position: relative;
        z-index: 1;
        background: #1a1d28;
        border: 1px solid rgba(149,128,255,0.25);
        border-radius: 20px;
        width: min(520px, calc(100vw - 32px));
        max-height: calc(100vh - 64px);
        overflow: hidden;
        display: flex;
        flex-direction: column;
        box-shadow: 0 32px 80px rgba(0,0,0,0.5);
      }
      .va-onboarding-skip {
        position: absolute;
        top: 16px;
        right: 16px;
        background: none;
        border: none;
        color: rgba(160,165,190,0.7);
        cursor: pointer;
        font-size: 0.8125rem;
        padding: 4px 8px;
        border-radius: 6px;
        transition: color 150ms ease, background 150ms ease;
      }
      .va-onboarding-skip:hover {
        color: #c5bfff;
        background: rgba(149,128,255,0.12);
      }
      .va-onboarding-slides {
        position: relative;
        flex: 1;
        overflow: hidden;
        min-height: 320px;
      }
      .va-onboarding-slide {
        position: absolute;
        inset: 0;
        padding: 48px 40px 32px;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        opacity: 0;
        transform: translateX(40px);
        transition: opacity 280ms ease, transform 280ms ease;
        pointer-events: none;
      }
      .va-onboarding-slide.is-active {
        opacity: 1;
        transform: translateX(0);
        pointer-events: auto;
      }
      .va-onboarding-icon {
        color: #9580ff;
        margin-bottom: 24px;
      }
      .va-onboarding-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #e0e4f0;
        margin: 0 0 12px;
      }
      .va-onboarding-body {
        font-size: 0.9375rem;
        line-height: 1.6;
        color: rgba(160,165,190,0.9);
        margin: 0;
        max-width: 380px;
      }
      .va-onboarding-footer {
        padding: 16px 24px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-top: 1px solid rgba(255,255,255,0.06);
      }
      .va-onboarding-dots {
        display: flex;
        gap: 8px;
      }
      .va-onboarding-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        border: none;
        background: rgba(160,165,190,0.3);
        cursor: pointer;
        padding: 0;
        transition: background 200ms ease, transform 200ms ease;
      }
      .va-onboarding-dot.is-active {
        background: #9580ff;
        transform: scale(1.3);
      }
      .va-onboarding-btns {
        display: flex;
        gap: 8px;
      }
      @media (prefers-reduced-motion: reduce) {
        .va-onboarding, .va-onboarding-slide { transition: none; }
      }
    `;
    document.head.appendChild(s);
  }
}
