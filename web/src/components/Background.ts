/**
 * Animated gradient background.
 *
 * Two radial blobs slowly pan in opposite directions using CSS-only
 * animations.  Respects `prefers-reduced-motion`: when the user has
 * requested reduced motion the blobs are static.
 */
export class Background {
  private el: HTMLElement;

  constructor(parent: HTMLElement) {
    this.el = document.createElement('div');
    this.el.className = 'va-bg';
    this.el.setAttribute('aria-hidden', 'true');
    this.el.innerHTML = `
      <div class="va-bg__blob va-bg__blob--a"></div>
      <div class="va-bg__blob va-bg__blob--b"></div>
    `;
    // Insert as first child so it sits behind everything.
    parent.insertBefore(this.el, parent.firstChild);

    if (!document.querySelector('#va-bg-style')) {
      const style = document.createElement('style');
      style.id = 'va-bg-style';
      style.textContent = `
        .va-bg {
          position: fixed;
          inset: 0;
          z-index: 0;
          pointer-events: none;
          background: linear-gradient(135deg, #0b0d10 0%, #15101f 50%, #0b0d10 100%);
          overflow: hidden;
        }
        .va-bg__blob {
          position: absolute;
          border-radius: 50%;
          filter: blur(80px);
          opacity: 0.18;
        }
        .va-bg__blob--a {
          width: 600px;
          height: 600px;
          background: radial-gradient(closest-side, #9580ff, transparent);
          top: -200px;
          left: -150px;
          animation: va-blob-a 18s ease-in-out infinite alternate;
        }
        .va-bg__blob--b {
          width: 500px;
          height: 500px;
          background: radial-gradient(closest-side, #6050cc, transparent);
          bottom: -180px;
          right: -100px;
          animation: va-blob-b 22s ease-in-out infinite alternate;
        }
        @keyframes va-blob-a {
          0%   { transform: translate(0, 0) scale(1); }
          50%  { transform: translate(80px, 60px) scale(1.08); }
          100% { transform: translate(160px, 120px) scale(0.94); }
        }
        @keyframes va-blob-b {
          0%   { transform: translate(0, 0) scale(1); }
          50%  { transform: translate(-60px, -40px) scale(1.1); }
          100% { transform: translate(-120px, -80px) scale(0.92); }
        }
        @media (prefers-reduced-motion: reduce) {
          .va-bg__blob { animation: none !important; }
        }
      `;
      document.head.appendChild(style);
    }
  }

  destroy(): void {
    this.el.remove();
  }
}
