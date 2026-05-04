import os
import re

d = 'app/templates'
for f in os.listdir(d):
    if f.endswith('.html'):
        filepath = os.path.join(d, f)
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Replace CSS links
        content = re.sub(r'href="\.\./css/(.*?)"', r'href="{{ url_for(\'static\', path=\'css/\1\') }}"', content)
        
        # Replace image src
        content = re.sub(r'src="\.\./assets/images/(.*?)"', r'src="{{ url_for(\'static\', path=\'assets/images/\1\') }}"', content)
        
        # Replace image path inside url_for
        content = re.sub(r"path='images/(.*?)'", r"path='assets/images/\1'", content)
        content = re.sub(r'path="images/(.*?)"', r'path="assets/images/\1"', content)
        
        # Replace JS src
        content = re.sub(r'src="\.\./js/(.*?)"', r'src="{{ url_for(\'static\', path=\'js/\1\') }}"', content)
        
        # Replace HTML links with FastAPI routes
        content = re.sub(r'href="beranda\.html"', r'href="/beranda"', content)
        content = re.sub(r'href="profil\.html"', r'href="/profil"', content)
        content = re.sub(r'href="latihan\.html"', r'href="/latihan"', content)
        content = re.sub(r'href="latihan-kata\.html"', r'href="/latihan-kata"', content)
        content = re.sub(r'href="canvas-latihan\.html"', r'href="/canvas-latihan"', content)
        content = re.sub(r'href="kuis\.html"', r'href="/kuis"', content)
        content = re.sub(r'href="kuis-soal\.html"', r'href="/kuis-soal"', content)
        content = re.sub(r'href="materi\.html"', r'href="/materi"', content)
        
        # Replace logout
        content = re.sub(r'onclick="window\.location\.href=\'\.\./index\.html\'"', r'onclick="window.location.href=\'/logout\'"', content)
        
        # Replace profile button in canvas-latihan
        content = re.sub(r'onclick="window\.location\.href=\'profil\.html\'"', r'onclick="window.location.href=\'/profil\'"', content)
        
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
print("Done")
