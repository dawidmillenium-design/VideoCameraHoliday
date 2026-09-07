# fix-canonicals.py
import re
import os

FIXES = {
    'guides/best-camera-ski-holidays.html': 'https://dawidmillenium-design.github.io/VideoCameraHoliday/guides/best-camera-ski-holidays.html',
    'how-to/film-yourself-solo.html': 'https://dawidmillenium-design.github.io/VideoCameraHoliday/how-to/film-yourself-solo.html',
    'destinations/index.html': 'https://dawidmillenium-design.github.io/VideoCameraHoliday/destinations/',
    'destinations/lyon-camera-guide.html': 'https://dawidmillenium-design.github.io/VideoCameraHoliday/destinations/lyon-camera-guide.html'
}

for file_path, correct_url in FIXES.items():
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = r'<link\s+rel=["\']canonical["\']\s+href=["\'][^"\'?]*["\']'
        replacement = f'<link rel="canonical" href="{correct_url}"'
        content = re.sub(pattern, replacement, content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'✅ Fixed: {file_path}')
    else:
        print(f'⚠️ File not found: {file_path}')

print('\n🎯 All critical canonical fixes applied!')
