import os

models_to_fix = [
    'Sale', 'CompletedOrder', 'PendingOrder', 'Notification', 
    'AirtimeProduct', 'AirtimeSale', 'UserActivity', 'ErrorLog',
    'SecurityAuditLog', 'APICallLog', 'SensitiveDataAccessLog', 'DataModificationLog',
    'AirtimeRequest', 'Product', 'FCMToken', 'WarehousePrice', 'PriceComparison'
]

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    modified = False
    new_content = ""
    idx = 0
    search_strs = [f"{m}.objects.create(" for m in models_to_fix] + [f"{m}.objects.get_or_create(" for m in models_to_fix]
    
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
                    
                    # Create a completely safe expression using only locals().get()
                    ws_expr = "workspace=getattr(getattr(locals().get('request', locals().get('user', locals().get('admin_user'))), 'userprofile', None), 'workspace', None)"
                    
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

for root, dirs, files in os.walk('nano'):
    if 'migrations' in root or '__pycache__' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            if f in ['tests_api.py', 'test_audit_access_simple.py']: continue # Skip tests
            path = os.path.join(root, f)
            fix_file(path)
