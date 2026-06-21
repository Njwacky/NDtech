import os

models_to_fix = [
    'Sale', 'CompletedOrder', 'PendingOrder', 'Notification', 
    'AirtimeProduct', 'AirtimeSale', 'UserActivity', 'ErrorLog',
    'SecurityAuditLog', 'APICallLog', 'SensitiveDataAccessLog', 'DataModificationLog',
    'AirtimeRequest', 'Product', 'FCMToken'
]

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # We want to find `.objects.create` and `.objects.get_or_create`
    search_strs = []
    for m in models_to_fix:
        search_strs.append(f"{m}.objects.create(")
        search_strs.append(f"{m}.objects.get_or_create(")
    
    modified = False
    
    # We will do a manual scan
    idx = 0
    new_content = ""
    while idx < len(content):
        found = False
        for s in search_strs:
            if content.startswith(s, idx):
                # Found a create call!
                found = True
                
                # Now find the matching closing parenthesis
                paren_count = 1
                curr_idx = idx + len(s)
                while curr_idx < len(content) and paren_count > 0:
                    if content[curr_idx] == '(':
                        paren_count += 1
                    elif content[curr_idx] == ')':
                        paren_count -= 1
                    curr_idx += 1
                
                # The call text is from idx to curr_idx
                call_text = content[idx:curr_idx]
                
                if 'workspace=' in call_text or 'workspace =' in call_text:
                    # Already has workspace, skip
                    new_content += call_text
                    idx = curr_idx
                    break
                else:
                    # We need to insert workspace=workspace before the last closing parenthesis
                    # which is at curr_idx - 1
                    inside_args = content[idx + len(s) : curr_idx - 1]
                    
                    if inside_args.strip() == "":
                        new_call_text = f"{s}workspace=workspace)"
                    elif inside_args.rstrip().endswith(','):
                        new_call_text = f"{s}{inside_args} workspace=workspace)"
                    else:
                        new_call_text = f"{s}{inside_args}, workspace=workspace)"
                        
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

for root, dirs, files in os.walk('nano'):
    if 'migrations' in root or '__pycache__' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            if f == 'cashier_views.py':
                continue
            path = os.path.join(root, f)
            fix_file(path)
