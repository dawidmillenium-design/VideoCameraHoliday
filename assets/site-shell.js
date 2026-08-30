(() => {
  const menu = document.querySelector('.top-nav .nav-links');
  const button = document.querySelector('.mobile-menu-toggle');
  if (menu && button) {
    button.addEventListener('click', () => {
      const open = menu.classList.toggle('is-open');
      button.setAttribute('aria-expanded', String(open));
    });
  }
  const current = window.location.pathname.replace(/index\.html$/, '').replace(/\/$/, '');
  document.querySelectorAll('.top-nav a[data-section]').forEach((link) => {
    const section = link.dataset.section;
    if ((section === 'home' && current.endsWith('/VideoCameraHoliday')) ||
        (section !== 'home' && current.includes('/' + section))) {
      link.setAttribute('aria-current', 'page');
    }
  });
})();
