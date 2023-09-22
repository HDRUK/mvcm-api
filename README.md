
# Medical Vocabulary Concept Mapping Application Programming Interface (MVCM API)

## Introduction
 
This repository contains a Flask REST API application designed to facilitate the mapping of medical concepts to standardized terms using a MySQL database loaded with concepts from the OMOP Common Data Model and OLS4. The application provides endpoints to interact with the concept data, offering functionalities such as searching for concepts based on textual queries.
 

## Dependencies

Ensure that the following Python packages are installed (see `requirements.txt` for versions):

- numpy==1.25.2
- Flask==2.2.5
- flask-restx==1.1.0
- pandas==2.1.0
- SQLAlchemy==2.0.20
- scikit-learn==1.3.0
- docker==6.1.3
- pyopenssl==23.2.0
- gunicorn==21.2.0
- tqdm==4.66.1
- requests==2.31.0
- pymysql==1.1.0
- rapidfuzz==3.3.0
- python-Levenshtein==0.21.1

Install the necessary packages with the following command:
```
pip install -r requirements.txt
```

## Database Setup

The MySQL database is initialized with data from the `CONCEPT.tsv` file, loaded into a table structured as defined in the `init_db.sql` script. The database configuration, including the host and credentials, can be set through environment variables.

To use an external database, set the `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` environment variables to the appropriate values for your database server before running the app. For Docker deployment, these variables can be set using the `-e` option with the `docker run` command. For example:

```
docker run -p 80:80 -e DB_HOST=your_db_host -e DB_USER=your_db_user -e DB_PASSWORD=your_db_password -e DB_NAME=your_db_name app
```

If `DB_HOST` is not set, the app will default to using a local MySQL database, and the `MYSQL_ROOT_PASSWORD` environment variable will be used as the root password for the local database.

## API

The Flask REST API, defined in `app.py`, facilitates interactions with the concept data stored in the MySQL database. The API employs various Python packages for functionalities such as fuzzy matching of query strings to concept names.

## Docker Deployment

Build and deploy the application using Docker, following the instructions defined in the `Dockerfile` and `entrypoint.sh`. The application is containerized with all necessary files and scripts, and can be run with the following command:
```
docker build -t app .
docker run -p 80:80 app
```

## License

This project is licensed under the GNU General Public License v3.0. See the `LICENSE` file for details.


## API Endpoints

### General Information

All API requests are made to `http://<hostname>:<port>` where `<hostname>` and `<port>` are the IP address and port where the Docker container is running.

#### Common Headers

- `Content-Type: application/json`

### `/CalculateBestMatch_OMOP`

**Method**: `POST`

**Description**: Calculate the best matches for a list of search terms using OMOP concepts.

**Request Body**:

```json
{
  "search_term": ["Asthma", "Heart"],
  "vocabulary_id": "snomed",
  "search_threshold": 80
}
```

**Response**: JSON array containing the best matches.

### `/calculate_best_match_OLS4`

**Method**: `POST`

**Description**: Calculate the best OLS4 matches for a list of search terms.

**Request Body**:

```json
{
  "search_term": ["Asthma", "Heart"],
  "vocabulary_id": "snomed",
  "search_threshold": 80
}
```

**Response**: JSON array containing the best matches.
