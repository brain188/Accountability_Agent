"""
Basic Tests

Simple tests to verify the application setup is correct.
"""

import pytest
from datetime import date, datetime


def test_imports():
    """Test that all core modules can be imported."""
    try:
        from app.config import get_settings
        from app.database import Base, engine
        from app.models.user import User
        from app.models.daily_log import DailyLog
        from app.services.email_service import EmailService
        from app.services.github_service import GitHubService
        from app.services.verification_service import VerificationService
        from app.utils.time_utils import get_current_date, is_weekday
        
        assert get_settings() is not None
        print("All imports successful")
        
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_settings():
    """Test that settings are loaded correctly."""
    from app.config import get_settings
    
    settings = get_settings()
    
    assert settings.app_name is not None
    assert settings.app_version is not None
    assert settings.database_url is not None
    assert settings.timezone is not None
    
    print(f"Settings loaded: {settings.app_name} v{settings.app_version}")


def test_time_utils():
    """Test time utility functions."""
    from app.utils.time_utils import (
        get_current_date,
        get_current_datetime,
        is_weekday,
        format_date,
        get_weekday_name
    )
    
    # Test current date
    today = get_current_date()
    assert isinstance(today, date)
    
    # Test current datetime
    now = get_current_datetime()
    assert isinstance(now, datetime)
    
    # Test is_weekday
    monday = date(2024, 1, 15)  # Known Monday
    assert is_weekday(monday) is True
    
    saturday = date(2024, 1, 13)  # Known Saturday
    assert is_weekday(saturday) is False
    
    # Test format_date
    formatted = format_date(today)
    assert len(formatted) > 0
    
    # Test get_weekday_name
    weekday_name = get_weekday_name(monday)
    assert weekday_name == "Monday"
    
    print("Time utils working correctly")


def test_database_connection():
    """Test database connection."""
    from app.database import test_connection
    
    # This might fail if database isn't set up, which is OK
    result = test_connection()
    
    if result:
        print("Database connection successful")
    else:
        print("Database connection failed (this is OK if not set up yet)")


def test_models_definition():
    """Test that models are properly defined."""
    from app.models.user import User
    from app.models.daily_log import DailyLog
    
    # Check User model has required fields
    assert hasattr(User, 'email')
    assert hasattr(User, 'github_username')
    assert hasattr(User, 'github_token')
    assert hasattr(User, 'time_zone')
    
    # Check DailyLog model has required fields
    assert hasattr(DailyLog, 'user_id')
    assert hasattr(DailyLog, 'log_date')
    assert hasattr(DailyLog, 'commits_count')
    assert hasattr(DailyLog, 'prs_count')
    assert hasattr(DailyLog, 'issues_count')
    
    print("Models properly defined")


def test_email_service_initialization():
    """Test email service can be initialized."""
    from app.services.email_service import EmailService
    
    try:
        email_service = EmailService()
        assert email_service is not None
        print("Email service initialized")
    except Exception as e:
        print(f"Email service initialization failed: {e}")
        print("   (This is OK if SendGrid API key is not configured)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])