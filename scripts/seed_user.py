"""
Seed User Script

Adds a new user to the database.
Use this to add yourself or other users to the system.
"""

import sys
import os

# Parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
from getpass import getpass

from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.database import get_db_context, init_db
from app.models.user import User

settings = get_settings()
logger = logging.getLogger(__name__)


def seed_user(
    email: str,
    github_username: str,
    github_token: str,
    time_zone: str = None
) -> bool:
    """
    Add a new user to the database.
    
    Args:
        email: User's email address
        github_username: GitHub username
        github_token: GitHub personal access token
        timezone: User's timezone (defaults to settings timezone)
    
    Returns:
        True if successful, False otherwise
    """
    if time_zone is None:
        time_zone = settings.timezone
    
    try:
        with get_db_context() as db:
            # Check if user already exists
            existing_user = User.get_by_email(db, email)
            if existing_user:
                logger.warning(f"User already exists with email: {email}")
                
                # Ask if user wants to update
                update = input("Do you want to update this user? (y/n): ").strip().lower()
                if update == 'y':
                    existing_user.github_username = github_username
                    existing_user.github_token = github_token
                    existing_user.time_zone = time_zone
                    existing_user.is_active = True
                    db.commit()
                    logger.info(f"User updated: {email}")
                    return True
                else:
                    return False
            
            # Create new user
            new_user = User(
                email=email,
                github_username=github_username,
                github_token=github_token,
                time_zone=time_zone,
                is_active=True
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info(f"User created successfully: {email}")
            logger.info(f"  - GitHub: {github_username}")
            logger.info(f"  - Timezone: {time_zone}")
            logger.info(f"  - User ID: {new_user.id}")
            
            return True
    
    except IntegrityError as e:
        logger.error(f"Database integrity error: {e}")
        logger.error("This might be due to duplicate email or GitHub username")
        return False
    
    except Exception as e:
        logger.error(f"Error creating user: {e}", exc_info=True)
        return False


def interactive_seed():
    """Interactive user creation."""
    print("=" * 80)
    print("Personal AI Agent - Add New User")
    print("=" * 80)
    print()
    
    # Ensure database is initialized
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
    
    print()
    print("Please provide the following information:")
    print()
    
    # Get user input
    email = input("Email address: ").strip()
    if not email or "@" not in email:
        print("Error: Invalid email address")
        return False
    
    github_username = input("GitHub username: ").strip()
    if not github_username:
        print("Error: GitHub username is required")
        return False
    
    print()
    print("GitHub Personal Access Token:")
    print("  - Go to: https://github.com/settings/tokens")
    print("  - Generate new token with 'repo' scope")
    print()
    github_token = getpass("GitHub token (hidden): ").strip()
    if not github_token:
        print("Error: GitHub token is required")
        return False
    
    time_zone = input(f"Timezone [{settings.timezone}]: ").strip()
    if not time_zone:
        time_zone = settings.timezone

    print()
    print("Creating user with:")
    print(f"  - Email: {email}")
    print(f"  - GitHub: {github_username}")
    print(f"  - Timezone: {time_zone}")
    print()
    
    confirm = input("Proceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled")
        return False
    
    # Create user
    success = seed_user(email, github_username, github_token, time_zone)
    
    if success:
        print()
        print("=" * 80)
        print("SUCCESS! User created.")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Set up cron jobs (see README.md)")
        print("2. Configure SendGrid webhook for email replies")
        print("3. Test by running: python cron/send_daily_checkins.py")
        print()
        return True
    else:
        print()
        print("=" * 80)
        print("FAILED to create user. Check logs above.")
        print("=" * 80)
        return False


def main():
    """Main entry point."""
    try:
        success = interactive_seed()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()