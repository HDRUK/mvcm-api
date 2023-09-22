import unittest
from flask_restx import Resource
from tests.testapp import TestApp

# API route for the unit tests
class Test_the_App(Resource):
    def get(self):
        try:
            # Run the Unit tests
            suite = unittest.TestLoader().loadTestsFromTestCase(TestApp)
            runner = unittest.TextTestRunner()
            test_results = runner.run(suite)

            # Return the result as JSON
            return {
                "status": "success",
                "total_tests": test_results.testsRun,
                "failures": len(test_results.failures),
                "errors": len(test_results.errors),
                "successful": test_results.wasSuccessful()
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}, 500
