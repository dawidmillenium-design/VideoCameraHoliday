import os
from pathlib import Path

# --- CONFIGURATION ---
TARGET_DIR = '.' # Root directory

# --- CODE SNIPPETS TO INJECT ---

MOBILE_CSS = """
/* --- Mobile Menu Styles --- */
.mobile-menu-toggle {
    display: none;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.5rem;
    flex-direction: column;
    gap: 5px;
}
.hamburger-line {
    display: block;
    width: 25px;
    height: 3px;
    background-color: var(--dark);
    border-radius: 2px;
    transition: all 0.3s ease;
}
.mobile-menu-toggle.active .hamburger-line:nth-child(1) { transform: translateY(8px) rotate(45deg); }
.mobile-menu-toggle.active .hamburger-line:nth-child(2) { opacity: 0; }
.mobile-menu-toggle.active .hamburger-line:nth-child(3) { transform: translateY(-8px) rotate(-45deg); }

@media (max-width: 768px) {
    .mobile-menu-toggle { display: flex; }
    .mega-menu {
        display: none;
        position: absolute;
        top: 100%;
        left: 0;
        width: 100%;
        background: #fff;
        border-bottom: 1px solid var(--border);
        flex-direction: column;
        padding: 1rem;
        gap: 0;
        box-shadow: 0 10px 15px rgba(0,0,0,0.1);
        max-height: 80vh;
        overflow-y: auto;
    }
    .mega-menu.active { display: flex; }
    .mega-menu > li { padding: 0; border-bottom: 1px solid var(--border); }
    .mega-menu > li > a { display: block; padding: 1rem 0; font-size: 1.1rem; }
    .dropdown {
        position: static;
        transform: none;
        min-width: 100%;
        box-shadow: none;
        border: none;
        padding: 0 0 1rem 1rem;
        grid-template-columns: 1fr;
        opacity: 1;
        visibility: visible;
        display: block;
    }
    .dropdown-col { margin-bottom: 1rem; }
    .dropdown-col h4 { font-size: 0.9rem; margin-top: 0.5rem; }
}
"""

MOBILE_HTML_BUTTON = """
<button class="mobile-menu-toggle" aria-label="Toggle navigation menu" aria-expanded="false">
    <span class="hamburger-line"></span>
    <span class="hamburger-line"></span>
    <span class="hamburger-line"></span>
</button>
"""

MOBILE_JS = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.querySelector('.mobile-menu-toggle');
    const mobileMenu = document.querySelector('.mega-menu');
    if (toggleBtn && mobileMenu) {
        toggleBtn.addEventListener('click', () => {
            const isActive = mobileMenu.classList.toggle('active');
            toggleBtn.classList.toggle('active');
            toggleBtn.setAttribute('aria-expanded', isActive);
        });
    }
});
</script>
"""

def main():
    updated_count = 0
    html_files = list(Path(TARGET_DIR).rglob('*.html'))
    
    # Filter out backup directories
    html_files = [f for f in html_files if 'backup' not in str(f)]

    print(f"🔍 Found {len(html_files)} HTML files to process.")

    for file_path in html_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip if already injected
        if 'mobile-menu-toggle' in content and 'Mobile Menu Styles' in content:
            continue

        # 1. Inject CSS before </style>
        if '</style>' in content:
            content = content.replace('</style>', f'{MOBILE_CSS}</style>')
        
        # 2. Inject Button before <nav> inside header
        if '<nav>' in content:
            content = content.replace('<nav>', f'{MOBILE_HTML_BUTTON}<nav>')
            
        # 3. Inject JS before </body>
        if '</body>' in content:
            content = content.replace('</body>', f'{MOBILE_JS}</body>')

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✅ Updated: {file_path.name}")
        updated_count += 1

    print(f"\n🎉 Done! Successfully updated {updated_count} files with the mobile menu.")

if __name__ == "__main__":
    main()