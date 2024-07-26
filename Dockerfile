
# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables for auth (adjust as needed)
ENV MYSQL_ROOT_PASSWORD=psw4MYSQL
ENV BASIC_AUTH_USERNAME=APIuser
ENV BASIC_AUTH_PASSWORD=psw4API

ENV UMLS_APIKEY=e8ac4aea-f310-4bcd-aded-3c256465fd94

# Copy the database initialization script, your Flask app, and requirements file
COPY app/ /app/

# Set the working directory
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 80

# Set environment variables for OMOP Data Model (adjust as needed)
ENV OMOP_DATA_FOLDER=data

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
