#!/usr/bin/env python3
"""
Command-line interface for GitHub commit analytics.
Provides a way to test the backend endpoints directly from the terminal.
"""

import argparse
import json
from datetime import datetime, timedelta
import sys
import os
import requests
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cli')

# Default API URL
API_URL = os.environ.get('API_URL', 'http://localhost:5000/api/v1')

def parse_date(date_str):
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        logger.error(f"Invalid date format: {date_str}. Use YYYY-MM-DD.")
        sys.exit(1)

def format_json(json_data):
    """Format JSON data for pretty printing."""
    return json.dumps(json_data, indent=2, sort_keys=True)

def get_authors(args):
    """Get unique commit authors within date range."""
    params = {}
    if args.start_date:
        params['start_date'] = args.start_date
    if args.end_date:
        params['end_date'] = args.end_date
    
    try:
        response = requests.get(f"{API_URL}/authors", params=params)
        response.raise_for_status()
        data = response.json()
        
        print(f"\nFound {data['count']} unique authors:")
        for i, author in enumerate(data['authors'], 1):
            print(f"{i}. {author}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\nResults saved to {args.output}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        sys.exit(1)

def get_deviations(args):
    """Get commits with significant deviations."""
    params = {}
    if args.start_date:
        params['start_date'] = args.start_date
    if args.end_date:
        params['end_date'] = args.end_date
    
    try:
        response = requests.get(f"{API_URL}/deviations", params=params)
        response.raise_for_status()
        data = response.json()
        
        print(f"\nFound {data['count']} commits with significant deviations (z-score > 2):")
        for i, commit in enumerate(data['commits'], 1):
            print(f"{i}. {commit['sha'][:7]} | Z-score: {commit['z_score']} | Changes: {commit['total_changes']} | {commit['title'][:60]}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\nResults saved to {args.output}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        sys.exit(1)

def get_day_of_week(args):
    """Get activity by day of week."""
    params = {
        'metric_type': args.metric_type
    }
    if args.start_date:
        params['start_date'] = args.start_date
    if args.end_date:
        params['end_date'] = args.end_date
    if args.author:
        params['author'] = args.author
    
    try:
        response = requests.get(f"{API_URL}/day-of-week", params=params)
        response.raise_for_status()
        data = response.json()
        
        print(f"\nActivity by day of week ({data['metric']})")
        if data['author']:
            print(f"Author: {data['author']}")
        
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        max_value = max(data['day_activity'].values())
        scale_factor = 40 / max_value if max_value > 0 else 1
        
        for day in days:
            value = data['day_activity'].get(day, 0)
            bar_length = int(value * scale_factor)
            bar = '█' * bar_length
            print(f"{day.ljust(10)}: {bar} {value}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\nResults saved to {args.output}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        sys.exit(1)

def get_word_frequencies(args):
    """Get word frequencies from commit messages."""
    params = {}
    if args.start_date:
        params['start_date'] = args.start_date
    if args.end_date:
        params['end_date'] = args.end_date
    
    try:
        response = requests.get(f"{API_URL}/word-frequencies", params=params)
        response.raise_for_status()
        data = response.json()
        
        word_freqs = data['word_frequencies']
        sorted_words = sorted(word_freqs.items(), key=lambda x: x[1], reverse=True)
        
        print("\nWord frequencies in commit messages:")
        for i, (word, freq) in enumerate(sorted_words[:20], 1):
            print(f"{i}. {word}: {freq}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\nResults saved to {args.output}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        sys.exit(1)

def fetch_data(args):
    """Fetch data from GitHub API."""
    payload = {}
    if args.start_date:
        payload['start_date'] = args.start_date
    if args.end_date:
        payload['end_date'] = args.end_date
    if args.repo_owner:
        payload['repo_owner'] = args.repo_owner
    if args.repo_name:
        payload['repo_name'] = args.repo_name
    payload['use_cache'] = not args.no_cache
    
    try:
        print("Fetching data from GitHub API. This may take a while...")
        response = requests.post(f"{API_URL}/fetch-data", json=payload)
        response.raise_for_status()
        data = response.json()
        
        print("\nData fetch result:")
        print(f"Status: {data['status']}")
        print(f"Message: {data['message']}")
        print(f"Cache used: {data['cache_used']}")
        print(f"Repository: {data['repository']}")
        print(f"Date range: {data['start_date']} to {data['end_date']}")
        
        if 'commit_count' in data:
            print(f"Commit count: {data['commit_count']}")
        
        if 'statistics' in data and data['statistics']:
            stats = data['statistics']
            print("\nStatistics:")
            for key, value in stats.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.2f}")
                else:
                    print(f"  {key}: {value}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\nResults saved to {args.output}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        sys.exit(1)

def main():
    # Create main parser
    parser = argparse.ArgumentParser(
        description='GitHub Commit Analytics CLI',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    subparsers.required = True
    
    # Common arguments
    def add_common_args(parser):
        parser.add_argument(
            '--start-date', '-s',
            type=parse_date,
            help='Start date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end-date', '-e',
            type=parse_date,
            help='End date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--output', '-o',
            help='Output file for JSON results'
        )
    
    # Authors command
    authors_parser = subparsers.add_parser(
        'authors',
        help='Get unique commit authors'
    )
    add_common_args(authors_parser)
    authors_parser.set_defaults(func=get_authors)
    
    # Deviations command
    dev_parser = subparsers.add_parser(
        'deviations',
        help='Get commits with significant deviations'
    )
    add_common_args(dev_parser)
    dev_parser.set_defaults(func=get_deviations)
    
    # Day of week command
    dow_parser = subparsers.add_parser(
        'day-of-week',
        help='Get activity by day of week'
    )
    add_common_args(dow_parser)
    dow_parser.add_argument(
        '--metric-type', '-m',
        required=True,
        choices=['commits', 'additions', 'deletions', 'total_changes'],
        help='Metric type to analyze'
    )
    dow_parser.add_argument(
        '--author', '-a',
        help='Filter by author'
    )
    dow_parser.set_defaults(func=get_day_of_week)
    
    # Word frequencies command
    word_parser = subparsers.add_parser(
        'word-frequencies',
        help='Get word frequencies from commit messages'
    )
    add_common_args(word_parser)
    word_parser.set_defaults(func=get_word_frequencies)
    
    # Fetch data command
    fetch_parser = subparsers.add_parser(
        'fetch-data',
        help='Fetch data from GitHub API'
    )
    add_common_args(fetch_parser)
    fetch_parser.add_argument(
        '--repo-owner',
        default='OpenRA',
        help='Repository owner'
    )
    fetch_parser.add_argument(
        '--repo-name',
        default='OpenRA',
        help='Repository name'
    )
    fetch_parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Ignore cache and fetch fresh data'
    )
    fetch_parser.set_defaults(func=fetch_data)
    
    # Parse arguments and call the appropriate function
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
