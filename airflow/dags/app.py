import pandas as pd
from pyspark.sql import SparkSession
import airflow.operators.python_operator as PythonOperator
from airflow import DAG
import subprocess
import os
import logging
import time
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s -', datefmt='%d-%b-%y %H:%M:%S',filemode='w',filename='./logs/log.log')





def inital_spark()->SparkSession:
    """ This function is used to create a spark session """
    logging.getLogger(__name__)
    logging.info("Creating spark session")
    session=SparkSession.builder.appName("heart_disease").getOrCreate()
    return session

def reader(path:str,session:SparkSession)->any:
     """ This function is used to read csv files """
     logging.info(f"Reading csv file from {path}")
     df=session.read.csv(path,header=True,inferSchema=True)
     return df

def ingest_row(path:str)->None:
    """ This function is used to ingest data from csv files  in hdfs"""
    logging.info(f"Ingesting data from {path} to hdfs")
    try:
        subprocess.run(["sudo","mv",path,"hadoop/namenode_data"],check=True)
        subprocess.run(["docker","exec","-i","hadoop-namenode","hdfs", "dfs", "-mkdir", "-p", "/user/heart_disease/row"],check=True)
        time.sleep(4)
        subprocess.run(["docker","exec","-i","hadoop-namenode","hdfs", "dfs", "-put", "hadoop/dfs/name/data/", "/user/hadoop/heart_disease/row"],check=True)
        logging.info("Data ingested successfully")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error occured while ingesting data {e}")
    

def main():
    session=inital_spark()
    ingest_row("/home/usmail/Desktop/health_care/heart_disease/heart_disease/data/")
    df1=reader("/home/usmail/Desktop/health_care/heart_disease/heart_disease/data/coronary artery disease.csv",session)    
    df2=reader("/home/usmail/Desktop/health_care/heart_disease/heart_disease/data/heart_statlog_cleveland_hungary_final.csv",session)
    df3=reader("/home/usmail/Desktop/health_care/heart_disease/heart_disease/data/heart_failure_clinical_records_dataset.csv",session) 
    df1_df2 = df1.join(df2, on=["age","sex"], how='inner')  # You can use 'outer', 'left', or 'right' depending on your need
    df3 = df1_df2.join(df3, on=["age","sex"], how='inner')  # Again, use the join type you prefer   
    #  rename columns
    df3=df3.withColumnRenamed("target","cleavland_target")
    df1.printSchema()

