import requests
import re
from rapidfuzz import fuzz
from urllib.parse import quote

class OLS4Matcher:
    def __init__(self):
        self.base_url = "http://www.ebi.ac.uk/ols4/api/search/"

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
                response_data = self.fetch_ols4_data(search_term, vocabulary_id, search_threshold)

                term_results = {
                    'search_term': search_term,
                    'matches': response_data
                }

                overall_results.append(term_results)

            return overall_results

        except Exception as e:
            raise ValueError(f"Error in calculate_best_OLS4_matches: {e}")

    def fetch_ols4_data(self, search_term, vocabulary_id, search_threshold):
        search_term_encoded = quote(f"{search_term.upper()},{search_term.lower()},{search_term.capitalize()}")
        url = self.base_url + f"?q={search_term_encoded}&queryFields=label&rows=10000"

        if vocabulary_id:
            vocabulary_id_encoded = quote(vocabulary_id)
            url += f"&ontology={vocabulary_id_encoded}"

        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers)
        docs = []
        if response.status_code == 200:
            json_data = response.json()
            if json_data['response']['numFound'] > 0:
                docs = json_data['response']['docs']

        matches = []
        for doc in docs:
            label = doc.get('label')
            if label is None:
                continue

            cleaned_concept_name = re.sub(r'\(.*?\)', '', label).strip()
            score = fuzz.ratio(search_term.lower(), cleaned_concept_name.lower())

            # Continue to the next iteration if the score is below the threshold
            if score < search_threshold:
                continue

            obo_id = doc.get('obo_id')
            vocabulary_concept_code = obo_id.split(':')[1] if obo_id and ':' in obo_id else obo_id

            match = {
                'concept_name': label,
                'concept_id': obo_id,
                'vocabulary_id': doc.get('ontology_prefix'),
                'vocabulary_concept_code': vocabulary_concept_code,
                'concept_name_similarity_score': score
            }
            matches.append(match)
            
        return matches