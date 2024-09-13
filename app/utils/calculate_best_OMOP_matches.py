import pandas as pd
import re
from rapidfuzz import fuzz
from sqlalchemy import create_engine, text
from os import environ
from .audit_publisher import publish_message
from sqlalchemy.exc import OperationalError

class OMOPMatcher:
    def __init__(self):
        # Connect to database
        try:
            print("Initialize the MySQL connection based on the configuration.")
            MYSQL_HOST = environ.get('DB_HOST', '127.0.0.1')
            MYSQL_USER = environ.get('DB_USER', 'root')
            MYSQL_PASSWORD = environ.get('DB_PASSWORD', 'psw4MYSQL')
            MYSQL_DB = environ.get('DB_NAME', 'mydb')
            # SSL CONFIGURATION
            MYSQL_SSL_ENABLED = environ.get('DB_SSL_ENABLED', False)
            MYSQL_SSL_CA = environ.get('DB_SSL_CA', '')
            MYSQL_SSL_CERT = environ.get('DB_SSL_CERT', '')
            MYSQL_SSL_KEY = environ.get('DB_SSL_KEY', '')

            connection_string = (f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}')
            if MYSQL_SSL_ENABLED:
                ssl_args = (f'?ssl_ca={MYSQL_SSL_CA}&ssl_cert={MYSQL_SSL_CERT}&ssl_key={MYSQL_SSL_KEY}&ssl_check_hostname=false') 
                connection_string = connection_string + ssl_args
            engine = create_engine(connection_string)
            
            print(publish_message(action_type="POST", action_name="OMOPMatcher.__init__", description="Connected to engine"))

        except Exception as e:
            print(publish_message(action_type="POST", action_name="OMOPMatcher.__init__", description="Failed to connect to engine"))
            raise ValueError(f"Failed to connect to MySQL: {e}")
        
        self.engine = engine

    def index_exists(self, connection, table_name, index_name):
        try:
            query = """
            SELECT COUNT(1) 
            FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = :table_name 
            AND INDEX_NAME = :index_name;
            """
            result = connection.execute(
                text(query), {"table_name": table_name, "index_name": index_name}
            )
            return result.scalar() > 0
        except Exception as e:
            raise ValueError(f"Error checking if index exists: {e}")

    def provision_indexes(self):
        try: 
            print(publish_message(action_type="POST", action_name="OMOPMatcher.provision_indexes", description="Running SQL to provision indexes..."))

            # SQL commands with table name and index name
            sql_commands = [
                ("CONCEPT_RELATIONSHIP", "idx_concept_relationship_on_id1_enddate",
                 "CREATE INDEX idx_concept_relationship_on_id1_enddate ON CONCEPT_RELATIONSHIP(concept_id_1, valid_end_date);"),
                ("CONCEPT_RELATIONSHIP", "idx_concept_relationship_on_id2",
                 "CREATE INDEX idx_concept_relationship_on_id2 ON CONCEPT_RELATIONSHIP(concept_id_2);"),
                
                ("CONCEPT_ANCESTOR", "idx_concept_ancestor_on_descendant_id",
                 "CREATE INDEX idx_concept_ancestor_on_descendant_id ON CONCEPT_ANCESTOR(descendant_concept_id);"),
                ("CONCEPT_ANCESTOR", "idx_concept_ancestor_on_ancestor_id",
                 "CREATE INDEX idx_concept_ancestor_on_ancestor_id ON CONCEPT_ANCESTOR(ancestor_concept_id);"),
                
                ("CONCEPT_SYNONYM", "idx_concept_synonym_name",
                 "CREATE FULLTEXT INDEX idx_concept_synonym_name ON CONCEPT_SYNONYM(concept_synonym_name);"),
                ("CONCEPT_SYNONYM", "idx_concept_synonym_id",
                 "CREATE INDEX idx_concept_synonym_id ON CONCEPT_SYNONYM(concept_id);"),
                
                ("CONCEPT", "idx_concept_name",
                 "CREATE FULLTEXT INDEX idx_concept_name ON CONCEPT(concept_name);"),
                ("CONCEPT", "idx_concept_id",
                 "CREATE INDEX idx_concept_id ON CONCEPT(concept_id);"),
                ("CONCEPT", "idx_standard_concept_vocabulary_id_concept_id",
                 "CREATE INDEX idx_standard_concept_vocabulary_id_concept_id ON CONCEPT(standard_concept, vocabulary_id, concept_id);"),
                
                # Create Table STANDARD_CONCEPTS
                ("", "", "CREATE TABLE IF NOT EXISTS STANDARD_CONCEPTS AS SELECT * FROM CONCEPT WHERE standard_concept = 'S';"),
                
                # Index creation for STANDARD_CONCEPTS
                ("STANDARD_CONCEPTS", "ft_concept_name",
                 "CREATE FULLTEXT INDEX ft_concept_name ON STANDARD_CONCEPTS(concept_name);"),
                ("STANDARD_CONCEPTS", "idx_vocabulary_id_concept_id",
                 "CREATE INDEX idx_vocabulary_id_concept_id ON STANDARD_CONCEPTS(vocabulary_id, concept_id);")
            ]

            # Execute each SQL command, checking for index existence where applicable
            with self.engine.connect() as connection:
                for table_name, index_name, sql_command in sql_commands:
                    if table_name and index_name:  # It's an index creation command
                        if not self.index_exists(connection, table_name, index_name):
                            try:
                                connection.execute(text(sql_command))
                                print(f"Running: {sql_command}")
                            except OperationalError as oe:
                                if "Duplicate key name" in str(oe):
                                    print(f"Index {index_name} already exists. Skipping.")
                                else:
                                    raise
                    else:
                        # For other commands like table creation
                        connection.execute(text(sql_command))

            print(publish_message(action_type="POST", action_name="OMOPMatcher.provision_indexes", description="Indexes successfully provisioned"))

        except Exception as e:
            print(publish_message(action_type="POST", action_name="OMOPMatcher.provision_indexes", description="Failed to provision indexes"))
            raise ValueError(f"Error in provisioning indexes: {e}")
        
    def calculate_best_matches(self, search_terms, vocabulary_id=None, concept_ancestor="y", concept_relationship="y", concept_synonym="y", search_threshold=None, max_separation_descendant=1, max_separation_ancestor=1):
        try:
            if not search_terms:
                print(publish_message(action_type="POST", action_name="OMOPMatcher.calculate_best_matches", description="No valid search_term values provided"))
                raise ValueError("No valid search_term values provided")

            print(publish_message(action_type="POST", action_name="OMOPMatcher.calculate_best_matches", description="Valid search_term values provided"))

            overall_results = []

            # Assuming vocabulary_id is meant to be a not empty string
            if not isinstance(vocabulary_id, str) or not vocabulary_id.strip():
                vocabulary_id = None

            # search_threshold should be a float or integer, so check if it's a number
            if not isinstance(search_threshold, (float, int)):
                search_threshold = 0
         
            for search_term in search_terms:
                OMOP_concepts = self.fetch_OMOP_concepts(search_term, vocabulary_id, concept_ancestor, concept_relationship,concept_synonym, search_threshold,max_separation_descendant,max_separation_ancestor)

                overall_results.append({
                    'search_term': search_term,
                    'CONCEPT': OMOP_concepts
                })

            print(publish_message(action_type="POST", action_name="OMOPMatcher.calculate_best_matches", description=f"Best OMOP matches for {str(search_terms)} calculated"))
            return overall_results
        
        except Exception as e:
            print(publish_message(action_type="POST", action_name="OMOPMatcher.calculate_best_matches", description=f"Failed to calculate best OMOP matches for {search_terms}"))
            raise ValueError(f"Error in calculate_best_OMOP_matches: {e}")
    
    def fetch_OMOP_concepts(self, search_term, vocabulary_id, concept_ancestor, concept_relationship,concept_synonym, search_threshold,max_separation_descendant,max_separation_ancestor):
        
        query1 = """
            WITH concept_matches AS (
                SELECT DISTINCT concept_id
                FROM STANDARD_CONCEPTS
                WHERE 
                    (%s IS NULL OR vocabulary_id = %s) AND
                    MATCH(concept_name) AGAINST (%s IN NATURAL LANGUAGE MODE)
            ),
            synonym_matches AS (
                SELECT DISTINCT concept_id
                FROM CONCEPT_SYNONYM
                WHERE MATCH(concept_synonym_name) AGAINST (%s IN NATURAL LANGUAGE MODE)
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
                STANDARD_CONCEPTS
            WHERE 
                (%s IS NULL OR vocabulary_id = %s) AND
                MATCH(concept_name) AGAINST (%s IN NATURAL LANGUAGE MODE) 
            """
        
        # use CS.language_concept_id = '4180186' as additional filter if needed
        if concept_synonym == "y":
            params = (vocabulary_id, vocabulary_id, search_term, search_term,)
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
                score = fuzz.ratio(search_term.lower(), cleaned_concept_name.lower())
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