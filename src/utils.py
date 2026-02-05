def sanitize_filename(name: str):
    """
    Sanitize the filename by removing illegal characters.
    """
    return "".join([c if c.isalnum() else " " for c in name]).strip().capitalize()
