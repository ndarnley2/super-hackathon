import os
import time
import logging
from datetime import datetime, timedelta
import requests
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from tqdm import tqdm
import redis
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Commit, CacheStatus, CommitWordFrequency

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('github_client')

class GitHubAPIClient:
    """
    Client for interacting with GitHub's GraphQL API.
    Handles authentication, rate limiting, pagination and caching.
    """
    def __init__(self, token=None, redis_url=None, db_url=None):
        self.token = token or os.environ.get('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        
        # Setup Redis connection for rate limiting
        self.redis_client = None
        if redis_url:
            self.redis_client = redis.from_url(redis_url)
        else:
            try:
                self.redis_client = redis.Redis(host='redis', port=6379, db=0)
            except redis.exceptions.ConnectionError:
                logger.warning("Redis connection failed. Rate limiting will be handled locally.")
        
        # Setup database connection
        if db_url:
            self.engine = create_engine(db_url)
        else:
            db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/github_analytics')
            self.engine = create_engine(db_url)
        
        self.Session = sessionmaker(bind=self.engine)
        
        # Setup GraphQL client configuration
        self.api_url = "https://api.github.com/graphql"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        # We'll create a new client for each request instead of reusing one
        
        # Rate limit settings
        self.rate_limit_remaining = 5000  # Default GitHub rate limit
        self.rate_limit_reset = 0
        
    def _check_rate_limit(self):
        """Check if we're within rate limits, wait if necessary."""
        now = time.time()
        
        # If using Redis, get rate limit info from there
        if self.redis_client:
            try:
                remaining = self.redis_client.get('github_rate_limit_remaining')
                reset_time = self.redis_client.get('github_rate_limit_reset')
                
                if remaining and reset_time:
                    self.rate_limit_remaining = int(remaining)
                    self.rate_limit_reset = float(reset_time)
            except Exception as e:
                logger.error(f"Redis error: {e}")
        
        # Check if we need to wait
        if self.rate_limit_remaining <= 1:
            wait_time = max(0, self.rate_limit_reset - now)
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time + 1)  # Add 1 second buffer
    
    def _update_rate_limit(self, response_headers):
        """Update rate limit information from response headers."""
        if 'X-RateLimit-Remaining' in response_headers:
            self.rate_limit_remaining = int(response_headers['X-RateLimit-Remaining'])
            
        if 'X-RateLimit-Reset' in response_headers:
            self.rate_limit_reset = int(response_headers['X-RateLimit-Reset'])
            
        # Store in Redis if available
        if self.redis_client:
            try:
                self.redis_client.set('github_rate_limit_remaining', self.rate_limit_remaining)
                self.redis_client.set('github_rate_limit_reset', self.rate_limit_reset)
            except Exception as e:
                logger.error(f"Redis error: {e}")
    
    def _get_commits_query(self):
        """Return the GraphQL query for fetching commits."""
        return gql("""
        query GetCommits($owner: String!, $repo: String!, $after: String, $since: GitTimestamp!, $until: GitTimestamp!) {
          repository(owner: $owner, name: $repo) {
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 100, after: $after, since: $since, until: $until) {
                    pageInfo {
                      hasNextPage
                      endCursor
                    }
                    nodes {
                      oid
                      message
                      author {
                        name
                        email
                        date
                      }
                      additions
                      deletions
                      parents(first: 2) {
                        totalCount
                      }
                    }
                  }
                }
              }
            }
          }
          rateLimit {
            limit
            remaining
            resetAt
          }
        }
        """)
    
    def _fetch_commits_page(self, owner, repo, after=None, since=None, until=None):
        """Fetch a single page of commits from GitHub."""
        self._check_rate_limit()
        
        query = self._get_commits_query()
        # GitHub's GraphQL API requires GitTimestamp in RFC3339 format: YYYY-MM-DDTHH:MM:SSZ
        variables = {
            "owner": owner,
            "repo": repo,
            "after": after,
            "since": since.strftime('%Y-%m-%dT%H:%M:%SZ') if since else None,
            "until": until.strftime('%Y-%m-%dT%H:%M:%SZ') if until else None
        }
        logger.debug(f"GraphQL variables: {variables}")
        
        try:
            # Create a new client for each request to avoid connection issues
            transport = AIOHTTPTransport(url=self.api_url, headers=self.headers)
            client = Client(transport=transport, fetch_schema_from_transport=True)
            result = client.execute(query, variable_values=variables)
            
            # Update rate limit info
            if "rateLimit" in result:
                self.rate_limit_remaining = result["rateLimit"]["remaining"]
                reset_time = datetime.fromisoformat(result["rateLimit"]["resetAt"].replace("Z", "+00:00"))
                self.rate_limit_reset = reset_time.timestamp()
                
                if self.redis_client:
                    try:
                        self.redis_client.set('github_rate_limit_remaining', self.rate_limit_remaining)
                        self.redis_client.set('github_rate_limit_reset', self.rate_limit_reset)
                    except Exception as e:
                        logger.error(f"Redis error: {e}")
            
            return result
        except Exception as e:
            logger.error(f"GraphQL query error: {e}")
            # If we get a rate limit error, wait and retry
            if "rate limit" in str(e).lower():
                logger.info("Rate limit exceeded. Waiting for reset...")
                time.sleep(60)  # Wait a minute and try again
                return self._fetch_commits_page(owner, repo, after, since, until)
            raise
    
    def fetch_commits(self, owner, repo, start_date=None, end_date=None, use_cache=True, progress_callback=None):
        """
        Fetch all commits for a repository within a date range.
        
        Args:
            owner (str): Repository owner
            repo (str): Repository name
            start_date (datetime): Starting date for commits
            end_date (datetime): Ending date for commits
            use_cache (bool): Whether to use cached data if available
            progress_callback (callable): Function to call with progress updates
            
        Returns:
            list: List of commit data dictionaries
        """
        # Default date range: 1 year ago to yesterday
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=365)
        if not end_date:
            end_date = datetime.utcnow() - timedelta(days=1)
        
        repository = f"{owner}/{repo}"
        session = self.Session()
        
        try:
            # Check if we have cached data
            cache_status = None
            if use_cache:
                cache_status = session.query(CacheStatus).filter(
                    CacheStatus.repository == repository,
                    CacheStatus.start_date <= start_date,
                    CacheStatus.end_date >= end_date,
                    CacheStatus.completed == True
                ).first()
                
                if cache_status:
                    logger.info(f"Using cached commit data for {repository} from {start_date} to {end_date}")
                    
                    commits = session.query(Commit).filter(
                        Commit.repository == repository,
                        Commit.author_date >= start_date,
                        Commit.author_date <= end_date
                    ).all()
                    
                    # Convert to dictionaries
                    commit_dicts = []
                    for commit in commits:
                        commit_dicts.append({
                            "sha": commit.sha,
                            "author_name": commit.author_name,
                            "author_email": commit.author_email,
                            "author_date": commit.author_date,
                            "message_title": commit.message_title,
                            "message_body": commit.message_body,
                            "additions": commit.additions,
                            "deletions": commit.deletions,
                            "total_changes": commit.total_changes,
                            "repository": commit.repository,
                            "z_score": commit.z_score
                        })
                    
                    return commit_dicts
            
            # Check if we have an incomplete fetch that we can resume
            incomplete_cache = session.query(CacheStatus).filter(
                CacheStatus.repository == repository,
                CacheStatus.start_date == start_date,
                CacheStatus.end_date == end_date,
                CacheStatus.completed == False
            ).first()
            
            last_cursor = None
            if incomplete_cache:
                logger.info(f"Resuming commit fetch for {repository} from {start_date} to {end_date}")
                last_cursor = incomplete_cache.last_cursor
            else:
                # Create a new cache status record
                cache_status = CacheStatus(
                    repository=repository,
                    start_date=start_date,
                    end_date=end_date,
                    completed=False
                )
                session.add(cache_status)
                session.commit()
            
            # Fetch all commits
            has_next_page = True
            after_cursor = last_cursor
            all_commits = []
            
            # Use tqdm for progress bar
            pbar = None
            
            while has_next_page:
                try:
                    result = self._fetch_commits_page(
                        owner,
                        repo,
                        after=after_cursor,
                        since=start_date,
                        until=end_date
                    )
                    
                    if not result or "repository" not in result or not result["repository"]["defaultBranchRef"]:
                        logger.error("Invalid response from GitHub API")
                        break
                    
                    history = result["repository"]["defaultBranchRef"]["target"]["history"]
                    commits = history["nodes"]
                    page_info = history["pageInfo"]
                    
                    # Process each commit
                    for commit in commits:
                        # Skip merge commits (more than one parent)
                        if commit["parents"]["totalCount"] > 1:
                            continue
                        
                        # Parse the message
                        message_lines = commit["message"].strip().split("\n", 1)
                        message_title = message_lines[0]
                        message_body = message_lines[1] if len(message_lines) > 1 else None
                        
                        # Check if commit already exists in the database
                        existing_commit = session.query(Commit).filter(Commit.sha == commit["oid"]).first()
                        
                        if existing_commit:
                            # Commit already exists, update it if needed
                            logger.debug(f"Commit {commit['oid']} already exists, skipping insert")
                            commit_obj = existing_commit
                        else:
                            # Create a new commit record
                            commit_obj = Commit(
                                sha=commit["oid"],
                                author_name=commit["author"]["name"],
                                author_email=commit["author"]["email"],
                                author_date=datetime.fromisoformat(commit["author"]["date"].replace("Z", "+00:00")),
                                message_title=message_title,
                                message_body=message_body,
                                additions=commit["additions"],
                                deletions=commit["deletions"],
                                total_changes=commit["additions"] + commit["deletions"],
                                repository=repository
                            )
                            
                            # Add to session
                            session.add(commit_obj)
                        
                        # Add to our return list
                        all_commits.append({
                            "sha": commit_obj.sha,
                            "author_name": commit_obj.author_name,
                            "author_email": commit_obj.author_email,
                            "author_date": commit_obj.author_date,
                            "message_title": commit_obj.message_title,
                            "message_body": commit_obj.message_body,
                            "additions": commit_obj.additions,
                            "deletions": commit_obj.deletions,
                            "total_changes": commit_obj.total_changes,
                            "repository": commit_obj.repository
                        })
                    
                    # Update progress bar
                    if not pbar:
                        # Initialize progress bar with an initial total (can be updated later)
                        pbar = tqdm(total=100, desc=f"Fetching commits for {repository}")
                    
                    # Update with actual progress
                    pbar.update(len(commits))
                    # Update total if we know more commits are coming
                    if page_info["hasNextPage"]:
                        # If we have more pages, increase the total estimate
                        new_total = pbar.n + 100
                        pbar.total = max(pbar.total, new_total)
                    
                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(len(all_commits), page_info["hasNextPage"])
                    
                    # Update cache status
                    if incomplete_cache:
                        incomplete_cache.last_cursor = page_info["endCursor"]
                        incomplete_cache.last_updated = datetime.utcnow()
                        session.commit()
                    else:
                        cache_status.last_cursor = page_info["endCursor"]
                        cache_status.last_updated = datetime.utcnow()
                        session.commit()
                    
                    # Prepare for next page
                    has_next_page = page_info["hasNextPage"]
                    after_cursor = page_info["endCursor"] if has_next_page else None
                
                except Exception as e:
                    logger.error(f"Error fetching commits: {e}")
                    # Save progress before raising
                    session.commit()
                    raise
            
            if pbar:
                pbar.close()
            
            # Mark cache as complete
            if incomplete_cache:
                incomplete_cache.completed = True
                session.commit()
            else:
                cache_status.completed = True
                session.commit()
            
            logger.info(f"Successfully fetched {len(all_commits)} commits for {repository}")
            return all_commits
            
        except Exception as e:
            logger.error(f"Error in fetch_commits: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def calculate_commit_statistics(self, owner, repo, start_date=None, end_date=None):
        """
        Calculate statistics for commits, including z-scores for commit sizes.
        
        Args:
            owner (str): Repository owner
            repo (str): Repository name
            start_date (datetime): Starting date for commits
            end_date (datetime): Ending date for commits
            
        Returns:
            dict: Statistics about the commits
        """
        import numpy as np
        
        # Default date range: 1 year ago to yesterday
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=365)
        if not end_date:
            end_date = datetime.utcnow() - timedelta(days=1)
        
        repository = f"{owner}/{repo}"
        session = self.Session()
        
        try:
            # Get all commits
            commits = session.query(Commit).filter(
                Commit.repository == repository,
                Commit.author_date >= start_date,
                Commit.author_date <= end_date
            ).all()
            
            if not commits:
                return {"error": "No commits found"}
            
            # Extract total changes
            total_changes_list = [commit.total_changes for commit in commits]
            
            # Calculate mean and standard deviation
            mean_changes = np.mean(total_changes_list)
            std_changes = np.std(total_changes_list)
            
            # Calculate z-scores and update commits
            for commit in commits:
                if std_changes > 0:  # Avoid division by zero
                    # Calculate z_score as a NumPy value but convert to Python float before storing
                    z_score = (commit.total_changes - mean_changes) / std_changes
                    commit.z_score = float(z_score)  # Convert NumPy float64 to Python float
            
            session.commit()
            
            return {
                "commit_count": len(commits),
                "mean_changes": mean_changes,
                "std_changes": std_changes
            }
        
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def calculate_word_frequencies(self, owner, repo, start_date=None, end_date=None):
        """
        Calculate word frequencies from commit messages and store them.
        
        Args:
            owner (str): Repository owner
            repo (str): Repository name
            start_date (datetime): Starting date for commits
            end_date (datetime): Ending date for commits
            
        Returns:
            dict: Word frequencies
        """
        import re
        from collections import Counter
        
        # Default date range: 1 year ago to yesterday
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=365)
        if not end_date:
            end_date = datetime.utcnow() - timedelta(days=1)
        
        repository = f"{owner}/{repo}"
        session = self.Session()
        
        try:
            # Get all commits
            commits = session.query(Commit).filter(
                Commit.repository == repository,
                Commit.author_date >= start_date,
                Commit.author_date <= end_date
            ).all()
            
            if not commits:
                return {"error": "No commits found"}
            
            # Common stop words to filter out
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                'be', 'been', 'being', 'to', 'of', 'for', 'in', 'on', 'by', 'at', 
                'this', 'that', 'these', 'those', 'with', 'as', 'from', 'about', 
                'into', 'through', 'during', 'before', 'after', 'above', 'below', 
                'up', 'down', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 
                'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 
                'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 
                'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 
                'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how', 
                'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 
                'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 
                'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now'
            }
            
            # Collect all words from commit messages
            all_words = []
            for commit in commits:
                message = f"{commit.message_title} {commit.message_body or ''}"
                # Convert to lowercase and split on non-alphanumeric characters
                words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]+\b', message.lower())
                # Filter out stop words
                words = [word for word in words if word not in stop_words]
                all_words.extend(words)
            
            # Count word frequencies
            word_counter = Counter(all_words)
            
            # Store in database
            for word, frequency in word_counter.items():
                word_freq = session.query(CommitWordFrequency).filter(
                    CommitWordFrequency.word == word,
                    CommitWordFrequency.repository == repository,
                    CommitWordFrequency.start_date == start_date,
                    CommitWordFrequency.end_date == end_date
                ).first()
                
                if word_freq:
                    word_freq.frequency = frequency
                else:
                    word_freq = CommitWordFrequency(
                        word=word,
                        frequency=frequency,
                        repository=repository,
                        start_date=start_date,
                        end_date=end_date
                    )
                    session.add(word_freq)
            
            session.commit()
            
            # Return the top words
            top_words = dict(word_counter.most_common(100))
            return top_words
        
        except Exception as e:
            logger.error(f"Error calculating word frequencies: {e}")
            session.rollback()
            raise
        finally:
            session.close()
