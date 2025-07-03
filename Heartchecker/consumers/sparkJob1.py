from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType
from pyspark.sql.functions import from_json, col, current_timestamp, when, isnan, isnull
import os
import logging
import sys
from pathlib import Path
import signal
import time
import subprocess
import pymongo
from pymongo import MongoClient
from datetime import datetime

class HeartDiseaseStreamProcessor:
    """Main class for processing heart disease streaming data with PyMongo"""
    
    def __init__(self):
        self.spark = None
        self.query = None
        self.mongo_client = None
        self.mongo_db = None
        self.mongo_collection = None
        self.logger = self._setup_logging()
        self.is_running = True
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self) -> logging.Logger:
        """Configure comprehensive logging"""
        logger = logging.getLogger('HeartDiseaseStreaming')
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
        )
        simple_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(simple_formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        
        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "heart_disease_streaming.log")
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        
        return logger
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
        self.is_running = False
        if self.query and self.query.isActive:
            self.query.stop()
        if self.mongo_client:
            self.mongo_client.close()
    
    @staticmethod
    def create_heart_disease_schema() -> StructType:
        return StructType([
            StructField("age", IntegerType(), True),
            StructField("sex", IntegerType(), True),
            StructField("cp", IntegerType(), True),
            StructField("trestbps", IntegerType(), True),
            StructField("chol", IntegerType(), True),
            StructField("fbs", IntegerType(), True),
            StructField("restecg", IntegerType(), True),
            StructField("thalach", IntegerType(), True),
            StructField("exang", IntegerType(), True),
            StructField("oldpeak", FloatType(), True),
            StructField("slope", IntegerType(), True),
            StructField("ca", IntegerType(), True),
            StructField("thal", IntegerType(), True),
            StructField("target", IntegerType(), True)
        ])
   
    def initialize_spark_session(self, master_url: str = "local[*]") -> SparkSession:
        """Initialize Spark session without MongoDB connector"""
        try:
            self.logger.info("Initializing Spark session...")
            
            # Create necessary directories
            checkpoint_dir = Path("checkpoints")
            checkpoint_dir.mkdir(exist_ok=True)
            
            spark_config = {
                # Core settings
                "spark.app.name": "HeartDiseaseStreaming",
                "spark.master": master_url or "local[*]",
                
                # Only include Kafka connector JAR - removed MongoDB connector
                "spark.jars.packages": "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0",
                
                # Memory and compute settings
                "spark.driver.memory": "2g",
                "spark.executor.memory": "2g",
                "spark.executor.cores": "2",
                "spark.default.parallelism": "4",
                
                # Network configuration
                "spark.driver.host": "localhost",
                "spark.driver.bindAddress": "0.0.0.0",
                
                # Streaming settings
                "spark.sql.streaming.checkpointLocation": str(checkpoint_dir),
                "spark.sql.streaming.forceDeleteTempCheckpointLocation": "true",
                "spark.streaming.stopGracefullyOnShutdown": "true",
                
                # Additional settings for optimization
                "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
                "spark.sql.adaptive.enabled": "true",
                "spark.sql.adaptive.coalescePartitions.enabled": "true"
            }
            
            # Build Spark session
            builder = SparkSession.builder
            for key, value in spark_config.items():
                builder = builder.config(key, value)
            
            self.spark = builder.getOrCreate()
            
            # Reduce log verbosity
            self.spark.sparkContext.setLogLevel("WARN")
            
            # Initialize MongoDB connection
            self._initialize_mongodb_connection()
            
            # Log session info
            self.logger.info(f"Spark session initialized successfully")
            self.logger.info(f"Application ID: {self.spark.sparkContext.applicationId}")
            self.logger.info(f"Spark version: {self.spark.version}")
            self.logger.info(f"Master URL: {master_url}")

            return self.spark
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Spark session: {str(e)}")
            raise
    
    def _initialize_mongodb_connection(self):
        """Initialize PyMongo connection"""
        try:
            self.logger.info("Initializing MongoDB connection...")
            
            # Get MongoDB configuration
            mongodb_uri = os.getenv("MONGODB_URI", "mongodb://admin:usmail1244@localhost:27017/?authSource=admin")
            mongodb_database = os.getenv("MONGODB_DATABASE", "db")
            mongodb_collection = os.getenv("MONGODB_COLLECTION", "patient")
            
            # Create MongoDB client with connection pool settings
            self.mongo_client = MongoClient(
                mongodb_uri,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=20000
            )
            
            # Test connection
            self.mongo_client.admin.command('ping')
            self.logger.info("MongoDB connection successful")
            
            # Get database and collection references
            self.mongo_db = self.mongo_client[mongodb_database]
            self.mongo_collection = self.mongo_db[mongodb_collection]
            
            # Create indexes for better performance
            self._create_indexes()
            
            self.logger.info(f"Connected to MongoDB - Database: {mongodb_database}, Collection: {mongodb_collection}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MongoDB connection: {e}")
            raise
    
    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            # Create index on timestamp fields for time-based queries
            self.mongo_collection.create_index([("processing_time", 1)])
            self.mongo_collection.create_index([("kafka_timestamp", 1)])
            
            # Create compound index for common queries
            self.mongo_collection.create_index([("target", 1), ("age", 1)])
            
            self.logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to create indexes (may already exist): {e}")
    
    def create_kafka_consumer(self, bootstrap_servers: str, topic: str):
        """Create Kafka streaming DataFrame"""
        try:
            if not bootstrap_servers or not topic:
                raise ValueError("Bootstrap servers and topic must be provided")
                
            self.logger.info(f"Creating Kafka consumer for {bootstrap_servers}, topic: {topic}")
            
            # Kafka consumer configuration
            kafka_options = {
                "kafka.bootstrap.servers": bootstrap_servers,
                "subscribe": topic,
                "startingOffsets": "earliest",
                "failOnDataLoss": "false",
                "kafka.security.protocol": "PLAINTEXT",
                "fetchOffset.numRetries": "10",
                "kafka.request.timeout.ms": "60000",
                "kafka.session.timeout.ms": "60000",
                "kafka.heartbeat.interval.ms": "20000",
                "maxOffsetsPerTrigger": "1000",
                "kafka.max.poll.interval.ms": "300000"
            }
            
            # Create streaming DataFrame with retry logic
            max_retries = 5
            retry_interval = 10
            
            for attempt in range(max_retries):
                try:
                    kafka_df = self.spark.readStream.format("kafka")
                    
                    for key, value in kafka_options.items():
                        kafka_df = kafka_df.option(key, value)
                    
                    return kafka_df.load()
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_interval} seconds...")
                    time.sleep(retry_interval)
            
        except Exception as e:
            self.logger.error(f"Failed to create Kafka consumer: {str(e)}")
            raise

    def process_streaming_data(self, kafka_df):
        """Process and transform streaming data"""
        try:
            self.logger.info("Setting up data processing pipeline...")
            
            schema = self.create_heart_disease_schema()
            
            # Parse JSON messages and add metadata
            processed_df = kafka_df \
                .selectExpr("CAST(value AS STRING) as json_data", 
                           "timestamp as kafka_timestamp", 
                           "topic", "partition", "offset") \
                .select(
                    from_json(col("json_data"), schema).alias("heart_data"),
                    col("kafka_timestamp"),
                    col("topic"),
                    col("partition"), 
                    col("offset"),
                    current_timestamp().alias("processing_time")
                ) \
                .select("heart_data.*", "kafka_timestamp", "topic", "partition", "offset", "processing_time") \
                .filter(col("heart_data").isNotNull())
            
            # Add data quality checks
            quality_checked_df = processed_df \
                .withColumn("age_valid", when(col("age").between(0, 120), True).otherwise(False)) \
                .withColumn("heart_rate_valid", when(col("thalach").between(60, 220), True).otherwise(False)) \
                .withColumn("has_nulls", 
                           when(col("age").isNull() | col("sex").isNull() | col("target").isNull(), True).otherwise(False))
            
            self.logger.info("Data processing pipeline configured")
            return quality_checked_df
            
        except Exception as e:
            self.logger.error(f"Error in data processing: {str(e)}")
            raise

    def write_to_mongodb_pymongo(self, df, epoch_id):
        """Write DataFrame to MongoDB using PyMongo"""
        try:
            self.logger.info(f"Writing batch {epoch_id} to MongoDB using PyMongo")
            
            # Check if DataFrame is empty
            record_count = df.count()
            if record_count == 0:
                self.logger.info(f"Batch {epoch_id} is empty, skipping MongoDB write")
                return
            
            self.logger.info(f"Batch {epoch_id} contains {record_count} records")
            
            # Convert DataFrame to list of dictionaries
            records = []
            for row in df.collect():
                record = row.asDict()
                
                # Convert timestamp objects to datetime for MongoDB
                if 'kafka_timestamp' in record and record['kafka_timestamp']:
                    record['kafka_timestamp'] = record['kafka_timestamp']
                if 'processing_time' in record and record['processing_time']:
                    record['processing_time'] = record['processing_time']
                
                # Add batch metadata
                record['batch_id'] = epoch_id
                record['inserted_at'] = datetime.now()
                
                # Handle None values
                record = {k: v for k, v in record.items() if v is not None}
                
                records.append(record)
            
            if records:
                # Insert documents in bulk for better performance
                try:
                    result = self.mongo_collection.insert_many(records, ordered=False)
                    inserted_count = len(result.inserted_ids)
                    self.logger.info(f"Successfully inserted {inserted_count} records from batch {epoch_id}")
                    
                    # Log some statistics
                    if epoch_id % 10 == 0:  # Every 10th batch
                        total_docs = self.mongo_collection.count_documents({})
                        self.logger.info(f"Total documents in collection: {total_docs}")
                        
                except pymongo.errors.BulkWriteError as bwe:
                    # Handle partial insertion errors
                    inserted_count = bwe.details.get('nInserted', 0)
                    self.logger.warning(f"Bulk write partially failed. Inserted: {inserted_count}, Errors: {len(bwe.details.get('writeErrors', []))}")
                    
                    # Log first few errors for debugging
                    for error in bwe.details.get('writeErrors', [])[:3]:
                        self.logger.error(f"Write error: {error}")
                        
            else:
                self.logger.warning(f"No valid records to insert from batch {epoch_id}")
                
        except Exception as e:
            self.logger.error(f"Error writing batch {epoch_id} to MongoDB: {str(e)}")
            import traceback
            self.logger.error(f"Full error trace: {traceback.format_exc()}")
            # Don't raise to avoid stopping the stream
    
    def start_streaming(self, processed_df, output_mode: str = "console"):
        """Start the streaming query"""
        try:
            self.logger.info(f"Starting streaming query with output mode: {output_mode}")
            
            if output_mode == "console":
                query = processed_df \
                    .writeStream \
                    .outputMode("append") \
                    .format("console") \
                    .option("truncate", False) \
                    .option("numRows", 20) \
                    .trigger(processingTime='5 seconds') \
                    .start()
        
            elif output_mode == "memory":
                query = processed_df \
                    .writeStream \
                    .outputMode("append") \
                    .format("memory") \
                    .queryName("heart_disease_stream") \
                    .trigger(processingTime='5 seconds') \
                    .start()
        
            elif output_mode == "mongodb":
                # Use foreachBatch with PyMongo
                query = processed_df \
                    .writeStream \
                    .outputMode("append") \
                    .foreachBatch(self.write_to_mongodb_pymongo) \
                    .option("checkpointLocation", "./checkpoints/mongodb") \
                    .trigger(processingTime='5 seconds') \
                    .start()
            
            else:
                raise ValueError(f"Unsupported output mode: {output_mode}")
        
            self.query = query
            self.logger.info("Streaming query started successfully")
            return query
    
        except Exception as e:
            self.logger.error(f"Failed to start streaming query: {str(e)}")
            raise
    
    def monitor_stream(self):
        """Monitor streaming query and log progress"""
        if not self.query:
            self.logger.error("No active query to monitor")
            return
        
        self.logger.info("Starting stream monitoring...")
        
        try:
            while self.is_running and self.query.isActive:
                # Get query progress
                progress = self.query.lastProgress
                if progress:
                    batch_id = progress.get('batchId', 'N/A')
                    input_rows = progress.get('inputRowsPerSecond', 0)
                    processing_time = progress.get('durationMs', {}).get('triggerExecution', 0)
                    
                    self.logger.info(f"Batch {batch_id}: Input rate: {input_rows:.2f} rows/sec, "
                                   f"Processing time: {processing_time}ms")
                
                # Log MongoDB collection stats periodically
                if hasattr(self, 'mongo_collection') and self.mongo_collection:
                    try:
                        doc_count = self.mongo_collection.count_documents({})
                        self.logger.info(f"Total documents in MongoDB: {doc_count}")
                    except Exception as e:
                        self.logger.warning(f"Failed to get MongoDB stats: {e}")
                
                time.sleep(10)
                
        except Exception as e:
            self.logger.error(f"Error in stream monitoring: {str(e)}")
        
        self.logger.info("Stream monitoring stopped")
    
    def stop_streaming(self):
        """Stop streaming query and close connections"""
        self.logger.info("Stopping streaming application...")
        
        if self.query:
            try:
                self.query.stop()
                self.logger.info("Streaming query stopped")
            except Exception as e:
                self.logger.warning(f"Error stopping query: {e}")
        
        if self.mongo_client:
            try:
                self.mongo_client.close()
                self.logger.info("MongoDB connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing MongoDB connection: {e}")
        
        if self.spark:
            try:
                self.spark.stop()
                self.logger.info("Spark session stopped")
            except Exception as e:
                self.logger.warning(f"Error stopping Spark session: {e}")
        
        self.logger.info("Application shutdown complete")
    
    def run(self):
        """Main execution method"""
        try:
            self.logger.info("="*60)
            self.logger.info("Starting Heart Disease Streaming Application with PyMongo")
            self.logger.info("="*60)
            
            # Get configuration
            bootstrap_servers = os.getenv('bootstrap_servers')
            topic = os.getenv('topic')
            master_url = os.getenv('SPARK_MASTER_URL')
            output_mode = os.getenv('OUTPUT_MODE', 'console')
            
            self.logger.info("Configuration details:")
            self.logger.info(f"Bootstrap Servers: {bootstrap_servers}")
            self.logger.info(f"Topic: {topic}")
            self.logger.info(f"Master URL: {master_url}")
            self.logger.info(f"Output Mode: {output_mode}")
            
            # Initialize components
            self.initialize_spark_session(master_url)
            kafka_df = self.create_kafka_consumer(bootstrap_servers, topic)
            processed_df = self.process_streaming_data(kafka_df)
            
            # Start streaming
            self.start_streaming(processed_df, output_mode)
            
            self.logger.info("Application started successfully!")
            self.logger.info("Press Ctrl+C to stop the application")
            
            # Monitor the stream
            self.monitor_stream()
            
            # Wait for termination
            if self.query:
                self.query.awaitTermination()
            
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Application failed: {str(e)}", exc_info=True)
            sys.exit(1)
        finally:
            self.stop_streaming()

def main():
    """Entry point for the application"""
    try:
        # Load environment variables
        try:
            from dotenv import load_dotenv
            if not load_dotenv():
                print("Warning: .env file not found")
        except ImportError:
            print("Warning: python-dotenv not installed, using system environment variables")
            
        # Verify required environment variables
        required_vars = ['bootstrap_servers', 'topic']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
        # Create and run the streaming processor
        processor = HeartDiseaseStreamProcessor()
        processor.run()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()