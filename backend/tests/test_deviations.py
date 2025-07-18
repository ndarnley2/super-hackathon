#!/usr/bin/env python3
"""
Unit tests for the deviations endpoint
"""

import unittest
import requests
import requests_mock
from datetime import datetime

from backend.tests.test_utils import BASE_URL, SimpleApiClient, register_mock_endpoints


class DeviationsEndpointTest(unittest.TestCase):
    """Test case for the deviations endpoint"""
    
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


if __name__ == '__main__':
    unittest.main()
