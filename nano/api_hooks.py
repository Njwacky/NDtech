"""
API documentation preprocessing hooks for drf-spectacular
"""

def remove_csrf_from_docs(result, generator, request, public, **kwargs):
    """
    Remove CSRF requirements from API documentation for cleaner API testing
    """
    # Remove CSRF authentication requirement from schema
    if 'components' in result and 'securitySchemes' in result['components']:
        if 'csrfAuth' in result['components']['securitySchemes']:
            del result['components']['securitySchemes']['csrfAuth']
    
    # Remove CSRF from security requirements
    if 'paths' in result:
        for path_item in result['paths'].values():
            for operation in path_item.values():
                if isinstance(operation, dict) and 'security' in operation:
                    new_security = []
                    for security_item in operation['security']:
                        if isinstance(security_item, dict) and 'csrfAuth' not in security_item:
                            new_security.append(security_item)
                    operation['security'] = new_security if new_security else []
    
    return result
