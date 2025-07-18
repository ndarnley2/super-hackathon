#!/usr/bin/env python3
"""
Unit tests for GitHub Analytics API endpoints
"""

import unittest
import sys
import os
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add parent directory to path to import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import app
from models import Commit, CacheStatus, CommitWordFrequency


class TestAPIEndpoints(unittest.TestCase):
    """Test cases for API endpoints"""

    def setUp(self):
        """Set up test client and mocked database session"""
        self.app = app.test_client()
        self.app.testing = True
        
        # Set up datetime objects for testing
        self.start_date = datetime.utcnow() - timedelta(days=30)
        self.end_date = datetime.utcnow()

    @patch('api.db.session')
    def test_authors_endpoint(self, mock_session):
        """Test the authors endpoint"""
        # Mock query results
        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_distinct = mock_filter.distinct.return_value
        mock_all = mock_distinct.all
        
        # Set up mock data
        mock_all.return_value = [('Author 1',), ('Author 2',), ('Author 3',)]
        
        # Make request to endpoint
        response = self.app.get(f'/api/v1/authors?start_date={self.start_date.strftime("%Y-%m-%d")}&end_date={self.end_date.strftime("%Y-%m-%d")}')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('authors', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 3)
        self.assertEqual(len(data['authors']), 3)
        self.assertIn('Author 1', data['authors'])
        self.assertIn('Author 2', data['authors'])
        self.assertIn('Author 3', data['authors'])

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
