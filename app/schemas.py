from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class JobCreate(BaseModel):
    query: str = Field(min_length=2, max_length=200)
    category_url: HttpUrl | None = None
    max_pages: int = Field(default=1, ge=1, le=10)
    sort: Literal["relevance", "price_asc", "price_desc"] = "relevance"

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        return " ".join(value.strip().split())


class JobOut(BaseModel):
    id: str
    query: str
    provider: str
    status: str
    progress: int
    item_count: int
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class ProductOut(BaseModel):
    id: int
    title: str
    price: float
    currency: str
    rating: float | None
    review_count: int | None
    sold_quantity: int | None
    product_url: str
    image_url: str | None
    position: int

    model_config = {"from_attributes": True}
