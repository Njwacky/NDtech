import re

def fix_middleware(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    models_to_fix = [
        'SecurityAuditLog', 'APICallLog', 'SensitiveDataAccessLog', 'DataModificationLog'
    ]
    
    modified = False
    idx = 0
    new_content = ""
    
    # search strings
    search_strs = [f"{m}.objects.create(" for m in models_to_fix]
    
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
                    # We need to figure out what user object is available.
                    # Usually it's `user=...` in the args
                    # So we can just use `workspace=getattr(getattr(request, 'user', None), 'userprofile', None).workspace if hasattr(getattr(request, 'user', None), 'userprofile') else None`
                    # Because request is always available in middleware methods process_request/process_view
                    inside_args = content[idx + len(s) : curr_idx - 1]
                    
                    ws_expr = "workspace=getattr(request.user.userprofile, 'workspace', None) if getattr(request, 'user', None) and hasattr(request.user, 'userprofile') else None"
                    
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

fix_middleware('nano/middleware.py')
fix_middleware('nano/enhanced_security_middleware.py')
fix_middleware('nano/serializers.py')
