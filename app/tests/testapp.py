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
            "search_threshold": 80
        }

    def test_Global_search_status(self):
        response = self.app.post('API/Global_search', json=self.payload)
        self.json_response = json.loads(response.data)  # Store JSON response
        self.assertEqual(response.status_code, 200)
        
    def test_OMOP_search_status(self):
        response = self.app.post('API/OMOP_search', json=self.payload)
        self.json_response = json.loads(response.data)  # Store JSON response
        self.assertEqual(response.status_code, 200)
    
    def test_OMOP_search_data(self):
        response = self.app.post('API/OMOP_search', json=self.payload)
        self.json_response = json.loads(response.data)  # Store JSON response
        self.assertIn("vocabulary_concept_code", self.json_response[0])
        self.assertEqual(self.json_response[0]["vocabulary_concept_code"], "195967001")
    
    def test_OLS4_search_status(self):
        response = self.app.post('API/OLS4_search', json=self.payload)
        self.json_response = json.loads(response.data)  # Store JSON response
        self.assertEqual(response.status_code, 200)
    
    def test_OLS4_search_data(self):
        response = self.app.post('API/OLS4_search', json=self.payload)
        self.json_response = json.loads(response.data)  # Store JSON response
        self.assertIn("vocabulary_concept_code", self.json_response[0])
        self.assertEqual(self.json_response[0]["vocabulary_concept_code"], "195967001")

    def test_UMLS_search_status(self):
        response = self.app.post('API/UMLS_search', json=self.payload)
        self.json_response = json.loads(response.data)  # Store JSON response
        self.assertEqual(response.status_code, 200)

    def test_UMLS_search_data(self):
        response = self.app.post('API/OLS4_search', json=self.payload)
        self.json_response = json.loads(response.data)  # Store JSON response
        self.assertIn("vocabulary_concept_code", self.json_response[0])
        self.assertEqual(self.json_response[0]["vocabulary_concept_code"], "C0004096")
    
    def test_List_OMOP_Vocabularies_status(self):
        response = self.app.get('API/List_OMOP_Vocabularies')
        self.json_response = json.loads(response.data)  # Store JSON response
        self.assertEqual(response.status_code, 200)