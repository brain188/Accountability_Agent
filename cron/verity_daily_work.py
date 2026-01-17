"""
Verify Daily Work Cron Job

Verifies GitHub activity for all active users and sends summary emails.
Should be run Monday-Friday at 11 PM (or desired time).
"""

import sys
import os

# Parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
from app.config import get_settings
from app.database import get_db_context
from app.services.verification_service import VerificationService
from app.utils.time_utils import get_current_date, is_weekday

# Configure logging
settings = get_settings()
logger = logging.getLogger(__name__)


def verify_daily_work():
    """
    Verify GitHub activity for all active users and send summaries.
    
    Only runs on weekdays (Monday-Friday).
    Checks GitHub for commits, PRs, and issues, then sends summary emails.
    """
    # Check if today is a weekday
    today = get_current_date()
    
    if not is_weekday(today):
        logger.info(f"Today ({today}) is not a weekday. Skipping verification.")
        return
    
    logger.info(f"Starting daily verification for {today}")
    
    try:
        with get_db_context() as db:
            # Initialize verification service
            verification_service = VerificationService(db)
            
            # Verify all users
            results = verification_service.verify_all_users(today)
            
            logger.info(
                f"Verification complete: {results['successful']}/{results['total_users']} successful, "
                f"{results['passed']} passed, {results['not_passed']} did not pass, "
                f"{results['failed']} failed"
            )
            
            return results
    
    except Exception as e:
        logger.error(f"Fatal error in verify_daily_work: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Main entry point for cron job."""
    logger.info("=" * 80)
    logger.info("DAILY VERIFICATION CRON JOB STARTED")
    logger.info("=" * 80)
    
    try:
        results = verify_daily_work()
        
        logger.info("=" * 80)
        logger.info("DAILY VERIFICATION CRON JOB COMPLETED")
        logger.info(f"Results: {results}")
        logger.info("=" * 80)
        
        # Exit with error code if there were failures
        if isinstance(results, dict):
            if not results.get("success", True) or results.get("failed", 0) > 0:
                sys.exit(1)
        
    except Exception as e:
        logger.error(f"Fatal error in cron job: {e}", exc_info=True)
        logger.info("=" * 80)
        logger.info("DAILY VERIFICATION CRON JOB FAILED")
        logger.info("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()