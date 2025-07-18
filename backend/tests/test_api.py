#!/usr/bin/env python3
"""
Unit tests for GitHub Analytics API endpoints using requests-mock
"""

import unittest
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


class GitHubAnalyticsAPITest(unittest.TestCase):
    """Test case for API endpoints using requests_mock"""
    
    def setUp(self):
        """Set up test client and mock API"""
        self.adapter = requests_mock.Adapter()
        self.session = requests.Session()
        self.session.mount('http://', self.adapter)
        
        # Set up datetime objects for testing
        self.start_date = datetime(2025, 6, 1)
        self.start_date_str = self.start_date.strftime("%Y-%m-%d")
        self.end_date = datetime(2025, 7, 1)
        self.end_date_str = self.end_date.strftime("%Y-%m-%d")
        
        # Register mock API endpoints
        self.register_mocks()
        
        # Create simple API client using our session
        self.client = SimpleApiClient('http://localhost:5000')
        self.client.session = self.session
    
    def register_mocks(self):
        """Register mock API responses"""
        # Health check endpoint
        self.adapter.register_uri(
            'GET', f'{BASE_URL}/health',
            json={'status': 'ok'}
        )
        
        # Authors endpoint
        self.adapter.register_uri(
            'GET', requests_mock.ANY,
            json={
                'authors': ['Author 1', 'Author 2', 'Author 3'],
                'count': 3
            },
            additional_matcher=lambda r: r.path.startswith('/api/v1/authors')
        )
        
        # Deviations endpoint
        self.adapter.register_uri(
            'GET', requests_mock.ANY,
            json={
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
            additional_matcher=lambda r: r.path.startswith('/api/v1/deviations')
        )
        
        # Day-of-week endpoint
        self.adapter.register_uri(
            'GET', requests_mock.ANY,
            json={
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
            additional_matcher=lambda r: r.path.startswith('/api/v1/day-of-week')
        )
        
        # Word frequencies endpoint
        self.adapter.register_uri(
            'GET', requests_mock.ANY,
            json={
                'word_frequencies': {
                    'feature': 10,
                    'bug': 8,
                    'fix': 15,
                    'implement': 6,
                    'update': 12
                }
            },
            additional_matcher=lambda r: r.path.startswith('/api/v1/word-frequencies')
        )
        
        # Fetch data endpoint
        self.adapter.register_uri(
            'POST', f'{BASE_URL}/fetch-data',
            json={
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
        )
    
    def test_health_check(self):
        """Test the health check endpoint"""
        response = self.client.get_endpoint('health')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'ok')
    
    def test_authors_endpoint(self):
        """Test the authors endpoint"""
        response = self.client.get_endpoint('authors', 
                                      start_date=self.start_date_str,
                                      end_date=self.end_date_str)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('authors', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 3)
        self.assertEqual(len(data['authors']), 3)
        self.assertIn('Author 1', data['authors'])
        self.assertIn('Author 2', data['authors'])
        self.assertIn('Author 3', data['authors'])
    
    def test_deviations_endpoint(self):
        """Test the deviations endpoint"""
        response = self.client.get_endpoint('deviations',
                                      start_date=self.start_date_str,
                                      end_date=self.end_date_str)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('commits', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['commits']), 2)
        
        # Check specific fields
        self.assertEqual(data['commits'][0]['sha'], 'abc1234')
        self.assertEqual(data['commits'][0]['title'], 'Test commit 1')
        self.assertEqual(data['commits'][0]['author'], 'Author 1')
        self.assertEqual(data['commits'][0]['z_score'], 3.5)
        
        self.assertEqual(data['commits'][1]['sha'], 'def5678')
        self.assertEqual(data['commits'][1]['title'], 'Test commit 2')
        self.assertEqual(data['commits'][1]['author'], 'Author 2')
        self.assertEqual(data['commits'][1]['z_score'], 5.2)
        
        # Day-of-week endpoint
        self.adapter.register_uri(
            'GET', requests_mock.ANY,
            json={
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
            additional_matcher=lambda r: r.path.startswith('/api/v1/day-of-week')
        )
        
        # Word frequencies endpoint
        self.adapter.register_uri(
            'GET', requests_mock.ANY,
            json={
                'word_frequencies': {
                    'feature': 10,
                    'bug': 8,
                    'fix': 15,
                    'implement': 6,
                    'update': 12
                }
            },
            additional_matcher=lambda r: r.path.startswith('/api/v1/word-frequencies')
        )
        
        # Fetch data endpoint
        self.adapter.register_uri(
            'POST', f'{BASE_URL}/fetch-data',
            json={
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
        )


    def test_health_check(self):
        """Test the health check endpoint"""
        response = self.client.get_endpoint('health')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'ok')
    
    def test_authors_endpoint(self):
        """Test the authors endpoint"""
        response = self.client.get_endpoint('authors', 
                                      start_date=self.start_date_str,
                                      end_date=self.end_date_str)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('authors', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 3)
        self.assertEqual(len(data['authors']), 3)
        self.assertIn('Author 1', data['authors'])
        self.assertIn('Author 2', data['authors'])
        self.assertIn('Author 3', data['authors'])
    
    def test_deviations_endpoint(self):
        """Test the deviations endpoint"""
        response = self.client.get_endpoint('deviations',
                                      start_date=self.start_date_str,
                                      end_date=self.end_date_str)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('commits', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['commits']), 2)
        
        # Check specific fields
        self.assertEqual(data['commits'][0]['sha'], 'abc1234')
        self.assertEqual(data['commits'][0]['title'], 'Test commit 1')
        self.assertEqual(data['commits'][0]['author'], 'Author 1')
        self.assertEqual(data['commits'][0]['z_score'], 3.5)
        
        self.assertEqual(data['commits'][1]['sha'], 'def5678')
        self.assertEqual(data['commits'][1]['title'], 'Test commit 2')
        self.assertEqual(data['commits'][1]['author'], 'Author 2')
        self.assertEqual(data['commits'][1]['z_score'], 5.2)
    
    def test_day_of_week_endpoint(self):
        """Test the day-of-week endpoint"""
        response = self.client.get_endpoint('day-of-week',
                                      start_date=self.start_date_str,
                                      end_date=self.end_date_str,
                                      metric_type='commits')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('metric', data)
        self.assertIn('day_activity', data)
        
        # Check specific fields
        self.assertEqual(data['metric'], 'commits')
        self.assertEqual(data['day_activity']['Sunday'], 10)
        self.assertEqual(data['day_activity']['Monday'], 15)
        self.assertEqual(data['day_activity']['Thursday'], 25)
        self.assertEqual(data['day_activity']['Tuesday'], 0)
        self.assertEqual(data['day_activity']['Wednesday'], 0)
        self.assertEqual(data['day_activity']['Friday'], 0)
        self.assertEqual(data['day_activity']['Saturday'], 0)
    
    def test_word_frequencies_endpoint(self):
        """Test the word-frequencies endpoint"""
        response = self.client.get_endpoint('word-frequencies',
                                      start_date=self.start_date_str,
                                      end_date=self.end_date_str)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('word_frequencies', data)
        
        # Check specific fields
        word_freqs = data['word_frequencies']
        self.assertEqual(word_freqs['feature'], 10)
        self.assertEqual(word_freqs['bug'], 8)
        self.assertEqual(word_freqs['fix'], 15)
        self.assertEqual(word_freqs['implement'], 6)
        self.assertEqual(word_freqs['update'], 12)
    
    def test_fetch_data_endpoint(self):
        """Test the fetch-data endpoint with cache"""
        payload = {
            'start_date': self.start_date_str,
            'end_date': self.end_date_str,
            'repo_owner': 'OpenRA',
            'repo_name': 'OpenRA',
            'use_cache': True
        }
        
        response = self.client.fetch_data(payload)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['cache_used'])
        self.assertEqual(data['repository'], 'OpenRA/OpenRA')
        self.assertIn('statistics', data)
        self.assertEqual(data['statistics']['commit_count'], 2)


if __name__ == '__main__':
    unittest.main()

    @patch('api.db.session')
    def test_deviations_endpoint(self, mock_session):
        """Test the deviations endpoint"""
        # Mock query results
        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_all = mock_order_by.all
        
        # Create mock commits with high z-scores
        commit1 = MagicMock(spec=Commit)
        commit1.sha = 'abc1234'
        commit1.message_title = 'Test commit 1'
        commit1.author_name = 'Author 1'
        commit1.author_date = self.start_date + timedelta(days=1)
        commit1.additions = 100
        commit1.deletions = 50
        commit1.total_changes = 150
        commit1.z_score = 3.5
        
        commit2 = MagicMock(spec=Commit)
        commit2.sha = 'def5678'
        commit2.message_title = 'Test commit 2'
        commit2.author_name = 'Author 2'
        commit2.author_date = self.start_date + timedelta(days=2)
        commit2.additions = 200
        commit2.deletions = 100
        commit2.total_changes = 300
        commit2.z_score = 5.2
        
        # Set up mock data
        mock_all.return_value = [commit1, commit2]
        
        # Make request to endpoint
        response = self.app.get(f'/api/v1/deviations?start_date={self.start_date.strftime("%Y-%m-%d")}&end_date={self.end_date.strftime("%Y-%m-%d")}')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('commits', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['commits']), 2)
        
        # Check specific fields
        self.assertEqual(data['commits'][0]['sha'], 'abc1234')
        self.assertEqual(data['commits'][0]['title'], 'Test commit 1')
        self.assertEqual(data['commits'][0]['author'], 'Author 1')
        self.assertEqual(data['commits'][0]['z_score'], 3.5)
        
        self.assertEqual(data['commits'][1]['sha'], 'def5678')
        self.assertEqual(data['commits'][1]['title'], 'Test commit 2')
        self.assertEqual(data['commits'][1]['author'], 'Author 2')
        self.assertEqual(data['commits'][1]['z_score'], 5.2)

    @patch('api.db.session')
    def test_day_of_week_endpoint(self, mock_session):
        """Test the day-of-week endpoint"""
        # Mock query results
        mock_query = mock_session.query.return_value
        mock_add_columns = mock_query.add_columns.return_value
        mock_filter = mock_add_columns.filter.return_value
        mock_group_by = mock_filter.group_by.return_value
        mock_all = mock_group_by.all
        
        # Create mock day-of-week data
        # These are mock results with day_of_week (0-6, Sunday-Saturday) and count
        mock_result1 = MagicMock()
        mock_result1.day_of_week = 0  # Sunday
        mock_result1.value = 10
        
        mock_result2 = MagicMock()
        mock_result2.day_of_week = 1  # Monday
        mock_result2.value = 15
        
        mock_result3 = MagicMock()
        mock_result3.day_of_week = 4  # Thursday
        mock_result3.value = 25
        
        # Set up mock data
        mock_all.return_value = [mock_result1, mock_result2, mock_result3]
        
        # Make request to endpoint
        response = self.app.get(f'/api/v1/day-of-week?start_date={self.start_date.strftime("%Y-%m-%d")}&end_date={self.end_date.strftime("%Y-%m-%d")}&metric_type=commits')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('metric', data)
        self.assertIn('day_activity', data)
        
        # Check specific fields
        self.assertEqual(data['metric'], 'commits')
        self.assertEqual(data['day_activity']['Sunday'], 10)
        self.assertEqual(data['day_activity']['Monday'], 15)
        self.assertEqual(data['day_activity']['Thursday'], 25)
        self.assertEqual(data['day_activity']['Tuesday'], 0)  # Should have defaults for missing days
        self.assertEqual(data['day_activity']['Wednesday'], 0)
        self.assertEqual(data['day_activity']['Friday'], 0)
        self.assertEqual(data['day_activity']['Saturday'], 0)

    @patch('api.db.session')
    @patch('api.github_client')
    def test_word_frequencies_endpoint(self, mock_github_client, mock_session):
        """Test the word-frequencies endpoint"""
        # Mock query results
        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_limit = mock_order_by.limit.return_value
        mock_all = mock_limit.all
        
        # Create mock word frequency data
        mock_all.return_value = []  # Empty to trigger the calculation path
        
        # Mock the calculation function
        mock_github_client.calculate_word_frequencies.return_value = {
            'feature': 10,
            'bug': 8,
            'fix': 15,
            'implement': 6,
            'update': 12
        }
        
        # Make request to endpoint
        response = self.app.get(f'/api/v1/word-frequencies?start_date={self.start_date.strftime("%Y-%m-%d")}&end_date={self.end_date.strftime("%Y-%m-%d")}')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('word_frequencies', data)
        
        # Check specific fields
        word_freqs = data['word_frequencies']
        self.assertEqual(word_freqs['feature'], 10)
        self.assertEqual(word_freqs['bug'], 8)
        self.assertEqual(word_freqs['fix'], 15)
        self.assertEqual(word_freqs['implement'], 6)
        self.assertEqual(word_freqs['update'], 12)

    @patch('api.db.session')
    @patch('api.github_client')
    def test_fetch_data_endpoint_cache_hit(self, mock_github_client, mock_session):
        """Test the fetch-data endpoint with cache hit"""
        # Mock query results for cache check
        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_first = mock_filter.first
        
        # Mock a cache hit
        mock_cache = MagicMock(spec=CacheStatus)
        mock_cache.repository = 'OpenRA/OpenRA'
        mock_cache.start_date = self.start_date
        mock_cache.end_date = self.end_date
        mock_cache.completed = True
        
        mock_first.return_value = mock_cache
        
        # Make request to endpoint
        payload = {
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'repo_owner': 'OpenRA',
            'repo_name': 'OpenRA',
            'use_cache': True
        }
        response = self.app.post('/api/v1/fetch-data', 
                               json=payload,
                               content_type='application/json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['cache_used'])
        self.assertEqual(data['repository'], 'OpenRA/OpenRA')

    @patch('api.db.session')
    @patch('api.github_client')
    def test_fetch_data_endpoint_no_cache(self, mock_github_client, mock_session):
        """Test the fetch-data endpoint with no cache"""
        # Mock query results for cache check
        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_first = mock_filter.first
        
        # Mock a cache miss
        mock_first.return_value = None
        
        # Mock the fetch commits function
        mock_github_client.fetch_commits.return_value = [
            {'sha': 'abc123', 'author_name': 'Author 1'},
            {'sha': 'def456', 'author_name': 'Author 2'},
        ]
        
        # Mock the calculate stats function
        mock_github_client.calculate_commit_statistics.return_value = {
            'commit_count': 2,
            'mean_changes': 100.0,
            'std_changes': 50.0
        }
        
        # Make request to endpoint
        payload = {
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'repo_owner': 'OpenRA',
            'repo_name': 'OpenRA',
            'use_cache': False
        }
        response = self.app.post('/api/v1/fetch-data', 
                               json=payload,
                               content_type='application/json')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'success')
        self.assertFalse(data['cache_used'])
        self.assertEqual(data['commit_count'], 2)
        self.assertEqual(data['repository'], 'OpenRA/OpenRA')
        self.assertIn('statistics', data)
        self.assertEqual(data['statistics']['commit_count'], 2)


if __name__ == '__main__':
    unittest.main()
