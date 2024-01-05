#from flask import current_app
import pandas as pd
from rapidfuzz import fuzz
import re
from .initialize_mysql_connection import initialize_mysql_connection
#from os import environ

# Connect to database
engine = initialize_mysql_connection()

#Function to calculate best OMOP matches based on search terms
# This function queries the MySQL database and performs string matching.
def calculate_best_OMOP_matches(search_terms, vocabulary_id=None,search_threshold=None):
    try:
        if not search_terms:
            raise ValueError("No valid search_term values provided")

        # Initialize separate dictionaries for each type of result
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

                # Query to fetch ancestors for the concept
                ancestor_query = """
                SELECT 
                    ancestor_concept_id
                FROM 
                    CONCEPT_ANCESTOR
                WHERE 
                    descendant_concept_id = %s
                """
                ancestor_params = (row['concept_id'],)
                ancestors = pd.read_sql(ancestor_query, con=engine, params=ancestor_params)

                # Iterate through each ancestor and append to result_dict
                for anc_idx, anc_row in ancestors.iterrows():
                    # Fetch details of the ancestor concept
                    ancestor_details_query = """
                    SELECT 
                        concept_name, vocabulary_id, concept_code
                    FROM 
                        CONCEPT
                    WHERE 
                        concept_id = %s
                    """
                    ancestor_details = pd.read_sql(ancestor_details_query, con=engine, params=(anc_row['ancestor_concept_id'],))

                    # For each ancestor concept, add a new entry to result_dict
                    for anc_detail_idx, anc_detail_row in ancestor_details.iterrows():
                        result_dict['search_term'].append(search_term)
                        result_dict['closely_mapped_term'].append(anc_detail_row['concept_name'])
                        result_dict['relationship_type'].append('OMOP_Ancestor')
                        result_dict['concept_id'].append(anc_row['ancestor_concept_id'])
                        result_dict['vocabulary_id'].append(anc_detail_row['vocabulary_id'])
                        result_dict['vocabulary_concept_code'].append(anc_detail_row['concept_code'])
                        result_dict['similarity_score'].append(score) # No similarity score for ancestor concepts

                # Query to fetch related concepts for the matched concept
                related_concepts_query = """
                SELECT 
                    concept_id_2, relationship_id
                FROM 
                    CONCEPT_RELATIONSHIP
                WHERE 
                    concept_id_1 = %s AND
                    valid_end_date > NOW()
                """
                related_concepts_params = (row['concept_id'],)
                related_concepts = pd.read_sql(related_concepts_query, con=engine, params=related_concepts_params)

                # Iterate through each related concept and append to result_dict
                for rel_idx, rel_row in related_concepts.iterrows():
                    # Fetch details of the related concept
                    related_concept_details_query = """
                    SELECT 
                        concept_name, vocabulary_id, concept_code
                    FROM 
                        CONCEPT
                    WHERE 
                        concept_id = %s
                    """
                    related_concept_details = pd.read_sql(related_concept_details_query, con=engine, params=(rel_row['concept_id_2'],))

                    # For each related concept, add a new entry to result_dict
                    for rel_detail_idx, rel_detail_row in related_concept_details.iterrows():
                        result_dict['search_term'].append(search_term)
                        result_dict['closely_mapped_term'].append(rel_detail_row['concept_name'])
                        result_dict['relationship_type'].append('OMOP_Related')
                        result_dict['concept_id'].append(rel_row['concept_id_2'])
                        result_dict['vocabulary_id'].append(rel_detail_row['vocabulary_id'])
                        result_dict['vocabulary_concept_code'].append(rel_detail_row['concept_code'])
                        result_dict['similarity_score'].append(score) # No similarity score for related concepts

        # Create a DataFrame from the result dict
        # Combine all dictionaries into a single DataFrame
        combined_results = pd.DataFrame(result_dict)

        results_df = combined_results.drop_duplicates().sort_values(by='similarity_score', ascending=False)

        if search_threshold is None:
            return results_df
        else:
            return results_df[results_df['similarity_score'] > search_threshold]
        
    # Fail gracefully and log
    except Exception as e:
        ValueError(f"Error in calculate_best_OMOP_matches: {e}")
        return pd.DataFrame()