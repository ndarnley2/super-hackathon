#!/usr/bin/env python3
"""
Unit tests for the health endpoint
"""

import unittest
import requests
import requests_mock
from datetime import datetime

from backend.tests.test_utils import BASE_URL, SimpleApiClient, register_mock_endpoints


class HealthEndpointTest(unittest.TestCase):
    """Test case for the health endpoint"""
    
    def setUp(self):
        """Set up test client and mock API"""
        self.adapter = requests_mock.Adapter()
        self.session = requests.Session()
        self.session.mount('http://', self.adapter)
        
        # Register mock API endpoints
        register_mock_endpoints(self.adapter)
        
        # Create simple API client using our session
        self.client = SimpleApiClient('http://localhost:5000')
        self.client.session = self.session
    
    def test_health_check(self):
        """Test the health check endpoint"""
        response = self.client.get_endpoint('health')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'ok')


if __name__ == '__main__':
    unittest.main()
