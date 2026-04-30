export {};
const root = document.querySelector<HTMLElement>('[data-install-tabs]');
if (root) {
  const tabs = Array.from(root.querySelectorAll<HTMLButtonElement>('[data-tab]'));
  const panels = Array.from(root.querySelectorAll<HTMLElement>('[data-panel]'));

  function activate(id: string) {
    tabs.forEach((t) => t.setAttribute('aria-selected', String(t.dataset.tab === id)));
    panels.forEach((p) => p.classList.toggle('hidden', p.dataset.panel !== id));
  }

  // Auto-detect OS on first load
  const ua = (navigator as any).userAgentData?.platform ?? navigator.platform ?? '';
  const lower = ua.toLowerCase();
  let initial = 'macos';
  if (lower.includes('win')) initial = 'windows';
  else if (lower.includes('linux')) initial = 'linux';
  else if (lower.includes('mac')) initial = 'macos';
  activate(initial);

  tabs.forEach((t) => t.addEventListener('click', () => activate(t.dataset.tab!)));

  // Copy buttons
  root.querySelectorAll<HTMLButtonElement>('[data-copy]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(btn.dataset.copy ?? '');
        const original = btn.textContent;
        btn.textContent = '✓ Copied';
        setTimeout(() => { btn.textContent = original; }, 1500);
      } catch {
        btn.textContent = 'Copy failed';
      }
    });
  });
}
