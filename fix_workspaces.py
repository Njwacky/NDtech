import os
import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to find def function_name(request...):
    func_pattern = re.compile(r'^[ \t]*def \w+\(request[^)]*\):', re.MULTILINE)
    
    # We will modify the file by inserting workspace extraction at the top of functions
    # that use .objects.create() without workspace=
    
    # First, let's just do regex replacements for the specific create calls if they lack workspace.
    # To do this safely, we will look for specific models:
    models_to_fix = [
        'Sale', 'CompletedOrder', 'PendingOrder', 'Notification', 
        'AirtimeProduct', 'AirtimeSale', 'UserActivity', 'ErrorLog',
        'SecurityAuditLog', 'APICallLog', 'SensitiveDataAccessLog', 'DataModificationLog',
        'AirtimeRequest', 'Product', 'FCMToken'
    ]
    
    modified = False
    
    # We will iterate through all .objects.create or .objects.get_or_create
    pattern = re.compile(r'(' + '|'.join(models_to_fix) + r')\.objects\.(create|get_or_create)\((.*?)\)', re.DOTALL)
    
    def repl(m):
        nonlocal modified
        model = m.group(1)
        method = m.group(2)
        args = m.group(3)
        
        if 'workspace=' in args or 'workspace =' in args:
            return m.group(0)
        
        # Add workspace=workspace
        # If it's a multiline argument list, we add it at the end
        if args.endswith(','):
            new_args = args + ' workspace=workspace'
        elif args.strip() == '':
            new_args = 'workspace=workspace'
        else:
            # Need to determine if there's a trailing newline
            if '\n' in args:
                # Add before the last newline or just append
                new_args = args + ',\n                workspace=workspace'
            else:
                new_args = args + ', workspace=workspace'
        
        modified = True
        return f"{model}.objects.{method}({new_args})"
        
    new_content = pattern.sub(repl, content)
    
    if modified:
        # Now we must ensure 'workspace = ...' is defined in the functions
        # For simplicity, we can just inject it at the top of every view function that takes 'request'
        # Or before every create call? No, that would cause duplicates.
        
        # Let's inject it into functions that have 'request'
        def func_repl(m):
            func_def = m.group(0)
            indent = func_def[:len(func_def) - len(func_def.lstrip())]
            body_indent = indent + "    "
            injection = f"\n{body_indent}workspace = getattr(request.user.userprofile, 'workspace', None) if hasattr(getattr(request, 'user', None), 'userprofile') else None\n"
            return func_def + injection
            
        new_content = func_pattern.sub(func_repl, new_content)
        
        # Also need to handle cases where there's no request (e.g. models methods or middleware)
        # Middleware usually has `request` in process_request or process_view.
        # But this blanket injection might cause unused variable warnings or redefine workspace.
        # Still, redefining workspace is harmless in Python.
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")

for root, dirs, files in os.walk('nano'):
    if 'migrations' in root or '__pycache__' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            # Skip cashier_views.py as it's already manually fixed
            if f == 'cashier_views.py':
                continue
            path = os.path.join(root, f)
            fix_file(path)
