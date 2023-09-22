import json
import unittest
from app import ns,app

class TestApp(unittest.TestCase):
    # Unit test class for API testing; Inherits from unittest.TestCase
    
    def setUp(self):
        # Initialize test client before each test case
        self.app = app.test_client()
        self.payload = {
        "search_term": ["Asthma", "Heart"],
        "vocabulary_id": "snomed",
        "search_threshold": 80
    }
        
    def test_OMOP_status(self):
        # Test case for status code in /OMOP API endpoint
        try:
            response = self.app.post('API/OMOP', json=self.payload)
            self.assertEqual(response.status_code, 200)
            print("Status code test for /OMOP passed.")
        except Exception as e:
            print(f"Status code test for /OMOP failed: {e}")
    
    def test_OMOP_data(self):
        # Test case for data content in /OMOP API endpoint
        try:
            response = self.app.post('API/OMOP', json=self.payload)
            response_data = json.loads(response.data)
            self.assertIn("vocabulary_concept_code", response_data[0])
            self.assertEqual(response_data[0]["vocabulary_concept_code"], "195967001")
            print("Data content test for /OMOP passed.")
        except Exception as e:
            print(f"Data content test for /OMOP failed: {e}")
            
    def test_OLS4_status(self):
        # Test case for status code in /OLS4 API endpoint
        try:
            response = self.app.post('API/OLS4', json=self.payload)
            self.assertEqual(response.status_code, 200)
            print("Status code test for /OLS4 passed.")
        except Exception as e:
            print(f"Status code test for /OLS4 failed: {e}")

    def test_OLS4_data(self):
        # Test case for data content in /OLS4 API endpoint
        try:
            response = self.app.post('API/OLS4', json=self.payload)
            response_data = json.loads(response.data)
            self.assertIn("vocabulary_concept_code", response_data[0])
            self.assertEqual(response_data[0]["vocabulary_concept_code"], "195967001")
            print("Data content test for /OLS4 passed.")
        except Exception as e:
            print(f"Data content test for /OLS4 failed: {e}")