from functools import lru_cache
import pandas as pd
from rapidfuzz import fuzz
from urllib.parse import quote
import requests
from rapidfuzz import fuzz
import re
from utils.Bert_match import bert_similarity

# Define a helper function for the API call to be cached
@lru_cache(maxsize=512)
def api_call(url):
    headers = {
        "Accept": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None
    
# Function to calculate best OLS4 matches based on search terms
# This function queries the OLS4 API and returns concept matches based on given search terms.
def calculate_best_OLS4_matches(search_terms, vocabulary_id=None, search_threshold=None,search_tool=None):
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
            'vocabulary_concept_code': [],
            'similarity_score': []  
        }

        # Iterate through each search term provided in the list to perform individual concept matching.
        for search_term in search_terms:
            search_term_encoded = quote(f"{search_term.upper()},{search_term.lower()},{search_term.capitalize()}")

            if vocabulary_id is None:
                url = f"http://www.ebi.ac.uk/ols4/api/search/?q={search_term_encoded}&queryFields=label&rows=10000"
            else:
                vocabulary_id_encoded = quote(vocabulary_id)
                url = f"http://www.ebi.ac.uk/ols4/api/search/?q={search_term_encoded}&queryFields=label&ontology={vocabulary_id_encoded}&rows=10000"

            # Send a GET request to the OLS4 API to fetch potentially matching concepts. Use query parameters for initial filtering.
            json_data = api_call(url)

            if json_data is not None:

                results_data = json_data['response']['docs']
                
                # Check if 'numFound' is greater than 0, if not continue to the next iteration
                if json_data['response']['numFound'] <= 0:
                    continue

                if not results_data:
                    continue

                # Iterate through each document in the API response to perform additional filtering and similarity scoring.
                for doc in results_data:
                    label = doc.get('label')
                    obo_id = doc.get('obo_id')
                    
                    if label is None:
                        continue
                    
                    cleaned_concept_name = re.sub(r'\(.*?\)', '', label).strip()

                    if search_tool == "rapidFuzz":
                        score = fuzz.ratio(search_term.lower(), cleaned_concept_name.lower())

                    elif search_tool == "pubmedBERT":
                        score = bert_similarity(search_term.lower(), cleaned_concept_name.lower())
                    else: 
                        score = fuzz.ratio(search_term.lower(), cleaned_concept_name.lower())
                        
                    if obo_id and ':' in obo_id:
                        vocabulary_concept_code = obo_id.split(':')[1]
                    else:
                        vocabulary_concept_code = obo_id

                    result_dict['search_term'].append(search_term)
                    result_dict['closely_mapped_term'].append(label)
                    result_dict['relationship_type'].append('OLS4_mapping')
                    result_dict['concept_id'].append(doc.get('obo_id'))
                    result_dict['vocabulary_id'].append(doc.get('ontology_prefix'))
                    result_dict['vocabulary_concept_code'].append(vocabulary_concept_code)
                    result_dict['similarity_score'].append(score)

        # Create a DataFrame from the result dict
        results_df = pd.DataFrame(result_dict).drop_duplicates().sort_values(by='similarity_score', ascending=False)

        if search_threshold is not None:
            results_df = results_df[results_df['similarity_score'] > search_threshold]

        return results_df
    
    # Fail gracefully and log
    except Exception as e:
        ValueError(f"Error in calculate_best_OLS4_matches: {e}")
        return pd.DataFrame()

#terms=["fracture of carpal bone"] 
#test = calculate_best_OLS4_matches(search_terms=terms, vocabulary_id=None, search_threshold=80)
#print(test)
# Test cache (this should return the cached DataFrame)
#test_cached = calculate_best_OLS4_matches(search_terms=terms, vocabulary_id=None, search_threshold=80)
#print(test_cached)