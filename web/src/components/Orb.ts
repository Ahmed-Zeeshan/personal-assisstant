export type OrbState = 'idle'|'listening'|'thinking'|'speaking'|'error';

export class Orb {
  private el: HTMLElement;
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private state: OrbState = 'idle';
  private rms: number = 0;
  private rafId: number | null = null;
  private startTime: number = performance.now();

  constructor(parent: HTMLElement) {
    this.el = document.createElement('div');
    this.el.className = 'flex-1 grid place-items-center relative';
    this.el.innerHTML = `
      <div class="absolute inset-0 pointer-events-none"
        style="background: radial-gradient(closest-side, rgba(149,128,255,0.10), transparent 60%); filter: blur(60px);"></div>
      <canvas data-orb width="384" height="384" class="relative"></canvas>
      <p data-hint class="absolute bottom-12 text-sm text-muted">Press the hotkey to talk</p>
    `;
    parent.appendChild(this.el);
    this.canvas = this.el.querySelector<HTMLCanvasElement>('[data-orb]')!;
    const ctx = this.canvas.getContext('2d');
    if (!ctx) throw new Error('canvas 2d context unavailable');
    this.ctx = ctx;
    this.loop();
  }

  setState(s: OrbState): void {
    this.state = s;
    const hint = this.el.querySelector<HTMLElement>('[data-hint]');
    if (hint) hint.textContent = {
      idle:      'Press the hotkey to talk',
      listening: 'Listening…',
      thinking:  'Thinking…',
      speaking:  'Speaking…',
      error:     'Something went wrong.',
    }[s];
  }

  setRms(v: number): void { this.rms = Math.max(0, Math.min(1, v)); }

  private loop = (): void => {
    const t = (performance.now() - this.startTime) / 1000;
    const w = this.canvas.width, h = this.canvas.height;
    this.ctx.clearRect(0, 0, w, h);
    const cx = w / 2, cy = h / 2;
    const accent = 'rgba(149,128,255,';

    // base radius, breathes slowly in idle
    let radius = 90 + Math.sin(t * 1.2) * 4;
    if (this.state === 'listening') radius = 90 + 60 * this.rms;
    if (this.state === 'speaking')  radius = 90 + Math.sin(t * 6) * 12;
    if (this.state === 'thinking')  radius = 90;

    // soft outer halo
    const g1 = this.ctx.createRadialGradient(cx, cy, radius * 0.4, cx, cy, radius * 1.6);
    g1.addColorStop(0, accent + '0.50)');
    g1.addColorStop(1, accent + '0)');
    this.ctx.fillStyle = g1;
    this.ctx.beginPath();
    this.ctx.arc(cx, cy, radius * 1.6, 0, Math.PI * 2);
    this.ctx.fill();

    // inner disc
    const g2 = this.ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
    g2.addColorStop(0, accent + '0.95)');
    g2.addColorStop(1, accent + '0.45)');
    this.ctx.fillStyle = g2;
    this.ctx.beginPath();
    this.ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    this.ctx.fill();

    // thinking arc
    if (this.state === 'thinking') {
      this.ctx.strokeStyle = '#e6e8eb';
      this.ctx.lineWidth = 3;
      this.ctx.lineCap = 'round';
      this.ctx.beginPath();
      const start = (t * 2) % (Math.PI * 2);
      this.ctx.arc(cx, cy, radius + 16, start, start + Math.PI * 0.6);
      this.ctx.stroke();
    }

    // error flash
    if (this.state === 'error') {
      this.ctx.fillStyle = `rgba(245,158,11,${0.4 + 0.3 * Math.sin(t * 8)})`;
      this.ctx.beginPath();
      this.ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      this.ctx.fill();
    }

    this.rafId = requestAnimationFrame(this.loop);
  };

  destroy(): void {
    if (this.rafId !== null) cancelAnimationFrame(this.rafId);
  }
}
