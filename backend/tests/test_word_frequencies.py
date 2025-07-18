#!/usr/bin/env python3
"""
Unit tests for the word-frequencies endpoint
"""

import unittest
import requests
import requests_mock
from datetime import datetime

from backend.tests.test_utils import BASE_URL, SimpleApiClient, register_mock_endpoints


class WordFrequenciesEndpointTest(unittest.TestCase):
    """Test case for the word-frequencies endpoint"""
    
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
    
    def test_word_frequencies_endpoint(self):
        """Test the word-frequencies endpoint"""
        response = self.client.get_endpoint('word-frequencies',
                                        start_date=self.start_date_str,
                                        end_date=self.end_date_str)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('word_frequencies', data)
        
        # Check specific word frequencies
        word_freqs = data['word_frequencies']
        self.assertEqual(word_freqs['feature'], 10)
        self.assertEqual(word_freqs['bug'], 8)
        self.assertEqual(word_freqs['fix'], 15)
        self.assertEqual(word_freqs['implement'], 6)
        self.assertEqual(word_freqs['update'], 12)


if __name__ == '__main__':
    unittest.main()
