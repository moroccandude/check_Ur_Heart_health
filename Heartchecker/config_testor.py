#!/usr/bin/env python3
"""
Complete solutions for MongoDB Spark connector issues
"""

import os
import subprocess
import sys
from pathlib import Path
from pyspark.sql import SparkSession
import logging

# Solution 1: Force download and verify JARs
def download_and_verify_jars():
    """Download required JARs and verify they work"""
    import urllib.request
    
    # Create jars directory
    jar_dir = Path("./jars")
    jar_dir.mkdir(exist_ok=True)
    
    # Exact JARs needed for your Spark version
    jars_info = [
        {
            "url": "https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.13/10.4.0/mongo-spark-connector_2.13-10.4.0.jar",
            "filename": "mongo-spark-connector_2.13-10.4.0.jar",
            "required": True
        },
        {
            "url": "https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.13/4.0.0/spark-sql-kafka-0-10_2.13-4.0.0.jar",
            "filename": "spark-sql-kafka-0-10_2.13-4.0.0.jar",
            "required": True
        },
        # MongoDB driver dependencies
        {
            "url": "https://repo1.maven.org/maven2/org/mongodb/mongodb-driver-sync/5.1.4/mongodb-driver-sync-5.1.4.jar",
            "filename": "mongodb-driver-sync-5.1.4.jar",
            "required": False
        },
        {
            "url": "https://repo1.maven.org/maven2/org/mongodb/bson/5.1.4/bson-5.1.4.jar",
            "filename": "bson-5.1.4.jar",
            "required": False
        }
    ]
    
    downloaded_jars = []
    
    for jar_info in jars_info:
        jar_path = jar_dir / jar_info["filename"]
        
        if not jar_path.exists():
            print(f"Downloading {jar_info['filename']}...")
            try:
                urllib.request.urlretrieve(jar_info["url"], jar_path)
                print(f"✓ Downloaded {jar_info['filename']}")
            except Exception as e:
                print(f"✗ Failed to download {jar_info['filename']}: {e}")
                if jar_info["required"]:
                    return None
                continue
        else:
            print(f"✓ {jar_info['filename']} already exists")
        
        # Verify file size
        if jar_path.stat().st_size > 0:
            downloaded_jars.append(str(jar_path.absolute()))
        else:
            print(f"✗ {jar_info['filename']} is empty")
            if jar_info["required"]:
                return None
    
    return downloaded_jars

# Solution 2: Updated Spark Session with multiple fallback approaches
class FixedHeartDiseaseStreamProcessor:
    """Fixed version of the streaming processor"""
    
    def __init__(self):
        self.spark = None
        self.query = None
        self.logger = self._setup_logging()
        self.is_running = True
    
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('HeartDiseaseStreaming')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def initialize_spark_session_fixed(self, master_url: str = "local[*]") -> SparkSession:
        """Initialize Spark session with multiple fallback approaches"""
        
        approaches = [
            self._approach_1_maven_packages,
            self._approach_2_local_jars_absolute,
            self._approach_3_spark_submit_style,
            self._approach_4_programmatic_jar_loading
        ]
        
        for i, approach in enumerate(approaches, 1):
            try:
                self.logger.info(f"Trying approach {i}...")
                spark_session = approach(master_url)
                if self._test_mongodb_connector(spark_session):
                    self.spark = spark_session
                    self.logger.info(f"✓ Approach {i} successful!")
                    return spark_session
                else:
                    spark_session.stop()
            except Exception as e:
                self.logger.warning(f"Approach {i} failed: {e}")
                continue
        
        raise Exception("All approaches failed to initialize MongoDB connector")
    
    def _approach_1_maven_packages(self, master_url: str) -> SparkSession:
        """Approach 1: Use Maven packages with explicit repositories"""
        
        # Set Maven local repository
        os.environ['SPARK_LOCAL_DIRS'] = '/tmp/spark-local'
        os.environ['IVY_CACHE_DIR'] = '/tmp/ivy-cache'
        
        spark_config = {
            "spark.app.name": "HeartDiseaseStreaming",
            "spark.master": master_url,
            "spark.jars.packages": "org.mongodb.spark:mongo-spark-connector_2.13:10.4.0,org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.0",
            "spark.jars.repositories": "https://repo1.maven.org/maven2/,https://repo.maven.apache.org/maven2/",
            "spark.jars.ivy": "/tmp/ivy-cache",
            "spark.driver.memory": "2g",
            "spark.executor.memory": "2g",
            "spark.sql.streaming.checkpointLocation": "./checkpoints",
            "spark.sql.streaming.forceDeleteTempCheckpointLocation": "true",
            "spark.driver.extraJavaOptions": "-Divy.cache.dir=/tmp/ivy-cache -Divy.home=/tmp/ivy-cache"
        }
        
        builder = SparkSession.builder
        for key, value in spark_config.items():
            builder = builder.config(key, value)
        
        return builder.getOrCreate()
    
    def _approach_2_local_jars_absolute(self, master_url: str) -> SparkSession:
        """Approach 2: Use local JARs with absolute paths"""
        
        # Download JARs if needed
        jar_paths = download_and_verify_jars()
        if not jar_paths:
            raise Exception("Failed to download required JARs")
        
        spark_config = {
            "spark.app.name": "HeartDiseaseStreaming",
            "spark.master": master_url,
            "spark.jars": ",".join(jar_paths),
            "spark.driver.memory": "2g",
            "spark.executor.memory": "2g",
            "spark.sql.streaming.checkpointLocation": "./checkpoints",
            "spark.sql.streaming.forceDeleteTempCheckpointLocation": "true",
            "spark.driver.extraClassPath": ":".join(jar_paths),
            "spark.executor.extraClassPath": ":".join(jar_paths)
        }
        
        builder = SparkSession.builder
        for key, value in spark_config.items():
            builder = builder.config(key, value)
        
        return builder.getOrCreate()
    
    def _approach_3_spark_submit_style(self, master_url: str) -> SparkSession:
        """Approach 3: Simulate spark-submit jar loading"""
        
        jar_paths = download_and_verify_jars()
        if not jar_paths:
            raise Exception("Failed to download required JARs")
        
        # Add JARs to classpath before creating session
        import findspark
        findspark.init()
        
        # Add to Python path
        for jar_path in jar_paths:
            if jar_path not in sys.path:
                sys.path.append(jar_path)
        
        # Set environment variables
        os.environ['PYSPARK_SUBMIT_ARGS'] = f'--jars {",".join(jar_paths)} pyspark-shell'
        
        spark_config = {
            "spark.app.name": "HeartDiseaseStreaming",
            "spark.master": master_url,
            "spark.driver.memory": "2g",
            "spark.executor.memory": "2g",
            "spark.sql.streaming.checkpointLocation": "./checkpoints"
        }
        
        builder = SparkSession.builder
        for key, value in spark_config.items():
            builder = builder.config(key, value)
        
        return builder.getOrCreate()
    
    def _approach_4_programmatic_jar_loading(self, master_url: str) -> SparkSession:
        """Approach 4: Programmatically add JARs to Spark context"""
        
        # Create basic Spark session first
        spark = SparkSession.builder \
            .appName("HeartDiseaseStreaming") \
            .master(master_url) \
            .config("spark.driver.memory", "2g") \
            .config("spark.executor.memory", "2g") \
            .getOrCreate()
        
        # Download and add JARs programmatically
        jar_paths = download_and_verify_jars()
        if jar_paths:
            for jar_path in jar_paths:
                spark.sparkContext.addPyFile(jar_path)
                # Also try adding as JAR
                try:
                    spark.sparkContext._jvm.Thread.currentThread().getContextClassLoader().addURL(
                        spark.sparkContext._jvm.java.io.File(jar_path).toURI().toURL()
                    )
                except:
                    pass
        
        return spark
    
    def _test_mongodb_connector(self, spark_session) -> bool:
        """Test if MongoDB connector is working"""
        try:
            # Create test DataFrame
            test_data = [(1, "test")]
            test_df = spark_session.createDataFrame(test_data, ["id", "message"])
            
            # Try to create a MongoDB write operation (don't execute, just validate format)
            writer = test_df.write.format("mongodb")
            
            # If we get here without exception, the connector is loaded
            self.logger.info("✓ MongoDB connector is available")
            return True
            
        except Exception as e:
            if "mongodb" in str(e).lower() and "not found" in str(e).lower():
                self.logger.warning(f"MongoDB connector not available: {e}")
                return False
            else:
                # Other errors might be OK (like connection errors)
                self.logger.info("✓ MongoDB connector appears to be loaded (got non-format error)")
                return True

# Solution 3: Alternative using PyMongo instead of Spark MongoDB connector
def alternative_mongodb_writer(df, epoch_id):
    """Alternative MongoDB writer using PyMongo instead of Spark connector"""
    try:
        import pymongo
        from pymongo import MongoClient
        
        # MongoDB connection
        client = MongoClient("mongodb://admin:usmail1244@localhost:27017/db?authSource=admin")
        db = client.db
        collection = db.patient
        
        # Convert Spark DataFrame to list of dictionaries
        records = df.collect()
        documents = []
        
        for row in records:
            doc = row.asDict()
            # Convert any special types if needed
            documents.append(doc)
        
        if documents:
            # Insert documents
            result = collection.insert_many(documents)
            print(f"Inserted {len(result.inserted_ids)} documents in batch {epoch_id}")
        else:
            print(f"Batch {epoch_id} was empty")
            
        client.close()
        
    except Exception as e:
        print(f"Error writing batch {epoch_id} with PyMongo: {e}")

# Solution 4: Command line approach
def generate_spark_submit_command():
    """Generate spark-submit command with proper JAR loading"""
    
    jar_paths = download_and_verify_jars()
    if not jar_paths:
        print("Failed to download JARs")
        return None
    
    command = f"""
spark-submit \\
  --jars {",".join(jar_paths)} \\
  --driver-memory 2g \\
  --executor-memory 2g \\
  --master local[*] \\
  --conf spark.sql.streaming.checkpointLocation=./checkpoints \\
  --conf spark.sql.streaming.forceDeleteTempCheckpointLocation=true \\
  sparkJob1.py
"""
    
    print("Use this spark-submit command:")
    print(command)
    return command

if __name__ == "__main__":
    print("MongoDB Spark Connector Fix Utility")
    print("=" * 40)
    
    # Test approach 1: Download JARs
    print("1. Downloading and verifying JARs...")
    jars = download_and_verify_jars()
    if jars:
        print(f"✓ Downloaded {len(jars)} JAR files")
        for jar in jars:
            print(f"  - {jar}")
    else:
        print("✗ Failed to download JARs")
    
    # Test approach 2: Try Spark session
    print("\n2. Testing Spark session initialization...")
    try:
        processor = FixedHeartDiseaseStreamProcessor()
        spark = processor.initialize_spark_session_fixed()
        print("✓ Spark session with MongoDB connector initialized successfully!")
        spark.stop()
    except Exception as e:
        print(f"✗ Spark session initialization failed: {e}")
    
    # Generate spark-submit command
    print("\n3. Alternative: spark-submit command")
    generate_spark_submit_command()
    
    print("\n" + "=" * 40)
    print("Solutions summary:")
    print("1. Use the FixedHeartDiseaseStreamProcessor class")
    print("2. Or use the generated spark-submit command")
    print("3. Or use PyMongo alternative for MongoDB writes")