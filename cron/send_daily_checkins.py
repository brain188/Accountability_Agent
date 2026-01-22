"""
Send Daily Check-ins Cron Job

Sends daily check-in emails to all active users.
Should be run Monday-Friday at 6 PM (or desired time).
"""

import sys
import os
from datetime import datetime, timezone

# Parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
from app.config import get_settings
from app.database import get_db_context
from app.models.user import User
from app.models.daily_log import DailyLog
from app.services.email_service import EmailService
from app.utils.time_utils import get_current_date, is_weekday, format_date, get_weekday_name

# Configure logging
settings = get_settings()
logger = logging.getLogger(__name__)


def send_daily_checkins():
    """
    Send daily check-in emails to all active users.
    
    Only runs on weekdays (Monday-Friday).
    Creates daily log entries and sends check-in emails.
    """
    # Check if today is a weekday
    today = get_current_date()
    
    if not is_weekday(today):
        logger.info(f"Today ({today}) is not a weekday. Skipping check-ins.")
        return
    
    logger.info(f"Starting daily check-ins for {today}")
    
    # Initialize email service
    email_service = EmailService()
    
    # Track results
    results = {
        "total_users": 0,
        "emails_sent": 0,
        "errors": 0,
        "date": today.isoformat()
    }
    
    try:
        with get_db_context() as db:
            # Get all active users
            users = User.get_active_users(db)
            results["total_users"] = len(users)
            
            logger.info(f"Found {len(users)} active users")
            
            for user in users:
                try:
                    logger.info(f"Processing user: {user.email}")
                    
                    # Get user's current date (in their timezone)
                    user_today = get_current_date(user.time_zone)
                    
                    # Get or create daily log for today
                    daily_log = DailyLog.get_or_create(db, user.id, user_today)
                    
                    # Check if check-in already sent
                    if daily_log.checkin_sent_at:
                        logger.info(f"Check-in already sent to {user.email} today")
                        continue
                    
                    # Format date string for email
                    date_str = f"{get_weekday_name(user_today)}, {format_date(user_today, '%B %d, %Y')}"
                    
                    # Send check-in email
                    email_sent = email_service.send_daily_checkin(
                        to_email=user.email,
                        user_name=user.github_username,
                        date_str=date_str
                    )
                    
                    if email_sent:
                        # Update daily log
                        daily_log.checkin_sent_at = datetime.now(timezone.utc)
                        db.commit()
                        
                        results["emails_sent"] += 1
                        logger.info(f"Check-in sent successfully to {user.email}")
                    else:
                        results["errors"] += 1
                        logger.error(f"Failed to send check-in to {user.email}")
                
                except Exception as e:
                    results["errors"] += 1
                    logger.error(f"Error processing user {user.email}: {e}", exc_info=True)
                    continue
    
    except Exception as e:
        logger.error(f"Fatal error in send_daily_checkins: {e}", exc_info=True)
        results["errors"] += 1
    
    # Log summary
    logger.info(
        f"Daily check-ins complete: {results['emails_sent']}/{results['total_users']} sent, "
        f"{results['errors']} errors"
    )
    
    return results


def main():
    """Main entry point for cron job."""
    logger.info("=" * 80)
    logger.info("DAILY CHECK-IN CRON JOB STARTED")
    logger.info("=" * 80)
    
    try:
        results = send_daily_checkins()
        
        logger.info("=" * 80)
        logger.info("DAILY CHECK-IN CRON JOB COMPLETED")
        logger.info(f"Results: {results}")
        logger.info("=" * 80)
        
        # Exit with error code if there were errors
        if results["errors"] > 0:
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Fatal error in cron job: {e}", exc_info=True)
        logger.info("=" * 80)
        logger.info("DAILY CHECK-IN CRON JOB FAILED")
        logger.info("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()