from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.sqlmodels import User, Project, ProjectUser
from app.schemas.pydantic import ProjectCreate, ProjectResponse, ProjectUpdate, ProjectWithTeam, TeamMemberAdd, UserResponse
from app.core.security import get_current_active_user, require_admin, require_pm_or_admin

router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


# Role constants
ROLE_ADMIN = "admin"
ROLE_PM = "project_manager"


def get_user_projects(db: Session, user: User) -> List[Project]:
    """Get projects accessible to a user based on their role"""
    if user.role == ROLE_ADMIN:
        # Admin can see all projects
        return db.query(Project).all()
    elif user.role == ROLE_PM:
        # PM can see projects they manage
        return db.query(Project).filter(Project.pm_id == user.id).all()
    else:
        # Developers and QA can see projects they're assigned to
        project_ids = db.query(ProjectUser.project_id).filter(ProjectUser.user_id == user.id).all()
        project_ids = [p[0] for p in project_ids]
        return db.query(Project).filter(Project.id.in_(project_ids)).all() if project_ids else []


@router.get("", response_model=List[ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all projects accessible to current user"""
    return get_user_projects(db, current_user)


@router.get("/{project_id}", response_model=ProjectWithTeam)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check access
    user_projects = get_user_projects(db, current_user)
    if project not in user_projects:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get team members
    team_members = db.query(ProjectUser).filter(ProjectUser.project_id == project_id).all()
    team = []
    for tm in team_members:
        u = db.query(User).filter(User.id == tm.user_id).first()
        if u:
            team.append(u)
    
    pm = db.query(User).filter(User.id == project.pm_id).first()
    
    return ProjectWithTeam(
        id=project.id,
        name=project.name,
        description=project.description,
        pm_id=project.pm_id,
        created_by=project.created_by,
        created_at=project.created_at,
        team_members=team,
        project_manager=pm
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new project (Admin only)"""
    # Verify PM exists
    pm = db.query(User).filter(User.id == project_data.pm_id, User.role == ROLE_PM).first()
    if not pm:
        raise HTTPException(status_code=400, detail="Project manager not found")
    
    project = Project(
        name=project_data.name,
        description=project_data.description,
        pm_id=project_data.pm_id,
        created_by=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update project (Admin only)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.pm_id is not None:
        pm = db.query(User).filter(User.id == project_data.pm_id, User.role == ROLE_PM).first()
        if not pm:
            raise HTTPException(status_code=400, detail="Project manager not found")
        project.pm_id = project_data.pm_id
    
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete project (Admin only)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return None


# Team Management
@router.post("/{project_id}/team", response_model=TeamMemberAdd)
def add_team_member(
    project_id: int,
    member_data: TeamMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pm_or_admin)
):
    """Add team member to project (PM or Admin only)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check permission - only PM of this project or admin can add members
    if current_user.role != ROLE_ADMIN and current_user.id != project.pm_id:
        raise HTTPException(status_code=403, detail="Not authorized to add team members")
    
    # Verify user exists
    user = db.query(User).filter(User.id == member_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already assigned
    existing = db.query(ProjectUser).filter(
        ProjectUser.project_id == project_id,
        ProjectUser.user_id == member_data.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already assigned to this project")
    
    project_user = ProjectUser(project_id=project_id, user_id=member_data.user_id)
    db.add(project_user)
    db.commit()
    return member_data


@router.delete("/{project_id}/team/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pm_or_admin)
):
    """Remove team member from project (PM or Admin only)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user.role != ROLE_ADMIN and current_user.id != project.pm_id:
        raise HTTPException(status_code=403, detail="Not authorized to remove team members")
    
    member = db.query(ProjectUser).filter(
        ProjectUser.project_id == project_id,
        ProjectUser.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    db.delete(member)
    db.commit()
    return None


@router.get("/{project_id}/team", response_model=List[UserResponse])
def get_team_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get team members of a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check access
    user_projects = get_user_projects(db, current_user)
    if project not in user_projects:
        raise HTTPException(status_code=403, detail="Access denied")
    
    team_members = db.query(ProjectUser).filter(ProjectUser.project_id == project_id).all()
    users = []
    for tm in team_members:
        u = db.query(User).filter(User.id == tm.user_id).first()
        if u:
            users.append(u)
    return users