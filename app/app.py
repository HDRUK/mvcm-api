
# Importing Flask and other required modules
# Import Flask library along with request and jsonify for handling HTTP methods and JSON.
from flask import Flask
from flask_restx import Api
import unittest

# import custom classes, functions and routes
from utils.StandaloneApplication import StandaloneApplication

# Initialize Flask application
# Initialize the Flask web application. The '__name__' argument helps Flask determine the root path.
app = Flask(__name__)

# Initialize API with Flask-RESTx and set metadata
# Initialize Flask-RESTx API. Set API metadata like version and title for the Swagger UI documentation.
api = Api(app, version='1.0', title='Medical Vocabulary Concept Mapping API (MVCM-API)', description='A Flask REST API application designed to facilitate the mapping of medical concepts to standardized terms using a MySQL database loaded with concepts from the OMOP Common Data Model and the OLS4 API.')
ns = api.namespace('API', description='OMOP and OLS4 search functions')


# Import routes
from routes.CalculateBestMatch_OMOP import CalculateBestMatch_OMOP
from routes.CalculateBestMatch_OLS4 import CalculateBestMatch_OLS4

# Add the route to the namespace
ns.add_resource(CalculateBestMatch_OMOP, '/OMOP')
ns.add_resource(CalculateBestMatch_OLS4, '/OLS4')
           
# Main entry point of the application
if __name__ == '__main__':

        # Start the App only if tests pass
        options = {'bind': '0.0.0.0:80'}
        StandaloneApplication(app, options).run()
        
# Run Unit Tests
print("Running Unit Testing")
from tests.testapp import TestApp
suite = unittest.TestLoader().loadTestsFromTestCase(TestApp)
runner = unittest.TextTestRunner()
test_results = runner.run(suite)

# Report status
print(f"Failures: {len(test_results.failures)}")
print(f"Errors: {len(test_results.errors)}")
print(f"Skipped: {len(test_results.skipped)}")

