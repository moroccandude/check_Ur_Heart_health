#!/bin/bash

# Set error handling
set -e
set -o pipefail

echo "=== Starting Alternative Hive Table Creation Script ==="
echo "$(date) - Script started"

# Function to execute Hive queries
execute_hive_query() {
    local query="$1"
    local description="$2"
    echo "Executing: $description"
    echo "Query: $query"
    
    beeline -u jdbc:hive2://localhost:10000 -e "$query"
    if [ $? -eq 0 ]; then
        echo "✓ Success: $description"
    else
        echo "✗ Failed: $description"
        return 1
    fi
}

# Set Hive execution engine to avoid MapReduce issues
echo "=== Setting Hive Configuration ==="
config_query="
SET hive.execution.engine=tez;
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;"
execute_hive_query "$config_query" "Setting Hive configuration"

# Create external tables
echo "=== Creating External Tables ==="

# Create heart_failure_clinical_records_dataset table
heart_failure_query="
CREATE EXTERNAL TABLE IF NOT EXISTS heart_failure_clinical_records_dataset (
    age INT,
    anaemia INT,
    creatinine_phosphokinase INT,
    diabetes INT,
    ejection_fraction INT,
    high_blood_pressure INT,
    platelets BIGINT,
    serum_creatinine DOUBLE,
    serum_sodium DOUBLE,
    sex STRING,
    smoking INT,
    time_ INT,
    DEATH_EVENT INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ',' 
LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION 'hdfs://namenode:9000/user/heart_disease/raw';"

execute_hive_query "$heart_failure_query" "Creating heart_failure_clinical_records_dataset table"

# Create coronary artery disease table (raw data)
coronary_raw_query="
CREATE EXTERNAL TABLE IF NOT EXISTS coronary_artery_disease (
    age INT,
    sex INT,
    cp INT,
    trestbps INT,
    chol INT,
    fbs INT,
    restecg INT,
    thalach INT,
    exang INT,
    oldpeak FLOAT,
    slope INT,
    ca INT,
    thal INT,
    target INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ',' 
LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION 'hdfs://namenode:9000/user/heart_disease/raw';"

execute_hive_query "$coronary_raw_query" "Creating coronary_artery_disease_raw table"

heart_statlog_query="
CREATE TABLE IF NOT EXISTS heart_statlog_cleveland_hungary_final (
  age INT,
  sex INT,
  chest_pain_type INT,
  resting_bp_s INT,
  cholesterol INT,
  fasting_blood_sugar INT,
  resting_ecg INT,
  max_heart_rate INT,
  exercise_angina INT,
  oldpeak FLOAT,
  st_slope INT,
  target INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ',' 
LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION 'hdfs://namenode:9000/user/heart_disease/raw';"

execute_hive_query "$heart_statlog_query" "Creating heart_statlog_cleveland_hungary_final"

# Create managed table with all description columns from the start
echo "=== Creating Enhanced Coronary Artery Disease Table ==="
coronary_enhanced_query="
CREATE TABLE IF NOT EXISTS coronary_artery_disease (
    age INT,
    sex INT,
    cp INT,
    trestbps INT,
    chol INT,
    fbs INT,
    restecg INT,
    thalach INT,
    exang INT,
    oldpeak FLOAT,
    slope INT,
    ca INT,
    thal INT,
    target INT,
    cp_description STRING,
    restecg_description STRING,
    slope_description STRING,
    thal_description STRING,
    chol_state STRING,
    age_group STRING,
    sex_description STRING,
    target_description STRING
)
STORED AS TEXTFILE;"

execute_hive_query "$coronary_enhanced_query" "Creating enhanced coronary_artery_disease table"
#!/bin/bash
# mapreduce-fix-alternatives.sh
# Multiple approaches to fix MapReduce job failures in Hive

set -e

echo "=== MapReduce Job Failure Fix - Multiple Approaches ==="
echo "$(date) - Starting fixes"



# APPROACH 1: Change Execution Engine and Settings
echo "=== APPROACH 1: Changing Hive Configuration ==="

config_fix_query="
SET hive.execution.engine=mr;
SET mapreduce.framework.name=local;
SET hive.exec.mode.local.auto=true;
SET hive.exec.mode.local.auto.inputbytes.max=134217728;
SET hive.exec.mode.local.auto.input.files.max=10;
SET mapreduce.job.maps=1;
SET mapreduce.job.reduces=1;"

execute_hive_query "$config_fix_query" "Setting local execution mode"

# APPROACH 2: Use CTAS (Create Table As Select) instead of INSERT
echo "=== APPROACH 2: Using CTAS Instead of INSERT ==="

# Drop the existing enhanced table if it exists
drop_table_query="DROP TABLE IF EXISTS coronary_artery_disease;"
execute_hive_query "$drop_table_query" "Dropping existing enhanced table"

# Create the enhanced table using CTAS - this often avoids MapReduce issues
ctas_query="
CREATE TABLE coronary_artery_disease AS
SELECT 
    age,
    sex,
    cp,
    trestbps,
    chol,
    fbs,
    restecg,
    thalach,
    exang,
    oldpeak,
    slope,
    ca,
    thal,
    target,
    CASE
        WHEN cp=1 THEN 'typical angina'
        WHEN cp=2 THEN 'atypical angina'
        WHEN cp=3 THEN 'non-anginal pain'
        WHEN cp=4 THEN 'asymptomatic'
        ELSE 'unknown'
    END as cp_description,
    CASE 
        WHEN restecg = 0 THEN 'normal'
        WHEN restecg = 1 THEN 'ST-T wave'
        WHEN restecg = 2 THEN 'probable ventricular hypertrophy'
        ELSE 'unknown'
    END AS restecg_description,
    CASE
        WHEN slope = 1 THEN 'upsloping'
        WHEN slope = 2 THEN 'flat'
        WHEN slope = 3 THEN 'downsloping'
        ELSE 'unknown'
    END AS slope_description,
    CASE
        WHEN thal = 0 THEN 'normal'
        WHEN thal = 1 THEN 'fixed defect'
        WHEN thal = 2 THEN 'reversable defect'
        ELSE 'unknown'
    END AS thal_description,
    CASE
        WHEN chol < 200 THEN 'normal'
        WHEN chol BETWEEN 200 AND 239 THEN 'borderline high'
        WHEN chol >= 240 THEN 'high'
        ELSE 'unknown'
    END AS chol_state,
    CASE
        WHEN age BETWEEN 18 AND 35 THEN 'young adult'
        WHEN age BETWEEN 36 AND 55 THEN 'middle-aged adult'
        WHEN age BETWEEN 56 AND 75 THEN 'older adult'
        WHEN age >= 76 THEN 'elderly'
        ELSE 'unknown'
    END AS age_group,
    CASE
        WHEN sex = 0 THEN 'female'
        WHEN sex = 1 THEN 'male'
        ELSE 'unknown'
    END AS sex_description,
    CASE
        WHEN target = 0 THEN 'no heart disease'
        WHEN target = 1 THEN 'heart disease present'
        ELSE 'unknown'
    END AS target_description
FROM coronary_artery_disease_raw;"

if execute_hive_query "$ctas_query" "Creating enhanced table using CTAS"; then
    echo "✓ CTAS approach worked!"
    CTAS_SUCCESS=true
else
    echo "✗ CTAS approach failed, trying next approach"
    CTAS_SUCCESS=false
fi

# APPROACH 3: Step-by-step table creation (if CTAS failed)
if [ "$CTAS_SUCCESS" = false ]; then
    echo "=== APPROACH 3: Step-by-Step Table Creation ==="
    
    # Create table structure first
    create_structure_query="
    CREATE TABLE IF NOT EXISTS coronary_artery_disease_enhanced (
        age INT,
        sex INT,
        cp INT,
        trestbps INT,
        chol INT,
        fbs INT,
        restecg INT,
        thalach INT,
        exang INT,
        oldpeak FLOAT,
        slope INT,
        ca INT,
        thal INT,
        target INT,
        cp_description STRING,
        restecg_description STRING,
        slope_description STRING,
        thal_description STRING,
        chol_state STRING,
        age_group STRING,
        sex_description STRING,
        target_description STRING
    )
    ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
    STORED AS TEXTFILE;"
    
    execute_hive_query "$create_structure_query" "Creating table structure"
    
    # Try inserting data in smaller batches
    echo "Trying batch insert approach..."
    
    batch_insert_query="
    INSERT INTO TABLE coronary_artery_disease_enhanced
    SELECT 
        age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal, target,
        'unknown' as cp_description,
        'unknown' as restecg_description,
        'unknown' as slope_description,
        'unknown' as thal_description,
        'unknown' as chol_state,
        'unknown' as age_group,
        'unknown' as sex_description,
        'unknown' as target_description
    FROM coronary_artery_disease_raw 
    LIMIT 10;"
    
    execute_hive_query "$batch_insert_query" "Inserting basic data first"
fi

# APPROACH 4: Use Views Instead of Tables (No MapReduce needed)
echo "=== APPROACH 4: Creating Views Instead ==="

view_query="
CREATE OR REPLACE VIEW coronary_artery_disease_view AS
SELECT 
    age,
    sex,
    cp,
    trestbps,
    chol,
    fbs,
    restecg,
    thalach,
    exang,
    oldpeak,
    slope,
    ca,
    thal,
    target,
    CASE
        WHEN cp=1 THEN 'typical angina'
        WHEN cp=2 THEN 'atypical angina'
        WHEN cp=3 THEN 'non-anginal pain'
        WHEN cp=4 THEN 'asymptomatic'
        ELSE 'unknown'
    END as cp_description,
    CASE 
        WHEN restecg = 0 THEN 'normal'
        WHEN restecg = 1 THEN 'ST-T wave'
        WHEN restecg = 2 THEN 'probable ventricular hypertrophy'
        ELSE 'unknown'
    END AS restecg_description,
    CASE
        WHEN slope = 1 THEN 'upsloping'
        WHEN slope = 2 THEN 'flat'
        WHEN slope = 3 THEN 'downsloping'
        ELSE 'unknown'
    END AS slope_description,
    CASE
        WHEN thal = 0 THEN 'normal'
        WHEN thal = 1 THEN 'fixed defect'
        WHEN thal = 2 THEN 'reversable defect'
        ELSE 'unknown'
    END AS thal_description,
    CASE
        WHEN chol < 200 THEN 'normal'
        WHEN chol BETWEEN 200 AND 239 THEN 'borderline high'
        WHEN chol >= 240 THEN 'high'
        ELSE 'unknown'
    END AS chol_state,
    CASE
        WHEN age BETWEEN 18 AND 35 THEN 'young adult'
        WHEN age BETWEEN 36 AND 55 THEN 'middle-aged adult'
        WHEN age BETWEEN 56 AND 75 THEN 'older adult'
        WHEN age >= 76 THEN 'elderly'
        ELSE 'unknown'
    END AS age_group,
    CASE
        WHEN sex = 0 THEN 'female'
        WHEN sex = 1 THEN 'male'
        ELSE 'unknown'
    END AS sex_description,
    CASE
        WHEN target = 0 THEN 'no heart disease'
        WHEN target = 1 THEN 'heart disease present'
        ELSE 'unknown'
    END AS target_description
FROM coronary_artery_disease_raw;"

execute_hive_query "$view_query" "Creating comprehensive view"

# Test the view
test_view_query="SELECT * FROM coronary_artery_disease_view LIMIT 5;"
execute_hive_query "$test_view_query" "Testing the view"

# APPROACH 5: Direct Dimension Table Creation from Raw Data
echo "=== APPROACH 5: Creating Dimension Tables Directly ==="

# CP Dimension
cp_dim_direct="
CREATE TABLE IF NOT EXISTS cp_dimension AS
SELECT DISTINCT 
    cp as cp_id,
    CASE
        WHEN cp=1 THEN 'typical angina'
        WHEN cp=2 THEN 'atypical angina'
        WHEN cp=3 THEN 'non-anginal pain'
        WHEN cp=4 THEN 'asymptomatic'
        ELSE 'unknown'
    END as cp_description
FROM coronary_artery_disease_raw;"

execute_hive_query "$cp_dim_direct" "Creating CP dimension directly"

# Similar approach for other dimensions
restecg_dim_direct="
CREATE TABLE IF NOT EXISTS restecg_dimension AS
SELECT DISTINCT 
    restecg as restecg_id,
    CASE 
        WHEN restecg = 0 THEN 'normal'
        WHEN restecg = 1 THEN 'ST-T wave'
        WHEN restecg = 2 THEN 'probable ventricular hypertrophy'
        ELSE 'unknown'
    END AS restecg_description
FROM coronary_artery_disease_raw;"

execute_hive_query "$restecg_dim_direct" "Creating RESTECG dimension directly"

# Fact table with simple structure
fact_simple="
CREATE TABLE IF NOT EXISTS heart_disease_fact_simple AS
SELECT 
    ROW_NUMBER() OVER (ORDER BY age) as record_id,
    age,
    sex,
    cp,
    trestbps,
    chol,
    fbs,
    restecg,
    thalach,
    exang,
    oldpeak,
    slope,
    ca,
    thal,
    target
FROM coronary_artery_disease_raw;"

execute_hive_query "$fact_simple" "Creating simple fact table"

echo "=== Testing Final Results ==="
execute_hive_query "SHOW TABLES;" "Showing all created tables"
execute_hive_query "SELECT COUNT(*) FROM coronary_artery_disease_view;" "Counting records in view"

echo "=== Summary ==="
echo "If CTAS worked: Use 'coronary_artery_disease' table"
echo "If CTAS failed: Use 'coronary_artery_disease_view' view"
echo "Dimension tables: cp_dimension, restecg_dimension"
echo "Fact table: heart_disease_fact_simple"
echo ""
echo "The view approach is often the most reliable for complex transformations"
echo "as it doesn't require MapReduce jobs for data movement."