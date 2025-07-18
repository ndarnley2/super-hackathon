#!/usr/bin/env python3
"""
Test utilities for GitHub Analytics API endpoints using requests-mock
"""

import sys
import os
import json
import requests
import requests_mock
from datetime import datetime, timedelta
from urllib.parse import urlencode

# Add parent directory to path to import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Base URL for our mock API
BASE_URL = 'http://localhost:5000/api/v1'


# Simple API client for testing
class SimpleApiClient:
    """Simple API client that doesn't depend on matplotlib"""
    
    def __init__(self, base_url):
        """Initialize with the base API URL"""
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def get_endpoint(self, endpoint, **params):
        """Make a GET request to the specified endpoint with params"""
        url = f"{self.base_url}/api/v1/{endpoint}"
        if params:
            url = f"{url}?{urlencode(params)}"
        return self.session.get(url)
    
    def fetch_data(self, payload):
        """Make a POST request to the fetch-data endpoint"""
        url = f"{self.base_url}/api/v1/fetch-data"
        return self.session.post(url, json=payload)


# Mock response data for various endpoints
mock_responses = {
    'health': {
        'status': 'ok'
    },
    'authors': {
        'authors': ['Author 1', 'Author 2', 'Author 3'],
        'count': 3
    },
    'deviations': {
        'commits': [
            {
                'sha': 'abc1234',
                'title': 'Test commit 1',
                'author': 'Author 1',
                'date': '2025-06-01T10:00:00Z',
                'additions': 100,
                'deletions': 50,
                'total_changes': 150,
                'z_score': 3.5
            },
            {
                'sha': 'def5678',
                'title': 'Test commit 2',
                'author': 'Author 2',
                'date': '2025-06-02T11:00:00Z',
                'additions': 200,
                'deletions': 100,
                'total_changes': 300,
                'z_score': 5.2
            }
        ],
        'count': 2
    },
    'day-of-week': {
        'metric': 'commits',
        'day_activity': {
            'Sunday': 10,
            'Monday': 15,
            'Tuesday': 0,
            'Wednesday': 0,
            'Thursday': 25,
            'Friday': 0,
            'Saturday': 0
        }
    },
    'word-frequencies': {
        'word_frequencies': {
            'feature': 10,
            'bug': 8,
            'fix': 15,
            'implement': 6,
            'update': 12
        }
    },
    'fetch-data': {
        'status': 'success',
        'cache_used': True,
        'repository': 'OpenRA/OpenRA',
        'commit_count': 2,
        'statistics': {
            'commit_count': 2,
            'mean_changes': 100.0,
            'std_changes': 50.0
        }
    }
}


def register_mock_endpoints(adapter):
    """Register all mock API endpoints on the requests_mock adapter"""
    # Health check endpoint
    adapter.register_uri(
        'GET', f'{BASE_URL}/health',
        json=mock_responses['health']
    )
    
    # Authors endpoint
    adapter.register_uri(
        'GET', requests_mock.ANY,
        json=mock_responses['authors'],
        additional_matcher=lambda r: r.path.startswith('/api/v1/authors')
    )
    
    # Deviations endpoint
    adapter.register_uri(
        'GET', requests_mock.ANY,
        json=mock_responses['deviations'],
        additional_matcher=lambda r: r.path.startswith('/api/v1/deviations')
    )
    
    # Day-of-week endpoint
    adapter.register_uri(
        'GET', requests_mock.ANY,
        json=mock_responses['day-of-week'],
        additional_matcher=lambda r: r.path.startswith('/api/v1/day-of-week')
    )
    
    # Word frequencies endpoint
    adapter.register_uri(
        'GET', requests_mock.ANY,
        json=mock_responses['word-frequencies'],
        additional_matcher=lambda r: r.path.startswith('/api/v1/word-frequencies')
    )
    
    # Fetch data endpoint
    adapter.register_uri(
        'POST', f'{BASE_URL}/fetch-data',
        json=mock_responses['fetch-data']
    )
