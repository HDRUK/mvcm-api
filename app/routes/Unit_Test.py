import unittest
from flask_restx import Resource
from tests.testapp import TestApp
from utils.custom_test_result import CustomTestRunner 
from utils.Basic_auth import auth

# API route for the unit tests

class Test_the_App(Resource):
    @auth.login_required
    def get(self):
        try:
            suite = unittest.TestLoader().loadTestsFromTestCase(TestApp)
            runner = CustomTestRunner()
            test_results = runner.run(suite)
            return {"status": "success", "data": test_results}
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500
