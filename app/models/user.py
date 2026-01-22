"""
User Model

Represents a user in the system with their email, GitHub username, and tokens.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """
    User model representing a person using the AI agent.
    
    Attributes:
        id: Primary key
        email: User's email address (unique)
        github_username: GitHub username (unique)
        github_token: Personal access token for GitHub API
        is_active: Whether the user is active (for soft deletion)
        timezone: User's timezone (e.g., 'America/New_York')
        created_at: Timestamp of user creation
        updated_at: Timestamp of last update
    """
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # User information
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User's email address"
    )
    
    github_username = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="GitHub username"
    )
    
    github_token = Column(
        Text,
        nullable=False,
        comment="GitHub personal access token (encrypted in production)"
    )
    
    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the user is active"
    )
    
    # Timezone for scheduling
    time_zone = Column(
        String(50),
        default="Africa/Douala",
        nullable=False,
        comment="User's timezone for scheduling"
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        nullable=False,
        comment="User creation timestamp"
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
        comment="Last update timestamp"
    )
    
    # Relationships
    daily_logs = relationship(
        "DailyLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        """String representation of User."""
        return (
            f"<User(id={self.id}, email='{self.email}', "
            f"github_username='{self.github_username}', "
            f"is_active={self.is_active})>"
        )
    
    def to_dict(self) -> dict:
        """
        Convert User to dictionary (excluding sensitive data).
        
        Returns:
            dict: User data without sensitive fields
        """
        return {
            "id": self.id,
            "email": self.email,
            "github_username": self.github_username,
            "is_active": self.is_active,
            "timezone": self.time_zone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def get_by_email(cls, db, email: str) -> Optional["User"]:
        """
        Get user by email address.
        
        Args:
            db: Database session
            email: User's email address
            
        Returns:
            User object or None if not found
        """
        return db.query(cls).filter(cls.email == email).first()
    
    @classmethod
    def get_by_github_username(cls, db, username: str) -> Optional["User"]:
        """
        Get user by GitHub username.
        
        Args:
            db: Database session
            username: GitHub username
            
        Returns:
            User object or None if not found
        """
        return db.query(cls).filter(cls.github_username == username).first()
    
    @classmethod
    def get_active_users(cls, db) -> list["User"]:
        """
        Get all active users.
        
        Args:
            db: Database session
            
        Returns:
            List of active User objects
        """
        return db.query(cls).filter(cls.is_active == True).all()