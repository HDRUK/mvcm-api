
# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set database environment variables for auth (adjust as needed)
ENV DB_HOST=127.0.0.1
ENV DB_USER=OMOP_user
ENV DB_PORT=3306
ENV DB_PASSWORD=psw4MYSQL
ENV DB_NAME=OMOP
ENV DB_REBUILD=True
#ENV DB_SSL_ENABLED=False
#ENV DB_SSL_CA=
#ENV DB_SSL_CERT=
#ENV DB_SSL_KEY=

# Set Google audit vars
#ENV AUDIT_ENABLED=1
#ENV PROJECT_ID=myprojectid 
#ENV TOPIC_ID=mytopicid
#ENV GOOGLE_APPLICATION_CREDENTIALS=/app/application_default_credentials.json

# Set API environment variables for auth (adjust as needed)
ENV BASIC_AUTH_USERNAME=APIuser
ENV BASIC_AUTH_PASSWORD=psw4API

# Set UMLS key (adjust as needed)
ENV UMLS_APIKEY=e8ac4aea-f310-4bcd-aded-3c256465fd94

# Set environment variables for OMOP Data Model folder (adjust as needed)
ENV OMOP_DATA_FOLDER=data

# Copy the database initialization script, your Flask app, and requirements file
COPY app/ /app/

# Set the working directory
WORKDIR /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 80

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
