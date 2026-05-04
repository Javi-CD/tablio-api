from uuid import UUID

from pydantic import BaseModel


class PublicProductResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    price: str
    image_url: str | None = None

    class Config:
        from_attributes = True


class PublicCategoryResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    sort_order: int
    products: list[PublicProductResponse] = []

    class Config:
        from_attributes = True


class PublicRestaurantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    logo_url: str | None = None
    phone: str | None = None
    address: str | None = None

    class Config:
        from_attributes = True


class PublicMenuResponse(BaseModel):
    restaurant: PublicRestaurantResponse
    categories: list[PublicCategoryResponse]
