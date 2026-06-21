import os
import re

pattern = re.compile(r'(\w+)\.objects\.(?:create|get_or_create)\([^)]+\)', re.DOTALL)
path = os.path.join('nano', 'views_legacy.py')
with open(path, 'r', encoding='utf-8', errors='ignore') as file:
    content = file.read()
    lines = content.splitlines()
    for m in pattern.finditer(content):
        match_str = m.group()
        model_name = m.group(1)
        if model_name in ['User', 'Workspace'] or 'UserProfile' in model_name:
            continue
        if 'workspace' not in match_str:
            # find line number
            start_pos = m.start()
            line_num = content[:start_pos].count('\n') + 1
            print(f"Line {line_num}: {model_name}.objects...")
            print(match_str)
            print("---")
