import os
import re

pattern = re.compile(r'(\w+)\.objects\.(?:create|get_or_create)\([^)]+\)', re.DOTALL)

for root, dirs, files in os.walk('nano'):
    if 'migrations' in root or '__pycache__' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                for m in pattern.finditer(content):
                    match_str = m.group()
                    model_name = m.group(1)
                    
                    # Ignore models that don't need workspace or we know are safe
                    if model_name in ['User', 'Workspace']:
                        continue
                    if 'UserProfile' in model_name:
                        continue
                        
                    # Check if 'workspace' is in the arguments
                    if 'workspace' not in match_str:
                        print(f"Missing workspace in {path}: {model_name}.objects...")
                        # print(match_str.split('\n')[0][:80] + '...')
