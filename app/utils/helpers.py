# Utility helper functions
# This file can contain reusable helper functions across the application


def format_date(date_obj, format_str='%B %d, %Y'):
    """Format a date object to a string"""
    if date_obj:
        return date_obj.strftime(format_str)
    return None


def slugify(text):
    """Convert text to URL-friendly slug"""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')
