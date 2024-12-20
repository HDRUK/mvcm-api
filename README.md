
# Medical Vocabulary Concept Mapping Application Programming Interface (MVCM API)

## Introduction

The Medical Vocabulary Concept Mapper (MVCM) is a software application developed using FastAPI, a modern, fast (high-performance) web framework for building APIs with Python. The primary purpose of MVCM is to assist in the mapping of medical concepts to standardized terms, facilitating the unification of terminologies to improve interoperability and linkage across different healthcare databases and systems. 
MVCM has three distinct endpoints. The first, primary endpoint queries the OMOP Common Data Model (CDM): This provides an interface for querying a MySQL database populated with the OMOP CDM's structured medical concepts. The automatically available local database contains information from OMOP  v5.0 31-AUG-23 and contains following vocabularies Snomed, LONC, Read, ICD10, MESH. However, it can be configured to run against an external database, or alternatively the tables can be replaced with alternative revisions by users manually. 

The search function of this endpoint primary use SQL natural language queries to compare terms to the CONCEPT_NAME field in the OMOP CONCEPT table. But has also been enhanced using the following relational OMOP vocabulary tables:

•	The CONCEPT_SYNONYM table can be used to expand the search space. When enabled the results will include matches between search terms and all synonymous versions of each of the OMOP terms. 
•	Results can be enriched with interactions as defined in the CONCEPT_RELATIONSHIP table, offering user the ability to expand their searches to identify a range of related concepts. 
•	Results can be enriched with relative defined in the CONCEPT_ANCESTOR table, offering user the ability to expand their searches to encompass related parental and child concepts. 

The other two provided endpoints query the UMLS (Unified Medical Language System and OLS4 (Ontology Lookup Service, version 4) API endpoint respectively. These searches are returned in the same array structure as the OMOP search results to improve interoperability. This structured approach to querying and mapping across resources effectively enhances the breadth and depth of search capabilities, providing users with a robust tool for the accurate mapping of medical concepts.

## App Setup and Deployment

To get a local copy of this applications, first clone the git repo: 

```bash
gh repo clone HDRUK/mvcm-api
```

The best way to build and deploy the application is using Docker. The application is containerized with all necessary files and scripts (except for the Google Application Credentials file necessary for using PubSub audit), and can be run with the following command:

```bash
docker build -t app . ; docker run -p 80:80 -e <various environment variables> app
```

In order to use the PubSub audit functionality, you'll need to place you `application_default_credentials.json` file into the directory before calling the `docker build` command as above.

### Internal/External Database setup

MVCM runs on an external OMOP database, set the `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` environment variables to the appropriate values for your database server before running the app. These can be set using the `-e` option with the docker run command. For example:

```bash
docker run -p 80:80 -e DB_HOST=your_db_host -e DB_USER=your_db_user -e DB_PASSWORD=your_db_password -e DB_NAME=your_db_name app
```

This approach also support SSL, the following additional envs must be set: `DB_SSL_ENABLED=True`, `ENV DB_SSL_CA=CertAgency`, `ENV DB_SSL_CERT=cert`, `ENV DB_SSL_KEY=key`. 

### Audit logging
To enable audit logging, you must first supply a google application credentials file during the build stage (see above). Then set `AUDIT_ENABLED=1` and then supply the environment variables `PROJECT_ID` and `TOPIC_ID` with the details of the Google PubSub instance, and `GOOGLE_APPLICATION_CREDENTIALS` pointing to the (in-container) location of the aforementioned `application_default_credentials.json` file e.g.

```bash
docker run -p 80:80 -e AUDIT_ENABLED=1 -e PROJECT_ID=myprojectid -e TOPIC_ID=mytopicid -e GOOGLE_APPLICATION_CREDENTIALS=/app/application_default_credentials.json app
```

### Notes
If you need to make changes to how the application runs please observe the processes defined in the Dockerfile and entrypoint.sh. 

The local SQL setup is also defined in the int_db.sql file. 

The MySQL database is initialized with data from the .tsv files in the data folder, which are loaded into a table structured as defined in the init_db.sql script. 

The database configuration, including the host and credentials, can be set through environment variables. 

For Testing a data.supermin folder is also provided, this only has asthma terms to reduce container build time.

Unless configured differently, the API service will be exposed on localhost (0.0.0.0) port 80. A swagger is available on `http://0.0.0.0/docs`.


## Dependencies

The following Python packages are required (see `requirements.txt` for versions):

- fastapi
- uvicorn
- pydantic
- pandas==2.1.0
- SQLAlchemy==2.0.20
- gunicorn==21.2.0
- requests==2.31.0
- pymysql==1.1.0
- rapidfuzz==3.3.0

Install the necessary packages with the following command:
```
pip install -r requirements.txt
``` 

## Directory Structure

- `/app`: Main directory containing the Flask application.
  - `/data`: Directory containing OMOP data.
  - `/utils`: Directory containing utility functions and database initialization,  searching the OMOP database / OLS4 + UMLS endpoints, breaking up OMOP tables into chunks for GIT storage and extracting the supermin data. 

 
## API Endpoints

### `/search/omop/`

#### Method: `POST`

Searches for standard concepts in the OMOP vocabulary based on search terms provided.

**Request Body:**

- `search_term`: List of search terms to find the best match for (e.g., `["Asthma", "Heart"]`)
- `vocabulary_id`: Vocabulary ID to filter the results by (e.g., "snomed"). Optional.
- `concept_ancestor`: Extend Search via CONCEPT_ANCESTOR OMOP Table. Optional.
- `max_separation_descendant`: How many degrees of seperation to search downstream in CONCEPT_ANCESTOR. Optional.
- `max_separation_ancestor`: How many degrees of seperation to search upstream in CONCEPT_ANCESTOR. Optional.
- `concept_relationship`: Extend Search via CONCEPT_RELATIONSHIP OMOP Table. Optional.
- `concept_relationship_types`: List of CONCEPT_RELATIONSHIP types, i.e. ["Concept same_as to", "Mapped from", "Concept same_as from"]
- `concept_synonym`: Extend Search via CONCEPT_SYNONYM OMOP Table. Optional.
- `search_threshold`: Filter threshold (default is 80). Optional.

**Example Request:**

```json
{
  "search_terms": ["Heart"],
  "vocabulary_id": "",
  "concept_ancestor": "n",
  "max_separation_descendant": 0,
  "max_separation_ancestor": 1,
  "concept_synonym": "y",
  "concept_relationship": "y",
  "concept_relationship_types": ["Concept same_as to", "Mapped from", "Concept same_as from"],
  "search_threshold": 80
}
```
**Example response:**
```json
[
  {
    "search_term": "heart",
    "CONCEPT": [
      {
        "concept_name": "Heart structure",
        "concept_id": 4217142,
        "vocabulary_id": "SNOMED",
        "concept_code": "80891009",
        "concept_name_similarity_score": 50,
        "CONCEPT_SYNONYM": [
          {
            "concept_synonym_name": "Heart",
            "concept_synonym_name_similarity_score": 100
          },
          {
            "concept_synonym_name": "Heart structure (body structure)",
            "concept_synonym_name_similarity_score": 50
          },
          {
            "concept_synonym_name": "Cardiac structure",
            "concept_synonym_name_similarity_score": 27.27272727272727
          }
        ],
        "CONCEPT_ANCESTOR": [],
        "CONCEPT_RELATIONSHIP": [
          {
            "concept_name": "[SO]Heart NEC",
            "concept_id": 45479486,
            "vocabulary_id": "Read",
            "concept_code": "7N41z00",
            "relationship": {
              "concept_id_1": 4217142,
              "relationship_id": "Mapped from",
              "concept_id_2": 45479486
            }
          }
        ]
      },
      {
        "concept_name": "Heart",
        "concept_id": 19391039,
        "vocabulary_id": "MeSH",
        "concept_code": "D006321",
        "concept_name_similarity_score": 100,
        "CONCEPT_SYNONYM": [
          {
            "concept_synonym_name": "Hearts",
            "concept_synonym_name_similarity_score": 90.9090909090909
          }
        ],
        "CONCEPT_ANCESTOR": [],
        "CONCEPT_RELATIONSHIP": []
      },
      {
        "concept_name": "Heart",
        "concept_id": 21496060,
        "vocabulary_id": "LOINC",
        "concept_code": "LP191607-3",
        "concept_name_similarity_score": 100,
        "CONCEPT_SYNONYM": [
          {
            "concept_synonym_name": "Chest>Heart",
            "concept_synonym_name_similarity_score": 62.5
          }
        ],
        "CONCEPT_ANCESTOR": [],
        "CONCEPT_RELATIONSHIP": []
      },
      {
        "concept_name": "Heart",
        "concept_id": 36308337,
        "vocabulary_id": "LOINC",
        "concept_code": "LA21016-3",
        "concept_name_similarity_score": 100,
        "CONCEPT_SYNONYM": [],
        "CONCEPT_ANCESTOR": [],
        "CONCEPT_RELATIONSHIP": []
      },
      {
        "concept_name": "Heart",
        "concept_id": 40791756,
        "vocabulary_id": "LOINC",
        "concept_code": "LP7289-4",
        "concept_name_similarity_score": 100,
        "CONCEPT_SYNONYM": [],
        "CONCEPT_ANCESTOR": [],
        "CONCEPT_RELATIONSHIP": []
      }
    ]
  }
]
```

### `/search/umls`

#### Method: `POST`

Searches for standard concepts using the UMLS API based on search terms provided.
Please note, the advanced functionality supported by UMLS (relations, parents, children etc is not yet supported in this API)

**Request Body:**

- `search_term`: List of search terms to find the best match for (e.g., `["Asthma", "Heart"]`)
- `vocabulary_id`: Vocabulary ID to filter the results by (e.g., "snomed"). Optional.
- `search_threshold`: Filter threshold (default is 80). Optional.

**Example Request:**

```json
{
  "search_term": [
    "Asthma", 
    "Heart"
  ],
  "vocabulary_id": "MSH",
  "search_threshold": 80
}
```
**Example response:**
```json
[
  {
    "search_term": "Asthma",
    "matches": [
      {
        "concept_name": "Asthma",
        "concept_id": "C0004096",
        "vocabulary_id": "MTH",
        "concept_code": "C0004096",
        "concept_name_similarity_score": 100
      }
    ]
  },
  {
    "search_term": "Heart",
    "matches": [
      {
        "concept_name": "Heart",
        "concept_id": "C0018787",
        "vocabulary_id": "MTH",
        "concept_code": "C0018787",
        "concept_name_similarity_score": 100
      }
    ]
  }
]
```


### `/search/ols4`

#### Method: `POST`

Searches for standard concepts using the OLS4 API based on search terms provided.

**Request Body:**

- `search_term`: List of search terms to find the best match for (e.g., `["Asthma", "Heart"]`)
- `vocabulary_id`: Vocabulary ID to filter the results by (e.g., "snomed"). Optional.
- `search_threshold`: Filter threshold (default is 80). Optional.

**Example Request:**

```json
{
  "search_term": [
    "Asthma", 
    "Heart",
    "Bronchial hyperreactivity"
  ],
  "vocabulary_id": "snomed",
  "search_threshold": 80
}
```
**Example response:**
```json
[
  {
    "search_term": "Asthma",
    "matches": [
      {
        "concept_name": "Asthma",
        "concept_id": "SNOMED:195967001",
        "vocabulary_id": "SNOMED",
        "vocabulary_concept_code": "195967001",
        "concept_name_similarity_score": 100
      }
    ]
  },
  {
    "search_term": "Heart",
    "matches": []
  },
  {
    "search_term": "Bronchial hyperreactivity",
    "matches": []
  }
]
```

## License

This project is licensed under the GNU General Public License v3.0. See the `LICENSE` file for details.
