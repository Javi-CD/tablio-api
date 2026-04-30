import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(gt=Decimal("0"))
    image_url: str | None = None
    category_id: uuid.UUID | None = None

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, v: str | None) -> str | None:
        if v is None:
            return None
        try:
            AnyHttpUrl(v)
        except Exception as exc:
            raise ValueError("image_url must be a valid HTTP/HTTPS URL") from exc
        return v


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=Decimal("0"))
    image_url: str | None = None
    category_id: uuid.UUID | None = None
    is_available: bool | None = None

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, v: str | None) -> str | None:
        if v is None:
            return None
        try:
            AnyHttpUrl(v)
        except Exception as exc:
            raise ValueError("image_url must be a valid HTTP/HTTPS URL") from exc
        return v


class ProductResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    restaurant_id: uuid.UUID
    category_id: uuid.UUID | None
    name: str
    description: str | None
    price: Decimal
    image_url: str | None
    is_available: bool
    created_at: datetime
    updated_at: datetime
