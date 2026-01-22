# Accountability Agent

A personal AI agent that helps developers maintain accountability through daily check-ins and GitHub activity verification. The system sends automated daily check-in emails, processes user responses, and verifies GitHub contributions to ensure consistent productivity.

## Features

- **Daily Check-ins**: Automated email reminders sent Monday-Friday at scheduled times
- **Email Integration**: Seamless email reply processing via SendGrid webhooks
- **GitHub Verification**: Automatic verification of commits, pull requests, and issues
- **Timezone Support**: User-specific timezone handling for global teams
- **Comprehensive Logging**: Detailed tracking of all interactions and verifications
- **RESTful API**: FastAPI-based backend with OpenAPI documentation
- **Background Jobs**: Cron-based automation for check-ins and verifications
- **Database Persistence**: PostgreSQL with SQLAlchemy ORM
- **Email Templates**: Professional HTML email templates with Jinja2

## Architecture

### Core Components

- **FastAPI Backend**: Main application server with REST API endpoints
- **Database Layer**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Email Service**: SendGrid integration for sending and receiving emails
- **GitHub Integration**: PyGitHub library for activity verification
- **Task Scheduling**: Cron jobs for automated daily operations
- **Webhook Processing**: Email reply handling via SendGrid webhooks

### Data Models

- **User**: Stores user information, GitHub credentials, and timezone
- **DailyLog**: Tracks daily check-ins, responses, and verification results

### Services

- **EmailService**: Handles email sending and template rendering
- **GitHubService**: Manages GitHub API interactions and activity verification
- **VerificationService**: Orchestrates the verification process for all users

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis (for Celery, if using background tasks)
- SendGrid account with API key
- GitHub personal access tokens for users

## Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd Accountability_Agent
   ```

2. **Create virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory:

   ```env
   # Application Settings
   APP_NAME="Personal AI Agent"
   APP_VERSION="1.0.0"
   DEBUG=true
   LOG_LEVEL=INFO

   # API Settings
   API_HOST=0.0.0.0
   API_PORT=8000

   # Database
   DATABASE_URL=postgresql://user:password@localhost/accountability_agent

   # SendGrid
   SENDGRID_API_KEY=your_sendgrid_api_key
   SENDGRID_FROM_EMAIL=noreply@yourdomain.com
   SENDGRID_REPLY_TO_EMAIL=checkins@yourdomain.com

   # Security
   WEBHOOK_SECRET=your_webhook_secret

   # Optional: Global GitHub token for testing
   GITHUB_GLOBAL_TOKEN=your_github_token
   ```

5. **Set up the database:**

   ```bash
   # Create database
   createdb accountability_agent

   # Run migrations (if using Alembic)
   alembic upgrade head
   ```

6. **Seed initial data:**

   ```bash
   python scripts/seed_user.py
   ```

## Usage

### Starting the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`.

### Daily Operations

The system runs two main cron jobs:

1. **Send Daily Check-ins** (6 PM weekdays):

   ```bash
   python cron/send_daily_checkins.py
   ```

2. **Verify Daily Work** (11 PM weekdays):

   ```bash
   python cron/verify_daily_work.py
   ```

Set these up in your system's cron scheduler:

```bash
# Send check-ins at 6 PM Monday-Friday
0 18 * * 1-5 /path/to/venv/bin/python /path/to/project/cron/send_daily_checkins.py

# Verify work at 11 PM Monday-Friday
0 23 * * 1-5 /path/to/venv/bin/python /path/to/project/cron/verify_daily_work.py
```

### SendGrid Webhook Setup

Configure SendGrid to forward email replies to your webhook endpoint:

1. In SendGrid dashboard, go to Settings > Mail Settings
2. Enable "Event Webhook"
3. Set the HTTP POST URL to: `https://yourdomain.com/api/replies/email`
4. Set the webhook secret in your environment variables
5. Select events: `processed`, `delivered`, `bounce`, `dropped`

## API Endpoints

### Core Endpoints

- `GET /` - Application root with basic info
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation

### Email Replies Webhook

- `POST /api/replies/email` - Process incoming email replies (SendGrid webhook)
- `GET /api/replies/health` - Webhook health check

### Authentication

Webhook endpoints are secured with a secret token passed in the `X-Webhook-Secret` header.

## Development

### Project Structure

```
Accountability_Agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection and setup
│   ├── api/
│   │   ├── __init__.py
│   │   └── replies.py       # Email reply webhook
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py          # User model
│   │   └── daily_log.py     # Daily log model
│   ├── services/
│   │   ├── __init__.py
│   │   ├── email_service.py     # Email operations
│   │   ├── github_service.py    # GitHub API integration
│   │   └── verification_service.py  # Verification logic
│   └── utils/
│       ├── __init__.py
│       └── time_utils.py     # Timezone utilities
├── cron/
│   ├── __init__.py
│   ├── send_daily_checkins.py   # Check-in cron job
│   └── verify_daily_work.py     # Verification cron job
├── scripts/
│   ├── __init__.py
│   └── seed_user.py         # Database seeding
└── tests/
    ├── __init__.py
    ├── test_basic.py        # Basic functionality tests
    ├── test_email_reply.py  # Email reply tests
    └── test_verification.py # Verification tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_email_reply.py
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Format code: `black .`
6. Submit a pull request

## Support

For support and questions:

- Check the API documentation at `/docs`
- Review application logs
- Ensure all environment variables are correctly set
- Verify SendGrid webhook configuration

## Changelog

### Version 1.0.0

- Initial release
- Daily check-in system
- GitHub verification
- Email integration
- RESTful API
- Cron job automation
