import re

def inject_workspace(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        if line.strip().startswith('def ') and '(request' in line:
            indent = line[:len(line) - len(line.lstrip())]
            body_indent = indent + '    '
            # Check if next lines already define workspace
            already_defined = False
            for j in range(i+1, min(len(lines), i+15)):
                if 'workspace =' in lines[j] or 'workspace=' in lines[j] and not 'objects.create' in lines[j]:
                    already_defined = True
                    break
                if lines[j].strip().startswith('def '):
                    break
            
            if not already_defined:
                injection = f"{body_indent}workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None"
                new_lines.append(injection)
                
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print(f"Injected into {filepath}")

for f in ['nano/views_legacy.py', 'nano/viewscOPY.py', 'nano/views/auth_views.py', 'nano/views/dashboard_views.py', 'nano/food_ordering_integration.py', 'nano/food_ordering_error_tracking.py']:
    inject_workspace(f)
