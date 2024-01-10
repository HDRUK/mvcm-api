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
                OMOP_concepts = self.fetch_OMOP_concepts(search_term, vocabulary_id)
                if OMOP_concepts.empty:
                    continue

                term_results = {
                    'search_term': search_term,
                    'CONCEPT': self.process_concepts(OMOP_concepts, search_term, concept_ancestor, concept_relationship, search_threshold,max_separation_descendant,max_separation_ancestor)
                }

                overall_results.append(term_results)

            return overall_results
        
        except Exception as e:
            raise ValueError(f"Error in calculate_best_OMOP_matches: {e}")

    def process_concepts(self, OMOP_concepts, search_term, concept_ancestor, concept_relationship, search_threshold,max_separation_descendant,max_separation_ancestor):
        matches = []

        # Remove duplicate rows based on 'concept_id'
        OMOP_concepts = OMOP_concepts.drop_duplicates(subset='concept_id')

        for _, row in OMOP_concepts.iterrows():
            cleaned_concept_name = re.sub(r'\(.*?\)', '', row['concept_name']).strip()
            score = fuzz.ratio(search_term.lower(), cleaned_concept_name.lower())

            # Continue to the next iteration if the score is below the threshold
            if search_threshold is not None and score < search_threshold:
                continue

            # Add match to the list if it meets or exceeds the threshold
            match = {
                'concept_name': row['concept_name'],
                'concept_id': row['concept_id'],
                'vocabulary_id': row['vocabulary_id'],
                'concept_code': row['concept_code'],
                'similarity_score': score,
                'CONCEPT_ANCESTOR': self.fetch_concept_ancestor(row['concept_id'],max_separation_descendant,max_separation_ancestor) if concept_ancestor == "y" else [],
                'CONCEPT_RELATIONSHIP': self.fetch_concept_relationship(row['concept_id']) if concept_relationship == "y" else []
            }
            matches.append(match)
        return matches
    
    def fetch_OMOP_concepts(self, search_term, vocabulary_id):
        query = """
        SELECT 
            C.concept_id,
            C.concept_name, 
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
        params = (vocabulary_id, vocabulary_id, search_term, search_term)

        return pd.read_sql(query, con=self.engine, params=params)
    

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
        results = pd.read_sql(query, con=self.engine, params=(concept_id, min_separation_ancestor, max_separation_ancestor, concept_id, min_separation_descendant, max_separation_descendant)).drop_duplicates().query("concept_id != @concept_id")

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