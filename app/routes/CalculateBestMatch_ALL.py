from collections import OrderedDict
from app import api, ns
from flask import request, jsonify
import pandas as pd
from flask_restx import Resource, fields
from utils.calculate_best_UMLS_matches import calculate_best_UMLS_matches
from utils.calculate_best_OMOP_matches import calculate_best_OMOP_matches
from utils.calculate_best_OLS4_matches import calculate_best_OLS4_matches
from utils.Basic_auth import auth
from utils.Hash_args import hash_args

GLOBAL_search_term_model = api.model('Global_search', {
    'search_term': fields.List(fields.String, required=True, description='The list of search terms to find the best match for', default=['Asthma', 'Heart']),
    'vocabulary_id': fields.String(required=False, description='The vocabulary ID to filter the results by', default=''),
    'search_threshold': fields.Float(required=False, description='The filter threshold', default=80, min=0, max=100),
    'search_tools': fields.List(fields.String, required=False, description='The list of search tools to use for matching', default=['OMOP', 'OLS4',"UMLS"]),

})

# Dictionary to hold Global_cached DataFrames with a limit of 1000 queries
Global_cache = OrderedDict()

# API route for the OLS4_search endpoint
@ns.route('/Global_search')  
class CalculateBestMatch_ALL(Resource):
    """
    Calculate Best Match for ALL
    ----------------------------
    This endpoint facilitates the mapping of medical concepts to standardized terms.
    It combines the power of multiple search tools (OMOP, OLS4, UMLS) to provide a comprehensive set of matching concepts.
    
    Parameters:
    - search_term: The list of search terms to find the best match for.
    - vocabulary_id: The vocabulary ID to filter the results by. If not provided, no filtering is done.
    - search_threshold: The filter threshold for similarity matching.
    - search_tools: The list of search tools to use for finding the best match. Options are "OMOP", "OLS4", "UMLS".

    Returns:
    A JSON array containing the best matches sorted by similarity score.
    """
    @auth.login_required
    @api.expect(GLOBAL_search_term_model, validate=True)  # Expect data model matching 'GLOBAL_search_term_model'; enable validation
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
            search_tools = request_data.get('search_tools')  # Extract 'search_threshold' parameter
            
            if vocabulary_id == "":
                vocabulary_id = None

            if search_tools == "":
                search_tools = ["OMOP","OLS4","UMLS"]

            if not search_tools:
                search_tools = ["OMOP","OLS4","UMLS"]
                
            if not search_terms:  # Validate 'search_term' parameter
                return {'error': "search_term parameter is required"}, 400

            # Check Global_cache
            Global_cache_key = hash_args(search_terms, vocabulary_id, search_threshold, search_tools)
            if Global_cache_key in Global_cache:
                return jsonify(Global_cache[Global_cache_key].to_dict(orient='records'))

            dfs = []  # List to hold individual DataFrames

            if 'OMOP' in search_tools:
                result_df1 = calculate_best_OMOP_matches(search_terms, vocabulary_id, search_threshold)
                dfs.append(result_df1)

            if 'OLS4' in search_tools:
                result_df2 = calculate_best_OLS4_matches(search_terms, vocabulary_id, search_threshold)
                dfs.append(result_df2)

            if 'UMLS' in search_tools:
                result_df3 = calculate_best_UMLS_matches(search_terms, vocabulary_id, search_threshold)
                dfs.append(result_df3)

            # Merge the DataFrames
            merged_df = pd.concat(dfs, ignore_index=True).sort_values(by='similarity_score', ascending=False)

             # Cache the result and enforce cache limit of 1000
            if len(Global_cache) >= 1000:
                Global_cache.popitem(last=False)  # Remove the oldest item
            Global_cache[Global_cache_key] = merged_df

            return jsonify(merged_df.to_dict(orient='records'))  # Return result as JSON
        
        except Exception as e:  # Handle exceptions
            return {'error': "An error occurred while processing the request"}, 500  # Return server error
 