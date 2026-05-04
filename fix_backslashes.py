import os
import re

d = 'app/templates'
for f in os.listdir(d):
    if f.endswith('.html'):
        filepath = os.path.join(d, f)
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Remove literal backslashes inside jinja {{ ... }}
        content = content.replace("\\'", "'")
        
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
print("Done fixing backslashes")
