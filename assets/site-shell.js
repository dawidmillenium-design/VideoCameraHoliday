// =========================================
// MEGA MENU: Mobile Toggle + Accessibility
// =========================================
document.addEventListener('DOMContentLoaded', function() {
    const megaTriggers = document.querySelectorAll('.mega-item > a');
    
    megaTriggers.forEach(trigger => {
        // Mobile click toggle
        trigger.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                const menu = this.nextElementSibling;
                const isExpanded = this.getAttribute('aria-expanded') === 'true';
                
                // Close all other open menus
                document.querySelectorAll('.mega-menu.active').forEach(openMenu => {
                    if (openMenu !== menu) {
                        openMenu.classList.remove('active');
                        openMenu.previousElementSibling.setAttribute('aria-expanded', 'false');
                    }
                });
                
                // Toggle current menu
                this.setAttribute('aria-expanded', !isExpanded);
                menu.classList.toggle('active');
            }
        });

        // Keyboard: Close on Escape
        trigger.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const menu = this.nextElementSibling;
                menu.classList.remove('active');
                this.setAttribute('aria-expanded', 'false');
                this.focus();
            }
        });

        // Keyboard: Arrow navigation inside mega menu
        trigger.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowDown' || e.key === 'Enter') {
                const menu = this.nextElementSibling;
                if (menu) {
                    e.preventDefault();
                    menu.classList.add('active');
                    this.setAttribute('aria-expanded', 'true');
                    const firstLink = menu.querySelector('a');
                    if (firstLink) firstLink.focus();
                }
            }
        });
    });

    // Close mega menus when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.mega-item')) {
            document.querySelectorAll('.mega-menu.active').forEach(menu => {
                menu.classList.remove('active');
                menu.previousElementSibling.setAttribute('aria-expanded', 'false');
            });
        }
    });
});
