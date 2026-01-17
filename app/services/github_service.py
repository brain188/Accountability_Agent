"""
GitHub Service

Handles interactions with the GitHub API.
Fetches user activity including commits, PRs, and issues.
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from functools import lru_cache

from github import Github, GithubException
from github.Repository import Repository
from github.Commit import Commit
from github.PullRequest import PullRequest
from github.Issue import Issue

from app.utils.time_utils import get_start_of_day, get_end_of_day

logger = logging.getLogger(__name__)


class GitHubService:
    """
    Service for interacting with GitHub API.
    
    Fetches user activity data including:
    - Commits
    - Pull requests
    - Issues
    """
    
    def __init__(self, github_token: str):
        """
        Initialize GitHub client.
        
        Args:
            github_token: Personal access token for GitHub API
        """
        self.client = Github(github_token)
        self._user = None
    
    @property
    def user(self):
        """Get authenticated user (cached)."""
        if self._user is None:
            try:
                self._user = self.client.get_user()
            except GithubException as e:
                logger.error(f"Failed to get GitHub user: {e}")
                raise
        return self._user
    
    def test_connection(self) -> bool:
        """
        Test GitHub API connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            _ = self.user.login
            logger.info(f"GitHub connection successful for user: {self.user.login}")
            return True
        except GithubException as e:
            logger.error(f"GitHub connection failed: {e}")
            return False
    
    def get_user_repos(
        self,
        visibility: str = "all",
        affiliation: str = "owner,collaborator"
    ) -> List[Repository]:
        """
        Get user's repositories.
        
        Args:
            visibility: Repository visibility (all, public, private)
            affiliation: Repository affiliation (owner, collaborator, organization_member)
        
        Returns:
            List of Repository objects
        """
        try:
            repos = self.user.get_repos(
                visibility=visibility,
                affiliation=affiliation,
                sort="updated",
                direction="desc"
            )
            return list(repos)
        except GithubException as e:
            logger.error(f"Failed to get user repos: {e}")
            return []
    
    def get_commits_for_date(
        self,
        target_date: date,
        username: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all commits by user on a specific date.
        
        Args:
            target_date: Date to check for commits
            username: GitHub username (uses authenticated user if None)
        
        Returns:
            List of commit dictionaries with metadata
        """
        if username is None:
            username = self.user.login
        
        start_dt = get_start_of_day(target_date)
        end_dt = get_end_of_day(target_date)
        
        commits_data = []
        repos = self.get_user_repos()
        
        logger.info(f"Checking {len(repos)} repositories for commits on {target_date}")
        
        for repo in repos:
            try:
                # Get commits in date range by the user
                commits = repo.get_commits(
                    author=username,
                    since=start_dt,
                    until=end_dt
                )
                
                for commit in commits:
                    commit_data = {
                        "sha": commit.sha,
                        "message": commit.commit.message,
                        "repository": repo.full_name,
                        "date": commit.commit.author.date.isoformat(),
                        "url": commit.html_url,
                        "author": commit.commit.author.name,
                    }
                    commits_data.append(commit_data)
                    logger.debug(f"Found commit in {repo.full_name}: {commit.sha[:7]}")
                
            except GithubException as e:
                logger.warning(f"Error fetching commits from {repo.full_name}: {e}")
                continue
        
        logger.info(f"Found {len(commits_data)} commits on {target_date}")
        return commits_data
    
    def get_pull_requests_for_date(
        self,
        target_date: date,
        username: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pull requests created or updated by user on a specific date.
        
        Args:
            target_date: Date to check for PRs
            username: GitHub username (uses authenticated user if None)
        
        Returns:
            List of PR dictionaries with metadata
        """
        if username is None:
            username = self.user.login
        
        start_dt = get_start_of_day(target_date)
        end_dt = get_end_of_day(target_date)
        
        prs_data = []
        repos = self.get_user_repos()
        
        logger.info(f"Checking {len(repos)} repositories for PRs on {target_date}")
        
        for repo in repos:
            try:
                # Check both open and closed PRs
                for state in ["open", "closed"]:
                    prs = repo.get_pulls(
                        state=state,
                        sort="updated",
                        direction="desc"
                    )
                    
                    for pr in prs:
                        # Check if PR was created or updated on target date
                        pr_created = pr.created_at.date() == target_date
                        pr_updated = pr.updated_at.date() == target_date
                        pr_by_user = pr.user.login == username
                        
                        if pr_by_user and (pr_created or pr_updated):
                            pr_data = {
                                "number": pr.number,
                                "title": pr.title,
                                "repository": repo.full_name,
                                "state": pr.state,
                                "created_at": pr.created_at.isoformat(),
                                "updated_at": pr.updated_at.isoformat(),
                                "url": pr.html_url,
                                "author": pr.user.login,
                            }
                            prs_data.append(pr_data)
                            logger.debug(f"Found PR in {repo.full_name}: #{pr.number}")
                        
                        # Stop checking older PRs
                        if pr.updated_at < start_dt:
                            break
                
            except GithubException as e:
                logger.warning(f"Error fetching PRs from {repo.full_name}: {e}")
                continue
        
        logger.info(f"Found {len(prs_data)} PRs on {target_date}")
        return prs_data
    
    def get_issues_for_date(
        self,
        target_date: date,
        username: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get issues created or updated by user on a specific date.
        
        Args:
            target_date: Date to check for issues
            username: GitHub username (uses authenticated user if None)
        
        Returns:
            List of issue dictionaries with metadata
        """
        if username is None:
            username = self.user.login
        
        start_dt = get_start_of_day(target_date)
        end_dt = get_end_of_day(target_date)
        
        issues_data = []
        repos = self.get_user_repos()
        
        logger.info(f"Checking {len(repos)} repositories for issues on {target_date}")
        
        for repo in repos:
            try:
                # Check both open and closed issues
                for state in ["open", "closed"]:
                    issues = repo.get_issues(
                        state=state,
                        sort="updated",
                        direction="desc",
                        creator=username
                    )
                    
                    for issue in issues:
                        # Skip pull requests (GitHub API returns PRs as issues)
                        if issue.pull_request is not None:
                            continue
                        
                        # Check if issue was created or updated on target date
                        issue_created = issue.created_at.date() == target_date
                        issue_updated = issue.updated_at.date() == target_date
                        
                        if issue_created or issue_updated:
                            issue_data = {
                                "number": issue.number,
                                "title": issue.title,
                                "repository": repo.full_name,
                                "state": issue.state,
                                "created_at": issue.created_at.isoformat(),
                                "updated_at": issue.updated_at.isoformat(),
                                "url": issue.html_url,
                                "author": issue.user.login,
                            }
                            issues_data.append(issue_data)
                            logger.debug(f"Found issue in {repo.full_name}: #{issue.number}")
                        
                        # Stop checking older issues
                        if issue.updated_at < start_dt:
                            break
                
            except GithubException as e:
                logger.warning(f"Error fetching issues from {repo.full_name}: {e}")
                continue
        
        logger.info(f"Found {len(issues_data)} issues on {target_date}")
        return issues_data
    
    def get_daily_activity(
        self,
        target_date: date,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all GitHub activity for a user on a specific date.
        
        Args:
            target_date: Date to check for activity
            username: GitHub username (uses authenticated user if None)
        
        Returns:
            Dictionary containing all activity data
        """
        logger.info(f"Fetching GitHub activity for {target_date}")
        
        commits = self.get_commits_for_date(target_date, username)
        prs = self.get_pull_requests_for_date(target_date, username)
        issues = self.get_issues_for_date(target_date, username)
        
        # Get unique repositories
        repos = set()
        for commit in commits:
            repos.add(commit["repository"])
        for pr in prs:
            repos.add(pr["repository"])
        for issue in issues:
            repos.add(issue["repository"])
        
        activity_data = {
            "date": target_date.isoformat(),
            "commits": commits,
            "commits_count": len(commits),
            "pull_requests": prs,
            "prs_count": len(prs),
            "issues": issues,
            "issues_count": len(issues),
            "repositories": sorted(list(repos)),
            "total_activity": len(commits) + len(prs) + len(issues),
        }
        
        logger.info(
            f"Activity summary for {target_date}: "
            f"{len(commits)} commits, {len(prs)} PRs, {len(issues)} issues "
            f"across {len(repos)} repositories"
        )
        
        return activity_data
    
    def close(self):
        """Close the GitHub client connection."""
        if self.client:
            self.client.close()


@lru_cache(maxsize=32)
def get_github_service(github_token: str) -> GitHubService:
    """
    Get cached GitHub service instance.
    
    Args:
        github_token: GitHub personal access token
    
    Returns:
        GitHubService instance
    """
    return GitHubService(github_token)