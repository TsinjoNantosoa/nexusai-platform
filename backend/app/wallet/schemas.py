from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionOut(BaseModel):
    status: str = "free"
    renews_at: datetime | None = Field(default=None, serialization_alias="renewsAt")
    cancel_at_period_end: bool = Field(default=False, serialization_alias="cancelAtPeriodEnd")

    model_config = ConfigDict(populate_by_name=True)


class WalletOut(BaseModel):
    balance: int
    in_review: bool = Field(default=False, serialization_alias="inReview")

    model_config = ConfigDict(populate_by_name=True)


class EntryOut(BaseModel):
    id: UUID
    type: str
    amount: int
    reference: str
    created_at: datetime = Field(serialization_alias="createdAt")
    status: str = "completed"

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
