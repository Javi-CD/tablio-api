import uuid
from decimal import Decimal

from pydantic import BaseModel


class PublicProductResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    description: str | None
    price: Decimal
    image_url: str | None


class PublicCategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    sort_order: int
    products: list[PublicProductResponse]


class PublicRestaurantResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    logo_url: str | None
    phone: str | None
    address: str | None


class PublicMenuResponse(BaseModel):
    restaurant: PublicRestaurantResponse
    categories: list[PublicCategoryResponse]
