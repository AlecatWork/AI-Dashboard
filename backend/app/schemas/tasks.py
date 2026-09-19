
from pydantic import BaseModel, ConfigDict, Field, config
from typing import Optional
from datetime import datetime
from app.models.tasks import Priority


class TaskCreate(BaseModel):
    """What a client sends us to create a new task."""
    title: str = Field(
        min_length=1, max_length=200,
        description="the title of the task",
        examples=["Clean"]
    )
    description: Optional[str] = Field(
        default=None,
        min_length=1, max_length=2000,
        description="the description of the task",
        examples=["Clean my room monday"]
    )
    priority: Priority | None = Field(
        default=None,
        description="priority of the task",
        examples=["low"]
    )
    completed: bool = Field(
        default=False,
        description="if the task is completed",
        examples=[False]
    )




class TaskPatch(BaseModel):
    """What a client sends us to partially update a task."""
    title: Optional[str] = Field(
        default=None,
        min_length=1, max_length=200,
        description="the title of the task",
        examples=["Clean"]
    )
    description: Optional[str] = Field(
        default=None,
        min_length=1, max_length=2000,
        description="the description of the task",
        examples=["Clean my room monday"]
    )
    priority: Priority | None = Field(
        default=None,
        description="priority of the task",
        examples=["low"]
    )
    completed: Optional[bool] = Field(
        default=None,
        description="if the task is completed",
        examples=[False]
    )





class TaskResponse(BaseModel):
    """What we send back after storing a task."""
    id: int
    title: str
    description: str | None = None
    priority: Priority | None = None
    completed: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


    model_config = ConfigDict(
        from_attributes = True,
        json_schema_extra = {
            "example": {
                "id": 2,
                "title": "Clean",
                "description": "Clean my room monday",
                "priority": "low",
                "completed": False,
                "created_at": "2026-08-28T00:30:00",
                "updated_at": "2026-09-08T00:30:00",
                
            }
        },
    )