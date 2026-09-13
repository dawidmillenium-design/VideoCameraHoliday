# Pseudo-code logic for the hotfix script

def safe_extract_title(soup, file_path):
    """Fallback chain to ensure we never get an empty or truncated H1."""
    # Priority 1: Try to find existing H1 if it looks valid
    existing_h1 = soup.find('h1')
    if existing_h1 and len(existing_h1.get_text().strip()) > 5:
        return existing_h1.get_text().strip()
    
    # Priority 2: Parse <title> tag safely
    title_tag = soup.find('title')
    if title_tag:
        full_title = title_tag.get_text().strip()
        # Remove brand suffix ONLY if it exists at the very end
        clean_title = re.sub(r'\s*–\s*Holiday Video Camera.*$', '', full_title, flags=re.IGNORECASE)
        if clean_title:
            return clean_title
        return full_title # Fallback to full title if cleaning fails
    
    # Priority 3: Generate from filename
    return file_path.stem.replace('-', ' ').title()

def generate_valid_json_ld(file_path, title):
    """Ensure sequential positions and absolute URLs."""
    breadcrumbs = []
    parts = file_path.parts
    
    current_url = BASE_URL
    position = 1
    
    for part in parts:
        if part.endswith('.html'):
            continue
        # Skip language folders if needed, or treat as root
        if part in ['de-DE', 'th-TH', ...]: 
            continue
            
        current_url += part + "/"
        breadcrumbs.append({
            "@type": "ListItem",
            "position": position, # Explicitly incrementing
            "name": part.replace('-', ' ').title(),
            "item": current_url
        })
        position += 1
        
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": breadcrumbs}
