from collections import OrderedDict
from app import api, ns
from flask import  request, jsonify
from flask_restx import Resource, fields
from utils.calculate_best_UMLS_matches  import calculate_best_UMLS_matches
from utils.Basic_auth import auth
from utils.Hash_args import hash_args

ULMS_search_term_model = api.model('UMLS_search', {
    'search_term': fields.List(fields.String, required=True, description='The list of search terms to find the best match for', default=['Asthma', 'Heart']),
    'vocabulary_id': fields.String(required=False, description='The vocabulary ID to filter the results by', default='MTH'),
    'search_threshold': fields.Float(required=False, description='The filter threshold', default=80, min=0, max=100),
})

# Dictionary to hold Global_cached DataFrames with a limit of 1000 queries
UMLS_cache = OrderedDict()

# API route for the UMLS_search endpoint
@ns.route('/UMLS_search')  
class CalculateBestMatch_UMLS(Resource):
    """
    Calculate Best Match using UMLS
    -------------------------------
    This endpoint facilitates the mapping of medical concepts to standardized terms using the UMLS framework.
    
    Parameters:
    - search_term: The list of search terms to find the best match for.
    - vocabulary_id: Optional. The vocabulary ID to filter the results by. Default is 'MTH'.
    - search_threshold: Optional. The filter threshold for similarity matching. Default is 80.
    
    Returns:
    A JSON array containing the best matches sorted by similarity score.
    """
    @auth.login_required
    @api.expect(ULMS_search_term_model, validate=True)  # Expect data model matching 'ULMS_search_term_model'; enable validation
    @api.response(200, 'Success')  # Successful operation returns 200
    @api.response(400, 'Validation Error')  # Validation issues return 400
    @api.response(500, 'Internal Server Error')  # Server errors return 500
    
    def post(self):
        # Handle POST requests for UMLS concept matching
        try:
            request_data = request.get_json()  # Parse incoming JSON data
            search_terms = request_data.get('search_term')  # Extract 'search_term' parameter
            vocabulary_id = request_data.get('vocabulary_id')  # Extract 'vocabulary_id' parameter
            search_threshold = request_data.get('search_threshold')  # Extract 'search_threshold' parameter
            
            if not search_terms:  # Validate 'search_term' parameter
                return {'error': "search_term parameter is required"}, 400

            # Check ULMS_cache
            ULMS_cache_key = hash_args(search_terms, vocabulary_id, search_threshold)
            if ULMS_cache_key in UMLS_cache:
                return jsonify(UMLS_cache[ULMS_cache_key].to_dict(orient='records'))
            # Call function to get best UMLS matches and convert result to dictionary
            result_df = calculate_best_UMLS_matches(search_terms, vocabulary_id, search_threshold)

            # Cache the result and enforce cache limit of 1000
            if len(UMLS_cache) >= 1000:
                UMLS_cache.popitem(last=False)  # Remove the oldest item
            UMLS_cache[ULMS_cache_key] = result_df


            return jsonify(result_df.to_dict(orient='records'))  # Return result as JSON
        
        except Exception as e:  # Handle exceptions
            return {'error': "An error occurred while processing the request"}, 500  # Return server error
 