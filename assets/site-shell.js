// site-shell.js — Robust mobile menu handler
(function() {
  'use strict';
  
  const toggleBtn = document.querySelector('.mobile-menu-toggle');
  const navLinks = document.querySelector('.nav-links');
  
  if (!toggleBtn || !navLinks) return;
  
  // Toggle menu on button click
  toggleBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    const isActive = navLinks.classList.toggle('active');
    toggleBtn.setAttribute('aria-expanded', isActive);
    toggleBtn.textContent = isActive ? '✕' : '☰';
  });
  
  // Close menu when clicking outside
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.top-nav') && navLinks.classList.contains('active')) {
      navLinks.classList.remove('active');
      toggleBtn.setAttribute('aria-expanded', 'false');
      toggleBtn.textContent = '☰';
    }
  });
  
  // Close menu when clicking any nav link (mobile UX)
  navLinks.querySelectorAll('a:not(.mega-item > a)').forEach(link => {
    link.addEventListener('click', function() {
      if (window.innerWidth <= 1024) {
        navLinks.classList.remove('active');
        toggleBtn.setAttribute('aria-expanded', 'false');
        toggleBtn.textContent = '☰';
      }
    });
  });
  
  // Handle mega-menu items on touch devices
  document.querySelectorAll('.mega-item > a').forEach(megaLink => {
    megaLink.addEventListener('click', function(e) {
      if (window.innerWidth <= 1024) {
        e.preventDefault();
        const parent = this.parentElement;
        const wasOpen = parent.classList.contains('open');
        
        // Close all other open menus
        document.querySelectorAll('.mega-item.open').forEach(item => {
          item.classList.remove('open');
          const menu = item.querySelector('.mega-menu');
          if (menu) menu.style.display = 'none';
        });
        
        // Toggle current menu
        if (!wasOpen) {
          parent.classList.add('open');
          const menu = parent.querySelector('.mega-menu');
          if (menu) menu.style.display = 'block';
        }
      }
    });
  });
  
  // Reset on window resize
  window.addEventListener('resize', function() {
    if (window.innerWidth > 1024) {
      navLinks.classList.remove('active');
      document.querySelectorAll('.mega-item.open').forEach(item => {
        item.classList.remove('open');
        const menu = item.querySelector('.mega-menu');
        if (menu) menu.style.display = '';
      });
      toggleBtn.setAttribute('aria-expanded', 'false');
      toggleBtn.textContent = '☰';
    }
  });
})();
