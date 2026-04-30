const toggle = document.getElementById('nav-toggle');
const panel = document.getElementById('nav-panel');
const nav = document.getElementById('site-nav');

if (toggle && panel) {
  const setOpen = (open: boolean) => {
    panel.classList.toggle('hidden', !open);
    toggle.setAttribute('aria-expanded', String(open));
    document.body.style.overflow = open ? 'hidden' : '';
  };
  toggle.addEventListener('click', () => setOpen(panel.classList.contains('hidden')));
  panel.querySelectorAll('[data-nav-close]').forEach((el) =>
    el.addEventListener('click', () => setOpen(false))
  );
}

if (nav) {
  const onScroll = () => {
    const scrolled = window.scrollY > 8;
    nav.classList.toggle('bg-bg/80', scrolled);
    nav.classList.toggle('backdrop-blur-md', scrolled);
    nav.classList.toggle('border-b', scrolled);
    nav.classList.toggle('border-border', scrolled);
  };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
}
