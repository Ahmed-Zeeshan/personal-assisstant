export type TranscriptLine = { speaker: 'user'|'assistant'; text: string; tool_call?: string };

export class Transcript {
  private el: HTMLElement;

  constructor(parent: HTMLElement) {
    this.el = document.createElement('section');
    this.el.className = 'flex-1 overflow-y-auto px-5 py-4 space-y-3';
    this.el.innerHTML = `<p class="text-dim text-sm">Press the hotkey or type a command to start.</p>`;
    parent.appendChild(this.el);
  }

  push(line: TranscriptLine): void {
    if (this.el.querySelector('p.text-dim')) this.el.replaceChildren();
    const wrapper = document.createElement('div');
    wrapper.className = 'flex gap-3';
    const tag = line.speaker === 'user'
      ? '<span class="text-xs text-dim shrink-0 mt-0.5 w-16">you</span>'
      : '<span class="text-xs text-accent shrink-0 mt-0.5 w-16">assistant</span>';
    const body = document.createElement('p');
    body.className = 'text-sm leading-6 text-fg';
    body.textContent = line.text;
    wrapper.innerHTML = tag;
    wrapper.appendChild(body);
    if (line.tool_call) {
      const tc = document.createElement('pre');
      tc.className = 'text-xs text-muted font-mono ml-19 mt-1';
      tc.textContent = `↳ ${line.tool_call}`;
      wrapper.appendChild(tc);
    }
    this.el.appendChild(wrapper);
    this.el.scrollTop = this.el.scrollHeight;
  }
}
