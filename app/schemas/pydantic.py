from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str  # admin, project_manager, developer, qa


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Project Schemas
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    pm_id: int


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    pm_id: Optional[int] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    pm_id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TeamMemberAdd(BaseModel):
    user_id: int


class TeamMemberResponse(BaseModel):
    id: int
    user_id: int
    user: UserResponse

    class Config:
        from_attributes = True


class ProjectWithTeam(BaseModel):
    id: int
    name: str
    description: Optional[str]
    pm_id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    team_members: List[TeamMemberResponse] = []

    class Config:
        from_attributes = True


# Bug Schemas
class BugCreate(BaseModel):
    title: str
    description: str
    project_id: int


class BugUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class BugResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    solution: Optional[str] = None
    project_id: int
    reporter_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    text: str


class CommentResponse(BaseModel):
    id: int
    text: str
    bug_id: int
    author_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BugWithComments(BugResponse):
    comments: List[CommentResponse] = []

    class Config:
        from_attributes = True