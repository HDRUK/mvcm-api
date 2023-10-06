#!/bin/bash

# If DB_HOST is not set, install and start MySQL server locally
if [ -z "$DB_HOST" ]; then
    echo "Using local database"
    apt-get update && apt-get install -y mariadb-server dialog

    # Start MySQL server manually
    mysqld_safe & 
    sleep 10

    # Set up MySQL
    mysql -u root -e "GRANT ALL ON *.* TO 'root'@'localhost' IDENTIFIED BY '${MYSQL_ROOT_PASSWORD}'; FLUSH PRIVILEGES;"
    
    # Increase MySQL timeouts
    mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "SET GLOBAL wait_timeout=28800; SET GLOBAL interactive_timeout=28800;"

    # Run initial script
    echo "Running init_db.sql"
    mysql -u root -p${MYSQL_ROOT_PASSWORD} < /app/init_db.sql

    # Count the number of .tsv files in the data directory
    file_count=$(ls -1 ./data/*.tsv 2>/dev/null | wc -l)
    echo $file_count "files to process"

    # Initialize a counter for the loop
    counter=1

    # Loop through each .tsv file in the data directory
    for file in ./data/*.tsv; do
        echo "Processing file $counter of $file_count: Importing $file"

        # Get the full path of the file
        full_path=$(realpath $file)

        # Run SQL command to load data from the .tsv file into the CONCEPT table
        mysql -u root -p${MYSQL_ROOT_PASSWORD} mydb -e "
        LOAD DATA INFILE '$full_path'
        INTO TABLE CONCEPT
        FIELDS TERMINATED BY '\t'
        LINES TERMINATED BY '\n'
        IGNORE 1 ROWS;
        "

        # Increment the counter
        ((counter++))
    done

    # Create Fulltext index and count rows
    echo "Indexing Database" 
    mysql -u root -p${MYSQL_ROOT_PASSWORD} mydb -e "
    CREATE FULLTEXT INDEX idx_concept_name ON CONCEPT(concept_name);
    SELECT 'Fulltext index created on concept_name' AS message;
    SELECT COUNT(*) AS 'Number of rows in CONCEPT table' FROM CONCEPT;
    "

else 
    echo "Using external database"
fi

pwd

# Start Flask app with Gunicorn --workers=2 --threads=4
gunicorn --timeout 3000 --workers=2 --threads=4 -b 0.0.0.0:80 app:app