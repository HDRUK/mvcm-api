import json
import unittest
import base64
from app import app
from flask import jsonify
from Credentials import APIusername, APIpassword  # Import the credentials

class TestApp(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()

        # Create base64 encoded string for HTTP Basic Authentication
        credentials = base64.b64encode(f"{APIusername}:{APIpassword}".encode()).decode('utf-8')
        self.headers = {
            'Authorization': f'Basic {credentials}'
        }
        self.payload = {
            "search_term": ["Asthma", "Heart"],
            "search_threshold": 80
        }

        self.invalid_payload = {
            "search_term": [],
            "search_threshold": 80
        }
    
    # Global Search Tests
    def test_Global_search_status(self):
        response = self.app.post('API/Global_search', headers=self.headers, json=self.payload)
        try:
            self.json_response = json.loads(response.data)
        except json.JSONDecodeError as e:
            self.fail(f"Failed to decode JSON: {e}")
        self.assertEqual(response.status_code, 200)

    def test_Global_search_bad_request(self):
        response = self.app.post('API/Global_search', headers=self.headers, json=self.invalid_payload)
        if response.status_code == 400:
            self.json_response = {'status_code': 400}
        self.assertEqual(response.status_code, 400)  # Expecting bad request

    def test_Global_search_auth(self):
        response = self.app.post('API/Global_search', json=self.invalid_payload)
        if response.status_code == 401:
            self.json_response = {'status_code': 401}
        self.assertEqual(response.status_code, 401)  # Expecting 401 bad request

    # OMOP Search Tests
    def test_OMOP_search_status(self):
        response = self.app.post('API/OMOP_search', json=self.payload)
        try:
            self.json_response = json.loads(response.data)
        except json.JSONDecodeError as e:
            self.fail(f"Failed to decode JSON: {e}")
        self.assertEqual(response.status_code, 200)

    def test_OMOP_search_bad_request(self):
        response = self.app.post('API/OMOP_search', headers=self.headers, json=self.invalid_payload)
        if response.status_code == 400:
            self.json_response = {'status_code': 400}
        self.assertEqual(response.status_code, 400)  # Expecting bad request

    def test_OMOP_search_auth(self):
        response = self.app.post('API/OMOP_search', json=self.invalid_payload)
        if response.status_code == 401:
            self.json_response = {'status_code': 401}
        self.assertEqual(response.status_code, 401)  # Expecting 401 bad request

    # OLS4 Search Tests
    def test_OLS4_search_status(self):
        response = self.app.post('API/OLS4_search', headers=self.headers, json=self.payload)
        try:
            self.json_response = json.loads(response.data)
        except json.JSONDecodeError as e:
            self.fail(f"Failed to decode JSON: {e}")
        self.assertEqual(response.status_code, 200)

    def test_OLS4_search_bad_request(self):
        response = self.app.post('API/OLS4_search', headers=self.headers, json=self.invalid_payload)
        if response.status_code == 400:
            self.json_response = {'status_code': 400}
        self.assertEqual(response.status_code, 400)  # Expecting 400 bad request

    def test_OLS4_search_auth(self):
        response = self.app.post('API/OLS4_search', json=self.invalid_payload)
        if response.status_code == 401:
            self.json_response = {'status_code': 401}
        self.assertEqual(response.status_code, 401)  # Expecting 401 bad request

    # ULMS Search Tests
    def test_UMLS_search_status(self):
        response = self.app.post('API/UMLS_search', headers=self.headers, json=self.payload)
        try:
            self.json_response = json.loads(response.data)
        except json.JSONDecodeError as e:
            self.fail(f"Failed to decode JSON: {e}")
        self.assertEqual(response.status_code, 200)

    def test_UMLS_search_bad_request(self):
        response = self.app.post('API/UMLS_search', headers=self.headers, json=self.invalid_payload)
        if response.status_code == 400:
            self.json_response = {'status_code': 400}
        self.assertEqual(response.status_code, 400)  # Expecting 400 bad request

    def test_UMLS_search_auth(self):
        response = self.app.post('API/UMLS_search', json=self.invalid_payload)
        if response.status_code == 401:
            self.json_response = {'status_code': 401}
        self.assertEqual(response.status_code, 401)  # Expecting 401 bad request

    # List OMOP vocabs Tests
    def test_List_OMOP_Vocabularies_status(self):
        response = self.app.get('API/List_OMOP_Vocabularies', headers=self.headers)
        try:
            self.json_response = json.loads(response.data)
        except json.JSONDecodeError as e:
            self.fail(f"Failed to decode JSON: {e}")
        self.assertEqual(response.status_code, 200)

    def test_List_OMOP_Vocabularies_auth(self):
        response = self.app.get('API/List_OMOP_Vocabularies')
        if response.status_code == 400:
            self.json_response = {'status_code': 400}
        self.assertEqual(response.status_code, 401)  # Expecting 401 bad request