import unittest
from flask_restx import Resource
from tests.testapp import TestApp
from utils.custom_test_result import CustomTestRunner 
from utils.Basic_auth import auth

# API route for the unit tests

class Test_the_App(Resource):
    """
    Run Unit Tests for the Application
    ----------------------------------
    This endpoint runs unit tests defined in the `TestApp` class and returns the results.

    Returns:
    A JSON object containing:
    - status: Indicates the operation's status as 'success' or 'error'.
    - data: A summary of the test results if successful.

    Authentication:
    Requires Basic Authentication.

    Errors:
    Returns 500 Internal Server Error if an exception occurs.
    """
    @auth.login_required
    def get(self):
        try:
            suite = unittest.TestLoader().loadTestsFromTestCase(TestApp)
            runner = CustomTestRunner()
            test_results = runner.run(suite)
            return {"status": "success", "data": test_results}
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500
