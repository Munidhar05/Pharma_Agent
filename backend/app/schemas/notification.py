from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: str = "JobMatch"
    channel: str = "dashboard"


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationBatchReadRequest(BaseModel):
    notification_ids: Optional[List[int]] = None
