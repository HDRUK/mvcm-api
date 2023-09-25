from app import api, ns
from flask import  request, jsonify
from flask_restx import Resource, fields
from utils.calculate_best_OLS4_matches  import calculate_best_OLS4_matches 
from utils.Basic_auth import auth

search_term_model = api.model('SearchTerm', {
    'search_term': fields.List(fields.String, required=True, description='The list of search terms to find the best match for', default=['Asthma', 'Heart']),
    'vocabulary_id': fields.String(required=False, description='The vocabulary ID to filter the results by', default='snomed'),
    'search_threshold': fields.Float(required=False, description='The filter threshold', default=80, min=0, max=100),
})

# API route for the OLS4_search endpoint
@ns.route('/OLS4_search')  
class CalculateBestMatch_OLS4(Resource):
    @auth.login_required
    @api.expect(search_term_model, validate=True)  # Expect data model matching 'search_term_model'; enable validation
    @api.response(200, 'Success')  # Successful operation returns 200
    @api.response(400, 'Validation Error')  # Validation issues return 400
    @api.response(500, 'Internal Server Error')  # Server errors return 500
    
    def post(self):
        # Handle POST requests for OLS4 concept matching
        try:
            request_data = request.get_json()  # Parse incoming JSON data
            search_terms = request_data.get('search_term')  # Extract 'search_term' parameter
            vocabulary_id = request_data.get('vocabulary_id')  # Extract 'vocabulary_id' parameter
            search_threshold = request_data.get('search_threshold')  # Extract 'search_threshold' parameter
            
            if not search_terms:  # Validate 'search_term' parameter
                return {'error': "search_term parameter is required"}, 400
            
            # Call function to get best OLS4 matches and convert result to dictionary
            result_df = calculate_best_OLS4_matches(search_terms, vocabulary_id, search_threshold)
            return jsonify(result_df.to_dict(orient='records'))  # Return result as JSON
        
        except Exception as e:  # Handle exceptions
            return {'error': "An error occurred while processing the request"}, 500  # Return server error
 