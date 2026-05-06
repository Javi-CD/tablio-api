"""
CLI to initialize and seed the development database.

Use:
    uv run python -m app.db.init_db --seed
"""

import argparse
import asyncio
import logging
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.category import Category
from app.models.product import Product
from app.models.restaurant import Restaurant
from app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("tablio.seed")

# ─── Seed constants ───────────────────────────────────────────────────────────


DEMO_EMAIL = settings.DEMO_EMAIL
DEMO_PASSWORD = settings.DEMO_PASSWORD
DEMO_SLUG = settings.DEMO_SLUG


@dataclass
class _ProductSeed:
    name: str
    description: str
    price: Decimal


@dataclass
class _CategorySeed:
    name: str
    sort_order: int
    products: list[_ProductSeed]


_SEED_DATA: list[_CategorySeed] = [
    _CategorySeed(
        name="Bebidas",
        sort_order=0,
        products=[
            _ProductSeed(
                "Limonada natural", "Limonada fresca hecha al momento", Decimal("8000")
            ),
            _ProductSeed(
                "Jugo de naranja", "Naranja exprimida al instante", Decimal("9000")
            ),
            _ProductSeed(
                "Café americano", "Café recién molido, 200 ml", Decimal("5000")
            ),
        ],
    ),
    _CategorySeed(
        name="Entradas",
        sort_order=1,
        products=[
            _ProductSeed(
                "Patacones con hogao",
                "Dos patacones con salsa de hogao casera",
                Decimal("12000"),
            ),
            _ProductSeed(
                "Ensalada verde",
                "Mix de lechugas, tomate y aguacate",
                Decimal("10000"),
            ),
            _ProductSeed(
                "Croquetas de papa",
                "Croquetas crujientes con queso y guascas",
                Decimal("11000"),
            ),
        ],
    ),
    _CategorySeed(
        name="Platos principales",
        sort_order=2,
        products=[
            _ProductSeed(
                "Bandeja paisa",
                "Fríjoles, chicharrón, chorizo, arroz, arepa y huevo",
                Decimal("35000"),
            ),
            _ProductSeed(
                "Arroz con pollo",
                "Pollo jugoso con arroz al azafrán y verduras",
                Decimal("28000"),
            ),
            _ProductSeed(
                "Hamburguesa artesanal",
                "Carne 200 g, queso cheddar, lechuga y tomate",
                Decimal("32000"),
            ),
        ],
    ),
    _CategorySeed(
        name="Postres",
        sort_order=3,
        products=[
            _ProductSeed(
                "Brownie con helado",
                "Brownie de chocolate tibio con helado de vainilla",
                Decimal("12000"),
            ),
            _ProductSeed(
                "Tres leches",
                "Torta húmeda bañada en tres tipos de leche",
                Decimal("10000"),
            ),
            _ProductSeed(
                "Fresas con crema",
                "Fresas frescas con crema chantilly",
                Decimal("9000"),
            ),
        ],
    ),
]

# ─── Seed logic ───────────────────────────────────────────────────────────────


async def _seed(db: AsyncSession) -> None:
    # 1. Demo user
    user_row = await db.execute(select(User).where(User.email == DEMO_EMAIL))
    existing_user: User | None = user_row.scalar_one_or_none()
    if existing_user is None:
        user = User(
            email=DEMO_EMAIL,
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name="Tablio Demo",
        )
        db.add(user)
        await db.flush()
        log.info("✓ usuario demo creado: %s", DEMO_EMAIL)
    else:
        user = existing_user
        log.info("· usuario demo ya existe, omitiendo")

    # 2. Demo restaurant
    rest_row = await db.execute(select(Restaurant).where(Restaurant.slug == DEMO_SLUG))
    existing_restaurant: Restaurant | None = rest_row.scalar_one_or_none()
    if existing_restaurant is None:
        restaurant = Restaurant(
            owner_id=user.id,
            name="Tablio Demo",
            slug=DEMO_SLUG,
            description=(
                "Menú de demostración de Tablio — digitaliza tu menú y recibe pedidos."
            ),
            phone="+57 300 000 0000",
            address="Calle del Demo 123, Bogotá",
        )
        db.add(restaurant)
        await db.flush()
        log.info("✓ restaurante demo creado: slug=%s", DEMO_SLUG)
    else:
        restaurant = existing_restaurant
        log.info("· restaurante demo ya existe, omitiendo")

    # 3. Categories + products — only if the restaurant has none yet
    cat_row = await db.execute(
        select(Category).where(Category.restaurant_id == restaurant.id).limit(1)
    )
    if cat_row.scalar_one_or_none() is not None:
        log.info("· categorías ya existen, omitiendo productos")
        await db.commit()
        return

    total_products = 0
    for cat_seed in _SEED_DATA:
        category = Category(
            restaurant_id=restaurant.id,
            name=cat_seed.name,
            sort_order=cat_seed.sort_order,
        )
        db.add(category)
        await db.flush()

        for prod_seed in cat_seed.products:
            db.add(
                Product(
                    restaurant_id=restaurant.id,
                    category_id=category.id,
                    name=prod_seed.name,
                    description=prod_seed.description,
                    price=prod_seed.price,
                )
            )
            total_products += 1

    await db.commit()
    log.info(
        "✓ %d categorías y %d productos creados",
        len(_SEED_DATA),
        total_products,
    )


async def _main() -> None:
    async with AsyncSessionLocal() as db:
        await _seed(db)


# ─── CLI entry point ──────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tablio — utilidades de base de datos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Ejemplo:\n  uv run python -m app.db.init_db --seed",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Inserta datos demo (usuario, restaurante, categorías y productos)",
    )
    args = parser.parse_args()

    if args.seed:
        log.info("Iniciando seed de datos demo...")
        asyncio.run(_main())
        log.info("Seed completado exitosamente.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
