"""
Verification Service

Handles verification of user's daily work by checking GitHub activity.
Combines data from multiple sources to determine if verification passed.
"""

import logging
from datetime import date, datetime, timezone
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.daily_log import DailyLog
from app.services.github_service import GitHubService
from app.services.email_service import EmailService
from app.utils.time_utils import get_current_date, format_date, get_weekday_name

logger = logging.getLogger(__name__)


class VerificationService:
    """
    Service for verifying daily work via GitHub activity.
    
    Handles:
    - Checking GitHub for commits, PRs, and issues
    - Updating daily log with verification results
    - Determining if verification passed
    """
    
    def __init__(self, db: Session):
        """
        Initialize verification service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.email_service = EmailService()
    
    def verify_user_day(
        self,
        user: User,
        target_date: Optional[date] = None,
        min_commits: int = 1
    ) -> Dict[str, Any]:
        """
        Verify a user's work for a specific day.
        
        Args:
            user: User object
            target_date: Date to verify (defaults to today)
            min_commits: Minimum commits required to pass (default: 1)
        
        Returns:
            Dictionary containing verification results
        """
        if target_date is None:
            target_date = get_current_date(user.timezone)
        
        logger.info(f"Starting verification for user {user.email} on {target_date}")
        
        try:
            # Get or create daily log
            daily_log = DailyLog.get_or_create(self.db, user.id, target_date)
            
            # Initialize GitHub service
            github_service = GitHubService(user.github_token)
            
            # Test connection
            if not github_service.test_connection():
                logger.error(f"GitHub connection failed for user {user.email}")
                return self._create_error_result(
                    "GitHub connection failed. Please check your token."
                )
            
            # Get daily activity
            activity = github_service.get_daily_activity(target_date, user.github_username)
            
            # Update daily log with activity data
            daily_log.commits_count = activity["commits_count"]
            daily_log.prs_count = activity["prs_count"]
            daily_log.issues_count = activity["issues_count"]
            daily_log.verification_details = activity
            daily_log.verification_completed_at = datetime.now(timezone.utc)
            
            # Determine if verification passed
            # Pass if there's at least one commit OR PR OR issue
            passed = activity["total_activity"] >= min_commits
            daily_log.verification_passed = passed
            
            # Commit changes
            self.db.commit()
            self.db.refresh(daily_log)
            
            result = {
                "success": True,
                "passed": passed,
                "date": target_date.isoformat(),
                "commits_count": activity["commits_count"],
                "prs_count": activity["prs_count"],
                "issues_count": activity["issues_count"],
                "repositories": activity["repositories"],
                "total_activity": activity["total_activity"],
                "user_response": daily_log.user_response,
                "details": activity,
            }
            
            logger.info(
                f"Verification completed for {user.email} on {target_date}: "
                f"{'PASSED' if passed else 'FAILED'} "
                f"({activity['total_activity']} total activities)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error verifying user {user.email} on {target_date}: {e}", exc_info=True)
            self.db.rollback()
            return self._create_error_result(str(e))
    
    def verify_and_notify(
        self,
        user: User,
        target_date: Optional[date] = None
    ) -> bool:
        """
        Verify user's work and send notification email.
        
        Args:
            user: User object
            target_date: Date to verify (defaults to today)
        
        Returns:
            True if successful, False otherwise
        """
        if target_date is None:
            target_date = get_current_date(user.timezone)
        
        # Perform verification
        result = self.verify_user_day(user, target_date)
        
        if not result.get("success"):
            logger.error(f"Verification failed for {user.email}: {result.get('error')}")
            return False
        
        # Format date string for email
        date_str = f"{get_weekday_name(target_date)}, {format_date(target_date, '%B %d, %Y')}"
        
        # Send summary email
        try:
            email_sent = self.email_service.send_verification_summary(
                to_email=user.email,
                user_name=user.github_username,
                date_str=date_str,
                verification_data=result
            )
            
            if email_sent:
                # Update daily log
                daily_log = DailyLog.get_by_date(self.db, user.id, target_date)
                if daily_log:
                    daily_log.summary_sent_at = datetime.now(timezone.utc)
                    self.db.commit()
                
                logger.info(f"Verification summary sent to {user.email}")
                return True
            else:
                logger.error(f"Failed to send summary email to {user.email}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending summary to {user.email}: {e}", exc_info=True)
            return False
    
    def verify_all_users(
        self,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Verify all active users for a specific date.
        
        Args:
            target_date: Date to verify (defaults to today)
        
        Returns:
            Dictionary containing summary of results
        """
        if target_date is None:
            target_date = get_current_date()
        
        logger.info(f"Starting verification for all users on {target_date}")
        
        # Get all active users
        users = User.get_active_users(self.db)
        
        results = {
            "date": target_date.isoformat(),
            "total_users": len(users),
            "successful": 0,
            "failed": 0,
            "passed": 0,
            "not_passed": 0,
            "user_results": []
        }
        
        for user in users:
            try:
                success = self.verify_and_notify(user, target_date)
                
                if success:
                    results["successful"] += 1
                    
                    # Check if verification passed
                    daily_log = DailyLog.get_by_date(self.db, user.id, target_date)
                    if daily_log and daily_log.verification_passed:
                        results["passed"] += 1
                    else:
                        results["not_passed"] += 1
                else:
                    results["failed"] += 1
                
                results["user_results"].append({
                    "user_email": user.email,
                    "success": success
                })
                
            except Exception as e:
                logger.error(f"Error verifying user {user.email}: {e}", exc_info=True)
                results["failed"] += 1
                results["user_results"].append({
                    "user_email": user.email,
                    "success": False,
                    "error": str(e)
                })
        
        logger.info(
            f"Verification complete: {results['successful']}/{results['total_users']} successful, "
            f"{results['passed']} passed, {results['not_passed']} did not pass"
        )
        
        return results
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """
        Create error result dictionary.
        
        Args:
            error_message: Error message
        
        Returns:
            Error result dictionary
        """
        return {
            "success": False,
            "passed": False,
            "error": error_message,
            "commits_count": 0,
            "prs_count": 0,
            "issues_count": 0,
            "total_activity": 0,
        }
    
    def get_user_stats(
        self,
        user: User,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get user's verification statistics for the past N days.
        
        Args:
            user: User object
            days: Number of days to look back
        
        Returns:
            Dictionary containing statistics
        """
        logs = DailyLog.get_recent_logs(self.db, user.id, days)
        
        total_days = len(logs)
        passed_days = sum(1 for log in logs if log.verification_passed)
        total_commits = sum(log.commits_count for log in logs)
        total_prs = sum(log.prs_count for log in logs)
        total_issues = sum(log.issues_count for log in logs)
        
        return {
            "user_email": user.email,
            "period_days": days,
            "total_days_checked": total_days,
            "passed_days": passed_days,
            "failed_days": total_days - passed_days,
            "pass_rate": round(passed_days / total_days * 100, 2) if total_days > 0 else 0,
            "total_commits": total_commits,
            "total_prs": total_prs,
            "total_issues": total_issues,
            "avg_commits_per_day": round(total_commits / total_days, 2) if total_days > 0 else 0,
        }