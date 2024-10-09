import pandas as pd
import re
import json
from rapidfuzz import fuzz
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from os import environ
import time
import json
from .audit_publisher import publish_message
from sqlalchemy.exc import OperationalError

class OMOPMatcher:
    def __init__(self):
        # Connect to database
        try:
            print("Initialize the MySQL connection based on the configuration.")
            
            # Fetch environment variables
            MYSQL_HOST=environ.get('DB_HOST', '0.0.0.0')
            MYSQL_PORT=environ.get('DB_PORT', '3306')  # Default to 3306 if DB_PORT is not set
            MYSQL_USER=environ.get('DB_USER', 'OMOP_user')
            MYSQL_PASSWORD=environ.get('DB_PASSWORD', 'psw4MYSQL')
            MYSQL_DB=environ.get('DB_NAME', 'OMOP')

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

            medical_terms = [
                "asthma", "heart", "diabetes", "hypertension", "stroke", "cancer", "arthritis", "depression", "anxiety", "migraine",
                "eczema", "bronchitis", "pneumonia", "sepsis", "anemia", "chronic pain", "osteoporosis", "glaucoma", "cataract", "allergy",
                "influenza", "obesity", "hypothyroidism", "hyperthyroidism", "renal failure", "liver disease", "hepatitis", "fibromyalgia",
                "dementia", "schizophrenia", "bipolar disorder", "epilepsy", "multiple sclerosis", "parkinson's disease", "alzheimer's disease",
                "sleep apnea", "gastroenteritis", "cholecystitis", "ulcerative colitis", "crohn's disease", "irritable bowel syndrome", "diverticulitis",
                "cirrhosis", "pancreatitis", "gout", "tuberculosis", "leukemia", "lymphoma", "melanoma", "psoriasis", "rheumatoid arthritis", "scoliosis",
                "kyphosis", "spina bifida", "cystic fibrosis", "COPD", "emphysema", "sinusitis", "otitis media", "hearing loss", "tinnitus", "vertigo",
                "conjunctivitis", "uveitis", "macular degeneration", "retinopathy", "hypertensive heart disease", "ischemic heart disease", "myocardial infarction",
                "angina", "atrial fibrillation", "ventricular fibrillation", "tachycardia", "bradycardia", "cardiomyopathy", "congestive heart failure",
                "pericarditis", "endocarditis", "valvular heart disease", "deep vein thrombosis", "pulmonary embolism", "varicose veins", "aneurysm", "peripheral artery disease",
                "raynaud's disease", "sickle cell anemia", "thalassemia", "hemophilia", "von willebrand disease", "lupus", "scleroderma", "sjogren's syndrome",
                "guillain-barre syndrome", "amyloidosis", "celiac disease", "vitamin D deficiency", "iron deficiency", "vitamin B12 deficiency", "rickets",
                "hypercalcemia", "hypocalcemia", "hypokalemia", "hyperkalemia", "metabolic syndrome", "polycystic ovary syndrome", "endometriosis", "uterine fibroids",
                "ovarian cysts", "pelvic inflammatory disease", "ectopic pregnancy", "miscarriage", "preeclampsia", "gestational diabetes", "menopause",
                "prostate cancer", "testicular cancer", "erectile dysfunction", "benign prostatic hyperplasia", "male infertility", "female infertility",
                "urinary tract infection", "kidney stones", "bladder cancer", "nephrotic syndrome", "acute kidney injury", "chronic kidney disease",
                "pyelonephritis", "interstitial cystitis", "overactive bladder", "glomerulonephritis", "prostatitis", "urethritis", "enuresis",
                "epididymitis", "hydrocele", "varicocele", "inguinal hernia", "hemorrhoids", "anal fissures", "rectal prolapse", "colorectal cancer",
                "appendicitis", "hernia", "celiac sprue", "gastroparesis", "esophageal varices", "gastritis", "duodenal ulcer", "peptic ulcer disease",
                "barrett's esophagus", "gastroesophageal reflux disease", "achalasia", "hepatocellular carcinoma", "liver abscess", "biliary atresia",
                "primary biliary cirrhosis", "portal hypertension", "esophageal cancer", "stomach cancer", "small intestine cancer", "colon cancer",
                "rectal cancer", "anal cancer", "carcinoid tumors", "neuroendocrine tumors", "pheochromocytoma", "hyperparathyroidism", "hypoparathyroidism",
                "hypoglycemia", "hyperglycemia", "gestational hypertension", "tension headache", "cluster headache", "temporal arteritis", "trigeminal neuralgia",
                "sciatica", "lumbar stenosis", "cervical stenosis", "herniated disc", "carpal tunnel syndrome", "cubital tunnel syndrome",
                "plantar fasciitis", "rotator cuff tear", "bursitis", "tendinitis", "achilles tendon rupture", "patellar tendonitis", "anterior cruciate ligament tear",
                "meniscus tear", "osteomyelitis", "septic arthritis", "bone cancer", "osteosarcoma", "ewing's sarcoma", "chondrosarcoma", "rhabdomyosarcoma",
                "soft tissue sarcoma", "myeloma", "neutropenia", "thrombocytopenia", "pancytopenia", "myelodysplastic syndrome", "aplastic anemia",
                "chronic lymphocytic leukemia", "chronic myelogenous leukemia", "acute lymphoblastic leukemia", "acute myeloid leukemia", "non-hodgkin lymphoma",
                "hodgkin lymphoma", "multiple myeloma", "skin cancer", "basal cell carcinoma", "squamous cell carcinoma", "actinic keratosis", "seborrheic keratosis",
                "keloid", "lipoma", "dermatofibroma", "alopecia areata", "seborrheic dermatitis", "contact dermatitis", "atopic dermatitis", "vitiligo",
                "melasma", "hidradenitis suppurativa", "tinea corporis", "onychomycosis", "herpes simplex", "herpes zoster", "human papillomavirus", "molluscum contagiosum",
                "impetigo", "cellulitis", "clavicle fracture", "humerus fracture", "radius fracture", "ulna fracture", "scaphoid fracture", "carpal fracture", 
                "metacarpal fracture", "phalangeal fracture", "femur fracture", "patella fracture", "tibia fracture", "fibula fracture", "tarsal fracture", 
                "metatarsal fracture", "calcaneal fracture", "talus fracture", "shoulder dislocation", "hip dislocation", "knee dislocation", "ankle sprain",
                "wrist sprain", "shoulder impingement", "frozen shoulder", "tennis elbow", "golfer's elbow", "ganglion cyst", "trigger finger", "de Quervain's tenosynovitis",
                "radial nerve palsy", "ulnar nerve palsy", "foot drop", "peripheral neuropathy", "diabetic neuropathy", "brachial plexus injury", 
                "thoracic outlet syndrome", "meralgia paresthetica", "herpes zoster ophthalmicus", "optic neuritis", "papilledema", "retinal detachment", 
                "macular hole", "retinitis pigmentosa", "keratoconus", "corneal abrasion", "corneal ulcer", "conjunctival hemorrhage", "anterior uveitis",
                "scleritis", "episcleritis", "ptosis", "blepharitis", "dacryocystitis", "hordeolum", "chalazion", "orbital cellulitis", "thyroid eye disease", 
                "strabismus", "amblyopia", "nystagmus", "hypertropia", "hypotropia", "esotropia", "exotropia", "neonatal jaundice", "hyperbilirubinemia", "kernicterus", 
                "galactosemia", "phenylketonuria", "maple syrup urine disease", "homocystinuria", "ornithine transcarbamylase deficiency", "cystinuria", "tyrosinemia", 
                "methylmalonic acidemia", "propionic acidemia", "isovaleric acidemia", "glutaric acidemia", "holocarboxylase synthetase deficiency", "biotinidase deficiency", 
                "zinc deficiency", "copper deficiency", "iodine deficiency", "selenium deficiency", "magnesium deficiency", "phosphorus deficiency", "calcium deficiency", 
                "potassium deficiency", "vitamin A deficiency", "vitamin K deficiency", "vitamin C deficiency", "vitamin E deficiency"
            ]

            self.calculate_best_matches(
                search_terms=medical_terms, 
                vocabulary_id="", 
                concept_ancestor="y",
                concept_relationship="y", 
                concept_synonym="y", 
                search_threshold=80,  
                max_separation_descendant=1,
                max_separation_ancestor=1
            )
        
            print("Cache initiated")

        except Exception as e:
            # Log failure and raise an error
            print(publish_message(action_type="POST", action_name="OMOPMatcher.__init__", description="Failed to connect to engine"))
            raise ValueError(f"Failed to connect to MySQL: {e}")
        
        
    
    def calculate_best_matches(self, search_terms, vocabulary_id=None, concept_ancestor="y",
                            concept_relationship="y", concept_synonym="y", search_threshold=0,
                            max_separation_descendant=1, max_separation_ancestor=1):
        if not search_terms:
            print(publish_message(action_type="POST", action_name="OMOPMatcher.calculate_best_matches", description="No valid search_term"))
            raise ValueError("No valid search_term values provided")

        if not isinstance(vocabulary_id, str) or not vocabulary_id.strip():
            vocabulary_id = None

        if not isinstance(search_threshold, (float, int)):
            search_threshold = 0

        overall_results = []

        for search_term in search_terms:

            #make lowercase
            search_term = search_term.lower()
            
            # Check if the result is cached
            cached_result = self.get_cached_result(
                search_term, vocabulary_id, concept_ancestor, concept_relationship,
                concept_synonym, search_threshold, max_separation_descendant, max_separation_ancestor
            )

            if cached_result is not None:
                # Use the cached result
                print("Using cached result for search term: {}".format(search_term))
                concepts = cached_result
            else:
                # Fetch concepts and store in cache
                concepts = self.fetch_OMOP_concepts(
                    search_term, vocabulary_id, concept_ancestor, concept_relationship,
                    concept_synonym, search_threshold, max_separation_descendant, max_separation_ancestor
                )

                if concepts:
                    # Cache the result
                    self.cache_result(
                        search_term, vocabulary_id, concept_ancestor, concept_relationship,
                        concept_synonym, search_threshold, max_separation_descendant, max_separation_ancestor,
                        concepts
                    )

            overall_results.append({'search_term': search_term, 'CONCEPT': concepts})

        return overall_results
    
    def get_cached_result(self, search_term, vocabulary_id, concept_ancestor, concept_relationship,
                        concept_synonym, search_threshold, max_separation_descendant, max_separation_ancestor):
        query = """
            SELECT result FROM omop_matcher_cache
            WHERE
                search_term = %s AND
                (%s IS NULL OR vocabulary_id = %s) AND
                concept_ancestor = %s AND
                concept_relationship = %s AND
                concept_synonym = %s AND
                search_threshold = %s AND
                max_separation_descendant = %s AND
                max_separation_ancestor = %s
        """
        params = (
            search_term,
            vocabulary_id, vocabulary_id,
            concept_ancestor,
            concept_relationship,
            concept_synonym,
            search_threshold,
            max_separation_descendant,
            max_separation_ancestor
        )
        try:

            result = pd.read_sql(query, con=self.engine, params=params)
            if not result.empty:
                cached_result = result['result'].iloc[0]
                return json.loads(cached_result)
            else:
                return None
        except SQLAlchemyError as e:
            print(publish_message(action_type="POST", action_name="OMOPMatcher.get_cached_result", description="Error fetching cached result"))
            print(f"Error fetching cached result: {e}")
            return None
        
    def cache_result(self, search_term, vocabulary_id, concept_ancestor, concept_relationship,
                    concept_synonym, search_threshold, max_separation_descendant, max_separation_ancestor,
                    concepts):
        # Serialize the concepts to JSON
        result_json = json.dumps(concepts)
        
        # Create a DataFrame for the new record
        data = {
            'search_term': [search_term],
            'vocabulary_id': [vocabulary_id],
            'concept_ancestor': [concept_ancestor],
            'concept_relationship': [concept_relationship],
            'concept_synonym': [concept_synonym],
            'search_threshold': [search_threshold],
            'max_separation_descendant': [max_separation_descendant],
            'max_separation_ancestor': [max_separation_ancestor],
            'result': [result_json]
        }
        df = pd.DataFrame(data)
        
        try:
            df.to_sql('omop_matcher_cache', con=self.engine, if_exists='append', index=False)
        except SQLAlchemyError as e:
            print(publish_message(action_type="POST", action_name="OMOPMatcher.cache_result", description="Error caching result"))
            print(f"Error caching/updating result for search_term '{search_term}': {e}")
        
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

        

# Outside the class definition for testing only! 


# if __name__ == "__main__":
#     # Record the start time
    

#     # Initialize the OMOPMatcher class
#     matcher = OMOPMatcher()
#     start_time = time.time()
#     results = matcher.set_up_cache()

#     # Record the end time
#     end_time = time.time()
#     # Iterate over results to count objects at each level
#     # Initialize counters for JSON objects at each level
#     concept_count = 0
#     concept_synonym_count = 0
#     concept_ancestor_count = 0
#     concept_relationship_count = 0

#     # Iterate over results to count objects at each level
#     for result in results:
#         if result and 'CONCEPT' in result and result['CONCEPT']:  # Check if 'CONCEPT' exists and is not None
#             for concept in result['CONCEPT']:
#                 concept_count += 1  # Increment by 1 for each concept
#                 if concept and 'CONCEPT_SYNONYM' in concept and concept['CONCEPT_SYNONYM']:
#                     concept_synonym_count += len(concept['CONCEPT_SYNONYM'])
#                 if concept and 'CONCEPT_ANCESTOR' in concept and concept['CONCEPT_ANCESTOR']:
#                     concept_ancestor_count += len(concept['CONCEPT_ANCESTOR'])
#                 if concept and 'CONCEPT_RELATIONSHIP' in concept and concept['CONCEPT_RELATIONSHIP']:
#                     concept_relationship_count += len(concept['CONCEPT_RELATIONSHIP'])

#     # Calculate the total execution time
#     execution_time = end_time - start_time

#     # Print the execution time
#     print(f"Execution Time: {execution_time:.2f} seconds")

#     # Print the counts for each level
#     print(f"Number of CONCEPT objects: {concept_count}")
#     print(f"Number of CONCEPT_SYNONYM objects: {concept_synonym_count}")
#     print(f"Number of CONCEPT_ANCESTOR objects: {concept_ancestor_count}")
#     print(f"Number of CONCEPT_RELATIONSHIP objects: {concept_relationship_count}")

#     # Optionally print the results (if needed)
#     #print("Results:", results)