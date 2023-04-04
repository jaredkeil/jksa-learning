from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.deps import get_session, get_current_user, get_current_teacher
from app.models import (
    GoalReadWithResources,
    User,
    GoalCreate,
    GoalResourceCreate,
    GoalResourceMultiCreate,
    Role,
)

router = APIRouter()


@router.post("/", status_code=201, response_model=GoalReadWithResources)
def create_goal(
    *,
    goal_in: GoalCreate,
    current_teacher: User = Depends(get_current_teacher),
    session: Session = Depends(get_session),
) -> Any:
    """Create a goal"""
    stu_id, grp_id, std_id = (goal_in.student_id, goal_in.group_id, goal_in.standard_id)
    student = crud.user.get(session, stu_id)
    group = crud.group.get(session, grp_id)
    standard = crud.standard.get(session, std_id)

    if not student:
        raise HTTPException(404, f"Student with ID {stu_id} not found")
    if not group:
        raise HTTPException(404, f"Group with ID {grp_id} not found")
    if not standard:
        raise HTTPException(404, f"Standard with ID {std_id} not found")

    if student.role != Role.student:
        raise HTTPException(422, f"User with ID {stu_id} is not Student")
    if current_teacher not in group.users:
        raise HTTPException(401, f"Teacher is not in Group {grp_id}")
    if student not in group.users:
        raise HTTPException(401, f"Student is not in Group {grp_id}")

    goal_in.teacher_id = current_teacher.id
    return crud.goal.create(session, obj_in=goal_in)


@router.post("/resource-link/", response_model=GoalReadWithResources)
def add_resource_link(
    *,
    goal_resource_in: GoalResourceCreate,
    current_teacher: User = Depends(get_current_teacher),
    session: Session = Depends(get_session),
) -> Any:
    """Link a resource to a teacher's goal. Resource can either belong to
    teacher, or be public"""
    gid, rid = goal_resource_in.dict().values()
    goal = crud.goal.get(session, goal_resource_in.goal_id)
    resource = crud.resource.get(session, rid)
    if not goal:
        raise HTTPException(404, f"Goal with ID {gid} not found")
    if current_teacher != goal.teacher:
        raise HTTPException(401, f"Not teacher on Goal {gid}")
    if not resource:
        raise HTTPException(404, f"Resource with ID {rid} not found")
    if resource.private and current_teacher != resource.creator:
        raise HTTPException(401, f"Not creator of private Resource")

    goal.resources.append(resource)
    crud.goal.refresh(session, goal)
    return goal


@router.post("/resource-link/multi/", response_model=GoalReadWithResources)
def add_resource_link(
    *,
    goal_resources_in: GoalResourceMultiCreate,
    current_teacher: User = Depends(get_current_teacher),
    session: Session = Depends(get_session),
) -> Any:
    """
    Link multiple Resources by ID to a teacher's Goal. If any resources
    requested are not public or created by current logged-in (teacher) user,
    will silently ignore them.
    """
    gid, rids = goal_resources_in.goal_id, set(goal_resources_in.resource_ids)
    goal = crud.goal.get(session, gid)
    resources = crud.resource.get_mult_by_ids(session, ids=rids)
    if not goal:
        raise HTTPException(404, f"Goal with ID {gid} not found")
    if current_teacher != goal.teacher:
        raise HTTPException(401, f"Not teacher on Goal {gid}")
    if not resources:
        raise HTTPException(404, f"Any Resource with IDs {rids} not found")

    resources = [r for r in resources if r.creator == current_teacher or not r.private]
    goal.resources.extend(resources)
    goal = crud.goal.refresh(session, goal)
    return goal


@router.get("/{goal_id}", status_code=200, response_model=GoalReadWithResources)
def fetch_goal(
    *,
    goal_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Any:
    """Fetch a goal by ID"""
    goal = crud.goal.get(session, goal_id)
    if not goal:
        raise HTTPException(404, f"Goal with ID {goal_id} not found")
    if current_user != goal.teacher and current_user != goal.student:
        raise HTTPException(401, f"Not a member of Goal with ID {goal_id}")
    return goal
