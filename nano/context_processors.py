"""
Context processors for NDtech POS System
Provides additional context variables to templates.
"""

def user_company_name(request):
    """
    Adds the user's company name and workspace to template context.
    Falls back to 'NDtech' if no company name is set.
    """
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        profile = request.user.userprofile
        workspace = getattr(profile, 'workspace', None)
        company_name = getattr(profile, 'company_name', None) or (workspace.name if workspace else None)
        
        return {
            'user_company_name': company_name or 'NDtech',
            'workspace': workspace
        }
    
    return {
        'user_company_name': 'NDtech',
        'workspace': None
    }
