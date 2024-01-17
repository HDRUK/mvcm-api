
# Medical Vocabulary Concept Mapping Application Programming Interface (MVCM API)

## Introduction
 
This repository contains a Flask REST API application designed to facilitate the mapping of medical concepts to standardized terms using a MySQL database loaded with concepts from the OMOP Common Data Model and OLS4. The application provides endpoints to interact with the concept data, offering functionalities such as searching for concepts based on textual queries.

## Setup

1. Install the required packages: `pip install -r requirements.txt`
2. Run the Flask application: `flask run`
 

## Dependencies

Ensure that the following Python packages are installed (see `requirements.txt` for versions):

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

## Database Setup

The MySQL database is initialized with data from the `.tsv` files in the `data` folder, these are loaded into a table structured as defined in the `init_db.sql` script. The database configuration, including the host and credentials, can be set through environment variables.

For Testing a `data.supermin` folder is also provided, this only has asthma terms to reduce container build time. 


To use an external database, set the `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` environment variables to the appropriate values for your database server before running the app. For Docker deployment, these variables can be set using the `-e` option with the `docker run` command. For example:

```
docker run -p 80:80 -e DB_HOST=your_db_host -e DB_USER=your_db_user -e DB_PASSWORD=your_db_password -e DB_NAME=your_db_name app
```

If `DB_HOST` is not set, the app will default to using a local MySQL database, and the `MYSQL_ROOT_PASSWORD` environment variable will be used as the root password for the local database.

## General App Structure and File Relationships

### Directory Structure

- `/app`: Main directory containing the Flask application.
  - `app.py`: Main Flask application file where the API and its routes are defined.
  - `/data`: Directory containing OMOP data.
  - `/utils`: Directory containing utility functions and database initialization.
    - `calculate_best_OLS4_matches.py`: Initializes MySQL database connection.
    - `break_up_CONCEPT.py`: Utility for breaking up OMOP tables into chunks for GIT storage.
    - `Extract_supermin_data.py`: Utility for extracting the asthma only data in the `data.supermin` folder.
    
## Docker Deployment

Build and deploy the application using Docker, following the instructions defined in the `Dockerfile` and `entrypoint.sh`. SQL setup is also defined in the `int_db.sql` file. The application is containerized with all necessary files and scripts, and can be run with the following command:
```
docker build -t app . ; docker run -p 80:80 app
```

## API Endpoints

### `/API/OMOP_search`

#### Method: `POST`

Searches for standard concepts in the OMOP vocabulary based on search terms provided.

**Request Body:**

- `search_term`: List of search terms to find the best match for (e.g., `["Asthma", "Heart"]`)
- `vocabulary_id`: Vocabulary ID to filter the results by (e.g., "snomed"). Optional.
- `concept_ancestor`: Extend Search via CONCEPT_ANCESTOR OMOP Table. Optional.
- `max_separation_descendant`: How many degrees of seperation to search downstream in CONCEPT_ANCESTOR. Optional.
- `max_separation_ancestor`: How many degrees of seperation to search upstream in CONCEPT_ANCESTOR. Optional.
- `concept_relationship`: Extend Search via CONCEPT_RELATIONSHIP OMOP Table. Optional.
- `concept_synonym`: Extend Search via CONCEPT_SYNONYM OMOP Table. Optional.
- `search_threshold`: Filter threshold (default is 80). Optional.

**Example Request:**

```json
{
  "search_terms": [
    "Asthma",
    "Heart"
  ],
  "vocabulary_id": "snomed",
  "concept_ancestor": "y",
  "max_separation_descendant": 1,
  "max_separation_ancestor": 1,
  "concept_relationship": "y",
  "concept_synonym": "y",
  "search_threshold": 80
}
```

### `/API/OLS4_search`

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
    "Heart"
  ],
  "vocabulary_id": "snomed",
  "search_threshold": 80
}
```

## License

This project is licensed under the GNU General Public License v3.0. See the `LICENSE` file for details.
