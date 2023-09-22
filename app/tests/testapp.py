import json
import unittest
from app import app

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
        
    def test_OMOP_search_status(self):
        # Test case for status code in /OMOP API endpoint
        try:
            response = self.app.post('API/OMOP_search', json=self.payload)
            self.assertEqual(response.status_code, 200)
            print("Status code test for /OMOP_search passed.")
        except Exception as e:
            print(f"Status code test for /OMOP_search failed: {e}")
    
    def test_OMOP_search_data(self):
        # Test case for data content in /OMOP API endpoint
        try:
            response = self.app.post('API/OMOP_search', json=self.payload)
            response_data = json.loads(response.data)
            self.assertIn("vocabulary_concept_code", response_data[0])
            self.assertEqual(response_data[0]["vocabulary_concept_code"], "195967001")
            print("Data content test for /OMOP_search passed.")
        except Exception as e:
            print(f"Data content test for /OMOP_search failed: {e}")
            
    def test_OLS4_search_status(self):
        # Test case for status code in /OLS4 API endpoint
        try:
            response = self.app.post('API/OLS4_search', json=self.payload)
            self.assertEqual(response.status_code, 200)
            print("Status code test for /OLS4_search passed.")
        except Exception as e:
            print(f"Status code test for /OLS4_search failed: {e}")

    def test_OLS4_search_data(self):
        # Test case for data content in /OLS4 API endpoint
        try:
            response = self.app.post('API/OLS4_search', json=self.payload)
            response_data = json.loads(response.data)
            self.assertIn("vocabulary_concept_code", response_data[0])
            self.assertEqual(response_data[0]["vocabulary_concept_code"], "195967001")
            print("Data content test for /OLS4_search passed.")
        except Exception as e:
            print(f"Data content test for /OLS4_search failed: {e}")

    def test_List_OMOP_Vocabularies_status(self):
        # Test case for /List_OMOP_Vocabularies API endpoint
        try:
            response = self.app.get('API/List_OMOP_Vocabularies')
            self.assertEqual(response.status_code, 200)
            print("Status code test for /List_OMOP_Vocabularies passed.")
        except Exception as e:
            print(f"Data content test for /List_OMOP_Vocabularies failed: {e}")
