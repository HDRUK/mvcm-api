from rapidfuzz import fuzz
from urllib.parse import quote
import requests
import re
from os import environ

class UMLSMatcher:
    def api_call(self, url):
        headers = {
            "Accept": "application/json",
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    def calculate_best_matches(self, search_terms, vocabulary_id=None, search_threshold=None):
        try:
            if not search_terms:
                raise ValueError("No valid search_term values provided")
            
            overall_results = []

            # Assuming vocabulary_id is meant to be a not empty string
            if not isinstance(vocabulary_id, str) or not vocabulary_id.strip():
                vocabulary_id = None

            # search_threshold should be a float or integer, so check if it's a number
            if not isinstance(search_threshold, (float, int)):
                search_threshold = 0

            for search_term in search_terms:
                response_data = self.fetch_umls_data(search_term, vocabulary_id, search_threshold)

                term_results = {
                    'search_term': search_term,
                    'matches': response_data
                }

                overall_results.append(term_results)

            return overall_results

        except Exception as e:
            raise ValueError(f"Error in calculate_best_UMLS_matches: {e}")

    def fetch_umls_data(self, search_term, vocabulary_id, search_threshold):
        
        search_term_encoded = quote(search_term)

        APIKEY = environ.get('UMLS_APIKEY')

        if vocabulary_id is None:
            url = f"https://uts-ws.nlm.nih.gov/rest/search/current?apiKey={APIKEY}&pageSize=10000&string={search_term_encoded}"
        else:
            vocabulary_id_encoded = quote(vocabulary_id)
            url = f"https://uts-ws.nlm.nih.gov/rest/search/current?apiKey={APIKEY}&pageSize=10000&sabs={vocabulary_id_encoded}&string={search_term}"

        json_data = self.api_call(url)
            
        if json_data is not None:
            results_data = json_data['result']['results']
            matches = []

            if results_data is not None:

                for result in results_data:
                    
                    label = result.get('name')
                    ui = result.get('ui')
                    vocab = result.get('rootSource')

                    if label is None:
                        continue

                    cleaned_concept_name = re.sub(r'\(.*?\)', '', label).strip()
                    score = fuzz.ratio(search_term.lower(), cleaned_concept_name.lower())
                    score = fuzz.ratio(search_term.lower(), cleaned_concept_name.lower())

                    # Continue to the next iteration if the score is below the threshold
                    if score < search_threshold:
                        continue
            
                    match = {
                        'concept_name': label,
                        'concept_id': ui,
                        'vocabulary_id': vocab,
                        'concept_code': ui,
                        'concept_name_similarity_score': score
                    }
                    matches.append(match)
            
            return matches


#UMLSMatcher().calculate_best_matches(search_terms=["asthma"], vocabulary_id=None, search_threshold=80)

#APIKEY="e8ac4aea-f310-4bcd-aded-3c256465fd94"
#search_term_encoded="C0004096"
#url = f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/{search_term_encoded}/relations?apiKey={APIKEY}&pageSize=10000"

#json_data = UMLSMatcher().api_call(url)
#print(json_data)