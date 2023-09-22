from app import api, ns
import pandas as pd
from flask_restx import Resource, fields  
from utils.initialize_mysql_connection import initialize_mysql_connection
from sqlalchemy import text

search_term_model = api.model('SearchTerm', {
    'search_term': fields.List(fields.String, required=True, description='The list of search terms to find the best match for', default=['Asthma', 'Heart']),
    'vocabulary_id': fields.String(required=False, description='The vocabulary ID to filter the results by', default='snomed'),
    'search_threshold': fields.Float(required=False, description='The filter threshold', default=80, min=0, max=100),
})

# Connect to database
engine = initialize_mysql_connection()

# API route for the List_OMOP_Vocabularies endpoint
@ns.route('/List_OMOP_Vocabularies')  
class List_OMOP_Vocabularies(Resource):
    def get(self):
        try:
            query = """
            SELECT 
                vocabulary_id, COUNT(*) as frequency
            FROM 
                CONCEPT
            GROUP BY 
                vocabulary_id
            """
            # Use pandas to execute SQL query and fetch results
            vocabularies_df = pd.read_sql(text(query), engine)

            # Convert DataFrame to a list of dictionaries for JSON response
            vocabularies = vocabularies_df.to_dict(orient='records')
            
            return {"status": "success", "data": vocabularies}

        except Exception as e:
            return {"status": "error", "message": str(e)}, 500