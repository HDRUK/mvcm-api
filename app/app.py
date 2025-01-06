from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List, Optional, Any  
import secrets
import os

from utils.calculate_best_OMOP_matches import OMOPMatcher
from utils.calculate_best_OLS4_matches import OLS4Matcher
from utils.calculate_best_UMLS_matches import UMLSMatcher
from utils.audit_publisher import publish_message

app = FastAPI(
    title="MVCM",
    description="HDR-UK Medical Vocabulary Concept Mapper",
    version="1.1.0",
    contact={
        "name": "Tom Giles",
        "email": "tom.giles@hdruk.ac.uk",
    },
)

security = HTTPBasic()

# Import OLS4Matcher, OMOPMatcher
omop_matcher = OMOPMatcher()
ols4_matcher = OLS4Matcher()
UMLS_matcher = UMLSMatcher()

class OLS4Request(BaseModel):
    search_terms: List[str] = ["Asthma", "Heart", "Bronchial hyperreactivity"]
    vocabulary_id: Optional[str] = ""
    search_threshold: Optional[int] = 80

class UMLSRequest(BaseModel):
    search_terms: List[str] = ["Asthma", "Heart", "Bronchial hyperreactivity"]
    vocabulary_id: Optional[str] = "MTH"
    search_threshold: Optional[int] = 80

class OMOPRequest(BaseModel):
    search_terms: List[str] = ["Asthma", "Heart", "Bronchial hyperreactivity"]
    vocabulary_id: Optional[str] = ""
    concept_ancestor: Optional[str] = "y"
    max_separation_descendant: Optional[int] = 0
    max_separation_ancestor: Optional[int] = 1
    concept_synonym: Optional[str] = "y"
    concept_synonym_language_concept_id: Optional[str] = "4180186"
    concept_relationship: Optional[str] = "y"
    concept_relationship_types: List[str] = ["Concept same_as to"]
    search_threshold: Optional[int] = 80

def get_credentials() -> tuple[str, str]:
    
    username = os.environ.get("BASIC_AUTH_USERNAME")
    password = os.environ.get("BASIC_AUTH_PASSWORD")

    if not username:
        username = "APIuser"
    
    if not password:
        password = "psw4API"

    return username, password

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)) -> Any:
    correct_username, correct_password = get_credentials()
    correct_credentials = secrets.compare_digest(credentials.username, correct_username) and secrets.compare_digest(credentials.password, correct_password)
    if not correct_credentials:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials

@app.post("/search/ols4/")
async def search_ols4(request: OLS4Request, credentials: HTTPBasicCredentials = Depends(authenticate_user)) -> Any:
    try:
        # Attempt to calculate best matches
        return ols4_matcher.calculate_best_matches(
            request.search_terms,
            request.vocabulary_id,
            request.search_threshold
        )
    except Exception as e:
        # Log the error and return a 500 response
        print(publish_message(action_type="POST", action_name="search_ols4", description=f"Error: {e}"))
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.post("/search/umls/")
async def search_umls(request: UMLSRequest, credentials: HTTPBasicCredentials = Depends(authenticate_user)) -> Any:
    try:
        # Attempt to calculate best matches
        return UMLS_matcher.calculate_best_matches(
            request.search_terms,
            request.vocabulary_id,
            request.search_threshold
        )
    except Exception as e:
        # Log the error and return a 500 response
        print(publish_message(action_type="POST", action_name="search_umls", description=f"Error: {e}"))
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.post("/search/omop/")
async def search_omop(request: OMOPRequest, credentials: HTTPBasicCredentials = Depends(authenticate_user)) -> Any:
    try:
        # Attempt to calculate best matches
        return omop_matcher.calculate_best_matches(
            search_terms=request.search_terms,
            vocabulary_id=request.vocabulary_id,
            concept_ancestor=request.concept_ancestor,
            concept_relationship=request.concept_relationship,
            concept_relationship_types=request.concept_relationship_types,
            concept_synonym=request.concept_synonym,
            concept_synonym_language_concept_id=request.concept_synonym_language_concept_id,
            search_threshold=request.search_threshold,
            max_separation_descendant=request.max_separation_descendant,
            max_separation_ancestor=request.max_separation_ancestor
        )
    except Exception as e:
        # Log the error and return a 500 response
        print(publish_message(action_type="POST", action_name="search_omop", description=f"Error: {e}"))
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.delete("/search/omop/clear_cache/")
async def clear_cache(credentials: HTTPBasicCredentials = Depends(authenticate_user)) -> dict:
    try:
        deleted_rows = omop_matcher.delete_all_cache()
        if deleted_rows is None:
            # Handle the case where deletion fails or returns None
            raise HTTPException(status_code=500, detail="Failed to clear the cache")
        return {"message": f"{deleted_rows} cache entries deleted."}
    
    except Exception as e:
        # Catch unexpected exceptions and return an appropriate HTTP error
        print(publish_message(action_type="POST", action_name="clear cache", description=f"Error: {e}"))
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")    