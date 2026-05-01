/**
 * ChatTranscript — chat-bubble layout replacing the plain Transcript.
 *
 * Public API matches Transcript exactly so main.ts needs no changes:
 *   push(line)          – add a complete user or assistant turn
 *   startAssistant()    – begin a streaming assistant bubble
 *   appendAssistant(t)  – append text to the streaming bubble
 *   endAssistant()      – seal the streaming bubble
 *   replayHistory(items)– populate from history (played back at startup)
 *
 * Layout:
 *   User    → right-aligned, accent/20 bg, rounded-2xl, max-w-[70%]
 *   Assistant → left-aligned, surface bg, rounded-2xl, with typing cursor during stream
 *   Tool calls → small italic line below assistant bubble
 */
import type { HistoryItem } from '../types';
import { T } from '../i18n';

export type TranscriptLine = {
  speaker: 'user' | 'assistant';
  text: string;
  tool_call?: string;
};

export class ChatTranscript {
  private el: HTMLElement;
  private streamingBubble: HTMLElement | null = null;
  private streamingBody: HTMLElement | null = null;
  private turnCounter = 0;

  constructor(parent: HTMLElement) {
    this.el = document.createElement('section');
    this.el.className = 'va-transcript flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3';
    this.el.innerHTML = `<p class="text-dim text-sm text-center mt-8 select-none">${T('transcript.prompt')}</p>`;
    parent.appendChild(this.el);
    this._injectStyles();
  }

  push(line: TranscriptLine): void {
    this._clearPlaceholder();
    const id = `turn-${++this.turnCounter}`;
    const wrapper = this._makeBubble(line.speaker, line.text, id);
    if (line.tool_call) {
      const tc = document.createElement('p');
      tc.className = 'va-tool-call text-xs text-dim italic mt-1 px-1';
      tc.textContent = `↳ ${line.tool_call}`;
      wrapper.appendChild(tc);
    }
    this.el.appendChild(wrapper);
    this._scrollToBottom();
  }

  startAssistant(): void {
    // Lazy: don't create the bubble until the first appendAssistant arrives.
    // This prevents an empty bubble appearing if the request errors before any
    // tokens stream back.
    this.streamingBubble = null;
    this.streamingBody = null;
  }

  appendAssistant(text: string): void {
    if (!this.streamingBody) {
      this._clearPlaceholder();
      const id = `turn-${++this.turnCounter}`;
      const wrapper = document.createElement('div');
      wrapper.className = 'va-bubble-row va-bubble-row--assistant va-reveal';
      wrapper.dataset.turnId = id;
      wrapper.innerHTML = `
        <div class="va-bubble va-bubble--assistant">
          <span class="va-bubble-body"></span><span class="va-cursor" aria-hidden="true">▋</span>
        </div>
      `;
      this.el.appendChild(wrapper);
      this.streamingBubble = wrapper;
      this.streamingBody = wrapper.querySelector<HTMLElement>('.va-bubble-body')!;
      requestAnimationFrame(() => wrapper.classList.add('is-visible'));
    }
    this.streamingBody.textContent = (this.streamingBody.textContent || '') + text;
    this._scrollToBottom();
  }

  endAssistant(): void {
    if (this.streamingBubble) {
      const cursor = this.streamingBubble.querySelector('.va-cursor');
      cursor?.remove();
    }
    this.streamingBubble = null;
    this.streamingBody = null;
  }

  replayHistory(items: HistoryItem[]): void {
    if (items.length === 0) return;
    this._clearPlaceholder();
    for (const item of items) {
      this.push({ speaker: item.speaker, text: item.text });
    }
  }

  // ------------------------------------------------------------------
  private _clearPlaceholder(): void {
    const p = this.el.querySelector('p.text-dim');
    if (p) p.remove();
  }

  private _makeBubble(speaker: 'user' | 'assistant', text: string, id: string): HTMLElement {
    const wrapper = document.createElement('div');
    wrapper.className = `va-bubble-row va-bubble-row--${speaker} va-reveal`;
    wrapper.dataset.turnId = id;

    const bubble = document.createElement('div');
    bubble.className = `va-bubble va-bubble--${speaker}`;

    const body = document.createElement('span');
    body.className = 'va-bubble-body';
    body.textContent = text;

    bubble.appendChild(body);
    wrapper.appendChild(bubble);

    requestAnimationFrame(() => wrapper.classList.add('is-visible'));
    return wrapper;
  }

  private _scrollToBottom(): void {
    this.el.scrollTop = this.el.scrollHeight;
  }

  private _injectStyles(): void {
    if (document.querySelector('#va-transcript-style')) return;
    const style = document.createElement('style');
    style.id = 'va-transcript-style';
    style.textContent = `
      .va-transcript { scrollbar-width: thin; scrollbar-color: #2a2d38 transparent; }
      .va-transcript::-webkit-scrollbar { width: 4px; }
      .va-transcript::-webkit-scrollbar-thumb { background: #2a2d38; border-radius: 2px; }

      .va-bubble-row {
        display: flex;
        max-width: 100%;
        opacity: 0;
        transform: translateY(8px);
        transition: opacity 200ms cubic-bezier(0.2, 0.8, 0.2, 1),
                    transform 200ms cubic-bezier(0.2, 0.8, 0.2, 1);
      }
      .va-bubble-row.is-visible { opacity: 1; transform: translateY(0); }

      /* RTL-aware alignment using logical values */
      .va-bubble-row--user    { justify-content: flex-end; }
      .va-bubble-row--assistant { justify-content: flex-start; }
      /* In RTL: user bubble aligns inline-end (right in LTR, left in RTL) */
      [dir="rtl"] .va-bubble-row--user    { justify-content: flex-start; }
      [dir="rtl"] .va-bubble-row--assistant { justify-content: flex-end; }

      .va-bubble {
        max-width: 70%;
        padding: 10px 14px;
        border-radius: 18px;
        font-size: 0.875rem;
        line-height: 1.5;
        word-break: break-word;
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .va-bubble--user {
        background: rgba(149, 128, 255, 0.18);
        border: 1px solid rgba(149, 128, 255, 0.28);
        color: #e8e6ff;
        border-end-end-radius: 4px;   /* bottom-right in LTR, bottom-left in RTL */
      }
      .va-bubble--assistant {
        background: rgba(30, 34, 46, 0.7);
        border: 1px solid rgba(255,255,255,0.07);
        backdrop-filter: blur(8px);
        color: #d8dce8;
        border-end-start-radius: 4px; /* bottom-left in LTR, bottom-right in RTL */
      }
      .va-cursor {
        display: inline-block;
        margin-left: 2px;
        opacity: 0.7;
        animation: va-blink 0.9s step-end infinite;
        font-size: 0.8em;
      }
      @keyframes va-blink {
        0%, 100% { opacity: 0.7; }
        50%       { opacity: 0; }
      }
      .va-tool-call { display: block; }

      @media (prefers-reduced-motion: reduce) {
        .va-bubble-row { transition: none; opacity: 1; transform: none; }
        .va-cursor { animation: none; }
      }
    `;
    document.head.appendChild(style);
  }

  destroy(): void { /* no-op */ }
}
