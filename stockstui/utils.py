def slugify(name: str) -> str:
    """Converts a string to a snake_case identifier, safe for use as a file or category name."""
    return name.strip().lower().replace(" ", "_")

def extract_cell_text(cell) -> str:
    """
    Safely extracts the plain text content from a Rich renderable or a DataTable cell.

    Args:
        cell: The cell or renderable object.

    Returns:
        The extracted plain text as a string.
    """
    if not cell:
        return ""
    # Prefer the .plain attribute for Rich objects, fall back to str()
    return getattr(cell, 'plain', str(cell)).strip()