#!/usr/bin/env python3
"""
Unit tests for the fetch-data endpoint
"""

import unittest
import requests
import requests_mock
from datetime import datetime

from backend.tests.test_utils import BASE_URL, SimpleApiClient, register_mock_endpoints


class FetchDataEndpointTest(unittest.TestCase):
    """Test case for the fetch-data endpoint"""
    
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
        register_mock_endpoints(self.adapter)
        
        # Create simple API client using our session
        self.client = SimpleApiClient('http://localhost:5000')
        self.client.session = self.session
    
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
        self.assertEqual(data['statistics']['mean_changes'], 100.0)
        self.assertEqual(data['statistics']['std_changes'], 50.0)


if __name__ == '__main__':
    unittest.main()
