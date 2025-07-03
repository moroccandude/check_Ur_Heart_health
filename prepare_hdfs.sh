#!/bin/bash

# Wait for NameNode to be ready
# echo "Waiting for NameNode to be ready..."
# until hdfs dfsadmin -safemode get 2>&1 | grep -q "Safe mode is"; do
#   sleep 2
# done

# # Optionally, wait until out of safe mode
# until hdfs dfsadmin -safemode get 2>&1 | grep -q "Safe mode is OFF"; do
#   echo "Waiting for NameNode to leave safe mode..."
#   sleep 2
# done

# Ensure /user/heart_disease/raw exists
hdfs dfs -test -d /user/heart_disease/raw || hdfs dfs -mkdir -p /user/heart_disease/raw

# Ensure /warehouse exists
hdfs dfs -test -d /warehouse || hdfs dfs -mkdir -p /warehouse

# Set permissions for /warehouse
hdfs dfs -chmod 777 /warehouse

# Ensure /hbase exists
hdfs dfs -test -d /hbase || hdfs dfs -mkdir -p /hbase