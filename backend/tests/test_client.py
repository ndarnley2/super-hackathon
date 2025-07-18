#!/usr/bin/env python3
"""
Test client for GitHub Analytics API endpoints
This utility allows testing all endpoints with various parameters
"""

import requests
import argparse
import json
from datetime import datetime, timedelta
import sys
import os
from tabulate import tabulate
from colorama import Fore, Style, init
import logging
from tqdm import tqdm
import time
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# Initialize colorama
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_client')

# Default API URL
API_URL = os.environ.get('API_URL', 'http://localhost:5000/api/v1')

def parse_date(date_str):
    """Parse date string in YYYY-MM-DD format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        logger.error(f"Invalid date format: {date_str}. Use YYYY-MM-DD.")
        sys.exit(1)

def format_json(json_data, color=True):
    """Format JSON data for pretty printing."""
    formatted = json.dumps(json_data, indent=2, sort_keys=True)
    if color:
        # Highlight keys
        lines = []
        for line in formatted.split('\n'):
            if ": " in line:
                key, value = line.split(": ", 1)
                line = f"{Fore.CYAN}{key}{Fore.RESET}: {value}"
            lines.append(line)
        return '\n'.join(lines)
    return formatted

def save_output(data, filename):
    """Save data to a file."""
    if filename:
        with open(filename, 'w') as f:
            if isinstance(data, dict) or isinstance(data, list):
                json.dump(data, f, indent=2)
            else:
                f.write(str(data))
        print(f"{Fore.GREEN}Results saved to {filename}")

def test_api_health():
    """Test API health."""
    print(f"\n{Fore.YELLOW}Testing API Health...")
    
    try:
        response = requests.get(f"{API_URL.split('/api')[0]}/health")
        response.raise_for_status()
        
        print(f"{Fore.GREEN}API is healthy! ✓")
        return True
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}API health check failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"{Fore.RED}Response: {e.response.text}")
        return False

def test_authors(args):
    """Test the authors endpoint."""
    params = {}
    if args.start_date:
        params['start_date'] = args.start_date.strftime('%Y-%m-%d')
    if args.end_date:
        params['end_date'] = args.end_date.strftime('%Y-%m-%d')
    
    print(f"\n{Fore.YELLOW}Testing /authors endpoint...")
    print(f"Parameters: {params}")
    
    try:
        response = requests.get(f"{API_URL}/authors", params=params)
        response.raise_for_status()
        data = response.json()
        
        print(f"{Fore.GREEN}Success! Found {data['count']} unique authors")
        
        # Create a table of authors
        if data['count'] > 0:
            author_table = []
            for i, author in enumerate(data['authors'], 1):
                author_table.append([i, author])
            print(tabulate(author_table, headers=["#", "Author Name"], tablefmt="grid"))
        
        save_output(data, args.output)
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}API request failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"{Fore.RED}Response: {e.response.text}")
        return None

def test_deviations(args):
    """Test the deviations endpoint."""
    params = {}
    if args.start_date:
        params['start_date'] = args.start_date.strftime('%Y-%m-%d')
    if args.end_date:
        params['end_date'] = args.end_date.strftime('%Y-%m-%d')
    
    print(f"\n{Fore.YELLOW}Testing /deviations endpoint...")
    print(f"Parameters: {params}")
    
    try:
        response = requests.get(f"{API_URL}/deviations", params=params)
        response.raise_for_status()
        data = response.json()
        
        print(f"{Fore.GREEN}Success! Found {data['count']} commits with significant deviations")
        
        # Create a table of commits
        if data['count'] > 0:
            commit_table = []
            for i, commit in enumerate(data['commits'], 1):
                commit_table.append([
                    i, 
                    commit['sha'][:7], 
                    commit['z_score'], 
                    commit['total_changes'],
                    commit['author'],
                    commit['date'].split('T')[0],
                    commit['title'][:40] + ('...' if len(commit['title']) > 40 else '')
                ])
            print(tabulate(commit_table, headers=["#", "SHA", "Z-Score", "Changes", "Author", "Date", "Title"], tablefmt="grid"))
            
            # Visualize z-scores if requested
            if args.visualize:
                plt.figure(figsize=(10, 6))
                z_scores = [commit['z_score'] for commit in data['commits']]
                plt.hist(z_scores, bins=20, alpha=0.75, color='skyblue', edgecolor='black')
                plt.axvline(x=2, color='red', linestyle='--', label='Threshold (Z=2)')
                plt.xlabel('Z-Score')
                plt.ylabel('Frequency')
                plt.title('Distribution of Commit Z-Scores')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                if args.output and args.output.endswith('.json'):
                    viz_output = args.output.replace('.json', '_z_score_dist.png')
                else:
                    viz_output = 'z_score_distribution.png'
                    
                plt.savefig(viz_output)
                print(f"{Fore.GREEN}Z-score visualization saved to {viz_output}")
                plt.close()
        
        save_output(data, args.output)
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}API request failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"{Fore.RED}Response: {e.response.text}")
        return None

def test_day_of_week(args):
    """Test the day-of-week endpoint."""
    params = {
        'metric_type': args.metric_type
    }
    if args.start_date:
        params['start_date'] = args.start_date.strftime('%Y-%m-%d')
    if args.end_date:
        params['end_date'] = args.end_date.strftime('%Y-%m-%d')
    if args.author:
        params['author'] = args.author
    
    print(f"\n{Fore.YELLOW}Testing /day-of-week endpoint...")
    print(f"Parameters: {params}")
    
    try:
        response = requests.get(f"{API_URL}/day-of-week", params=params)
        response.raise_for_status()
        data = response.json()
        
        print(f"{Fore.GREEN}Success! Got day-of-week activity for {data['metric']}")
        if data['author']:
            print(f"Author: {data['author']}")
        
        # Create a table of activity
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        day_activity = data['day_activity']
        max_value = max(day_activity.values()) if day_activity.values() else 0
        
        activity_table = []
        for day in days:
            value = day_activity.get(day, 0)
            bar_length = int(50 * value / max_value) if max_value > 0 else 0
            bar = '█' * bar_length
            activity_table.append([day, value, bar])
        
        print(tabulate(activity_table, headers=["Day", "Value", "Distribution"], tablefmt="grid"))
        
        # Visualize if requested
        if args.visualize:
            plt.figure(figsize=(10, 6))
            values = [day_activity.get(day, 0) for day in days]
            plt.bar(days, values, color='skyblue', edgecolor='black')
            plt.xlabel('Day of Week')
            plt.ylabel(data['metric'].capitalize())
            title = f"Activity by Day of Week ({data['metric']})"
            if data['author']:
                title += f" - {data['author']}"
            plt.title(title)
            plt.grid(True, axis='y', alpha=0.3)
            plt.tight_layout()
            
            if args.output and args.output.endswith('.json'):
                viz_output = args.output.replace('.json', '_day_of_week.png')
            else:
                viz_output = 'day_of_week_activity.png'
                
            plt.savefig(viz_output)
            print(f"{Fore.GREEN}Day-of-week visualization saved to {viz_output}")
            plt.close()
        
        save_output(data, args.output)
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}API request failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"{Fore.RED}Response: {e.response.text}")
        return None

def test_word_frequencies(args):
    """Test the word-frequencies endpoint."""
    params = {}
    if args.start_date:
        params['start_date'] = args.start_date.strftime('%Y-%m-%d')
    if args.end_date:
        params['end_date'] = args.end_date.strftime('%Y-%m-%d')
    
    print(f"\n{Fore.YELLOW}Testing /word-frequencies endpoint...")
    print(f"Parameters: {params}")
    
    try:
        response = requests.get(f"{API_URL}/word-frequencies", params=params)
        response.raise_for_status()
        data = response.json()
        
        word_freqs = data['word_frequencies']
        sorted_words = sorted(word_freqs.items(), key=lambda x: x[1], reverse=True)
        
        print(f"{Fore.GREEN}Success! Got word frequencies for commit messages")
        
        # Create a table of top words
        word_table = []
        for i, (word, freq) in enumerate(sorted_words[:20], 1):
            word_table.append([i, word, freq])
        
        print(tabulate(word_table, headers=["#", "Word", "Frequency"], tablefmt="grid"))
        
        # Visualize if requested
        if args.visualize and sorted_words:
            plt.figure(figsize=(12, 8))
            words = [word for word, _ in sorted_words[:30]]
            freqs = [freq for _, freq in sorted_words[:30]]
            
            plt.barh(words[::-1], freqs[::-1], color='skyblue', edgecolor='black')
            plt.xlabel('Frequency')
            plt.ylabel('Word')
            plt.title('Top 30 Words in Commit Messages')
            plt.grid(True, axis='x', alpha=0.3)
            plt.tight_layout()
            
            if args.output and args.output.endswith('.json'):
                viz_output = args.output.replace('.json', '_word_frequencies.png')
            else:
                viz_output = 'word_frequencies.png'
                
            plt.savefig(viz_output)
            print(f"{Fore.GREEN}Word frequencies visualization saved to {viz_output}")
            plt.close()
        
        save_output(data, args.output)
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}API request failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"{Fore.RED}Response: {e.response.text}")
        return None

def test_fetch_data(args):
    """Test the fetch-data endpoint."""
    payload = {}
    if args.start_date:
        payload['start_date'] = args.start_date.strftime('%Y-%m-%d')
    if args.end_date:
        payload['end_date'] = args.end_date.strftime('%Y-%m-%d')
    if args.repo_owner:
        payload['repo_owner'] = args.repo_owner
    if args.repo_name:
        payload['repo_name'] = args.repo_name
    payload['use_cache'] = not args.no_cache
    
    print(f"\n{Fore.YELLOW}Testing /fetch-data endpoint...")
    print(f"Parameters: {payload}")
    
    try:
        # Set up progress bar with unknown total
        print("Fetching data from GitHub API. This may take a while...")
        progress = tqdm(desc="Fetching data", unit="commits")
        
        start_time = time.time()
        response = requests.post(f"{API_URL}/fetch-data", json=payload)
        response.raise_for_status()
        data = response.json()
        elapsed_time = time.time() - start_time
        
        progress.close()
        
        print(f"{Fore.GREEN}Success! Data fetch completed in {elapsed_time:.2f} seconds")
        print(f"Status: {data['status']}")
        print(f"Message: {data['message']}")
        print(f"Cache used: {Fore.CYAN}{data['cache_used']}")
        print(f"Repository: {data['repository']}")
        print(f"Date range: {data['start_date']} to {data['end_date']}")
        
        if 'commit_count' in data:
            print(f"Commit count: {Fore.CYAN}{data['commit_count']}")
        
        if 'statistics' in data and data['statistics']:
            stats = data['statistics']
            print(f"\n{Fore.YELLOW}Statistics:")
            stats_table = []
            for key, value in stats.items():
                if isinstance(value, float):
                    stats_table.append([key, f"{value:.2f}"])
                else:
                    stats_table.append([key, value])
            print(tabulate(stats_table, headers=["Metric", "Value"], tablefmt="grid"))
        
        save_output(data, args.output)
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}API request failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"{Fore.RED}Response: {e.response.text}")
        return None

def test_all(args):
    """Run all tests in sequence."""
    results = {}
    
    if not test_api_health():
        print(f"{Fore.RED}API health check failed. Aborting all tests.")
        return
    
    print(f"\n{Fore.YELLOW}Running all endpoint tests...")
    
    # Test authors endpoint
    results['authors'] = test_authors(args)
    
    # Test deviations endpoint
    results['deviations'] = test_deviations(args)
    
    # Test day-of-week endpoint for all metrics
    for metric in ['commits', 'additions', 'deletions', 'total_changes']:
        args.metric_type = metric
        results[f'day_of_week_{metric}'] = test_day_of_week(args)
    
    # Test word frequencies endpoint
    results['word_frequencies'] = test_word_frequencies(args)
    
    # Test fetch data endpoint
    results['fetch_data'] = test_fetch_data(args)
    
    # Save overall results
    if args.output:
        save_output(results, args.output)
    
    print(f"\n{Fore.GREEN}All tests completed!")

def main():
    parser = argparse.ArgumentParser(
        description='GitHub Commit Analytics API Test Client',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
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
        parser.add_argument(
            '--visualize', '-v',
            action='store_true',
            help='Generate visualizations for results'
        )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    subparsers.required = True
    
    # Health check
    health_parser = subparsers.add_parser(
        'health',
        help='Check API health'
    )
    health_parser.set_defaults(func=lambda args: test_api_health())
    
    # Authors command
    authors_parser = subparsers.add_parser(
        'authors',
        help='Test the authors endpoint'
    )
    add_common_args(authors_parser)
    authors_parser.set_defaults(func=test_authors)
    
    # Deviations command
    dev_parser = subparsers.add_parser(
        'deviations',
        help='Test the deviations endpoint'
    )
    add_common_args(dev_parser)
    dev_parser.set_defaults(func=test_deviations)
    
    # Day of week command
    dow_parser = subparsers.add_parser(
        'day-of-week',
        help='Test the day-of-week endpoint'
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
    dow_parser.set_defaults(func=test_day_of_week)
    
    # Word frequencies command
    word_parser = subparsers.add_parser(
        'word-frequencies',
        help='Test the word-frequencies endpoint'
    )
    add_common_args(word_parser)
    word_parser.set_defaults(func=test_word_frequencies)
    
    # Fetch data command
    fetch_parser = subparsers.add_parser(
        'fetch-data',
        help='Test the fetch-data endpoint'
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
    fetch_parser.set_defaults(func=test_fetch_data)
    
    # All tests command
    all_parser = subparsers.add_parser(
        'all',
        help='Run all tests'
    )
    add_common_args(all_parser)
    all_parser.add_argument(
        '--repo-owner',
        default='OpenRA',
        help='Repository owner'
    )
    all_parser.add_argument(
        '--repo-name',
        default='OpenRA',
        help='Repository name'
    )
    all_parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Ignore cache and fetch fresh data'
    )
    all_parser.set_defaults(func=test_all)
    
    # Parse arguments and call the appropriate function
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
