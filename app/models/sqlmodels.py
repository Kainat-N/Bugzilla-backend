from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class UserRole:
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    DEVELOPER = "developer"
    QA = "qa"


class BugStatus:
    OPEN = "open"
    RESOLVED = "resolved"
    DONE = "done"
    REOPENED = "reopened"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    created_projects = relationship("Project", back_populates="created_by_user", foreign_keys="Project.created_by")
    managed_projects = relationship("Project", back_populates="project_manager", foreign_keys="Project.pm_id")
    assigned_projects = relationship("ProjectUser", back_populates="user")
    reported_bugs = relationship("Bug", back_populates="reporter", foreign_keys="Bug.reporter_id")
    assigned_bugs = relationship("BugUser", back_populates="user")
    comments = relationship("Comment", back_populates="author")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    pm_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project_manager = relationship("User", foreign_keys=[pm_id], back_populates="managed_projects")
    created_by_user = relationship("User", foreign_keys=[created_by], back_populates="created_projects")
    team_members = relationship("ProjectUser", back_populates="project")
    bugs = relationship("Bug", back_populates="project")


class ProjectUser(Base):
    __tablename__ = "project_users"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="team_members")
    user = relationship("User", back_populates="assigned_projects")


class Bug(Base):
    __tablename__ = "bugs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="open", nullable=False)
    solution = Column(Text, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="bugs")
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reported_bugs")
    assigned_users = relationship("BugUser", back_populates="bug")
    comments = relationship("Comment", back_populates="bug")


class BugUser(Base):
    __tablename__ = "bug_users"

    id = Column(Integer, primary_key=True, index=True)
    bug_id = Column(Integer, ForeignKey("bugs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    bug = relationship("Bug", back_populates="assigned_users")
    user = relationship("User", back_populates="assigned_bugs")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    bug_id = Column(Integer, ForeignKey("bugs.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    bug = relationship("Bug", back_populates="comments")
    author = relationship("User", back_populates="comments")