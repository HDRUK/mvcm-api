#from flask import current_app
import pandas as pd
from rapidfuzz import fuzz
import re
from .initialize_mysql_connection import initialize_mysql_connection

# Connect to database
engine = initialize_mysql_connection()

#Function to calculate best OMOP matches based on search terms
# This function queries the MySQL database and performs string matching.
def calculate_best_OMOP_matches(search_terms, vocabulary_id=None,search_threshold=None):
    try:
        if not search_terms:
            raise ValueError("No valid search_term values provided")

        # Initialize an empty dictionary to store the search results. This dictionary will be converted to a DataFrame at the end.
        result_dict = {
            'search_term': [], 
            'closely_mapped_term': [], 
            'relationship_type': [], 
            'concept_id': [], 
            'vocabulary_id': [],
            'vocabulary_concept_code':[],
            'similarity_score': []  
        }

        # Iterate through each search term provided in the list to perform individual concept matching.
        for search_term in search_terms:
            # Fetch potentially matching standard concepts from the database

            if vocabulary_id is None:
                query = """
                SELECT 
                    concept_name, concept_id, vocabulary_id, concept_code
                FROM 
                    CONCEPT 
                WHERE 
                    standard_concept = 'S' AND
                    MATCH(concept_name) AGAINST (%s IN NATURAL LANGUAGE MODE)
                """
                params = (search_term,)
            else:
                query = """
                SELECT 
                    concept_name, concept_id, vocabulary_id, concept_code
                FROM 
                    CONCEPT 
                WHERE 
                    vocabulary_id = %s AND
                    standard_concept = 'S' AND
                    MATCH(concept_name) AGAINST (%s IN NATURAL LANGUAGE MODE)
                """
                params = (vocabulary_id, search_term)
            
            

            # Query the database to fetch potentially matching standard concepts. Use MySQL full-text search for initial filtering.
            standard_concepts = pd.read_sql(query, con=engine, params=params)
            


            # If no matches were found using full-text search, skip to the next search term
            if standard_concepts.empty:
                continue

            # Iterate through each row of the fetched standard concepts to perform additional filtering and similarity scoring.
            for idx, row in standard_concepts.iterrows():

                # Remove the bracketed part from the concept_name
                cleaned_concept_name = re.sub(r'\(.*?\)', '', row['concept_name']).strip()

                score = fuzz.ratio(search_term.lower(), cleaned_concept_name.lower())

                result_dict['search_term'].append(search_term)
                result_dict['closely_mapped_term'].append(row['concept_name'])
                result_dict['relationship_type'].append('OMOP_hit')
                result_dict['concept_id'].append(row['concept_id'])
                result_dict['vocabulary_id'].append(row['vocabulary_id'])
                result_dict['vocabulary_concept_code'].append(row['concept_code'])
                result_dict['similarity_score'].append(score)
        
        # Create a DataFrame from the result dict
        results_df = pd.DataFrame(result_dict).drop_duplicates().sort_values(by='similarity_score', ascending=False)

        if search_threshold is not None:
            results_df = results_df[results_df['similarity_score'] > search_threshold]

        return results_df
    
    # Fail gracefully and log
    except Exception as e:
        ValueError(f"Error in calculate_best_OMOP_matches: {e}")
        return pd.DataFrame()
    
