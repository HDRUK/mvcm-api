
# Use Ubuntu Focal (20.04)
FROM python:3.11-slim


# DEFAULT database environment variables (adjust as needed)
ENV DB_PORT=3306
# API environment variables for auth (adjust as needed)
ENV BASIC_AUTH_USERNAME=APIuser
ENV BASIC_AUTH_PASSWORD=psw4API

# Set UMLS key (adjust as needed)
ENV UMLS_APIKEY=e8ac4aea-f310-4bcd-aded-3c256465fd94


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