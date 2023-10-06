
# Medical Vocabulary Concept Mapping Application Programming Interface (MVCM API) v1.1

## Introduction
 
This repository contains a Flask REST API application designed to facilitate the mapping of medical concepts to standardized terms using a MySQL database loaded with concepts from the OMOP Common Data Model, OLS4 and the NCBI Unified Medical Language System (UMLS). The application provides endpoints to interact with the concept data, offering functionalities such as searching for concepts based on textual queries.

## Dependencies

The following Python packages are installed as default (see `requirements.txt`):

- Flask==2.2.5
- flask-restx==1.1.0
- flask-httpauth==4.8.0
- pandas==2.1.0
- SQLAlchemy==2.0.20
- gunicorn==21.2.0
- requests==2.31.0
- pymysql==1.1.0
- rapidfuzz==3.3.0
- transformers==4.33.2
- torch==2.0.1



## Database Setup

The MySQL database is initialized with data from the `.tsv` files in the data folder, these are loaded into a table structured as defined in the `init_db.sql` script. The database configuration, including the host and credentials, can be set through environment variables.

To use an external database, set the `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` environment variables to the appropriate values for your database server before running the app. For Docker deployment, these variables can be set using the `-e` option with the `docker run` command. For example:

```
docker run -p 80:80 -e DB_HOST=your_db_host -e DB_USER=your_db_user -e DB_PASSWORD=your_db_password -e DB_NAME=your_db_name app
```

If `DB_HOST` is not set, the app will default to using a local MySQL database, and the `MYSQL_ROOT_PASSWORD` environment variable will be used as the root password for the local database.

### Directory Structure

- `/app`: Main directory containing the Flask application.
  - `app.py`: Main Flask application file where the API and its routes are defined.
  - `Credentials.py`: File where API credentials (username and password) are stored.
  - `/data`: Directory containing OMOP data.
  - `/routes`: Directory containing individual route files.
    - `CalculateBestMatch_ALL.py`: API route for searching all data source.
    - `CalculateBestMatch_OMOP.py`: API route for OMOP database search.
    - `CalculateBestMatch_OLS4.py`: API route for OLS4 database search.
    - `CalculateBestMatch_UMLS.py`: API route for UMLS database search.
    - `List_OMOP_Vocabularies.py`: API route for listing OMOP vocabularies.
    - `Unit_Test.py`: API route for executing unit tests.
  - `/tests`: Directory containing unit tests.
    - `testapp.py`: Unit test file.
  - `/utils`: Directory containing utility functions and database initialization.
    - `Basic_auth.py`: Basic authentication
    - `Bert_match.py`: Function for using pubmed bert for scoring
    - `calculate_best_OLS4_matches.py`: Function for getting OLS4 matches
    - `calculate_best_OMOP_matches.py`: Function for getting OMOP matches
    - `calculate_best_UMLS_matches.py`: Function for getting UMLS matches
    - `initialize_mysql_connection.py`: Initializes MySQL database connection.
    - `break_up_CONCEPT.py`: Simple function to splits OMOP concept table into chunks for effective storage in Git. 
    - `custom_test_result.py`: Utility functions for custom unit tests
    - `Hash_args.py`: Utility functions for hashing cached queries
    
## Testing

Unit tests are located in the `/tests` directory. To run the tests:

```
python -m unittest discover tests
```

## Docker Deployment

Build and deploy the application using Docker, following the instructions defined in the `Dockerfile` and `entrypoint.sh`. The application is containerized with all necessary files and scripts, and can be run with the following command:
```
docker build -t app .
docker run --memory=4g -p 80:80 app
```

## Single tool API Endpoints

### `/API/OMOP_search`
### `/API/OLS4_search`
### `/API/UMLS_search`

#### Method: `POST`

Searches for standard concepts in the vocabulary based on search terms provided.

**Request Body:**

- `search_term`: List of search terms to find the best match for (e.g., `["Asthma", "Heart"]`)
- `vocabulary_id`: Vocabulary ID to filter the results by (e.g., "snomed"). Optional.
- `search_threshold`: Filter threshold (default is 80). Optional.
- `search_tool`: tool to use, one of rapidFuzz or pubmedBERT. Optional

**Example Request:**

```json
{
  "search_term": ["Asthma", "Heart"],
  "vocabulary_id": "snomed",
  "search_tool": "rapidFuzz",
  "search_threshold": 80
}
```

### `/API/Global_search`

#### Method: `POST`

Searches for standard concepts using all three tools based on search terms provided.

**Request Body:**

- `search_term`: List of search terms to find the best match for (e.g., `["Asthma", "Heart"]`)
- `vocabulary_id`: Vocabulary ID to filter the results by (e.g., "snomed"). Optional.
- `search_threshold`: Filter threshold (default is 80). Optional.
- `search_tool`: tool to use, one of rapidFuzz or pubmedBERT. Optional
- `data_sources`: The list of data sources to search


**Example Request:**

```json
{
  "search_term": ["Asthma", "Heart"],
  "vocabulary_id": "snomed",
  "search_threshold": 80,
  "search_tool": "rapidFuzz"
  "data_sources": ["OMOP", "OLS4","UMLS"]
}
```

### `/API/List_OMOP_Vocabularies`

#### Method: `GET`

Lists all unique vocabularies in the CONCEPT table along with their frequencies.

**Example Request:**

GET `/API/List_OMOP_Vocabularies`


### `/API/Run_Tests`

#### Method: `GET`

Executes unit tests for the API and returns the status of the tests.

**Example Request:**

GET `/API/Run_Tests`

## Authentication

The API and SWAGGER both uses Basic Authentication. Set the username and password for these services in the `/app/Credentials.py` file.

**Response**: JSON array containing the best matches.

## License

This project is licensed under the GNU General Public License v3.0. See the `LICENSE` file for details.
