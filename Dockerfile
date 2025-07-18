
# Use Ubuntu Focal (20.04)
FROM python:3.11-slim-bookworm


# DEFAULT database environment variables (adjust as needed)
ENV DB_PORT=3306
# API environment variables for auth (adjust as needed)
ENV BASIC_AUTH_USERNAME=**********
ENV BASIC_AUTH_PASSWORD=**********

# Set UMLS key (adjust as needed)
ENV UMLS_APIKEY=**********


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
