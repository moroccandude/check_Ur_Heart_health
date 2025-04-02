FROM apache/airflow:2.7.1

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    git \
    && apt-get clean

# # Add your user with matching UID/GID
# RUN groupadd -g 0 airflow && \
#     useradd -u 1000 -m -g airflow airflow

USER airflow
# Create required directories
RUN mkdir -p /opt/airflow/dags /opt/airflow/plugins /opt/airflow/logs /opt/airflow/data \
    && chown -R airflow:0 /opt/airflow  && chmod -R 775 /opt/airflow

# Install Python dependencies - specify your actual requirements
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt


