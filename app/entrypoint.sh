#!/bin/bash

if [ "$DB_REBUILD" = "True" ]; then

    echo "Building the database"

    # If DB_HOST is not set, install and start MySQL server locally
    if [ "$DB_HOST" = "127.0.0.1" ] || [ "$DB_HOST" = "localhost" ]; then

        echo "Using local database"
        service mysql start

        # Enable local file uploads in MySQL server configuration
        echo "Enabling local file upload support in MySQL"
        sed -i '/\[mysqld\]/a local-infile=1' /etc/mysql/mysql.conf.d/mysqld.cnf

        # Restart MySQL to apply changes
        service mysql restart

        # Check if the MySQL server is running
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

    else 
        echo "Using external database: $DB_HOST"
    fi

    # Set up MySQL

    # Increase MySQL timeouts
    mysql -h ${DB_HOST} -P ${DB_PORT} -u ${DB_USER} -p${DB_PASSWORD} -e "SET GLOBAL wait_timeout=28800; SET GLOBAL interactive_timeout=28800;"

    # Create DATABASE if it doesn't exist
    mysql -h ${DB_HOST} -P ${DB_PORT} -u ${DB_USER} -p${DB_PASSWORD} -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME};"

    # Run initial script
    echo "Running init_db.sql on: ${DB_NAME} at: ${DB_HOST}:${DB_PORT} as: ${DB_USER}"
    mysql -h ${DB_HOST} -P ${DB_PORT} -u ${DB_USER} -p${DB_PASSWORD} ${DB_NAME} < /app/init_db.sql

    # Function to process TSV files
    process_tsv() {
        table=$1
        file=$2

        full_path=$(realpath $file)

        echo "Importing $file into $table"
        mysql  --local-infile=1 -h ${DB_HOST} -P ${DB_PORT} -u ${DB_USER} -p${DB_PASSWORD} ${DB_NAME} -e "
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
    mysql -h ${DB_HOST} -P ${DB_PORT} -u ${DB_USER} -p${DB_PASSWORD} ${DB_NAME} -e "INSERT INTO STANDARD_CONCEPTS SELECT * FROM CONCEPT WHERE standard_concept = 'S';" 

else 
    echo "Not rebuilding the database"
fi

# Start Flask app with uvicorn --workers=2 --threads=4
uvicorn --workers 2 --host 0.0.0.0 --port 80 app:app
