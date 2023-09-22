
from sqlalchemy import create_engine
from os import environ
# Configuration: MySQL Database Credentials
# Define environment variables for MySQL database connection. These variables are used to initialize the SQLAlchemy engine.
# Function to initialize MySQL database connection
# Define a function to initialize the MySQL database connection using SQLAlchemy. Global engine variable is set here.
# Set variables for MySQL credentials
# Configuration: MySQL Database Credentials
# Define environment variables for MySQL database connection. These variables are used to initialize the SQLAlchemy engine.


def initialize_mysql_connection():

    try:
        print("Initialize the MySQL connection based on the configuration.")
        MYSQL_HOST = environ.get('DB_HOST', '127.0.0.1')
        MYSQL_USER = environ.get('DB_USER', 'root')
        MYSQL_PASSWORD = environ.get('DB_PASSWORD', 'psw4MYSQL')
        MYSQL_DB = environ.get('DB_NAME', 'mydb')
        engine = create_engine(f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}')
    except Exception as e:
        ValueError(f"Failed to connect to MySQL: {e}")

    return engine