from datetime import date

from pydantic import BaseModel, Field


class GoldRefreshResponse(BaseModel):
    reference_date: date
    refreshed: dict[str, int] = Field(default_factory=dict)
