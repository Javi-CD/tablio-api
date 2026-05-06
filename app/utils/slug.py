import re
import unicodedata
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID


def generate_slug(name: str) -> str:
    """Convert a restaurant name to a URL-safe, lowercase slug."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^\w\s-]", "", ascii_text.lower())
    slug = re.sub(r"[-\s]+", "-", slug).strip("-")
    return slug or "restaurant"


async def ensure_unique_slug(
    base_slug: str,
    slug_lookup: Callable[[str], Awaitable[Any]],
    exclude_id: UUID | None = None,
) -> str:
    """Append a numeric suffix until the slug is unique.

    Args:
        base_slug: The initial slug to check.
        slug_lookup: Async callable that returns an object (or None) for a given slug.
        exclude_id: If set, the existing record with this ID is considered available.
    """
    slug = base_slug
    counter = 1
    while True:
        existing = await slug_lookup(slug)
        if existing is None or (exclude_id is not None and existing.id == exclude_id):
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1
