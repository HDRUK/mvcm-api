import pandas as pd
import re
from rapidfuzz import fuzz
from sqlalchemy import create_engine
from os import environ

class OMOPMatcher:
    def __init__(self):
        # Connect to database
        try:
            print("Initialize the MySQL connection based on the configuration.")
            MYSQL_HOST = environ.get('DB_HOST', '127.0.0.1')
            MYSQL_USER = environ.get('DB_USER', 'root')
            MYSQL_PASSWORD = environ.get('DB_PASSWORD', 'psw4MYSQL')
            MYSQL_DB = environ.get('DB_NAME', 'mydb')
            engine = create_engine(f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}')
            
        except Exception as e:
            ValueError(f"Failed to connect to MySQL: {e}")

        self.engine = engine

    def calculate_best_matches(self, search_terms, vocabulary_id=None, concept_ancestor="y", concept_relationship="y", search_threshold=None, max_separation_descendant=1, max_separation_ancestor=1):
        try:
            if not search_terms:
                raise ValueError("No valid search_term values provided")

            overall_results = []

            # Assuming vocabulary_id is meant to be a not empty string
            if not isinstance(vocabulary_id, str) or not vocabulary_id.strip():
                vocabulary_id = None

            # search_threshold should be a float or integer, so check if it's a number
            if not isinstance(search_threshold, (float, int)):
                search_threshold = None
         
            for search_term in search_terms:
                OMOP_concepts = self.fetch_OMOP_concepts(search_term, vocabulary_id, concept_ancestor, concept_relationship, search_threshold,max_separation_descendant,max_separation_ancestor)

                overall_results.append({
                    'search_term': search_term,
                    'CONCEPT': OMOP_concepts
                })

            return overall_results
        
        except Exception as e:
            raise ValueError(f"Error in calculate_best_OMOP_matches: {e}")

    
    def fetch_OMOP_concepts(self, search_term, vocabulary_id, concept_ancestor, concept_relationship, search_threshold,max_separation_descendant,max_separation_ancestor):
        query = """
            SELECT 
                C.concept_id,
                C.concept_name, 
                CS.concept_synonym_name,
                C.vocabulary_id, 
                C.concept_code
            FROM 
                CONCEPT AS C
            LEFT JOIN CONCEPT_SYNONYM AS CS ON C.concept_id = CS.concept_id
            WHERE 
                C.standard_concept = 'S' AND
                
                (%s IS NULL OR C.vocabulary_id = %s) AND
                (MATCH(C.concept_name) AGAINST (%s IN NATURAL LANGUAGE MODE) OR
                MATCH(CS.concept_synonym_name) AGAINST (%s IN NATURAL LANGUAGE MODE))
            """
        
        # use CS.language_concept_id = '4180186' as additional filter if needed

        # Calculate similarity scores and add a new column
            

        params = (vocabulary_id, 
                  vocabulary_id, 
                  search_term, 
                  search_term,)

        results = pd.read_sql(query, con=self.engine, params=params).drop_duplicates()
        
        # Define a function to calculate similarity score using the provided logic
        def calculate_similarity(row):
            cleaned_concept_name = re.sub(r'\(.*?\)', '', row).strip()
            score = fuzz.ratio(search_term.lower(), cleaned_concept_name.lower())
            return score

        # Apply the score function to 'concept_name' and 'concept_synonym_name' columns
        results['concept_name_similarity_score'] = results['concept_name'].apply(calculate_similarity)
        results['concept_synonym_name_similarity_score'] = results['concept_synonym_name'].apply(calculate_similarity)
        
        # Filter the DataFrame by score
        filtered_results = results[(results['concept_name_similarity_score'] > search_threshold) | (results['concept_synonym_name_similarity_score'] > search_threshold)]

        # Sort the filtered results by the highest score (descending order)
        filtered_results = filtered_results.sort_values(by=['concept_name_similarity_score', 'concept_synonym_name_similarity_score'], ascending=False)

        # Group by 'concept_id' and aggregate the relevant columns
        grouped_results = filtered_results.groupby('concept_id').agg({
            'concept_name': 'first',
            'vocabulary_id': 'first',
            'concept_code': 'first',
            'concept_name_similarity_score': 'first',
            'concept_synonym_name': list,
            'concept_synonym_name_similarity_score': list,
        }).reset_index()

        # Define the final output format
        return [{
            'concept_name': row['concept_name'],
            'concept_id': row['concept_id'],
            'vocabulary_id': row['vocabulary_id'],
            'concept_code': row['concept_code'],
            'concept_name_similarity_score': row['concept_name_similarity_score'],
            'CONCEPT_SYNONYM': [{
                'concept_synonym_name': syn_name,
                'concept_synonym_name_similarity_score': syn_score
            } for syn_name, syn_score in zip(row['concept_synonym_name'], row['concept_synonym_name_similarity_score'])],
            'CONCEPT_ANCESTOR': self.fetch_concept_ancestor(row['concept_id'], max_separation_descendant, max_separation_ancestor) if concept_ancestor == "y" else [],
            'CONCEPT_RELATIONSHIP': self.fetch_concept_relationship(row['concept_id']) if concept_relationship == "y" else []
        } for _, row in grouped_results.iterrows()]
    
    def fetch_concept_ancestor(self, concept_id,max_separation_descendant,max_separation_ancestor):
        query = """
            (
                SELECT 
                    'Ancestor' as relationship_type,
                    ca.ancestor_concept_id AS concept_id,
                    ca.ancestor_concept_id,
                    ca.descendant_concept_id,
                    c.concept_name, 
                    c.vocabulary_id, 
                    c.concept_code,
                    ca.min_levels_of_separation,
                    ca.max_levels_of_separation
                FROM 
                    CONCEPT_ANCESTOR ca
                JOIN 
                    CONCEPT c ON ca.ancestor_concept_id = c.concept_id
                WHERE 
                    ca.descendant_concept_id = %s AND
                    ca.min_levels_of_separation >= %s AND
                    ca.max_levels_of_separation <= %s
            )
            UNION
            (
                SELECT 
                    'Descendant' as relationship_type,
                    ca.descendant_concept_id AS concept_id,
                    ca.ancestor_concept_id,
                    ca.descendant_concept_id,
                    c.concept_name, 
                    c.vocabulary_id, 
                    c.concept_code,
                    ca.min_levels_of_separation,
                    ca.max_levels_of_separation
                FROM 
                    CONCEPT_ANCESTOR ca
                JOIN 
                    CONCEPT c ON ca.descendant_concept_id = c.concept_id
                WHERE 
                    ca.ancestor_concept_id = %s AND
                    ca.min_levels_of_separation >= %s AND
                    ca.max_levels_of_separation <= %s
            )   
        """
        min_separation_ancestor =1 
        min_separation_descendant=1

        params = (concept_id, 
                  min_separation_ancestor, 
                  max_separation_ancestor, 
                  concept_id, 
                  min_separation_descendant, 
                  max_separation_descendant,)
        
        results = pd.read_sql(query, con=self.engine, params=params).drop_duplicates().query("concept_id != @concept_id")

        return [{
            'concept_name': row['concept_name'],
            'concept_id': row['concept_id'],
            'vocabulary_id': row['vocabulary_id'],
            'concept_code': row['concept_code'],
            'relationship': {
                'relationship_type': row['relationship_type'],
                'ancestor_concept_id': row['ancestor_concept_id'],
                'descendant_concept_id': row['descendant_concept_id'],
                'min_levels_of_separation': row['min_levels_of_separation'],
                'max_levels_of_separation': row['max_levels_of_separation']
            }
        } for _, row in results.iterrows()]


    def fetch_concept_relationship(self, concept_id):
        query = """
            SELECT 
                cr.concept_id_2 AS concept_id,
                cr.concept_id_1,
                cr.relationship_id,
                cr.concept_id_2, 
                c.concept_name, 
                c.vocabulary_id, 
                c.concept_code
            FROM 
                CONCEPT_RELATIONSHIP cr
            JOIN 
                CONCEPT c ON cr.concept_id_2 = c.concept_id
            WHERE 
                cr.concept_id_1 = %s AND
                cr.valid_end_date > NOW()
        """
        results = pd.read_sql(query, con=self.engine, params=(concept_id,)).drop_duplicates().query("concept_id != @concept_id")

        return [{
            'concept_name': row['concept_name'],
            'concept_id': row['concept_id'],
            'vocabulary_id': row['vocabulary_id'],
            'concept_code': row['concept_code'],
            'relationship': {
                'concept_id_1': row['concept_id_1'],
                'relationship_id': row['relationship_id'],
                'concept_id_2': row['concept_id_2']
            }
        } for _, row in results.iterrows()]