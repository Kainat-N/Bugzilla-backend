from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.sqlmodels import User, Bug, Comment
from app.schemas.pydantic import CommentResponse, CommentCreate
from app.core.security import get_current_active_user

router = APIRouter(prefix="/api/v1/comments", tags=["Comments"])


def get_user_project_ids(db: Session, user: User) -> List[int]:
    """Get project IDs accessible to user"""
    from app.models.sqlmodels import Project, ProjectUser
    
    if user.role == "admin":
        projects = db.query(Project).all()
        return [p.id for p in projects]
    elif user.role == "project_manager":
        projects = db.query(Project).filter(Project.pm_id == user.id).all()
        return [p.id for p in projects]
    else:
        project_ids = db.query(ProjectUser.project_id).filter(ProjectUser.user_id == user.id).all()
        return [p[0] for p in project_ids]


@router.get("/{comment_id}", response_model=CommentResponse)
def get_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get comment by ID"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check access via bug's project
    bug = db.query(Bug).filter(Bug.id == comment.bug_id).first()
    project_ids = get_user_project_ids(db, current_user)
    if bug.project_id not in project_ids:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return comment


@router.put("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a comment (author only)"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Only author can update
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
    
    comment.text = comment_data.text
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a comment (author or admin)"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Only author or admin can delete
    if comment.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    db.delete(comment)
    db.commit()
    return None