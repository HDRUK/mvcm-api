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

    # Function to process TSV files
    process_tsv() {
        table=$1
        file=$2

        full_path=$(realpath $file)

        echo "Importing $file into $table"
        mysql -u root -p${MYSQL_ROOT_PASSWORD} mydb -e "
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

else 
    echo "Using external database"
fi

# Start Flask app with uvicorn --workers=2 --threads=4
uvicorn --workers 2 --host 0.0.0.0 --port 80 app:app
