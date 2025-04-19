import pandas as pd
from pyspark.sql import SparkSession
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.decorators import task, dag
from airflow import DAG
import subprocess
import os
import logging
import time
from datetime import timedelta, datetime
from typing import List, Optional, Dict, Any
import tempfile

# Configure logging properly
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('./logs/pipeline.log'),
        logging.StreamHandler()  # Also log to console
    ]
)

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Define function to create Spark session - will be called within tasks
def create_spark_session():
    """Create and return a Spark session."""
    logger.info("Creating Spark session")
    try:
        # Configure Spark with appropriate settings
        spark = (SparkSession.builder
                 .appName("heart_disease_analysis")
                 .config("spark.executor.memory", "2g")
                 .config("spark.driver.memory", "1g")
                 .config("spark.sql.shuffle.partitions", "10")
                 .getOrCreate())

        spark_context = spark.sparkContext
        app_id = spark_context.applicationId

        logger.info(f"Spark session created successfully with app ID: {app_id}")

        return spark
    except Exception as e:
        logger.error(f"Failed to create Spark session: {str(e)}", exc_info=True)
        raise

@dag(
    dag_id="hdfs_csv_processing_pipeline",
    description="Pipeline to process CSV files from HDFS",
    schedule_interval="@daily",
    start_date=datetime(2025, 4, 1),  # Set a specific start date
    catchup=False,
    default_args=default_args,
    tags=['hdfs', 'csv', 'processing'],
)
def full_pipeline():

    @task(task_id="initialize_spark")
    def initialize_spark_task() -> Dict[str, Any]:
        """Initialize Spark and return context information."""
        try:
            # Create a Spark session to verify it works
            spark = create_spark_session()
            app_id = spark.sparkContext.applicationId

            # Stop the session since we just need to check it works
            spark.stop()

            # Return only serializable information
            return {
                "app_id": app_id,
                "start_time": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to initialize Spark reportage: {str(e)}", exc_info=True)
            raise

    @task(task_id="create_hdfs_directories")
    def create_hdfs_directories(base_path: str) -> str:
        """Create necessary HDFS directories for the pipeline."""
        logger.info(f"Creating HDFS directories at {base_path}")
        try:
            # Create base directory
            cmd = ["docker", "exec", "namenode", "hdfs", "dfs", "-mkdir", "-p", base_path]
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Base directory created: {base_path}")

            # Create subdirectories for raw, processed, and archive
            subdirs = ["/raw", "/processed", "/archive"]
            for subdir in subdirs:
                full_path = f"{base_path}{subdir}"
                cmd = ["docker", "exec", "namenode", "hdfs", "dfs", "-mkdir", "-p", full_path]
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info(f"Created subdirectory: {full_path}")

            return base_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create HDFS directories: {e.stderr}", exc_info=True)
            raise

    @task(task_id="ingest_data_to_hdfs")
    def ingest_data_to_hdfs(local_data_path: str, hdfs_path: str) -> List[str]:
        """Ingest local CSV files to HDFS raw directory."""
        logger.info(f"Ingesting data from {local_data_path} to {hdfs_path}/raw")

        csv_files = [
            "coronary_artery_disease.csv",
            "heart_statlog_cleveland_hungary_final.csv",
            "heart_failure_clinical_records_dataset.csv"
        ]

        transferred_files = []

        try:
            # Safe mode retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    cmd = ["docker", "exec", "namenode", "hdfs", "dfsadmin", "-safemode", "leave"]
                    result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
                    logger.info("Successfully left HDFS safe mode")
                    break
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to leave safe mode (attempt {attempt + 1}/{max_retries}): {e.stderr}")
                    if attempt == max_retries - 1:
                        logger.error("Max retries reached for leaving safe mode")
                        raise ValueError("Failed to leave HDFS safe mode after multiple attempts")
                    time.sleep(10)  # Corrected indentation to be under except block

            # Process CSV files
            for csv_file in csv_files:
                local_file_path = os.path.join(local_data_path, csv_file)
                logger.info(f"current directory is : {os.getcwd()}")
                # Check if local file exists
                if not os.path.exists(local_file_path):
                    logger.warning(f"Local file not found: {local_file_path}")
                    continue

                # Put file to HDFS
                hdfs_target = f"{hdfs_path}/raw/{csv_file}"

                logger.info(f"path of target file is {hdfs_target}")  # Corrected f-string syntax
                cmd = [
                    "docker", "exec", "namenode", "hdfs", "dfs", "-put", "-f", local_file_path, hdfs_target
                ]  # Corrected command to include docker exec

                # Execute with proper error handling
                try:
                    result = subprocess.run(
                        cmd,
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    logger.info(f"Successfully transferred {csv_file} to HDFS")
                    transferred_files.append(hdfs_target)
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to transfer {csv_file}: {e.stderr}")
                except subprocess.TimeoutExpired:
                    logger.error(f"Timeout transferring {csv_file}")

            if not transferred_files:
                raise ValueError("No files were transferred to HDFS")

            return transferred_files

        except Exception as e:
            logger.error(f"Error during data ingestion: {str(e)}", exc_info=True)
            raise

    @task(task_id="read_hdfs_csv_files", multiple_outputs=True)
    def read_hdfs_csv_files(hdfs_files: List[str]) -> Dict[str, Any]:
        """Read CSV files from HDFS using Spark and return statistics (not DataFrames)."""
        logger.info(f"Reading {len(hdfs_files)} CSV files from HDFS")

        # Create a new Spark session within this task
        spark = create_spark_session()
        file_stats = {}

        try:
            for hdfs_file_path in hdfs_files:
                try:
                    # Check if file exists in HDFS
                    check_cmd = [
                        "docker", "exec", "namenode", "hdfs", "dfs",
                        "-test", "-e", hdfs_file_path
                    ]

                    file_exists = subprocess.run(
                        check_cmd,
                        capture_output=True,
                        text=True
                    ).returncode == 0

                    if not file_exists:
                        logger.warning(f"File does not exist in HDFS: {hdfs_file_path}")
                        continue

                    # Get file size for logging
                    size_cmd = [
                        "docker", "exec", "namenode", "hdfs", "dfs",
                        "-du", "-s", hdfs_file_path
                    ]

                    size_output = subprocess.run(
                        size_cmd,
                        capture_output=True,
                        text=True,
                        check=True
                    ).stdout.strip()

                    file_size = size_output.split()[0] if size_output else "unknown"

                    # Read the file with Spark
                    logger.info(f"Reading file: {hdfs_file_path} (size: {file_size} bytes)")

                    # Extract file name from path
                    file_name = os.path.basename(hdfs_file_path)
                    dataset_name = os.path.splitext(file_name)[0]

                    # Read with proper options
                    df = spark.read.option("header", "true") \
                        .option("inferSchema", "true") \
                        .option("mode", "DROPMALFORMED") \
                        .csv(hdfs_file_path)

                    row_count = df.count()
                    col_count = len(df.columns)

                    logger.info(f"Successfully read {dataset_name}: {row_count} rows, {col_count} columns")

                    # Store only statistics (not the DataFrame itself)
                    file_stats[dataset_name] = {
                        "path": hdfs_file_path,
                        "rows": row_count,
                        "columns": col_count,
                        "size_bytes": file_size,
                        "column_names": df.columns
                    }

                except Exception as e:
                    logger.error(f"Error reading file {hdfs_file_path}: {str(e)}", exc_info=True)

            if not file_stats:
                raise ValueError("No CSV files were successfully read from HDFS")

            # Important: Stop the Spark session when done with it
            spark.stop()

            # Return only serializable data (statistics, not DataFrames)
            return {
                "stats": file_stats,
                "total_files_read": len(file_stats)
            }

        except Exception as e:
            # Make sure to stop Spark session even if there's an error
            if spark:
                spark.stop()
            logger.error(f"Error in read_hdfs_csv_files: {str(e)}", exc_info=True)
            raise

    # Define task dependencies
    spark_info = initialize_spark_task()
    hdfs_base_path = create_hdfs_directories("/user/heart_disease")
    hdfs_files = ingest_data_to_hdfs("./data", hdfs_base_path)
    data_results = read_hdfs_csv_files(hdfs_files)

    # Set task dependencies
    spark_info >> hdfs_base_path >> hdfs_files >> data_results

# Instantiate the DAG
hdfs_csv_pipeline = full_pipeline()