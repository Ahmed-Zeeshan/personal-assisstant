export type AvatarState = 'idle'|'listening'|'thinking'|'speaking'|'error';

const AVATAR_SRC: Record<string, string> = {
  aria: '/avatars/aria.svg',
  liam: '/avatars/liam.svg',
  sage: '/avatars/sage.svg',
};

export class Avatar {
  private el: HTMLElement;
  private img: HTMLImageElement;
  private halo: HTMLElement;
  private dots: HTMLElement;

  constructor(parent: HTMLElement, initialAvatar = 'aria') {
    this.el = document.createElement('div');
    this.el.className = 'flex-1 grid place-items-center relative';
    this.el.innerHTML = `
      <div data-halo class="absolute h-72 w-72 rounded-full opacity-0 transition-opacity duration-300"
        style="background: radial-gradient(closest-side, rgba(149,128,255,0.45), transparent 70%); filter: blur(40px);"></div>
      <img data-img alt="assistant avatar" class="relative h-56 w-56 rounded-full object-cover shadow-2xl shadow-black/40 border-2 border-border"
        style="background: linear-gradient(135deg, #1f242c, #0b0d10);" />
      <div data-dots class="absolute -top-4 hidden gap-1.5">
        <span class="block h-2 w-2 rounded-full bg-accent animate-bounce"></span>
        <span class="block h-2 w-2 rounded-full bg-accent animate-bounce" style="animation-delay: 0.15s"></span>
        <span class="block h-2 w-2 rounded-full bg-accent animate-bounce" style="animation-delay: 0.30s"></span>
      </div>
      <p data-hint class="absolute bottom-12 text-sm text-muted">Press the hotkey to talk</p>
    `;
    parent.appendChild(this.el);
    this.img = this.el.querySelector<HTMLImageElement>('[data-img]')!;
    this.halo = this.el.querySelector<HTMLElement>('[data-halo]')!;
    this.dots = this.el.querySelector<HTMLElement>('[data-dots]')!;
    this.setAvatar(initialAvatar);
    this.startBreathing();
  }

  setAvatar(name: string): void {
    const src = AVATAR_SRC[name] ?? AVATAR_SRC['aria'];
    this.img.src = src;
  }

  setState(s: AvatarState): void {
    const hint = this.el.querySelector<HTMLElement>('[data-hint]')!;
    hint.textContent = {
      idle:      'Press the hotkey to talk',
      listening: 'Listening…',
      thinking:  'Thinking…',
      speaking:  '',
      error:     'Something went wrong.',
    }[s];

    // Halo intensity per state
    const haloClass = (op: string) => { this.halo.style.opacity = op; };
    haloClass(s === 'listening' || s === 'speaking' ? '1' :
              s === 'thinking' ? '0.4' :
              s === 'error' ? '0' : '0.6');

    // Thinking dots
    this.dots.classList.toggle('hidden', s !== 'thinking');
    this.dots.classList.toggle('flex', s === 'thinking');

    // Bobbing intensity
    if (s === 'speaking') {
      this.img.style.animation = 'va-bob 0.4s ease-in-out infinite alternate';
    } else if (s === 'listening') {
      this.img.style.animation = 'va-bob 1.2s ease-in-out infinite alternate';
    } else {
      this.img.style.animation = 'va-breathe 4s ease-in-out infinite';
    }
  }

  setRms(_v: number): void {
    // Reserved for future audio-reactive scaling.
  }

  private startBreathing(): void {
    if (!document.querySelector('#va-avatar-keyframes')) {
      const style = document.createElement('style');
      style.id = 'va-avatar-keyframes';
      style.textContent = `
        @keyframes va-breathe { 0%,100% { transform: scale(1); } 50% { transform: scale(1.02); } }
        @keyframes va-bob { 0% { transform: translateY(0); } 100% { transform: translateY(-4px); } }
        @media (prefers-reduced-motion: reduce) {
          [data-img] { animation: none !important; }
        }
      `;
      document.head.appendChild(style);
    }
    this.img.style.animation = 'va-breathe 4s ease-in-out infinite';
  }

  destroy(): void { /* no-op (CSS animations stop with element removal) */ }
}
