import re
import os

missing = []

# Collect missing files from script logic
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
                    if model_name in ['User', 'Workspace'] or 'UserProfile' in model_name:
                        continue
                    if 'workspace' not in match_str:
                        missing.append((path, m.start(), m.group()))

# Now fix them
# We will use parenthesis balancing to find the exact end of the call, even if re.DOTALL matched partially due to nested parens!
for filepath, _, _ in missing:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    models = [
        'Sale', 'CompletedOrder', 'PendingOrder', 'Notification', 
        'AirtimeProduct', 'AirtimeSale', 'UserActivity', 'ErrorLog',
        'SecurityAuditLog', 'APICallLog', 'SensitiveDataAccessLog', 'DataModificationLog',
        'AirtimeRequest', 'Product', 'FCMToken'
    ]
    
    modified = False
    new_content = ""
    idx = 0
    search_strs = [f"{m}.objects.create(" for m in models] + [f"{m}.objects.get_or_create(" for m in models]
    
    while idx < len(content):
        found = False
        for s in search_strs:
            if content.startswith(s, idx):
                found = True
                paren_count = 1
                curr_idx = idx + len(s)
                while curr_idx < len(content) and paren_count > 0:
                    if content[curr_idx] == '(':
                        paren_count += 1
                    elif content[curr_idx] == ')':
                        paren_count -= 1
                    curr_idx += 1
                
                call_text = content[idx:curr_idx]
                
                if 'workspace=' in call_text or 'workspace =' in call_text:
                    new_content += call_text
                    idx = curr_idx
                    break
                else:
                    inside_args = content[idx + len(s) : curr_idx - 1]
                    
                    # Logic to determine workspace string based on file
                    if 'middleware' in filepath or 'error_tracking' in filepath or 'serializers' in filepath:
                        # use user.userprofile if available or None
                        ws_expr = "workspace=getattr(request.user.userprofile, 'workspace', None) if getattr(request, 'user', None) and hasattr(getattr(request, 'user', None), 'userprofile') else getattr(getattr(locals().get('user'), 'userprofile', None), 'workspace', None)"
                    else:
                        ws_expr = "workspace=workspace"
                    
                    if inside_args.strip() == "":
                        new_call_text = f"{s}{ws_expr})"
                    elif inside_args.rstrip().endswith(','):
                        new_call_text = f"{s}{inside_args} {ws_expr})"
                    else:
                        new_call_text = f"{s}{inside_args}, {ws_expr})"
                        
                    new_content += new_call_text
                    idx = curr_idx
                    modified = True
                    break
                    
        if not found:
            new_content += content[idx]
            idx += 1

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")
