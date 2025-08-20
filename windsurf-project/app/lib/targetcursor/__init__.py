from markupsafe import Markup


def render_attrs(field_id: str | None = None) -> Markup:
    """
    Return minimal, standards-based attributes for initial focus.
    Usage in Jinja: <input ... {{ targetcursor() }}>
    """
    return Markup('autofocus')
