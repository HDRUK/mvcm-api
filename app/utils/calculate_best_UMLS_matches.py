from functools import lru_cache
import pandas as pd
from rapidfuzz import fuzz
from urllib.parse import quote
import requests
import re

APIKEY="e8ac4aea-f310-4bcd-aded-3c256465fd94"

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
def calculate_best_UMLS_matches(search_terms, vocabulary_id=None, search_threshold=None):
    try:
        if not search_terms:
            raise ValueError("No valid search_term values provided")

        result_dict = {
            'search_term': [],
            'closely_mapped_term': [],
            'relationship_type': [],
            'concept_id': [],
            'vocabulary_id': [],
            'vocabulary_concept_code': [],
            'similarity_score': []
        }

        for search_term in search_terms:
            search_term_encoded = quote(search_term)

            if vocabulary_id is None:
                url = f"https://uts-ws.nlm.nih.gov/rest/search/current?apiKey={APIKEY}&pageSize=10000&string={search_term_encoded}"
            else:
                vocabulary_id_encoded = quote(vocabulary_id)
                url = f"https://uts-ws.nlm.nih.gov/rest/search/current?apiKey={APIKEY}&pageSize=10000&sabs={vocabulary_id_encoded}&string={search_term}"

            json_data = api_call(url)
            
            if json_data is not None:
                results_data = json_data['result']['results']

                if not results_data:
                    continue

                for result in results_data:
                    label = result.get('name')
                    ui = result.get('ui')
                    vocab = result.get('rootSource')

                    if label is None:
                        continue

                    cleaned_concept_name = re.sub(r'\(.*?\)', '', label).strip()
                    score = fuzz.ratio(search_term.lower(), cleaned_concept_name.lower())

                    result_dict['search_term'].append(search_term)
                    result_dict['closely_mapped_term'].append(label)
                    result_dict['relationship_type'].append('UMLS_mapping')
                    result_dict['concept_id'].append(ui)
                    result_dict['vocabulary_id'].append(vocab)
                    result_dict['vocabulary_concept_code'].append(ui)
                    result_dict['similarity_score'].append(score)

        results_df = pd.DataFrame(result_dict).drop_duplicates().sort_values(by='similarity_score', ascending=False)

        if search_threshold is not None:
            results_df = results_df[results_df['similarity_score'] > search_threshold]

        return results_df

    except Exception as e:
        raise(ValueError(f"Error in calculate_best_UMLS_matches: {e}"))
      

#terms=["fracture of carpal bone"] 
#test = calculate_best_OLS4_matches(search_terms=terms, vocabulary_id=None, search_threshold=80)
#print(test)
# Test cache (this should return the cached DataFrame)
#test_cached = calculate_best_OLS4_matches(search_terms=terms, vocabulary_id=None, search_threshold=80)
#print(test_cached)
