#!/usr/bin/env python3
"""
Unit tests for the authors endpoint
"""

import unittest
import requests
import requests_mock
from datetime import datetime

from backend.tests.test_utils import BASE_URL, SimpleApiClient, register_mock_endpoints


class AuthorsEndpointTest(unittest.TestCase):
    """Test case for the authors endpoint"""
    
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


if __name__ == '__main__':
    unittest.main()
