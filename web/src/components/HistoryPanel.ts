/**
 * HistoryPanel — left-side conversation history sidebar (≥1024px only).
 *
 * Populates from `history_replay` events.  Clicking an item scrolls the
 * ChatTranscript to that turn via `data-turn-id` linking.
 */
import type { HistoryItem } from '../types';
import { T } from '../i18n';

export class HistoryPanel {
  private el: HTMLElement;
  private listEl: HTMLElement;

  constructor(parent: HTMLElement) {
    this.el = document.createElement('aside');
    this.el.className = 'va-history-panel';
    this.el.setAttribute('aria-label', 'Conversation history');

    this.el.innerHTML = `
      <div class="va-history-header">
        <span class="va-history-title">${T('history.title')}</span>
      </div>
      <div class="va-history-list"></div>
    `;
    parent.appendChild(this.el);
    this.listEl = this.el.querySelector('.va-history-list')!;
    this._injectStyles();
  }

  populate(items: HistoryItem[]): void {
    this.listEl.innerHTML = '';
    if (items.length === 0) {
      const empty = document.createElement('p');
      empty.className = 'va-history-empty';
      empty.textContent = T('history.empty');
      this.listEl.appendChild(empty);
      return;
    }
    let turnIndex = 0;
    for (const item of items) {
      if (item.speaker === 'user') {
        turnIndex++;
        const btn = document.createElement('button');
        btn.className = 'va-history-item';
        btn.type = 'button';
        btn.dataset.turnIndex = String(turnIndex);
        btn.textContent = this._truncate(item.text, 60);
        btn.title = item.text;
        btn.addEventListener('click', () => this._scrollToTurn(turnIndex));
        this.listEl.appendChild(btn);
      }
    }
  }

  private _scrollToTurn(index: number): void {
    const target = document.querySelector<HTMLElement>(
      `[data-turn-id="turn-${index}"]`
    );
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      target.classList.add('va-turn-highlight');
      setTimeout(() => target.classList.remove('va-turn-highlight'), 1200);
    }
  }

  private _truncate(text: string, max: number): string {
    return text.length <= max ? text : text.slice(0, max - 1) + '…';
  }

  destroy(): void { this.el.remove(); }

  private _injectStyles(): void {
    if (document.querySelector('#va-history-style')) return;
    const style = document.createElement('style');
    style.id = 'va-history-style';
    style.textContent = `
      .va-history-panel {
        display: none; /* hidden on narrow viewports */
        flex-direction: column;
        width: 220px;
        min-width: 180px;
        max-width: 260px;
        border-right: 1px solid rgba(255,255,255,0.07);
        background: rgba(11,13,16,0.5);
        backdrop-filter: blur(8px);
        overflow: hidden;
      }
      @media (min-width: 1024px) {
        .va-history-panel { display: flex; }
      }
      .va-history-header {
        display: flex;
        align-items: center;
        height: 48px;
        padding: 0 14px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        flex-shrink: 0;
      }
      .va-history-title {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: rgba(200,200,220,0.5);
      }
      .va-history-list {
        flex: 1;
        overflow-y: auto;
        padding: 6px 0;
        scrollbar-width: thin;
        scrollbar-color: #2a2d38 transparent;
      }
      .va-history-item {
        display: block;
        width: 100%;
        padding: 7px 14px;
        font-size: 0.75rem;
        line-height: 1.4;
        text-align: start;
        color: rgba(200,205,220,0.7);
        background: transparent;
        border: none;
        cursor: pointer;
        border-radius: 0;
        transition: background 150ms ease, color 150ms ease;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .va-history-item:hover {
        background: rgba(149,128,255,0.12);
        color: #e8e6ff;
      }
      .va-history-empty {
        padding: 14px;
        font-size: 0.75rem;
        color: rgba(200,200,220,0.35);
        text-align: center;
      }
      .va-turn-highlight {
        outline: 2px solid rgba(149,128,255,0.5);
        outline-offset: -2px;
        border-radius: 12px;
        transition: outline 0.2s ease;
      }
    `;
    document.head.appendChild(style);
  }
}
