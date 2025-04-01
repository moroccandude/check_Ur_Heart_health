FROM apache/airflow:2.7.1

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    git \
    && apt-get clean

# Add your user with matching UID/GID
RUN useradd  -m airflow
USER airflow
# Create required directories
RUN mkdir -p /opt/airflow/dags /opt/airflow/plugins /opt/airflow/logs /opt/airflow/data \
    && chown -R airflow:0 /opt/airflow  && chmod -R 775 /opt/airflow

# Install Python dependencies - specify your actual requirements
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Switch to the airflow user for running the services
# Note: Using airflow user instead of custom user is recommended
# USER airflow

# The db init and user creation will be handled by the airflow-init service
# in your docker-compose file, not here