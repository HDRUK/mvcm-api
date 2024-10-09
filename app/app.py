from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List, Optional, Any  
import secrets
import os

from utils.calculate_best_OMOP_matches import OMOPMatcher
from utils.calculate_best_OLS4_matches import OLS4Matcher
from utils.calculate_best_UMLS_matches import UMLSMatcher

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

# Initialize OMOPMatcher only when it's first needed
omop_matcher = None
def get_omop_matcher():
    global omop_matcher
    if omop_matcher is None:
        omop_matcher = OMOPMatcher()
    return omop_matcher

ols4_matcher = None
def get_ols4_matcher():
    global ols4_matcher
    if ols4_matcher is None:
        ols4_matcher = OLS4Matcher()
    return ols4_matcher

UMLS_matcher = None
def get_UMLS_matcher():
    global UMLS_matcher
    if UMLS_matcher is None:
        UMLS_matcher = UMLSMatcher()
    return UMLS_matcher


class OLS4Request(BaseModel):
    search_terms: List[str] = ["Asthma", "Heart", "Bronchial hyperreactivity"]
    vocabulary_id: Optional[str] = "snomed"
    search_threshold: Optional[int] = 80

class UMLSRequest(BaseModel):
    search_terms: List[str] = ["Asthma", "Heart", "Bronchial hyperreactivity"]
    vocabulary_id: Optional[str] = "MTH"
    search_threshold: Optional[int] = 80

class OMOPRequest(BaseModel):
    search_terms: List[str] = ["Asthma", "Heart", "Bronchial hyperreactivity"]
    vocabulary_id: Optional[str] = "snomed"
    concept_ancestor: Optional[str] = "n"
    max_separation_descendant: Optional[int] = 1
    max_separation_ancestor: Optional[int] = 1
    concept_synonym: Optional[str] = "n"
    concept_relationship: Optional[str] = "n"
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
    ols4_matcher = get_ols4_matcher()
    return ols4_matcher.calculate_best_matches(request.search_terms, 
                                               request.vocabulary_id, 
                                               request.search_threshold)

@app.post("/search/umls/")
async def search_umls(request: UMLSRequest, credentials: HTTPBasicCredentials = Depends(authenticate_user)) -> Any:
    UMLS_matcher = get_UMLS_matcher()
    return UMLS_matcher.calculate_best_matches(request.search_terms, 
                                               request.vocabulary_id, 
                                               request.search_threshold)

@app.post("/search/omop/")
async def search_omop(request: OMOPRequest, credentials: HTTPBasicCredentials = Depends(authenticate_user)) -> Any:
    omop_matcher = get_omop_matcher()
    return omop_matcher.calculate_best_matches(search_terms=request.search_terms, 
                                               vocabulary_id=request.vocabulary_id, 
                                               concept_ancestor=request.concept_ancestor,
                                               concept_relationship=request.concept_relationship, 
                                               concept_synonym=request.concept_synonym, 
                                               search_threshold=request.search_threshold,
                                               max_separation_descendant=request.max_separation_descendant,
                                               max_separation_ancestor=request.max_separation_ancestor)
