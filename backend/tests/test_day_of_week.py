#!/usr/bin/env python3
"""
Unit tests for the day-of-week endpoint
"""

import unittest
import requests
import requests_mock
from datetime import datetime

from backend.tests.test_utils import BASE_URL, SimpleApiClient, register_mock_endpoints


class DayOfWeekEndpointTest(unittest.TestCase):
    """Test case for the day-of-week endpoint"""
    
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
    
    def test_day_of_week_endpoint(self):
        """Test the day-of-week endpoint"""
        response = self.client.get_endpoint('day-of-week',
                                     start_date=self.start_date_str,
                                     end_date=self.end_date_str)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('metric', data)
        self.assertEqual(data['metric'], 'commits')
        self.assertIn('day_activity', data)
        
        # Check specific day values
        day_activity = data['day_activity']
        self.assertEqual(day_activity['Sunday'], 10)
        self.assertEqual(day_activity['Monday'], 15)
        self.assertEqual(day_activity['Tuesday'], 0)
        self.assertEqual(day_activity['Wednesday'], 0)
        self.assertEqual(day_activity['Thursday'], 25)
        self.assertEqual(day_activity['Friday'], 0)
        self.assertEqual(day_activity['Saturday'], 0)


if __name__ == '__main__':
    unittest.main()
