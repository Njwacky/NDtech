"""
Context processors for NDtech POS System
Provides additional context variables to templates.
"""

def user_company_name(request):
    """
    Adds the user's company name to template context.
    Falls back to 'NDtech' if no company name is set.
    """
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        company_name = getattr(request.user.userprofile, 'company_name', None)
        if company_name:
            return {'user_company_name': company_name}
    
    return {'user_company_name': 'NDtech'}
