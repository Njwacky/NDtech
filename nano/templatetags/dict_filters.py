import json
from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """
    Looks up a key in a dictionary and returns the value.
    Returns empty string if key is not found.
    """
    if dictionary is None:
        return ''
    return dictionary.get(key, '')

@register.filter
def parse_json(value):
    """
    Parses a JSON string and returns the parsed object.
    Returns empty list if parsing fails.
    """
    if not value:
        return []
    try:
        if isinstance(value, str):
            return json.loads(value)
        return value
    except (json.JSONDecodeError, TypeError):
        return []
