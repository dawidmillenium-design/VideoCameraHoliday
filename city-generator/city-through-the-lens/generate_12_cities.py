import json
import os
from pathlib import Path

# Read the 14 East Asia cities
with open('east-asia-cities.json', 'r', encoding='utf-8') as f:
    all_cities = json.load(f)

# Read the Beijing template from current folder
with open('beijing-interview-preview.html', 'r', encoding='utf-8') as f:
    template = f.read()

# Cities to generate (excluding Tokyo and Shanghai which exist on GitHub)
cities_to_generate = [c for c in all_cities if c['slug'] not in ['tokyo-interview-preview', 'shanghai-interview-preview']]

created = 0
skipped = 0

for city in cities_to_generate:
    filename = f"{city['slug']}.html"
    
    if os.path.exists(filename):
        skipped += 1
        print(f"⏭️ Skipped {filename} (already exists)")
        continue
    
    # Simple find-and-replace for key fields
    content = template
    content = content.replace('Beijing', city['city'])
    content = content.replace('China', city['country'])
    content = content.replace('beijing-interview-preview', city['slug'])
    
    # Add more specific replacements as needed
    # This is a basic version - your actual template may need more work
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    created += 1
    print(f"✅ Created {filename}")

print(f"\n🎉 Created {created} files, skipped {skipped}")
print(f"Total files now: {len([f for f in os.listdir('.') if f.endswith('-interview-preview.html')])}")