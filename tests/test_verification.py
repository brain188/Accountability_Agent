"""
Verification Service Tests

Tests for the verification service and GitHub integration.
"""

import sys
import os

# Parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.daily_log import DailyLog
from app.services.verification_service import VerificationService
from app.services.github_service import GitHubService


# Test database setup
@pytest.fixture(scope="function")
def test_db():
    """Create a test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSessionLocal()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = User(
        email="test@example.com",
        github_username="testuser",
        github_token="fake_token_12345",
        time_zone="West African Time (WAT)",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def mock_github_service():
    """Create a mock GitHub service."""
    with patch("app.services.verification_service.GitHubService") as mock:
        instance = mock.return_value
        instance.test_connection.return_value = True
        instance.get_daily_activity.return_value = {
            "date": "2024-01-15",
            "commits": [
                {
                    "sha": "abc123",
                    "message": "Test commit",
                    "repository": "testuser/repo1",
                    "date": datetime.now().isoformat(),
                    "url": "https://github.com/testuser/repo1/commit/abc123",
                    "author": "testuser"
                }
            ],
            "commits_count": 1,
            "pull_requests": [],
            "prs_count": 0,
            "issues": [],
            "issues_count": 0,
            "repositories": ["testuser/repo1"],
            "total_activity": 1
        }
        yield instance


class TestUser:
    """Tests for User model."""
    
    def test_create_user(self, test_db):
        """Test creating a user."""
        user = User(
            email="new@example.com",
            github_username="newuser",
            github_token="token123",
            time_zone="UTC"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        assert user.id is not None
        assert user.email == "new@example.com"
        assert user.github_username == "newuser"
        assert user.is_active is True
    
    def test_get_by_email(self, test_db, test_user):
        """Test getting user by email."""
        found_user = User.get_by_email(test_db, "test@example.com")
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.email == test_user.email
    
    def test_get_by_github_username(self, test_db, test_user):
        """Test getting user by GitHub username."""
        found_user = User.get_by_github_username(test_db, "testuser")
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.github_username == test_user.github_username
    
    def test_get_active_users(self, test_db, test_user):
        """Test getting active users."""
        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            github_username="inactiveuser",
            github_token="token",
            is_active=False
        )
        test_db.add(inactive_user)
        test_db.commit()
        
        active_users = User.get_active_users(test_db)
        assert len(active_users) == 1
        assert active_users[0].id == test_user.id
    
    def test_user_to_dict(self, test_user):
        """Test user to_dict method."""
        user_dict = test_user.to_dict()
        assert "id" in user_dict
        assert "email" in user_dict
        assert "github_username" in user_dict
        assert "github_token" not in user_dict  # Sensitive data excluded


class TestDailyLog:
    """Tests for DailyLog model."""
    
    def test_create_daily_log(self, test_db, test_user):
        """Test creating a daily log."""
        today = date.today()
        log = DailyLog(
            user_id=test_user.id,
            log_date=today,
            commits_count=5,
            prs_count=2,
            issues_count=1
        )
        test_db.add(log)
        test_db.commit()
        test_db.refresh(log)
        
        assert log.id is not None
        assert log.user_id == test_user.id
        assert log.log_date == today
        assert log.commits_count == 5
    
    def test_get_or_create(self, test_db, test_user):
        """Test get_or_create method."""
        today = date.today()
        
        # First call should create
        log1 = DailyLog.get_or_create(test_db, test_user.id, today)
        assert log1.id is not None
        
        # Second call should return existing
        log2 = DailyLog.get_or_create(test_db, test_user.id, today)
        assert log2.id == log1.id
    
    def test_get_by_date(self, test_db, test_user):
        """Test get_by_date method."""
        today = date.today()
        log = DailyLog.get_or_create(test_db, test_user.id, today)
        
        found_log = DailyLog.get_by_date(test_db, test_user.id, today)
        assert found_log is not None
        assert found_log.id == log.id
    
    def test_unique_constraint(self, test_db, test_user):
        """Test unique constraint on user_id and log_date."""
        today = date.today()
        
        log1 = DailyLog(user_id=test_user.id, log_date=today)
        test_db.add(log1)
        test_db.commit()
        
        # Trying to create duplicate should fail
        log2 = DailyLog(user_id=test_user.id, log_date=today)
        test_db.add(log2)
        
        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()


class TestVerificationService:
    """Tests for VerificationService."""
    
    def test_verify_user_day_success(self, test_db, test_user, mock_github_service):
        """Test successful verification."""
        verification_service = VerificationService(test_db)
        today = date.today()
        
        with patch.object(verification_service, 'db', test_db):
            result = verification_service.verify_user_day(test_user, today)
        
        assert result["success"] is True
        assert result["passed"] is True
        assert result["commits_count"] == 1
        assert result["total_activity"] == 1
    
    def test_verify_user_day_no_activity(self, test_db, test_user):
        """Test verification with no activity."""
        with patch("app.services.verification_service.GitHubService") as mock:
            instance = mock.return_value
            instance.test_connection.return_value = True
            instance.get_daily_activity.return_value = {
                "date": "2024-01-15",
                "commits": [],
                "commits_count": 0,
                "pull_requests": [],
                "prs_count": 0,
                "issues": [],
                "issues_count": 0,
                "repositories": [],
                "total_activity": 0
            }
            
            verification_service = VerificationService(test_db)
            today = date.today()
            
            result = verification_service.verify_user_day(test_user, today)
        
        assert result["success"] is True
        assert result["passed"] is False
        assert result["commits_count"] == 0
    
    def test_verify_user_day_github_error(self, test_db, test_user):
        """Test verification with GitHub connection error."""
        with patch("app.services.verification_service.GitHubService") as mock:
            instance = mock.return_value
            instance.test_connection.return_value = False
            
            verification_service = VerificationService(test_db)
            today = date.today()
            
            result = verification_service.verify_user_day(test_user, today)
        
        assert result["success"] is False
        assert "error" in result


class TestGitHubService:
    """Tests for GitHubService."""
    
    @patch("app.services.github_service.Github")
    def test_connection(self, mock_github):
        """Test GitHub connection."""
        mock_user = Mock()
        mock_user.login = "testuser"
        mock_github.return_value.get_user.return_value = mock_user
        
        service = GitHubService("fake_token")
        assert service.test_connection() is True
    
    @patch("app.services.github_service.Github")
    def test_get_user_repos(self, mock_github):
        """Test getting user repositories."""
        mock_repo = Mock()
        mock_repo.full_name = "testuser/repo1"
        
        mock_user = Mock()
        mock_user.login = "testuser"
        mock_user.get_repos.return_value = [mock_repo]
        
        mock_github.return_value.get_user.return_value = mock_user
        
        service = GitHubService("fake_token")
        repos = service.get_user_repos()
        
        assert len(repos) == 1
        assert repos[0].full_name == "testuser/repo1"


def test_imports():
    """Test that all modules can be imported."""
    from app.config import get_settings
    from app.database import Base, engine
    from app.models.user import User
    from app.models.daily_log import DailyLog
    from app.services.email_service import EmailService
    from app.services.github_service import GitHubService
    from app.services.verification_service import VerificationService
    from app.utils.time_utils import get_current_date, is_weekday
    
    assert get_settings() is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])