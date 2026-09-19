from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.tasks import Task, User
from app.schemas.tasks import TaskCreate, TaskPatch, TaskResponse
from app.utils.exceptions import NotFoundException, DuplicateException, ForbiddenException
from app.models.tasks import Priority
from app.utils.security import get_current_user
from sqlalchemy.exc import IntegrityError
from app.utils.notifications import send_notification
from app.utils.rate_limit import limiter



router = APIRouter(prefix="/tasks", tags=["Tasks"])





@router.get(
    "/", 
    response_model=list[TaskResponse], 
    responses= {
        400: {"description": "Bad request (ex: invalid syntax)"},
        401: {"description": "Missing or invalid Bearer token"},
        422: {"description": "Validation error"},
    },
    summary="List all tasks",
)
@limiter.limit("60/minute")
def list_tasks(
    request: Request,
    completed: Optional[bool] = Query(None),
    priority: Optional[Priority] = Query(None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=50),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List tasks, with optional filters.
    - **Auth:** required
    - **Rate limit:** 60 requests/minute
    - **Query:** `completed` (optional bool), `priority` (optional low,medium,high)
    - **200:** JSON array of tasks (empty array `[]` if none match)
    - **400:** bad request (ex: invalid query syntax) 
    - **401:** missing/invalid token
    - **422:** `body/query  fails verification` query out of range
    
    """

    query= db.query(Task).filter(Task.user_id == current_user.id)
    if completed is not None:
        query = query.filter(Task.completed == completed)
    
    if priority is not None:
        query = query.filter(Task.priority == priority)

    return query.offset(skip).limit(limit).all()

    



@router.get(
    "/{task_id}",response_model=TaskResponse,
    responses= {
        401: {"description": "Missing or invalid Bearer token"},
        404:{"description": "There is no task with this id"},
        422: {"description": "task_id is not an integer"},
    },
    summary= "Get a specific task"
)
@limiter.limit("60/minute")
def get_task(
    request: Request,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a task by id.

    - **Auth:** required
    - **Rate limit:** 60 requests/minute
    - **Path:** `task_id` (integer)
    - **200:** that task's record
    - **401:** missing/invalid token
    - **404:** no task with that id
    - **422:** `task_id` is not an integer
    
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundException("Task", task_id)
    if task.user_id != current_user.id:
        raise ForbiddenException("You do not have permission to access this task")
    return task




@router.post(
    "/", response_model=TaskResponse, 
    status_code=201,
    responses= {
        401: {"description": "Missing or invalid Bearer token"},
        422: {"description": "Request body failed validation"},
    },
    summary="Create a new task",
)
@limiter.limit("20/minute")
def create_task(
    request: Request,
    task: TaskCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    create a new task.

    - **Auth:** required
    - **Rate limit:** 20 requests/minute
    - **Body:** `title` (1-200), `description` (1-2000), optional `priority` (low,medium,high), optional `completed` (default `false`)
    - **Side effects:** notification email to the **current user**
    - **201:** created task, including `id` and `created_at`
    - **401:** missing/invalid token
    - **422:** body fails validation (missing `title`, invalid priority , etc.)
    
    """
    db_task = Task(**task.model_dump(), user_id=current_user.id)
    try:
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Task could not be created due to database constraint"
        )
    background_tasks.add_task(
        send_notification, 
        current_user.email,
        f"New task {db_task.title} added"
    )
    return db_task




@router.patch(
    "/{task_id}", 
    response_model=TaskResponse,
    responses= {
        401: {"description": "Missing or invalid Bearer token"},
        404: {"description": "No task with this id"},
        422: {"description": "A provided field is invalid"},

    },
    summary="Partially update a task"
)
@limiter.limit("20/minute")
def update_task(
    request: Request,
    task_id: int,
    task_data: TaskPatch,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partially update a task by id.

    - **Auth:** required
    - **Rate limit:** 20 requests/minute
    - **Side effect::** notification email to the **current user**
    - **Body:** any subset of `title`, `description`, `priority`, `completed`
    - **200:** task after the patch (omitted fields keep their previous values)
    - **401:** missing/invalid token
    - **404:** no task with that id
    - **422:** a provided field is invalid (empty title, invalid priority, etc.)
    
    """

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundException("Task", task_id)
    if task.user_id != current_user.id:
        raise ForbiddenException("You do not have permission to access this task")
    
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    background_tasks.add_task(
        send_notification,
        current_user.id,
        f"Updated task {task_id}",
    )
    return task




@router.delete(
    "/{task_id}",
    status_code= 204,
    responses= {
        400: {"description": "Task still exists"},
        401: {"description": "Missing or invalid Bearer token"},
        404: {"description": "No task with this id"},
    },
    summary="Delete a specific task",
)
@limiter.limit("20/minute")
def delete_task(
    request: Request,
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a task by id.

    - **Auth:** required
    - **Rate limit:** 20 requests/minute
    - **Side effect::** notification email to the **current user**
    - **204:** deleted (empty body — do not parse JSON)
    - **400:** task still exists 
    - **401:** missing/invalid token
    - **404:** no task with that id
    
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        if task.user_id != current_user.id:
            raise ForbiddenException("You do not have permission to access this task")
        else: 
            db.delete(task)
            db.commit()
            background_tasks.add_task(
                send_notification,
                current_user.id,
                f"deleted task {task_id}",
            )
        
    else:
        raise NotFoundException("Task", task_id)

