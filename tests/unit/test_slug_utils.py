from unittest.mock import AsyncMock

from app.utils.slug import ensure_unique_slug, generate_slug


class TestGenerateSlug:
    def test_simple_name(self) -> None:
        assert generate_slug("La Hamburguesería") == "la-hamburgueseria"

    def test_strips_leading_trailing_hyphens(self) -> None:
        slug = generate_slug("  Mi Restaurante  ")
        assert not slug.startswith("-")
        assert not slug.endswith("-")

    def test_collapses_multiple_spaces(self) -> None:
        assert generate_slug("El   Rincón") == "el-rincon"

    def test_removes_special_characters(self) -> None:
        slug = generate_slug("Café & Bar!")
        assert "&" not in slug
        assert "!" not in slug

    def test_fallback_on_empty_name(self) -> None:
        assert generate_slug("!!!") == "restaurant"

    def test_accents_are_stripped(self) -> None:
        assert generate_slug("Ñoño") == "nono"


class TestEnsureUniqueSlug:
    async def test_returns_slug_when_no_conflict(self) -> None:
        lookup = AsyncMock(return_value=None)
        result = await ensure_unique_slug("mi-restaurante", lookup)
        assert result == "mi-restaurante"

    async def test_appends_counter_on_conflict(self) -> None:
        existing = object()
        lookup = AsyncMock(side_effect=[existing, None])
        result = await ensure_unique_slug("mi-restaurante", lookup)
        assert result == "mi-restaurante-1"

    async def test_increments_counter_until_unique(self) -> None:
        existing = object()
        lookup = AsyncMock(side_effect=[existing, existing, None])
        result = await ensure_unique_slug("slug", lookup)
        assert result == "slug-2"
