"""
Daily Log Model

Tracks daily check-ins, user responses, and GitHub verification results.
"""

from datetime import datetime, date, timezone
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, Date, 
    ForeignKey, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class DailyLog(Base):
    """
    Daily log model representing a single day's check-in and verification.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        log_date: Date of this log entry
        checkin_sent_at: When the check-in email was sent
        user_response: User's response to the check-in
        user_responded_at: When the user responded
        verification_completed_at: When GitHub verification was completed
        commits_count: Number of commits found
        prs_count: Number of pull requests
        issues_count: Number of issues
        verification_passed: Whether verification passed
        verification_details: JSON details of verification
        summary_sent_at: When the summary email was sent
    """
    
    __tablename__ = "daily_logs"
    
    # Add unique constraint on user_id and log_date
    __table_args__ = (
        UniqueConstraint('user_id', 'log_date', name='uix_user_log_date'),
    )
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to User
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to users table"
    )
    
    # Date of this log
    log_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Date of this log entry"
    )
    
    # Check-in information
    checkin_sent_at = Column(
        DateTime,
        nullable=True,
        comment="When the check-in email was sent"
    )
    
    # User response
    user_response = Column(
        Text,
        nullable=True,
        comment="User's response to the check-in"
    )
    
    user_responded_at = Column(
        DateTime,
        nullable=True,
        comment="When the user responded"
    )
    
    # Verification information
    verification_completed_at = Column(
        DateTime,
        nullable=True,
        comment="When GitHub verification was completed"
    )
    
    commits_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of commits found"
    )
    
    prs_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of pull requests"
    )
    
    issues_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of issues"
    )
    
    verification_passed = Column(
        Boolean,
        nullable=True,
        comment="Whether verification passed"
    )
    
    verification_details = Column(
        JSON,
        nullable=True,
        comment="JSON details of verification (repos, commits, etc.)"
    )
    
    # Summary email
    summary_sent_at = Column(
        DateTime,
        nullable=True,
        comment="When the summary email was sent"
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        nullable=False,
        comment="Record creation timestamp"
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
        comment="Last update timestamp"
    )
    
    # Relationships
    user = relationship("User", back_populates="daily_logs")
    
    def __repr__(self) -> str:
        """String representation of DailyLog."""
        return (
            f"<DailyLog(id={self.id}, user_id={self.user_id}, "
            f"log_date={self.log_date}, verification_passed={self.verification_passed})>"
        )
    
    def to_dict(self) -> dict:
        """
        Convert DailyLog to dictionary.
        
        Returns:
            dict: DailyLog data
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "log_date": self.log_date.isoformat() if self.log_date else None,
            "checkin_sent_at": self.checkin_sent_at.isoformat() if self.checkin_sent_at else None,
            "user_response": self.user_response,
            "user_responded_at": self.user_responded_at.isoformat() if self.user_responded_at else None,
            "verification_completed_at": self.verification_completed_at.isoformat() if self.verification_completed_at else None,
            "commits_count": self.commits_count,
            "prs_count": self.prs_count,
            "issues_count": self.issues_count,
            "verification_passed": self.verification_passed,
            "verification_details": self.verification_details,
            "summary_sent_at": self.summary_sent_at.isoformat() if self.summary_sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def get_or_create(cls, db, user_id: int, log_date: date) -> "DailyLog":
        """
        Get or create a daily log for a user on a specific date.
        
        Args:
            db: Database session
            user_id: User ID
            log_date: Date for the log
            
        Returns:
            DailyLog object (existing or newly created)
        """
        log = db.query(cls).filter(
            cls.user_id == user_id,
            cls.log_date == log_date
        ).first()
        
        if not log:
            log = cls(user_id=user_id, log_date=log_date)
            db.add(log)
            db.commit()
            db.refresh(log)
        
        return log
    
    @classmethod
    def get_by_date(cls, db, user_id: int, log_date: date) -> Optional["DailyLog"]:
        """
        Get daily log for a user on a specific date.
        
        Args:
            db: Database session
            user_id: User ID
            log_date: Date for the log
            
        Returns:
            DailyLog object or None if not found
        """
        return db.query(cls).filter(
            cls.user_id == user_id,
            cls.log_date == log_date
        ).first()
    
    @classmethod
    def get_recent_logs(cls, db, user_id: int, days: int = 7) -> list["DailyLog"]:
        """
        Get recent daily logs for a user.
        
        Args:
            db: Database session
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            List of DailyLog objects
        """
        return db.query(cls).filter(
            cls.user_id == user_id
        ).order_by(
            cls.log_date.desc()
        ).limit(days).all()