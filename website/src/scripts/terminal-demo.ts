const root = document.querySelector<HTMLElement>('[data-loop]');
if (root && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const lines = Array.from(root.querySelectorAll<HTMLElement>('.t-line'));
  const typed1 = root.querySelector<HTMLElement>('[data-typed]');
  const typed2 = root.querySelector<HTMLElement>('[data-typed-2]');
  const meter = root.querySelector<HTMLElement>('.t-meter');
  if (meter) {
    for (let i = 0; i < 20; i++) meter.appendChild(document.createElement('span'));
  }

  const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

  async function type(el: HTMLElement | null, text: string, perChar = 35) {
    if (!el) return;
    el.textContent = '';
    for (const ch of text) { el.textContent += ch; await sleep(perChar); }
  }

  function show(idx: number) { lines[idx]?.classList.add('is-on'); }
  function hideAll() { lines.forEach((l) => l.classList.remove('is-on')); if (typed1) typed1.textContent = ''; if (typed2) typed2.textContent = ''; meter?.classList.remove('is-on'); }

  async function loop() {
    while (true) {
      hideAll();
      show(0);
      await type(typed1, 'voice-assistant');
      await sleep(700);
      show(1); await sleep(1500);
      show(2); meter?.classList.add('is-on'); await sleep(1000); meter?.classList.remove('is-on');
      show(3); await sleep(1000);
      show(4); await type(typed2, 'create_folder(path="~/Desktop/notes")', 22);
      await sleep(700);
      show(5); await sleep(1000);
      show(6); await sleep(2000);
      show(7); await sleep(2500);
    }
  }

  // Pause when not visible to save battery
  const io = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) { io.disconnect(); loop(); }
  }, { rootMargin: '0px 0px -10% 0px' });
  io.observe(root);
}
