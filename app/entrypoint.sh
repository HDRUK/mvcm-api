#!/bin/bash

if [ "$DB_REBUILD" = "True" ]; then

    echo "Building the database"

    # If DB_HOST is not set, install and start MySQL server locally
    if [ "$DB_HOST" = "127.0.0.1" ] || [ "$DB_HOST" = "localhost" ]; then

        echo "Using local database"

        echo "Starting MySQL"
        service mysql start

        # Check if the MySQL server is running
        echo "Checking if MySQL is alive"
        mysql_ready() {
            mysqladmin ping --silent
        }

        # Wait for MySQL to be ready
        while !(mysql_ready)
        do
            echo "Waiting for MySQL to start..."
            sleep 2
        done

        # Create a dedicated application user
        if [ "$DB_USER" != "root" ]; then
            echo "Creating new user: $DB_USER"
            mysql -u root -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';"
        else 
            echo "Using root user"    
        fi

        # Grant privileges
        echo "Granting privileges"    
        mysql -u root -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'%';"
        mysql -u root -e "GRANT SYSTEM_VARIABLES_ADMIN ON *.* TO '${DB_USER}'@'%';"

        # Increase MySQL timeouts
        echo "Increasing timeouts"
        mysql -u root  -e "SET GLOBAL wait_timeout=28800; SET GLOBAL interactive_timeout=28800;"

        # Allow file uploads
        echo "Allowing local infile"
        mysql -u root  -e "SET GLOBAL local_infile = 1;"

    else 
        echo "Using external database: $DB_HOST"
    fi

    # Create MySQL configuration file for secure credential storage
    echo "Creating MySQL config file ~/.my.cnf"

    echo "[client]" >> ~/.my.cnf
    echo "user=${DB_USER}" >> ~/.my.cnf
    echo "password=${DB_PASSWORD}" >> ~/.my.cnf
    echo "host=${DB_HOST}" >> ~/.my.cnf
    echo "port=${DB_PORT}" >> ~/.my.cnf 

    # Secure the MySQL config file by limiting permissions
    chmod 600 ~/.my.cnf  # Ensure only the owner can read/write the file

    # Set up MySQL

    # Create DATABASE if it doesn't exist
    mysql -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME};"

    # Run initial script
    echo "Running init_db.sql on: ${DB_NAME} at: ${DB_HOST}:${DB_PORT} as: ${DB_USER}"
    mysql ${DB_NAME} < /app/init_db.sql

    # Function to process TSV files
    process_tsv() {
        table=$1
        file=$2

        full_path=$(realpath $file)

        echo "Importing $file into $table"
        mysql --local-infile=1 ${DB_NAME} -e "
        LOAD DATA LOCAL INFILE '$full_path'
        INTO TABLE $table
        FIELDS TERMINATED BY '\t'
        LINES TERMINATED BY '\n'
        IGNORE 1 ROWS;
        "
    }
    export -f process_tsv

    # Process file import
    for table in CONCEPT CONCEPT_SYNONYM CONCEPT_ANCESTOR CONCEPT_RELATIONSHIP; 
        do
        echo "Processing $table files"
        for file in ./${OMOP_DATA_FOLDER}/$table/*.tsv; 
            do
            process_tsv $table $file
            done
        done

    echo "Data import completed."

    # Copy standard concepts across to STANDARD_CONCEPTS
    mysql ${DB_NAME} -e "INSERT INTO STANDARD_CONCEPTS SELECT * FROM CONCEPT WHERE standard_concept = 'S';" 

else 
    echo "Not rebuilding the database"

    
fi

# Start Flask app with uvicorn --workers=2 --threads=4
uvicorn --workers 2 --host 0.0.0.0 --port 80 app:app
