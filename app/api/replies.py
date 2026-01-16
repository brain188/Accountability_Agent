"""
Email Replies API

Webhook endpoint for processing email replies from SendGrid.
Updates daily logs with user responses.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.daily_log import DailyLog
from app.config import get_settings
from app.utils.time_utils import get_current_date

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/replies", tags=["replies"])


def verify_webhook_secret(x_webhook_secret: str = Header(None)) -> bool:
    """
    Verify webhook secret from header.
    
    Args:
        x_webhook_secret: Secret from request header
    
    Returns:
        True if valid
    
    Raises:
        HTTPException: If secret is invalid
    """
    if x_webhook_secret != settings.webhook_secret:
        logger.warning(f"Invalid webhook secret received: {x_webhook_secret}")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    return True


@router.post("/email")
async def handle_email_reply(
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_webhook_secret)
) -> Dict[str, Any]:
    """
    Handle incoming email reply from SendGrid webhook.
    
    This endpoint receives email replies and updates the daily log
    with the user's response.
    
    Args:
        request: FastAPI request object
        db: Database session
        _: Webhook secret validation
    
    Returns:
        Dictionary with status and message
    
    Raises:
        HTTPException: If processing fails
    """
    try:
        # Parse JSON body
        payload = await request.json()
        logger.info(f"Received email reply webhook: {payload.keys()}")
        
        # Extract email data from SendGrid payload
        # SendGrid sends data in a specific format
        from_email = payload.get("from", {}).get("email")
        to_email = payload.get("to", [{}])[0].get("email")
        subject = payload.get("subject", "")
        text_content = payload.get("text", "")
        html_content = payload.get("html", "")
        
        # Use text content, fallback to HTML
        user_response = text_content if text_content else html_content
        
        if not from_email or not user_response:
            logger.error("Missing from_email or response content in webhook")
            raise HTTPException(
                status_code=400,
                detail="Invalid email data: missing from_email or content"
            )
        
        logger.info(f"Processing email reply from {from_email}")
        
        # Find user by email
        user = User.get_by_email(db, from_email)
        
        if not user:
            logger.warning(f"Email reply from unknown user: {from_email}")
            raise HTTPException(
                status_code=404,
                detail=f"User not found: {from_email}"
            )
        
        # Get today's date in user's timezone
        today = get_current_date(user.timezone)
        
        # Get or create daily log for today
        daily_log = DailyLog.get_or_create(db, user.id, today)
        
        # Update with user response
        daily_log.user_response = user_response.strip()
        daily_log.user_responded_at = datetime.utcnow()
        
        db.commit()
        db.refresh(daily_log)
        
        logger.info(
            f"Updated daily log for user {user.email} on {today} "
            f"with response ({len(user_response)} chars)"
        )
        
        return {
            "status": "success",
            "message": "Email reply processed successfully",
            "user_email": user.email,
            "log_date": today.isoformat(),
            "response_length": len(user_response)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing email reply: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        Dictionary with status
    """
    return {"status": "healthy", "service": "email_replies"}