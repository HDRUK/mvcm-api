import pandas as pd
import re
import json
import hashlib
from rapidfuzz import fuzz
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from os import environ
import time
from .audit_publisher import publish_message
from sqlalchemy.exc import OperationalError

class OMOPMatcher:
    def __init__(self):
        # Connect to database
        try:
            print("Initialize the MySQL connection based on the configuration.")
            
            # Fetch environment variables
            MYSQL_HOST=environ.get('DB_HOST')
            MYSQL_PORT=environ.get('DB_PORT')
            MYSQL_USER=environ.get('DB_USER')
            MYSQL_PASSWORD=environ.get('DB_PASSWORD')
            MYSQL_DB=environ.get('DB_NAME')
            
            # SSL Configuration
            MYSQL_SSL_ENABLED = environ.get('DB_SSL_ENABLED', False)
            MYSQL_SSL_CA = environ.get('DB_SSL_CA', False)
            MYSQL_SSL_CERT = environ.get('DB_SSL_CERT', False)
            MYSQL_SSL_KEY = environ.get('DB_SSL_KEY', False)

            # Build the connection string, including the port
            connection_string = (
                f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
            )

            # Append SSL arguments if SSL is enabled
            if MYSQL_SSL_ENABLED and MYSQL_SSL_CA and MYSQL_SSL_CERT and MYSQL_SSL_KEY:
                ssl_args = (
                    f'?ssl_ca={MYSQL_SSL_CA}&ssl_cert={MYSQL_SSL_CERT}&ssl_key={MYSQL_SSL_KEY}&ssl_check_hostname=false'
                )
                connection_string += ssl_args

            # Create SQLAlchemy engine
            engine = create_engine(connection_string)
            
            # Log success
            print(publish_message(action_type="POST", action_name="OMOPMatcher.__init__", description="Connected to engine"))

            self.engine = engine

        except Exception as e:
            # Log failure and raise an error
            print(publish_message(action_type="POST", action_name="OMOPMatcher.__init__", description="Failed to connect to engine"))
            raise ValueError(f"Failed to connect to MySQL: {e}")
        
    def compute_search_params_hash(self, search_parameters):
        # Serialize the JSON with consistent ordering
        search_parameters_json = json.dumps(search_parameters, sort_keys=True)
        # Compute the SHA256 hash
        return hashlib.sha256(search_parameters_json.encode()).hexdigest()

    def calculate_best_matches(self, search_terms, vocabulary_id=None, concept_ancestor="n",
                            concept_relationship="n", concept_relationship_types="Mapped from", 
                            concept_synonym="n", concept_synonym_language_concept_id="4180186",
                            search_threshold=80,
                            max_separation_descendant=0, max_separation_ancestor=1):

        if not search_terms:
            print(publish_message(action_type="POST", action_name="OMOPMatcher.calculate_best_matches", description="No valid search_term"))
            raise ValueError("No valid search_term values provided")

        if not isinstance(vocabulary_id, str) or not vocabulary_id.strip():
            vocabulary_id = None

        if not isinstance(search_threshold, (float, int)):
            search_threshold = 0

        overall_results = []
        cache_usage_info = []

        for search_term in search_terms:

            #make lowercase
            search_term = search_term.lower()

            cached_search_parameters = {
                "vocabulary_id": vocabulary_id,
                "concept_ancestor": concept_ancestor,
                "max_separation_descendant": max_separation_descendant,
                "max_separation_ancestor": max_separation_descendant,
                "concept_synonym": concept_synonym,
                "concept_synonym_language_concept_id": concept_synonym_language_concept_id,
                "concept_relationship": concept_relationship,
                "concept_relationship_types": concept_relationship_types,
                "search_threshold": search_threshold
            }

            search_params_hash = self.compute_search_params_hash(cached_search_parameters)
            
            # Check if the result is cached
            cached_result = self.get_cached_result(
                search_term, search_params_hash
            )

            if cached_result is not None:
                # Use the cached result
                results = cached_result
                cache_usage_info.append({'search_term': search_term, 'cache_used': True})
            else:
                # Fetch concepts and store in cache
                results = self.fetch_OMOP_concepts(
                    search_term, vocabulary_id, concept_ancestor, concept_relationship,concept_relationship_types,
                    concept_synonym, concept_synonym_language_concept_id, search_threshold, max_separation_descendant, max_separation_ancestor
                )

                self.cache_result(search_term, search_params_hash, results)
                cache_usage_info.append({'search_term': search_term, 'cache_used': False})

            overall_results.append({'search_term': search_term, 'CONCEPT': results})

        # Print cache usage summary at the end
        cache_summary = ": ".join([
            f"{entry['search_term']}: {'Cache Used' if entry['cache_used'] else 'Not Cached'}"
            for entry in cache_usage_info
        ])

        print(f"INFO:   Cache usage summary: {cache_summary}")
        print(publish_message(action_type="POST", action_name="OMOPMatcher.calculate_best_matches", description="Query ran sucessfully: summary: {cache_summary}"))
        
        return overall_results
    
    def delete_all_cache(self):
        try:
            with self.engine.begin() as connection:

                # Step 1: Count rows before deletion
                pre_delete_count_df = pd.read_sql("SELECT COUNT(*) AS count FROM omop_matcher_cache", con=connection)
                pre_delete_count = pre_delete_count_df['count'].iloc[0]

                # Step 2: Perform the deletion
                delete_query = text("DELETE FROM omop_matcher_cache")
                connection.execute(delete_query)
                
                # Step 3: Count rows after deletion
                post_delete_count_df = pd.read_sql("SELECT COUNT(*) AS count FROM omop_matcher_cache", con=connection)
                post_delete_count = post_delete_count_df['count'].iloc[0]

                # Step 4: Calculate the number of rows deleted
                deleted_rows = pre_delete_count - post_delete_count
                
                # Log the number of deleted rows
                print(f"Info:    Rows before Deletion: {pre_delete_count}: Deleted rows: {deleted_rows}")  # Debug statement
                print(publish_message(action_type="POST", action_name="OMOPMatcher.delete_all_cache", description=f"{deleted_rows} cache entries deleted."))

                # Return the number of rows deleted
                return deleted_rows

        except SQLAlchemyError as e:
            print(publish_message(action_type="POST", action_name="OMOPMatcher.delete_all_cache", description=f"Error deleting all cache: {e}"))

        except Exception as e:
            print(publish_message(action_type="POST", action_name="OMOPMatcher.delete_all_cache", description=f"Unexpected error occurred: {e}"))

    def get_cached_result(self, search_term, search_params_hash):
        
        query = """
            SELECT result FROM omop_matcher_cache
            WHERE search_term = %s AND search_parameters = %s
        """
        params = (search_term, search_params_hash)

        try:
            result = pd.read_sql(query, con=self.engine, params=params)
            if not result.empty:
                cached_result = result['result'].iloc[0]
                return json.loads(cached_result)
            else:
                return None
        except SQLAlchemyError as e:
            print(publish_message(action_type="POST", action_name="OMOPMatcher.get_cached_result",
                                description=f"Error fetching cached result: {e}"))
            return None

    def cache_result(self, search_term, search_params_hash, results):

        # Serialize results to JSON
        result_json = json.dumps(results)

        # Create a DataFrame for the new record
        data = {
            'search_term': [search_term],
            'search_parameters': [search_params_hash],
            'result': [result_json]
        }
        df = pd.DataFrame(data)

        try:
            df.to_sql('omop_matcher_cache', con=self.engine, if_exists='append', index=False)
        except SQLAlchemyError as e:
            print(publish_message(action_type="POST", action_name="OMOPMatcher.cache_result",
                                description=f"Error caching result: {e}"))

    def fetch_OMOP_concepts(self, search_term, vocabulary_id, concept_ancestor, concept_relationship, 
                            concept_relationship_types, concept_synonym, concept_synonym_language_concept_id, search_threshold, max_separation_descendant, 
                            max_separation_ancestor):
        
        query1 = """
            WITH concept_matches AS (
                SELECT DISTINCT concept_id
                FROM CONCEPT
                WHERE 
                    (%s IS NULL OR vocabulary_id = %s) AND
                    MATCH(concept_name) AGAINST (%s IN NATURAL LANGUAGE MODE)
            ),
            synonym_matches AS (
                SELECT DISTINCT concept_id
                FROM CONCEPT_SYNONYM
                WHERE 
                    (%s IS NULL OR language_concept_id = %s) AND
                    MATCH(concept_synonym_name) AGAINST (%s IN NATURAL LANGUAGE MODE)
            ),
            combined_matches AS (
                SELECT concept_id FROM concept_matches
                UNION
                SELECT concept_id FROM synonym_matches
            )
            SELECT 
                C.concept_id,
                C.concept_name, 
                CS.concept_synonym_name,
                C.vocabulary_id, 
                C.concept_code
            FROM 
                combined_matches CM
            JOIN CONCEPT C ON CM.concept_id = C.concept_id
            LEFT JOIN CONCEPT_SYNONYM CS ON C.concept_id = CS.concept_id
            """
        
        query2 = """
            SELECT 
                concept_id,
                concept_name, 
                "" as concept_synonym_name,
                vocabulary_id, 
                concept_code
            FROM 
                CONCEPT
            WHERE 
                (%s IS NULL OR vocabulary_id = %s) AND
                MATCH(concept_name) AGAINST (%s IN NATURAL LANGUAGE MODE) 
            """
        
        # use CS.language_concept_id = '4180186' as additional filter if needed
        if concept_synonym == "y":
            params = (vocabulary_id, vocabulary_id, search_term, concept_synonym_language_concept_id, concept_synonym_language_concept_id, search_term, )
            results = pd.read_sql(query1, con=self.engine, params=params)
        else:
            params = (vocabulary_id, vocabulary_id, search_term,)
            results = pd.read_sql(query2, con=self.engine, params=params).replace("", None)

        if not results.empty:
            # Define a function to calculate similarity score using the provided logic
            def calculate_similarity(row):
                if row is None:
                    return 0  # Return a default score (e.g., 0) for null values
                cleaned_concept_name = re.sub(r'\(.*?\)', '', row).strip()
                score = fuzz.ratio(search_term, cleaned_concept_name.lower())
                return score

            # Apply the score function to 'concept_name' and 'concept_synonym_name' columns
            results['concept_name_similarity_score'] = results['concept_name'].apply(calculate_similarity)
            results['concept_synonym_name_similarity_score'] = results['concept_synonym_name'].apply(calculate_similarity)
            
            concept_ids_above_threshold = set(
                results.loc[
                    (results['concept_name_similarity_score'] > search_threshold) | 
                    (results['concept_synonym_name_similarity_score'] > search_threshold), 
                    'concept_id'
                ]
            )

            # Step 2: Filter the original DataFrame to include all rows with these concept_ids
            results = results[results['concept_id'].isin(concept_ids_above_threshold)]

            # Sort the filtered results by the highest score (descending order)
            results = results.sort_values(by=['concept_name_similarity_score', 'concept_synonym_name_similarity_score'], ascending=False)

            # Group by 'concept_id' and aggregate the relevant columns
            grouped_results = results.groupby('concept_id').agg({
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
                } for syn_name, syn_score in zip(row['concept_synonym_name'], row['concept_synonym_name_similarity_score']) if syn_name is not None],
                'CONCEPT_ANCESTOR': self.fetch_concept_ancestor(row['concept_id'], max_separation_descendant, max_separation_ancestor) if concept_ancestor == "y" else [],
                'CONCEPT_RELATIONSHIP': self.fetch_concept_relationship(row['concept_id'], concept_relationship_types) if concept_relationship == "y" else []
            } for _, row in grouped_results.iterrows()]

    def fetch_concept_ancestor(self, concept_id, max_separation_descendant, max_separation_ancestor):
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
        
        try:
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
        except Exception as e:
            print(publish_message(action_type="POST", action_name="OMOPMatcher.fetch_concept_ancestor", description="Error fetching concept ancestors"))
            return []

    def fetch_concept_relationship(self, concept_id, concept_relationship_types):
        # Clean the `concept_relationship_types` list by removing empty strings
        concept_relationship_types = [t for t in concept_relationship_types if t.strip()] if concept_relationship_types else None

        try:
            if not concept_relationship_types:
                # Query when no relationship types are provided
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
                            cr.concept_id_1 = %s
                            AND cr.valid_end_date > NOW()
                    """
                
                params = (concept_id,)
                results = pd.read_sql(query, con=self.engine, params=params).drop_duplicates()
            else:
                # Query when relationship types are provided
                results = pd.DataFrame()  # Initialize an empty DataFrame
                for concept_relationship_type in concept_relationship_types:
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
                            cr.concept_id_1 = %s
                            AND cr.relationship_id = %s
                            AND cr.valid_end_date > NOW()
                    """
                    # Execute the query for the current relationship type
                    params = (concept_id, concept_relationship_type)
                    result = pd.read_sql(query, con=self.engine, params=params).drop_duplicates()
                    results = pd.concat([results, result], ignore_index=True)  # Concatenate the new result

            # Process the DataFrame into the desired output format
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
        except Exception as e:
            print(publish_message(action_type="POST", action_name="OMOPMatcher.fetch_concept_relationship", description="Error fetching concept relationships"))
            return []

    
