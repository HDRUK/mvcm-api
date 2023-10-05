
# Importing Flask and other required modules
# Import Flask library along with request and jsonify for handling HTTP methods and JSON.

from flask import Flask, request, Response
from flask_restx import Api

# import custom classes for running the app
from utils.StandaloneApplication import StandaloneApplication
from Credentials import Swaggerusername, Swaggerpassword

# Initialize Flask application
# Initialize the Flask web application. The '__name__' argument helps Flask determine the root path.
app = Flask(__name__)

# Initialize API with Flask-RESTx and set metadata
# Initialize Flask-RESTx API. Set API metadata like version and title for the Swagger UI documentation.
api = Api(app, version='1.0', title='Medical Vocabulary Concept Mapping API (MVCM-API)', description='A Flask REST API application designed to facilitate the mapping of medical concepts to standardized terms using a MySQL database loaded with concepts from the OMOP Common Data Model and the OLS4 API.')
ns = api.namespace('API', description='OMOP and OLS4 search functions')

# Add swagger auth
@app.before_request
def require_auth():
    if request.path in ['/', '/.json']:
        auth = request.authorization
        if not auth or not (auth.username == Swaggerusername and auth.password == Swaggerpassword):
            return Response(status=401, headers={'WWW-Authenticate': 'Basic realm="Login Required"'})

       
# Import routes
from routes.CalculateBestMatch_ALL import CalculateBestMatch_ALL    
from routes.CalculateBestMatch_OMOP import CalculateBestMatch_OMOP
from routes.CalculateBestMatch_OLS4 import CalculateBestMatch_OLS4
from routes.CalculateBestMatch_UMLS import CalculateBestMatch_UMLS
from routes.List_OMOP_Vocabularies import List_OMOP_Vocabularies
from routes.Unit_Test import Test_the_App

# Add the route to the namespace
ns.add_resource(CalculateBestMatch_ALL, '/Global_search')
ns.add_resource(CalculateBestMatch_OMOP, '/OMOP_search')
ns.add_resource(CalculateBestMatch_OLS4, '/OLS4_search')
ns.add_resource(CalculateBestMatch_UMLS, '/UMLS_search')
ns.add_resource(List_OMOP_Vocabularies, '/List_OMOP_Vocabularies')


ns.add_resource(Test_the_App, '/Test')
          
# Main entry point of the application
if __name__ == '__main__':

        # Start the App only if tests pass
        options = {'bind': '0.0.0.0:80'}
        StandaloneApplication(app, options).run()



