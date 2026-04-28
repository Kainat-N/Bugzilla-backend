from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.sqlmodels import User, Project, Bug, BugStatus, ProjectUser
from app.schemas.pydantic import (
    BugCreate, BugResponse, BugUpdate, BugWithComments,
    CommentCreate, CommentResponse
)
from app.core.security import get_current_active_user, require_admin, require_pm_or_admin

router = APIRouter(prefix="/api/v1/bugs", tags=["Bugs"])

# Role constants
ROLE_ADMIN = "admin"
ROLE_PM = "project_manager"
ROLE_DEVELOPER = "developer"
ROLE_QA = "qa"


def get_user_projects(db: Session, user: User) -> List[int]:
    """Get project IDs accessible to a user"""
    if user.role == ROLE_ADMIN:
        projects = db.query(Project).all()
        return [p.id for p in projects]
    elif user.role == ROLE_PM:
        projects = db.query(Project).filter(Project.pm_id == user.id).all()
        return [p.id for p in projects]
    else:
        project_ids = db.query(ProjectUser.project_id).filter(ProjectUser.user_id == user.id).all()
        return [p[0] for p in project_ids]


@router.get("", response_model=List[BugResponse])
def get_bugs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all bugs accessible to current user"""
    project_ids = get_user_projects(db, current_user)
    if not project_ids:
        return []
    return db.query(Bug).filter(Bug.project_id.in_(project_ids)).all()


@router.get("/{bug_id}", response_model=BugWithComments)
def get_bug(
    bug_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get bug by ID"""
    bug = db.query(Bug).filter(Bug.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    
    # Check access
    project_ids = get_user_projects(db, current_user)
    if bug.project_id not in project_ids:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return bug


@router.post("", response_model=BugResponse, status_code=status.HTTP_201_CREATED)
def create_bug(
    bug_data: BugCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new bug (QA only)"""
    if current_user.role != ROLE_QA and current_user.role != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Only QA can create bugs")
    
    # Check project access
    project_ids = get_user_projects(db, current_user)
    if bug_data.project_id not in project_ids:
        raise HTTPException(status_code=403, detail="Access denied to project")
    
    bug = Bug(
        title=bug_data.title,
        description=bug_data.description,
        project_id=bug_data.project_id,
        reporter_id=current_user.id,
        status=BugStatus.OPEN
    )
    db.add(bug)
    db.commit()
    db.refresh(bug)
    return bug


@router.put("/{bug_id}", response_model=BugResponse)
def update_bug(
    bug_id: int,
    bug_data: BugUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a bug"""
    bug = db.query(Bug).filter(Bug.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    
    # Check access
    project_ids = get_user_projects(db, current_user)
    if bug.project_id not in project_ids:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Only reporter or admin can update
    if bug.reporter_id != current_user.id and current_user.role != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if bug_data.title:
        bug.title = bug_data.title
    if bug_data.description:
        bug.description = bug_data.description
    
    db.commit()
    db.refresh(bug)
    return bug


@router.put("/{bug_id}/resolve", response_model=BugResponse)
def resolve_bug(
    bug_id: int,
    solution: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark bug as resolved with solution (Developer only)"""
    if current_user.role != ROLE_DEVELOPER and current_user.role != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Only developers can resolve bugs")
    
    bug = db.query(Bug).filter(Bug.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    
    # Check project access
    project_ids = get_user_projects(db, current_user)
    if bug.project_id not in project_ids:
        raise HTTPException(status_code=403, detail="Access denied")
    
    bug.solution = solution
    bug.status = BugStatus.RESOLVED
    db.commit()
    db.refresh(bug)
    return bug


@router.put("/{bug_id}/done", response_model=BugResponse)
def mark_bug_done(
    bug_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark bug as done (QA only)"""
    if current_user.role != ROLE_QA and current_user.role != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Only QA can mark bugs as done")
    
    bug = db.query(Bug).filter(Bug.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    
    if bug.status != BugStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Bug must be resolved first")
    
    bug.status = BugStatus.DONE
    db.commit()
    db.refresh(bug)
    return bug


@router.put("/{bug_id}/reopen", response_model=BugResponse)
def reopen_bug(
    bug_id: int,
    comment: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reopen a bug with comment (QA only)"""
    if current_user.role != ROLE_QA and current_user.role != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Only QA can reopen bugs")
    
    bug = db.query(Bug).filter(Bug.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    
    bug.status = BugStatus.REOPENED
    db.commit()
    db.refresh(bug)
    return bug


# Comments
@router.post("/{bug_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    bug_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a comment to a bug"""
    bug = db.query(Bug).filter(Bug.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    
    from app.models.sqlmodels import Comment
    comment = Comment(
        text=comment_data.text,
        bug_id=bug_id,
        author_id=current_user.id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment